#!/usr/bin/env python3
"""
Test script to manually insert a finding into the database.
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / "packages"))

from packages.core.models import FindingModel, SecretKind, FindingStatus
from datetime import datetime

def test_db_insert():
    """Test inserting a finding into the database."""
    print("🧪 Testing database insert...")
    
    # Initialize database
    engine = create_engine("sqlite:///./vaultsentinel.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create a test finding
        finding = FindingModel(
            id="test-123",
            fingerprint="test-fingerprint",
            kind=SecretKind.AWS_ACCESS_KEY,
            confidence=0.9,
            location="test.py:1",
            preview_masked="AKIA****",
            repo="test/repo",
            commit_sha="test-commit",
            file_path="test.py",
            line_start=1,
            line_end=1,
            status=FindingStatus.NEW,
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            notes=""
        )
        
        session.add(finding)
        session.commit()
        print("✅ Successfully inserted finding!")
        
        # Query it back
        retrieved = session.query(FindingModel).filter(FindingModel.id == "test-123").first()
        if retrieved:
            print(f"✅ Successfully retrieved: {retrieved.kind}")
        else:
            print("❌ Failed to retrieve finding")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    test_db_insert()
