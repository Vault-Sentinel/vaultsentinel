"""Tests for entropy detection."""

import pytest
from detection.entropy import calculate_entropy, detect_high_entropy_strings, is_likely_secret


def test_entropy_calculation():
    """Test entropy calculation."""
    # High entropy string
    high_entropy = "aB3dE9fG2hI5jK8lM1nO4pQ7rS0tU3vW6xY9z"
    assert calculate_entropy(high_entropy) > 4.0
    
    # Low entropy string
    low_entropy = "aaaaaaaa"
    assert calculate_entropy(low_entropy) < 2.0


def test_high_entropy_detection():
    """Test high entropy string detection."""
    text = "password = aB3dE9fG2hI5jK8lM1nO4pQ7rS0tU3vW6xY9z"
    
    matches = detect_high_entropy_strings(text, threshold=4.0, min_length=20)
    
    assert len(matches) == 1
    assert matches[0][0] == "aB3dE9fG2hI5jK8lM1nO4pQ7rS0tU3vW6xY9z"


def test_likely_secret():
    """Test likely secret detection."""
    # High entropy string
    is_secret, confidence = is_likely_secret("aB3dE9fG2hI5jK8lM1nO4pQ7rS0tU3vW6xY9z")
    assert is_secret
    assert confidence > 4.0
    
    # Low entropy string
    is_secret, confidence = is_likely_secret("password123")
    assert not is_secret
    assert confidence < 4.0
