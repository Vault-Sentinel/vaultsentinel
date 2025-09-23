"""Tests for context filter."""

import pytest
from detection.context_filter import ContextFilter


def test_allowlist_path_scoring():
    """Test allowlist path scoring."""
    filter = ContextFilter()
    
    # Test file in allowlist path
    adjustment, reason = filter.score_context("/tests/test_file.py", "secret = 'test'", "aws_access_key")
    assert adjustment < 0  # Should reduce confidence
    assert "allowlisted_path" in reason


def test_denylist_pattern_scoring():
    """Test denylist pattern scoring."""
    filter = ContextFilter()
    
    # Test file with denylist pattern
    adjustment, reason = filter.score_context("dummy_config.py", "secret = 'test'", "aws_access_key")
    assert adjustment < 0  # Should reduce confidence
    assert "denylist_pattern" in reason


def test_config_file_scoring():
    """Test config file scoring."""
    filter = ContextFilter()
    
    # Test config file
    adjustment, reason = filter.score_context("config.json", "secret = 'test'", "aws_access_key")
    assert adjustment > 0  # Should increase confidence
    assert "config_file" in reason


def test_test_content_scoring():
    """Test test content scoring."""
    filter = ContextFilter()
    
    # Test line with test content
    adjustment, reason = filter.score_context("test.py", "secret = 'test_mock'", "aws_access_key")
    assert adjustment < 0  # Should reduce confidence
    assert "test_content" in reason
