"""API routes for the VaultSentinel scanner."""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from .scanner_models import Scan, Finding, AggregateDaily, get_db
from scanner.scan_engine import ScanEngine
from detection.mcp_classifier import MCPClassifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["scanner"])


# Request/Response Models
from pydantic import BaseModel

class ScanRequest(BaseModel):
    """Scan request model."""
    repo_url: str
    branch: str = "main"
    mode: str = "full"
    include: List[str] = ["**/*.py", "**/*.js", "**/*.env", "**/*.yml"]
    exclude: List[str] = ["**/node_modules/**", "**/dist/**", ".git/**"]
    max_files: int = 2000
    max_bytes_per_file: int = 200000
    timeout_sec: int = 120


class ScanResponse(BaseModel):
    """Scan response model."""
    scan_id: str
    status: str
    message: str


class ScanStatusResponse(BaseModel):
    """Scan status response model."""
    status: str
    progress: int
    message: Optional[str] = None


class FindingResponse(BaseModel):
    """Finding response model."""
    id: str
    type: str
    severity: str
    confidence: float
    repo: str
    file_path: str
    start_line: int
    end_line: int
    description: str
    remediation_text: str
    created_at: datetime


class RemediationRequest(BaseModel):
    """Remediation request model."""
    finding_ids: List[str]
    repo_url: str
    branch: str = "main"


class RemediationResponse(BaseModel):
    """Remediation response model."""
    unified_diff: str
    pr_title: str
    pr_body: str


class ClassifyRequest(BaseModel):
    """MCP classify request model."""
    text: str


class ClassifyResponse(BaseModel):
    """MCP classify response model."""
    is_secret: bool
    is_vulnerability: bool
    type: str
    severity: str
    confidence: float
    remediation: str
    reasoning: str


# Scan Management Routes
@router.post("/scans", response_model=ScanResponse)
async def create_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new scan job."""
    try:
        # Validate repository URL
        if not request.repo_url.startswith("https://github.com/"):
            raise HTTPException(status_code=400, detail="Only GitHub repositories are supported")
        
        # Create scan record
        scan = Scan(
            repo_url=request.repo_url,
            branch=request.branch,
            mode=request.mode,
            status="queued"
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        # Start scan in background
        scan_config = {
            "repo_url": request.repo_url,
            "branch": request.branch,
            "mode": request.mode,
            "include": request.include,
            "exclude": request.exclude,
            "max_files": request.max_files,
            "max_bytes_per_file": request.max_bytes_per_file,
            "timeout_sec": request.timeout_sec
        }
        
        background_tasks.add_task(execute_scan_task, str(scan.id), scan_config)
        
        return ScanResponse(
            scan_id=str(scan.id),
            status="queued",
            message="Scan job created successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to create scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scans/{scan_id}/status", response_model=ScanStatusResponse)
async def get_scan_status(scan_id: str, db: Session = Depends(get_db)):
    """Get scan status."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Calculate progress
    progress = 0
    if scan.status == "queued":
        progress = 0
    elif scan.status == "running":
        if scan.total_files > 0:
            progress = min(90, int((scan.scanned_files / scan.total_files) * 90))
        else:
            progress = 50
    elif scan.status == "done":
        progress = 100
    elif scan.status == "error":
        progress = 0
    
    return ScanStatusResponse(
        status=scan.status,
        progress=progress,
        message=scan.error_message if scan.status == "error" else None
    )


@router.get("/scans/{scan_id}/report")
async def get_scan_report(scan_id: str, db: Session = Depends(get_db)):
    """Get scan report as HTML."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan.status != "done":
        raise HTTPException(status_code=400, detail="Scan not completed yet")
    
    # Get findings
    findings = db.query(Finding).filter(Finding.scan_id == scan_id).all()
    
    # Render HTML report
    from .report_renderer import render_scan_report
    html_content = render_scan_report(scan, findings)
    
    return HTMLResponse(content=html_content)


# Findings Routes
@router.get("/findings", response_model=List[FindingResponse])
async def get_findings(
    repo: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    finding_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get findings with filters."""
    query = db.query(Finding)
    
    if repo:
        query = query.filter(Finding.repo == repo)
    if severity:
        query = query.filter(Finding.severity == severity)
    if finding_type:
        query = query.filter(Finding.type == finding_type)
    
    findings = query.order_by(desc(Finding.created_at)).offset(offset).limit(limit).all()
    
    return [
        FindingResponse(
            id=str(finding.id),
            type=finding.type,
            severity=finding.severity,
            confidence=finding.confidence,
            repo=finding.repo,
            file_path=finding.file_path,
            start_line=finding.start_line,
            end_line=finding.end_line,
            description=finding.description,
            remediation_text=finding.remediation_text,
            created_at=finding.created_at
        )
        for finding in findings
    ]


@router.get("/findings/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: str, db: Session = Depends(get_db)):
    """Get finding details."""
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    return FindingResponse(
        id=str(finding.id),
        type=finding.type,
        severity=finding.severity,
        confidence=finding.confidence,
        repo=finding.repo,
        file_path=finding.file_path,
        start_line=finding.start_line,
        end_line=finding.end_line,
        description=finding.description,
        remediation_text=finding.remediation_text,
        created_at=finding.created_at
    )


# Remediation Routes
@router.post("/remediate", response_model=RemediationResponse)
async def generate_remediation(
    request: RemediationRequest,
    db: Session = Depends(get_db)
):
    """Generate remediation patch."""
    try:
        # Get findings
        findings = db.query(Finding).filter(Finding.id.in_(request.finding_ids)).all()
        
        if not findings:
            raise HTTPException(status_code=404, detail="No findings found")
        
        # Generate unified diff and PR content
        unified_diff = generate_unified_diff(findings)
        pr_title = f"Security: Fix {len(findings)} secret(s) in {request.repo_url}"
        pr_body = generate_pr_body(findings)
        
        return RemediationResponse(
            unified_diff=unified_diff,
            pr_title=pr_title,
            pr_body=pr_body
        )
        
    except Exception as e:
        logger.error(f"Failed to generate remediation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# MCP Classify Route
@router.post("/mcp/classify", response_model=ClassifyResponse)
async def classify_text(request: ClassifyRequest):
    """Classify text using MCP."""
    try:
        classifier = MCPClassifier()
        result = await classifier.classify_single_text(request.text)
        
        return ClassifyResponse(
            is_secret=result.is_secret,
            is_vulnerability=result.is_vulnerability,
            type=result.type,
            severity=result.severity,
            confidence=result.confidence,
            remediation=result.remediation,
            reasoning=result.reasoning
        )
        
    except Exception as e:
        logger.error(f"MCP classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Dashboard Routes
@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    total_scans = db.query(Scan).count()
    total_findings = db.query(Finding).count()
    
    # Severity breakdown
    severity_counts = db.query(
        Finding.severity,
        func.count(Finding.id)
    ).group_by(Finding.severity).all()
    
    # Top secret types
    type_counts = db.query(
        Finding.type,
        func.count(Finding.id)
    ).group_by(Finding.type).order_by(desc(func.count(Finding.id))).limit(10).all()
    
    # Recent scans
    recent_scans = db.query(Scan).order_by(desc(Scan.started_at)).limit(5).all()
    
    return {
        "total_scans": total_scans,
        "total_findings": total_findings,
        "severity_breakdown": dict(severity_counts),
        "top_secret_types": dict(type_counts),
        "recent_scans": [
            {
                "id": str(scan.id),
                "repo_url": scan.repo_url,
                "status": scan.status,
                "risk_score": scan.risk_score,
                "started_at": scan.started_at.isoformat() if scan.started_at else None
            }
            for scan in recent_scans
        ]
    }


# Background Tasks
async def execute_scan_task(scan_id: str, scan_config: Dict[str, Any]):
    """Execute scan in background."""
    try:
        engine = ScanEngine()
        await engine.execute_scan(scan_id, scan_config)
    except Exception as e:
        logger.error(f"Background scan task failed: {e}")


# Helper Functions
def generate_unified_diff(findings: List[Finding]) -> str:
    """Generate unified diff for findings."""
    # This is a simplified implementation
    # In a real implementation, you'd generate actual git patches
    diff_lines = []
    for finding in findings:
        diff_lines.append(f"--- a/{finding.file_path}")
        diff_lines.append(f"+++ b/{finding.file_path}")
        diff_lines.append(f"@@ -{finding.start_line},1 +{finding.start_line},1 @@")
        diff_lines.append(f"-{finding.description}")
        diff_lines.append(f"+# SECRET REMOVED - {finding.remediation_text}")
        diff_lines.append("")
    
    return "\n".join(diff_lines)


def generate_pr_body(findings: List[Finding]) -> str:
    """Generate PR body for findings."""
    body = f"## Security Fix: {len(findings)} Secret(s) Removed\n\n"
    body += "This PR addresses the following security findings:\n\n"
    
    for finding in findings:
        body += f"### {finding.type} in {finding.file_path}:{finding.start_line}\n"
        body += f"- **Severity**: {finding.severity}\n"
        body += f"- **Confidence**: {finding.confidence:.2f}\n"
        body += f"- **Remediation**: {finding.remediation_text}\n\n"
    
    body += "## Next Steps\n"
    body += "1. Review the changes carefully\n"
    body += "2. Test the application to ensure functionality is preserved\n"
    body += "3. Update any documentation that references the removed secrets\n"
    body += "4. Consider implementing secret scanning in CI/CD pipeline\n"
    
    return body
