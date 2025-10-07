#!/usr/bin/env python3
"""
Test script to run VaultSentinel against the test repository.
This demonstrates VaultSentinel in action without requiring GitHub API access.
"""

import sys
import os
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / "packages"))

from core.agent import VaultSentinelAgent
from core.config import Config
from core.storage import Storage
from packages.detectors.regex_detector import RegexDetector
from packages.detectors.entropy_detector import EntropyDetector
from packages.connectors.github_connector import GitHubConnector
from packages.remediation.slack_notifier import SlackNotifier
from packages.remediation.aws_remediation import AWSRemediationHandler

def test_local_scan():
    """Test VaultSentinel by scanning local files."""
    print("🔍 VaultSentinel Test Scan")
    print("=" * 50)
    
    # Initialize storage
    storage = Storage()
    storage.init_db()
    
    # Initialize detectors
    regex_detector = RegexDetector()
    entropy_detector = EntropyDetector()
    
    # Test files to scan
    test_files = [
        "test-secrets-repo/config.py",
        "test-secrets-repo/README.md"
    ]
    
    findings = []
    
    print(f"📁 Scanning {len(test_files)} files...")
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {file_path}")
            continue
            
        print(f"\n🔍 Scanning: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Run regex detection
        regex_findings = regex_detector.detect({
            'content': content,
            'file_path': file_path,
            'commit_sha': 'test-commit-123'
        })
        
        # Run entropy detection
        entropy_findings = entropy_detector.detect({
            'content': content,
            'file_path': file_path,
            'commit_sha': 'test-commit-123'
        })
        
        # Combine findings
        file_findings = list(regex_findings) + list(entropy_findings)
        findings.extend(file_findings)
        
        print(f"   Found {len(file_findings)} secrets")
        
        for finding in file_findings:
            print(f"   🔐 {finding.secret_kind}: {finding.masked_preview} (confidence: {finding.confidence:.2f})")
    
    print(f"\n📊 Summary:")
    print(f"   Total findings: {len(findings)}")
    
    # Group by secret type
    secret_types = {}
    for finding in findings:
        kind = finding.secret_kind
        if kind not in secret_types:
            secret_types[kind] = 0
        secret_types[kind] += 1
    
    print(f"   Secret types found:")
    for kind, count in secret_types.items():
        print(f"     - {kind}: {count}")
    
    # Store findings in database
    print(f"\n💾 Storing findings in database...")
    for finding in findings:
        storage.store_finding(finding)
    
    print(f"✅ Test scan completed! Found {len(findings)} secrets.")
    print(f"🌐 View results at: http://localhost:8000/findings")
    
    return findings

if __name__ == "__main__":
    test_local_scan()
