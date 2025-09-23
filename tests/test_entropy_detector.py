"""Tests for entropy detector."""

import pytest
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from detectors.entropy_detector import EntropyDetector
from core.models import DetectionContext, SecretKind


def test_high_entropy_detection():
    """Test high entropy string detection."""
    detector = EntropyDetector()
    context = DetectionContext(
        repo="test/repo",
        commit_sha="abc123",
        file_path="config.py",
        content="password = aB3dE9fG2hI5jK8lM1nO4pQ7rS0tU3vW6xY9z"
    )
    
    findings = list(detector.detect(context))
    
    assert len(findings) == 1
    assert findings[0].kind == SecretKind.HIGH_ENTROPY_STRING
    assert findings[0].confidence > 0.3


def test_low_entropy_ignored():
    """Test that low entropy strings are ignored."""
    detector = EntropyDetector()
    context = DetectionContext(
        repo="test/repo",
        commit_sha="abc123",
        file_path="config.py",
        content="password = password123"
    )
    
    findings = list(detector.detect(context))
    
    assert len(findings) == 0


def test_false_positive_filtering():
    """Test that false positives are filtered out."""
    detector = EntropyDetector()
    context = DetectionContext(
        repo="test/repo",
        commit_sha="abc123",
        file_path="config.py",
        content="version = 1.2.3.4.5.6.7.8.9.0"
    )
    
    findings = list(detector.detect(context))
    
    assert len(findings) == 0


def test_entropy_calculation():
    """Test entropy calculation."""
    detector = EntropyDetector()
    
    # High entropy string
    high_entropy = "aB3dE9fG2hI5jK8lM1nO4pQ7rS0tU3vW6xY9z"
    entropy = detector._calculate_entropy(high_entropy)
    assert entropy > 4.0
    
    # Low entropy string
    low_entropy = "aaaaaaaa"
    entropy = detector._calculate_entropy(low_entropy)
    assert entropy < 2.0
