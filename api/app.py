"""FastAPI application for VaultSentinel."""

import time
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
import time
import uuid
import logging
from typing import List, Optional, Dict, Any

from .config import settings, get_redacted_config
from .clients import get_mcp_client
from .scanner_routes import router as scanner_router
from .scanner_models import init_db, get_db

def create_app():
    """Create and configure the FastAPI application."""
    return app

app = FastAPI(
    title="VaultSentinel",
    description="Agentic system for continuous secrets shielding",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Will be configurable
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

# Include scanner routes
app.include_router(scanner_router)

# Initialize scanner database
init_db()

# Mount static files
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

# Setup logging
logger = logging.getLogger(__name__)

# Startup time for uptime calculation
startup_time = time.time()


class FindingUpdate(BaseModel):
    """Model for updating finding status."""
    status: Optional[str] = None
    notes: Optional[str] = None


class MCPTestRequest(BaseModel):
    """Model for MCP test request."""
    text: str
    context: dict = {}


class MCPChatMessage(BaseModel):
    """Model for MCP chat message."""
    role: str  # "user", "assistant", "system"
    content: str


class MCPChatRequest(BaseModel):
    """Model for MCP chat request."""
    messages: List[MCPChatMessage]
    provider: Optional[str] = "gemini"  # "gemini" or "openai"


class MCPHealthResponse(BaseModel):
    """Model for MCP health response."""
    status: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class MCPChatResponse(BaseModel):
    """Model for MCP chat response."""
    status: str
    result: Optional[Any] = None  # Can be dict, list, or any other type
    request_id: Optional[str] = None
    mcp_meta: Optional[Dict[str, Any]] = None


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    uptime = time.time() - startup_time
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime": uptime,
        "config": get_redacted_config()
    }


@app.post("/mcp/test")
async def test_mcp_classification(request: MCPTestRequest):
    """Test MCP classification endpoint."""
    try:
        # Get MCP client
        mcp_client = get_mcp_client()
        
        # Build conversation for classification
        conversation = {
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a security expert analyzing potential secrets. Respond with JSON only."
                },
                {
                    "role": "user", 
                    "content": f"""
Analyze this potential secret and determine if it's a real security risk.

Text: "{request.text}"
Context: {request.context}

Consider:
1. Is this a real secret or a placeholder/example?
2. What's the confidence level (0.0-1.0)?
3. What type of secret is it?

Respond with JSON:
{{
    "is_secret": true/false,
    "confidence": 0.0-1.0,
    "secret_type": "aws_access_key|github_token|etc",
    "reasoning": "brief explanation"
}}
"""
                }
            ],
            "model": "gpt-3.5-turbo",
            "temperature": 0.1,
            "max_tokens": 200
        }
        
        # Call MCP client
        response = await mcp_client.chat(conversation)
        
        # Return response with MCP request ID
        return {
            "mcp_request_id": response.get("request_id"),
            "mcp_status": response.get("status"),
            "result": response.get("result"),
            "mcp_meta": response.get("mcp_meta", {}),
            "client_stats": mcp_client.get_stats()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "mcp_request_id": None,
            "mcp_status": "error"
        }


@app.get("/findings")
async def get_findings(
    status: Optional[str] = Query(None, description="Filter by status"),
    kind: Optional[str] = Query(None, description="Filter by secret kind"),
    since: Optional[str] = Query(None, description="Filter by date (ISO format)"),
    repo: Optional[str] = Query(None, description="Filter by repository"),
    limit: int = Query(100, description="Limit results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Get findings with optional filters."""
    query = db.query(Finding)
    
    if status:
        query = query.filter(Finding.status == status)
    if kind:
        query = query.filter(Finding.secret_kind == kind)
    if since:
        try:
            since_date = datetime.fromisoformat(since.replace('Z', '+00:00'))
            query = query.filter(Finding.first_seen_at >= since_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    if repo:
        query = query.filter(Finding.repo == repo)
    
    total = query.count()
    findings = query.order_by(desc(Finding.first_seen_at)).offset(offset).limit(limit).all()
    
    return {
        "findings": [finding.to_dict() for finding in findings],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.patch("/findings/{finding_id}")
async def update_finding(
    finding_id: str,
    update: FindingUpdate,
    db: Session = Depends(get_db)
):
    """Update finding status and notes."""
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    if update.status:
        if update.status not in ["NEW", "ACKNOWLEDGED", "RESOLVED"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        finding.status = update.status
    
    if update.notes is not None:
        finding.notes = update.notes
    
    finding.last_seen_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Finding updated successfully"}


@app.get("/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """Get basic metrics."""
    # Count by status
    status_counts = db.query(
        Finding.status, 
        func.count(Finding.id)
    ).group_by(Finding.status).all()
    
    # Count by kind
    kind_counts = db.query(
        Finding.secret_kind,
        func.count(Finding.id)
    ).group_by(Finding.secret_kind).all()
    
    # Last scan time
    last_scan = db.query(ScanRun).order_by(desc(ScanRun.started_at)).first()
    
    # MTTA (Mean Time To Acknowledge) - simplified
    acknowledged_findings = db.query(Finding).filter(
        Finding.status == "ACKNOWLEDGED"
    ).all()
    
    mtta = None
    if acknowledged_findings:
        total_time = sum([
            (f.last_seen_at - f.first_seen_at).total_seconds()
            for f in acknowledged_findings
            if f.last_seen_at and f.first_seen_at
        ])
        mtta = total_time / len(acknowledged_findings) if acknowledged_findings else None
    
    return {
        "counts_by_status": dict(status_counts),
        "counts_by_kind": dict(kind_counts),
        "last_scan_at": last_scan.started_at.isoformat() if last_scan else None,
        "mtta_seconds": mtta,
        "total_findings": db.query(Finding).count()
    }


# MCP Proxy Routes
@app.get("/api/mcp/health", response_model=MCPHealthResponse)
async def mcp_health(request: Request):
    """MCP health check proxy endpoint."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Get MCP client
        mcp_client = get_mcp_client()
        
        # Call MCP health endpoint
        response = await mcp_client._request("GET", "/health")
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Log request
        logger.info(
            "MCP health check - status: %s, latency: %dms, request_id: %s",
            "ok", latency_ms, request_id
        )
        
        return MCPHealthResponse(
            status="ok",
            details=response,
            request_id=request_id
        )
        
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "MCP health check failed - error: %s, latency: %dms, request_id: %s",
            str(e), latency_ms, request_id
        )
        
        return MCPHealthResponse(
            status="error",
            details={"error": str(e)},
            request_id=request_id
        )


@app.post("/api/mcp/chat", response_model=MCPChatResponse)
async def mcp_chat(request: MCPChatRequest, http_request: Request):
    """MCP chat proxy endpoint."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Get MCP client
        mcp_client = get_mcp_client()
        
        # Convert to MCP format
        conversation = {
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "provider": request.provider
        }
        
        # Call MCP chat endpoint
        response = await mcp_client.chat(conversation)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Log request (redacted)
        logger.info(
            "MCP chat request - status: %s, latency: %dms, request_id: %s",
            response.get("status", "unknown"), latency_ms, request_id
        )
        
        return MCPChatResponse(
            status=response.get("status", "error"),
            result=response.get("result"),
            request_id=response.get("request_id", request_id),
            mcp_meta=response.get("mcp_meta", {})
        )
        
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "MCP chat request failed - error: %s, latency: %dms, request_id: %s",
            str(e), latency_ms, request_id
        )
        
        return MCPChatResponse(
            status="error",
            result={"error": str(e)},
            request_id=request_id,
            mcp_meta={"error": str(e)}
        )


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Simple dashboard."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>VaultSentinel Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
            .findings { margin-top: 20px; }
            .finding { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
            .status-new { border-left: 4px solid #ff6b6b; }
            .status-acknowledged { border-left: 4px solid #ffa726; }
            .status-resolved { border-left: 4px solid #66bb6a; }
            .confidence { font-weight: bold; }
            .high { color: #d32f2f; }
            .medium { color: #f57c00; }
            .low { color: #388e3c; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>VaultSentinel Dashboard</h1>
            <p>Continuous secrets shielding for your repositories</p>
            <p><a href="/docs">API Documentation</a> | <a href="/metrics">Metrics</a></p>
        </div>
        <div class="findings">
            <h2>Recent Findings</h2>
            <div id="findings-list">Loading...</div>
        </div>
        
        <script>
            async function loadFindings() {
                try {
                    const response = await fetch('/findings?limit=20');
                    const data = await response.json();
                    const findingsList = document.getElementById('findings-list');
                    
                    if (data.findings.length === 0) {
                        findingsList.innerHTML = '<p>No findings detected.</p>';
                        return;
                    }
                    
                    findingsList.innerHTML = data.findings.map(finding => `
                        <div class="finding status-${finding.status.toLowerCase()}">
                            <h3>${finding.secret_kind} in ${finding.file_path}</h3>
                            <p><strong>Repository:</strong> ${finding.repo}</p>
                            <p><strong>Commit:</strong> ${finding.commit_sha}</p>
                            <p><strong>Preview:</strong> ${finding.masked_preview}</p>
                            <p><strong>Confidence:</strong> 
                                <span class="confidence ${finding.confidence > 0.8 ? 'high' : finding.confidence > 0.5 ? 'medium' : 'low'}">
                                    ${(finding.confidence * 100).toFixed(1)}%
                                </span>
                            </p>
                            <p><strong>Status:</strong> ${finding.status}</p>
                            <p><strong>First Seen:</strong> ${new Date(finding.first_seen_at).toLocaleString()}</p>
                        </div>
                    `).join('');
                } catch (error) {
                    document.getElementById('findings-list').innerHTML = '<p>Error loading findings.</p>';
                }
            }
            
            loadFindings();
            setInterval(loadFindings, 30000); // Refresh every 30 seconds
        </script>
    </body>
    </html>
    """
