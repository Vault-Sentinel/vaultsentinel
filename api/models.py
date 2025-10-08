"""Database models for VaultSentinel."""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
# Removed agent.config import - using direct database URL

Base = declarative_base()


class Finding(Base):
    """Secret finding model."""
    
    __tablename__ = "findings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repo = Column(String, nullable=False)
    commit_sha = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    secret_fingerprint = Column(String, nullable=False)  # SHA256 hash for deduplication
    secret_kind = Column(String, nullable=False)  # aws_access_key, bearer_token, etc.
    confidence = Column(Float, nullable=False)
    status = Column(String, default="NEW")  # NEW, ACKNOWLEDGED, RESOLVED
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    masked_preview = Column(String, nullable=False)  # e.g., AKIA****7Q
    notes = Column(Text, default="")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "repo": self.repo,
            "commit_sha": self.commit_sha,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "secret_fingerprint": self.secret_fingerprint,
            "secret_kind": self.secret_kind,
            "confidence": self.confidence,
            "status": self.status,
            "first_seen_at": self.first_seen_at.isoformat() if self.first_seen_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "masked_preview": self.masked_preview,
            "notes": self.notes,
        }


class ScanRun(Base):
    """Scan run model."""
    
    __tablename__ = "scan_runs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String, default="OK")  # OK, ERROR
    new_findings_count = Column(Integer, default=0)
    repo = Column(String, nullable=False)
    commit_range = Column(String, nullable=True)


# Database setup
import os
database_url = os.getenv("DATABASE_URL", "sqlite:///./vaultsentinel.db")
engine = create_engine(database_url)
Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
