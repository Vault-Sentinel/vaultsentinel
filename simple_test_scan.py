#!/usr/bin/env python3
"""
Simple test script to demonstrate VaultSentinel detection capabilities.
"""

import sys
import os
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / "packages"))

from packages.detectors.regex_detector import RegexDetector
from packages.detectors.entropy_detector import EntropyDetector
from packages.core.interfaces import DetectionContext

def test_detection():
    """Test VaultSentinel detection on local files."""
    print("🔍 VaultSentinel Detection Test")
    print("=" * 50)
    
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
        
        # Create detection context
        context = DetectionContext(
            repo="Vault-Sentinel/test-VS",
            commit_sha="test-commit-123",
            file_path=file_path,
            content=content
        )
        
        # Run regex detection
        regex_findings = regex_detector.detect(context)
        
        # Run entropy detection
        entropy_findings = entropy_detector.detect(context)
        
        # Combine findings
        file_findings = list(regex_findings) + list(entropy_findings)
        findings.extend(file_findings)
        
        print(f"   Found {len(file_findings)} secrets")
        
        for finding in file_findings:
            print(f"   🔐 {finding.kind.value}: {finding.preview_masked} (confidence: {finding.confidence:.2f})")
    
    print(f"\n📊 Summary:")
    print(f"   Total findings: {len(findings)}")
    
    # Group by secret type
    secret_types = {}
    for finding in findings:
        kind = finding.kind.value
        if kind not in secret_types:
            secret_types[kind] = 0
        secret_types[kind] += 1
    
    print(f"   Secret types found:")
    for kind, count in secret_types.items():
        print(f"     - {kind}: {count}")
    
    print(f"\n✅ Detection test completed!")
    print(f"🌐 Start the API server to view results in the dashboard:")
    print(f"   python main.py --api-only")
    print(f"   Then visit: http://localhost:8000")
    
    return findings

if __name__ == "__main__":
    test_detection()
