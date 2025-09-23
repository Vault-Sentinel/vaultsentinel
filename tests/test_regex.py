"""Tests for regex scanner."""

import pytest
from detection.regex_scanner import RegexScanner


def test_aws_access_key_detection():
    """Test AWS access key detection."""
    scanner = RegexScanner()
    text = "AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF"
    
    matches = scanner.scan_text(text)
    
    assert len(matches) == 1
    assert matches[0].secret_kind == "aws_access_key"
    assert matches[0].confidence == 0.9
    assert matches[0].masked_preview == "AKIA**************"


def test_slack_webhook_detection():
    """Test Slack webhook detection."""
    scanner = RegexScanner()
    text = "webhook_url = https://hooks.slack.com/services/T123/B456/xyz789"
    
    matches = scanner.scan_text(text)
    
    assert len(matches) == 1
    assert matches[0].secret_kind == "slack_webhook"
    assert matches[0].confidence == 0.9


def test_jwt_token_detection():
    """Test JWT token detection."""
    scanner = RegexScanner()
    text = "token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    matches = scanner.scan_text(text)
    
    assert len(matches) == 1
    assert matches[0].secret_kind == "jwt_token"
    assert matches[0].confidence == 0.8


def test_rsa_private_key_detection():
    """Test RSA private key detection."""
    scanner = RegexScanner()
    text = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKB
...
-----END PRIVATE KEY-----"""
    
    matches = scanner.scan_text(text)
    
    assert len(matches) == 1
    assert matches[0].secret_kind == "rsa_private_key"
    assert matches[0].confidence == 0.95


def test_multiple_secrets():
    """Test detection of multiple secrets."""
    scanner = RegexScanner()
    text = """
    AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF
    webhook_url = https://hooks.slack.com/services/T123/B456/xyz789
    token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
    """
    
    matches = scanner.scan_text(text)
    
    assert len(matches) == 3
    secret_kinds = [match.secret_kind for match in matches]
    assert "aws_access_key" in secret_kinds
    assert "slack_webhook" in secret_kinds
    assert "jwt_token" in secret_kinds


def test_no_secrets():
    """Test text with no secrets."""
    scanner = RegexScanner()
    text = "This is just regular text with no secrets."
    
    matches = scanner.scan_text(text)
    
    assert len(matches) == 0
