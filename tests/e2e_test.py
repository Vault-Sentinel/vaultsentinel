"""End-to-end test for VaultSentinel."""

import pytest
import sys
import tempfile
import os
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from core.agent import VaultSentinelAgent
from core.config import Config


def test_e2e_detection():
    """Test end-to-end secret detection."""
    # This is a placeholder for e2e testing
    # In a real implementation, this would:
    # 1. Create a test repository with seeded secrets
    # 2. Run VaultSentinel against it
    # 3. Verify detection and alerting
    
    # For now, just test that the agent can be initialized
    agent = VaultSentinelAgent()
    assert agent is not None
    
    # Test that we can get status
    status = agent.get_status()
    assert "running" in status
    assert "config" in status


def test_plugin_registration():
    """Test that plugins are properly registered."""
    from core.interfaces import get_registry
    
    registry = get_registry()
    
    # Check that detectors are registered
    detectors = registry.get_detectors()
    assert len(detectors) > 0
    assert "regex" in detectors
    assert "entropy" in detectors
    
    # Check that connectors are registered
    connectors = registry.get_connectors()
    assert len(connectors) > 0
    assert "github" in connectors
    
    # Check that remediation handlers are registered
    handlers = registry.get_remediation_handlers()
    assert len(handlers) > 0
    assert "slack" in handlers
    assert "aws" in handlers


def test_config_validation():
    """Test configuration validation."""
    config = Config()
    
    # Test with missing required fields
    errors = config.validate()
    assert len(errors) > 0
    assert "GITHUB_REPO is required" in errors
    assert "GITHUB_TOKEN is required" in errors
    assert "SLACK_WEBHOOK_URL is required" in errors
    
    # Test with valid config
    config.github_repo = "test/repo"
    config.github_token = "test_token"
    config.slack_webhook_url = "https://hooks.slack.com/test"
    
    errors = config.validate()
    assert len(errors) == 0