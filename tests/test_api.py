"""Tests for API endpoints."""

import pytest
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from fastapi.testclient import TestClient
from api.app import create_app

client = TestClient(create_app())


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime" in data


def test_findings_endpoint():
    """Test findings endpoint."""
    response = client.get("/findings")
    assert response.status_code == 200
    data = response.json()
    assert "findings" in data
    assert "total" in data


def test_metrics_endpoint():
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "findings" in data
    assert "last_scan_at" in data


def test_dashboard_endpoint():
    """Test dashboard endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "VaultSentinel Dashboard" in response.text