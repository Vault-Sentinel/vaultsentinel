"""FastAPI application for VaultSentinel."""

import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from core.config import get_config
from core.storage import FindingRepository, ScanRunRepository
from core.models import Finding, FindingStatus, SecretKind
from core.agent import VaultSentinelAgent

# Global agent instance
_agent: Optional[VaultSentinelAgent] = None

def get_agent() -> VaultSentinelAgent:
    """Get the global agent instance."""
    global _agent
    if _agent is None:
        _agent = VaultSentinelAgent()
    return _agent

def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="VaultSentinel",
        description="Agentic system for continuous secrets shielding",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files for React build
    import os
    from pathlib import Path
    
    # Get the absolute path to the dist directory
    current_dir = Path(__file__).parent.parent.parent
    dist_path = current_dir / "packages" / "ui" / "dist"
    
    if dist_path.exists():
        # Mount assets directory to serve CSS and JS files
        assets_path = dist_path / "assets"
        if assets_path.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
            print(f"Frontend assets mounted from: {assets_path}")
        else:
            print(f"Warning: Assets directory not found at {assets_path}")
    else:
        print(f"Warning: Frontend dist directory not found at {dist_path}")
    
    # Startup time for uptime calculation
    startup_time = time.time()
    
    class FindingUpdate(BaseModel):
        """Model for updating finding status."""
        status: Optional[FindingStatus] = None
        notes: Optional[str] = None
    
    @app.get("/healthz")
    async def health_check():
        """Health check endpoint."""
        print("Health check requested")
        uptime = time.time() - startup_time
        agent = get_agent()
        status = agent.get_status()
        
        return {
            "status": "ok",
            "version": "1.0.0",
            "uptime": uptime,
            "agent_status": status
        }
    
    @app.get("/findings")
    async def get_findings(
        status: Optional[FindingStatus] = Query(None, description="Filter by status"),
        kind: Optional[SecretKind] = Query(None, description="Filter by secret kind"),
        since: Optional[str] = Query(None, description="Filter by date (ISO format)"),
        repo: Optional[str] = Query(None, description="Filter by repository"),
        limit: int = Query(100, description="Limit results"),
        offset: int = Query(0, description="Offset for pagination")
    ):
        """Get findings with optional filters."""
        agent = get_agent()
        finding_repo = agent.finding_repo
        
        findings = finding_repo.get_all(
            limit=limit,
            offset=offset,
            status=status,
            kind=kind,
            repo=repo
        )
        
        return {
            "findings": [finding.to_dict() for finding in findings],
            "total": len(findings),
            "limit": limit,
            "offset": offset
        }
    
    @app.patch("/findings/{finding_id}")
    async def update_finding(
        finding_id: str,
        update: FindingUpdate
    ):
        """Update finding status and notes."""
        agent = get_agent()
        finding_repo = agent.finding_repo
        
        finding = finding_repo.get_by_id(finding_id)
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        
        if update.status:
            finding.status = update.status
        
        if update.notes is not None:
            finding.notes = update.notes
        
        finding.last_seen_at = datetime.utcnow()
        finding_repo.update(finding)
        
        return {"message": "Finding updated successfully"}
    
    @app.get("/metrics")
    async def get_metrics():
        """Get basic metrics."""
        agent = get_agent()
        finding_repo = agent.finding_repo
        scan_run_repo = agent.scan_run_repo
        
        # Get finding metrics
        finding_metrics = finding_repo.get_metrics()
        
        # Get last scan time
        last_scan = scan_run_repo.get_latest()
        
        return {
            "findings": finding_metrics,
            "last_scan_at": last_scan.started_at.isoformat() if last_scan else None,
            "agent_status": agent.get_status()
        }
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Serve React frontend."""
        try:
            html_path = dist_path / "index.html"
            with open(html_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>VaultSentinel Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>VaultSentinel Dashboard</h1>
                    <p>Continuous secrets shielding for your repositories</p>
                    <p><a href="/docs">API Documentation</a> | <a href="/metrics">Metrics</a></p>
                    <p><strong>Note:</strong> React frontend not built. Run <code>cd packages/ui && npm run build</code> to build the frontend.</p>
                </div>
            </body>
            </html>
            """
    
    return app
