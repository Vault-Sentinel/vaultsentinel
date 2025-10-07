#!/usr/bin/env python3
"""
Script to run VaultSentinel scan and populate the database.
"""

import sys
import os
import requests
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / "packages"))

from packages.detectors.regex_detector import RegexDetector
from packages.detectors.entropy_detector import EntropyDetector
from packages.core.interfaces import DetectionContext
from packages.core.storage import FindingRepository, ScanRunRepository
from packages.core.models import Finding, ScanRun, FindingStatus, SecretKind
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

def run_scan():
    """Run VaultSentinel scan on test repository."""
    print("🔍 Running VaultSentinel Scan")
    print("=" * 50)
    
    # Initialize database
    engine = create_engine("sqlite:///./vaultsentinel.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Initialize repositories
    finding_repo = FindingRepository(session)
    scan_repo = ScanRunRepository(session)
    
    # Initialize detectors
    regex_detector = RegexDetector()
    entropy_detector = EntropyDetector()
    
    # Test files to scan
    test_files = [
        "test-secrets-repo/config.py",
        "test-secrets-repo/README.md"
    ]
    
    all_findings = []
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {file_path}")
            continue
            
        print(f"\n🔍 Scanning: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create detection context
        context = DetectionContext(
            repo="Vault-Sentinel/test-VS",
            commit_sha="demo-commit-123",
            file_path=file_path,
            content=content
        )
        
        # Run detection
        regex_findings = list(regex_detector.detect(context))
        entropy_findings = list(entropy_detector.detect(context))
        file_findings = regex_findings + entropy_findings
        all_findings.extend(file_findings)
        
        print(f"   Found {len(file_findings)} secrets")
        
        # Store findings in database
        for finding in file_findings:
            try:
                finding_repo.create(finding)
                print(f"   ✅ Stored: {finding.kind.value} - {finding.preview_masked}")
            except Exception as e:
                print(f"   ❌ Error storing finding: {e}")
    
    # Create a scan run
    scan_run = ScanRun(
        id="demo-scan-123",
        repo="Vault-Sentinel/test-VS",
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
        status="OK",
        new_findings_count=len(all_findings),
        commit_range="demo-commit-123"
    )
    
    try:
        scan_repo.create(scan_run)
        print(f"\n✅ Scan completed successfully!")
        print(f"📊 Total findings: {len(all_findings)}")
        print(f"🌐 View results at: http://localhost:8000")
    except Exception as e:
        print(f"❌ Error creating scan run: {e}")
    
    session.close()
    return len(all_findings)

if __name__ == "__main__":
    run_scan()
