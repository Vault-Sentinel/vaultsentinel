"""Database models for the VaultSentinel scanner."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Scan(Base):
    """Scan job model."""
    __tablename__ = "scans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_url = Column(String(500), nullable=False)
    branch = Column(String(100), default="main")
    mode = Column(String(20), default="full")  # full, diff
    status = Column(String(20), default="queued")  # queued, running, done, error
    risk_score = Column(Float, default=0.0)
    total_files = Column(Integer, default=0)
    scanned_files = Column(Integer, default=0)
    skipped_files = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    duration_ms = Column(Integer)
    engines_json = Column(JSON)
    error_message = Column(Text)
    
    # Relationships
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_scans_repo_url', 'repo_url'),
        Index('idx_scans_status', 'status'),
        Index('idx_scans_started_at', 'started_at'),
    )


class Finding(Base):
    """Finding model."""
    __tablename__ = "findings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String(36), ForeignKey("scans.id"), nullable=False)
    type = Column(String(50), nullable=False)  # aws_access_key, github_token, etc.
    severity = Column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    confidence = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    repo = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    evidence_snippet_hash = Column(String(64), nullable=False)
    engine = Column(String(50), nullable=False)  # regex, mcp, semgrep, etc.
    description = Column(Text, nullable=False)
    remediation_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scan = relationship("Scan", back_populates="findings")
    
    # Indexes
    __table_args__ = (
        Index('idx_findings_scan_id', 'scan_id'),
        Index('idx_findings_severity', 'severity'),
        Index('idx_findings_type', 'type'),
        Index('idx_findings_repo', 'repo'),
        Index('idx_findings_created_at', 'created_at'),
        Index('idx_findings_file_path', 'file_path'),
    )


class AggregateDaily(Base):
    """Daily aggregates for dashboards."""
    __tablename__ = "aggregates_daily"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    day = Column(DateTime, nullable=False)
    repo = Column(String(200), nullable=False)
    findings_total = Column(Integer, default=0)
    critical = Column(Integer, default=0)
    high = Column(Integer, default=0)
    medium = Column(Integer, default=0)
    low = Column(Integer, default=0)
    risk_score_avg = Column(Float, default=0.0)
    
    # Indexes
    __table_args__ = (
        Index('idx_aggregates_day', 'day'),
        Index('idx_aggregates_repo', 'repo'),
    )


class Artifact(Base):
    """Scan artifacts (SARIF, raw outputs)."""
    __tablename__ = "artifacts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String(36), ForeignKey("scans.id"), nullable=False)
    kind = Column(String(50), nullable=False)  # sarif, raw_gitleaks, raw_semgrep
    blob = Column(Text)  # compressed JSON/XML
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    scan = relationship("Scan")


# Database setup
def get_database_url() -> str:
    """Get database URL from environment."""
    import os
    return os.getenv("DATABASE_URL", "sqlite:///./vaultsentinel.db")


def create_engine_and_session():
    """Create database engine and session."""
    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal


def get_db():
    """Get database session."""
    engine, SessionLocal = create_engine_and_session()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    engine, _ = create_engine_and_session()
    Base.metadata.create_all(bind=engine)
