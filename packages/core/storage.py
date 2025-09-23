"""Storage layer for VaultSentinel."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime

from .models import Finding, ScanRun, FindingModel, ScanRunModel, FindingStatus, SecretKind


class FindingRepository:
    """Repository for finding operations."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create(self, finding: Finding) -> Finding:
        """Create a new finding."""
        db_finding = FindingModel(
            id=finding.id,
            fingerprint=finding.fingerprint,
            kind=finding.kind,
            confidence=finding.confidence,
            location=finding.location,
            preview_masked=finding.preview_masked,
            repo=finding.repo,
            commit_sha=finding.commit_sha,
            file_path=finding.file_path,
            line_start=finding.line_start,
            line_end=finding.line_end,
            status=finding.status,
            first_seen_at=finding.first_seen_at,
            last_seen_at=finding.last_seen_at,
            notes=finding.notes
        )
        
        self.db.add(db_finding)
        self.db.commit()
        return finding
    
    def get_by_id(self, finding_id: str) -> Optional[Finding]:
        """Get finding by ID."""
        db_finding = self.db.query(FindingModel).filter(FindingModel.id == finding_id).first()
        return db_finding.to_domain() if db_finding else None
    
    def get_all(self, limit: int = 100, offset: int = 0, 
                status: Optional[FindingStatus] = None,
                kind: Optional[SecretKind] = None,
                repo: Optional[str] = None) -> List[Finding]:
        """Get findings with optional filters."""
        query = self.db.query(FindingModel)
        
        if status:
            query = query.filter(FindingModel.status == status)
        if kind:
            query = query.filter(FindingModel.kind == kind)
        if repo:
            query = query.filter(FindingModel.repo == repo)
        
        db_findings = query.order_by(desc(FindingModel.first_seen_at)).offset(offset).limit(limit).all()
        return [f.to_domain() for f in db_findings]
    
    def update(self, finding: Finding) -> Finding:
        """Update an existing finding."""
        db_finding = self.db.query(FindingModel).filter(FindingModel.id == finding.id).first()
        if not db_finding:
            raise ValueError(f"Finding {finding.id} not found")
        
        db_finding.status = finding.status
        db_finding.notes = finding.notes
        db_finding.last_seen_at = finding.last_seen_at
        
        self.db.commit()
        return finding
    
    def exists(self, fingerprint: str, file_path: str) -> bool:
        """Check if finding exists by fingerprint and file path."""
        return self.db.query(FindingModel).filter(
            FindingModel.fingerprint == fingerprint,
            FindingModel.file_path == file_path
        ).first() is not None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get finding metrics."""
        # Count by status
        status_counts = self.db.query(
            FindingModel.status,
            func.count(FindingModel.id)
        ).group_by(FindingModel.status).all()
        
        # Count by kind
        kind_counts = self.db.query(
            FindingModel.kind,
            func.count(FindingModel.id)
        ).group_by(FindingModel.kind).all()
        
        # Total count
        total_count = self.db.query(FindingModel).count()
        
        return {
            "counts_by_status": dict(status_counts),
            "counts_by_kind": dict(kind_counts),
            "total_findings": total_count
        }


class ScanRunRepository:
    """Repository for scan run operations."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create(self, scan_run: ScanRun) -> ScanRun:
        """Create a new scan run."""
        db_scan_run = ScanRunModel(
            id=scan_run.id,
            repo=scan_run.repo,
            started_at=scan_run.started_at,
            ended_at=scan_run.ended_at,
            status=scan_run.status,
            new_findings_count=scan_run.new_findings_count,
            commit_range=scan_run.commit_range
        )
        
        self.db.add(db_scan_run)
        self.db.commit()
        return scan_run
    
    def update(self, scan_run: ScanRun) -> ScanRun:
        """Update an existing scan run."""
        db_scan_run = self.db.query(ScanRunModel).filter(ScanRunModel.id == scan_run.id).first()
        if not db_scan_run:
            raise ValueError(f"Scan run {scan_run.id} not found")
        
        db_scan_run.ended_at = scan_run.ended_at
        db_scan_run.status = scan_run.status
        db_scan_run.new_findings_count = scan_run.new_findings_count
        db_scan_run.commit_range = scan_run.commit_range
        
        self.db.commit()
        return scan_run
    
    def get_latest(self) -> Optional[ScanRun]:
        """Get the latest scan run."""
        db_scan_run = self.db.query(ScanRunModel).order_by(desc(ScanRunModel.started_at)).first()
        return db_scan_run.to_domain() if db_scan_run else None
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[ScanRun]:
        """Get all scan runs."""
        db_scan_runs = self.db.query(ScanRunModel).order_by(desc(ScanRunModel.started_at)).offset(offset).limit(limit).all()
        return [s.to_domain() for s in db_scan_runs]
