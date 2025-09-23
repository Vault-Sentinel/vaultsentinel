"""Tests for regex detector."""

import pytest
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from detectors.regex_detector import RegexDetector
from core.models import DetectionContext, SecretKind


def test_aws_access_key_detection():
    """Test AWS access key detection."""
    detector = RegexDetector()
    context = DetectionContext(
        repo="test/repo",
        commit_sha="abc123",
        file_path="config.py",
        content="AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF"
    )
    
    findings = list(detector.detect(context))
    
    assert len(findings) == 1
    assert findings[0].kind == SecretKind.AWS_ACCESS_KEY
    assert findings[0].confidence == 0.9
    assert findings[0].preview_masked == "AKIA**************"


def test_slack_webhook_detection():
    """Test Slack webhook detection."""
    detector = RegexDetector()
    context = DetectionContext(
        repo="test/repo",
        commit_sha="abc123",
        file_path="config.py",
        content="webhook_url = https://hooks.slack.com/services/T123/B456/xyz789"
    )
    
    findings = list(detector.detect(context))
    
    assert len(findings) == 1
    assert findings[0].kind == SecretKind.SLACK_WEBHOOK
    assert findings[0].confidence == 0.9


def test_jwt_token_detection():
    """Test JWT token detection."""
    detector = RegexDetector()
    context = DetectionContext(
        repo="test/repo",
        commit_sha="abc123",
        file_path="config.py",
        content="token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )
    
    findings = list(detector.detect(context))
    
    assert len(findings) == 1
    assert findings[0].kind == SecretKind.JWT_TOKEN
    assert findings[0].confidence == 0.8


def test_multiple_secrets():
    """Test detection of multiple secrets."""
    detector = RegexDetector()
    context = DetectionContext(
        repo="test/repo",
        commit_sha="abc123",
        file_path="config.py",
        content="""
        AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF
        webhook_url = https://hooks.slack.com/services/T123/B456/xyz789
        token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
        """
    )
    
    findings = list(detector.detect(context))
    
    assert len(findings) == 3
    secret_kinds = [finding.kind for finding in findings]
    assert SecretKind.AWS_ACCESS_KEY in secret_kinds
    assert SecretKind.SLACK_WEBHOOK in secret_kinds
    assert SecretKind.JWT_TOKEN in secret_kinds


def test_no_secrets():
    """Test text with no secrets."""
    detector = RegexDetector()
    context = DetectionContext(
        repo="test/repo",
        commit_sha="abc123",
        file_path="config.py",
        content="This is just regular text with no secrets."
    )
    
    findings = list(detector.detect(context))
    
    assert len(findings) == 0
