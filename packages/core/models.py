"""Domain models for VaultSentinel."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class FindingStatus(Enum):
    """Status of a finding."""
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class SecretKind(Enum):
    """Type of secret detected."""
    AWS_ACCESS_KEY = "aws_access_key"
    AWS_SECRET_KEY = "aws_secret_key"
    GITHUB_TOKEN = "github_token"
    SLACK_WEBHOOK = "slack_webhook"
    JWT_TOKEN = "jwt_token"
    RSA_PRIVATE_KEY = "rsa_private_key"
    DATABASE_URL = "database_url"
    BEARER_TOKEN = "bearer_token"
    HIGH_ENTROPY_STRING = "high_entropy_string"
    UNKNOWN = "unknown"


@dataclass
class Finding:
    """Domain model for a secret finding."""
    fingerprint: str
    kind: SecretKind
    confidence: float
    location: str
    preview_masked: str
    repo: str
    commit_sha: str
    file_path: str
    line_start: int
    line_end: int
    status: FindingStatus = FindingStatus.NEW
    first_seen_at: datetime = field(default_factory=datetime.utcnow)
    last_seen_at: datetime = field(default_factory=datetime.utcnow)
    notes: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "fingerprint": self.fingerprint,
            "kind": self.kind.value,
            "confidence": self.confidence,
            "location": self.location,
            "preview_masked": self.preview_masked,
            "repo": self.repo,
            "commit_sha": self.commit_sha,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "status": self.status.value,
            "first_seen_at": self.first_seen_at.isoformat(),
            "last_seen_at": self.last_seen_at.isoformat(),
            "notes": self.notes
        }


@dataclass
class ScanRun:
    """Domain model for a scan run."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    repo: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    status: str = "OK"  # OK, ERROR
    new_findings_count: int = 0
    commit_range: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "repo": self.repo,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "new_findings_count": self.new_findings_count,
            "commit_range": self.commit_range
        }


# SQLAlchemy models for persistence
class FindingModel(Base):
    """SQLAlchemy model for findings."""
    __tablename__ = "findings"
    
    id = Column(String, primary_key=True)
    fingerprint = Column(String, nullable=False, index=True)
    kind = Column(SQLEnum(SecretKind), nullable=False)
    confidence = Column(Float, nullable=False)
    location = Column(String, nullable=False)
    preview_masked = Column(String, nullable=False)
    repo = Column(String, nullable=False, index=True)
    commit_sha = Column(String, nullable=False, index=True)
    file_path = Column(String, nullable=False)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    status = Column(SQLEnum(FindingStatus), default=FindingStatus.NEW)
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, default="")
    
    def to_domain(self) -> Finding:
        """Convert to domain model."""
        return Finding(
            id=self.id,
            fingerprint=self.fingerprint,
            kind=self.kind,
            confidence=self.confidence,
            location=self.location,
            preview_masked=self.preview_masked,
            repo=self.repo,
            commit_sha=self.commit_sha,
            file_path=self.file_path,
            line_start=self.line_start,
            line_end=self.line_end,
            status=self.status,
            first_seen_at=self.first_seen_at,
            last_seen_at=self.last_seen_at,
            notes=self.notes or ""
        )


class ScanRunModel(Base):
    """SQLAlchemy model for scan runs."""
    __tablename__ = "scan_runs"
    
    id = Column(String, primary_key=True)
    repo = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String, default="OK")
    new_findings_count = Column(Integer, default=0)
    commit_range = Column(String, nullable=True)
    
    def to_domain(self) -> ScanRun:
        """Convert to domain model."""
        return ScanRun(
            id=self.id,
            repo=self.repo,
            started_at=self.started_at,
            ended_at=self.ended_at,
            status=self.status,
            new_findings_count=self.new_findings_count,
            commit_range=self.commit_range
        )
