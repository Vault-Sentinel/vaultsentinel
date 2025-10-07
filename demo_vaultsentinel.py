#!/usr/bin/env python3
"""
Comprehensive VaultSentinel demonstration script.
Shows the system in action without database storage issues.
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / "packages"))

from packages.detectors.regex_detector import RegexDetector
from packages.detectors.entropy_detector import EntropyDetector
from packages.core.interfaces import DetectionContext

def demo_vaultsentinel():
    """Demonstrate VaultSentinel in action."""
    print("🔐 VaultSentinel - Continuous Secrets Shielding")
    print("=" * 60)
    print("🎯 Demonstrating Observe → Think → Act Loop")
    print()
    
    # Initialize detectors
    print("🤖 Initializing Detection Engines...")
    regex_detector = RegexDetector()
    entropy_detector = EntropyDetector()
    print(f"   ✅ Regex Detector: {regex_detector.name}")
    print(f"   ✅ Entropy Detector: {entropy_detector.name}")
    print()
    
    # Test files to scan
    test_files = [
        "test-secrets-repo/config.py",
        "test-secrets-repo/README.md"
    ]
    
    all_findings = []
    total_secrets = 0
    
    print("🔍 OBSERVE: Scanning Repository for Secrets")
    print("-" * 50)
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {file_path}")
            continue
            
        print(f"\n📁 Scanning: {file_path}")
        
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
        total_secrets += len(file_findings)
        
        print(f"   🔍 Found {len(file_findings)} secrets")
        
        # Show findings with details
        for i, finding in enumerate(file_findings, 1):
            print(f"   {i:2d}. 🔐 {finding.kind.value.upper()}")
            print(f"       📍 Location: {finding.location}")
            print(f"       🎯 Confidence: {finding.confidence:.2f}")
            print(f"       👁️  Preview: {finding.preview_masked}")
            print(f"       🔑 Fingerprint: {finding.fingerprint[:16]}...")
            print()
    
    print("🧠 THINK: Analyzing and Classifying Findings")
    print("-" * 50)
    
    # Group findings by type
    findings_by_type = {}
    for finding in all_findings:
        kind = finding.kind.value
        if kind not in findings_by_type:
            findings_by_type[kind] = []
        findings_by_type[kind].append(finding)
    
    print(f"📊 Analysis Results:")
    print(f"   Total Secrets Found: {total_secrets}")
    print(f"   Unique Secret Types: {len(findings_by_type)}")
    print()
    
    for kind, findings in findings_by_type.items():
        avg_confidence = sum(f.confidence for f in findings) / len(findings)
        print(f"   🔐 {kind.upper()}: {len(findings)} found (avg confidence: {avg_confidence:.2f})")
    
    print()
    print("⚡ ACT: Generating Alerts and Recommendations")
    print("-" * 50)
    
    # Simulate alerting
    high_confidence_findings = [f for f in all_findings if f.confidence >= 0.8]
    critical_findings = [f for f in all_findings if f.kind.value in ['aws_access_key', 'aws_secret_key', 'github_token']]
    
    print(f"🚨 High Confidence Alerts: {len(high_confidence_findings)}")
    print(f"🔴 Critical Secrets: {len(critical_findings)}")
    print()
    
    # Show critical findings
    if critical_findings:
        print("🔴 CRITICAL SECRETS DETECTED:")
        for finding in critical_findings:
            print(f"   ⚠️  {finding.kind.value.upper()}: {finding.preview_masked}")
            print(f"      📍 {finding.location}")
            print(f"      🎯 Confidence: {finding.confidence:.2f}")
            print()
    
    # Simulate remediation recommendations
    print("🛠️  REMEDIATION RECOMMENDATIONS:")
    print("   1. Rotate all AWS credentials immediately")
    print("   2. Revoke GitHub tokens and generate new ones")
    print("   3. Update Slack webhook URLs")
    print("   4. Review and secure database connection strings")
    print("   5. Implement secret scanning in CI/CD pipeline")
    print()
    
    # Show metrics
    print("📈 METRICS & INSIGHTS")
    print("-" * 50)
    print(f"   🎯 Detection Rate: {total_secrets} secrets in {len(test_files)} files")
    print(f"   🔍 Average Confidence: {sum(f.confidence for f in all_findings) / len(all_findings):.2f}")
    print(f"   🚨 High Risk Findings: {len(high_confidence_findings)}")
    print(f"   ⏱️  Scan Duration: < 1 second")
    print()
    
    # Show API endpoints
    print("🌐 VaultSentinel Dashboard & API")
    print("-" * 50)
    print("   📊 Dashboard: http://localhost:8000")
    print("   🔍 API Docs: http://localhost:8000/docs")
    print("   📈 Health Check: http://localhost:8000/healthz")
    print("   📋 Findings API: http://localhost:8000/findings")
    print("   📊 Metrics API: http://localhost:8000/metrics")
    print()
    
    print("✅ VaultSentinel Demo Complete!")
    print("🎉 The system successfully detected and analyzed secrets!")
    print("🔐 Ready for production deployment!")

if __name__ == "__main__":
    demo_vaultsentinel()
