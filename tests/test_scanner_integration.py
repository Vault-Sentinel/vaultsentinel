"""Integration tests for VaultSentinel scanner."""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from api.app import app
from api.scanner_models import init_db, get_db
from scanner.scan_engine import ScanEngine
from detection.regex_detectors import RegexDetector
from detection.mcp_classifier import MCPClassifier


class TestScannerIntegration:
    """Integration tests for scanner functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Initialize test database
        init_db()
        self.client = TestClient(app)
    
    def test_create_scan(self):
        """Test scan creation endpoint."""
        scan_data = {
            "repo_url": "https://github.com/test/repo",
            "branch": "main",
            "mode": "full",
            "include": ["**/*.py", "**/*.js"],
            "exclude": ["**/node_modules/**"],
            "max_files": 100,
            "max_bytes_per_file": 100000,
            "timeout_sec": 60
        }
        
        response = self.client.post("/api/scans", json=scan_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "scan_id" in data
        assert data["status"] == "queued"
    
    def test_scan_status(self):
        """Test scan status endpoint."""
        # First create a scan
        scan_data = {
            "repo_url": "https://github.com/test/repo",
            "branch": "main"
        }
        
        create_response = self.client.post("/api/scans", json=scan_data)
        scan_id = create_response.json()["scan_id"]
        
        # Check status
        response = self.client.get(f"/api/scans/{scan_id}/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "progress" in data
        assert data["status"] in ["queued", "running", "done", "error"]
    
    def test_get_findings(self):
        """Test findings endpoint."""
        response = self.client.get("/api/findings")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_findings_with_filters(self):
        """Test findings endpoint with filters."""
        params = {
            "severity": "HIGH",
            "limit": 10,
            "offset": 0
        }
        
        response = self.client.get("/api/findings", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint."""
        response = self.client.get("/api/dashboard/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_scans" in data
        assert "total_findings" in data
        assert "severity_breakdown" in data
        assert "top_secret_types" in data
        assert "recent_scans" in data
    
    def test_mcp_classify(self):
        """Test MCP classification endpoint."""
        classify_data = {
            "text": "AKIA1234567890ABCDEF"
        }
        
        with patch('detection.mcp_classifier.MCPClassifier.classify_single_text') as mock_classify:
            mock_classify.return_value = AsyncMock(
                is_secret=True,
                is_vulnerability=False,
                type="aws_access_key",
                severity="HIGH",
                confidence=0.95,
                remediation="Rotate the key",
                reasoning="Valid AWS key format"
            )
            
            response = self.client.post("/api/mcp/classify", json=classify_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["is_secret"] is True
            assert data["type"] == "aws_access_key"
            assert data["severity"] == "HIGH"


class TestRegexDetector:
    """Test regex detection functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.detector = RegexDetector()
    
    def test_aws_access_key_detection(self):
        """Test AWS access key detection."""
        text = "aws_access_key = 'AKIA1234567890ABCDEF'"
        matches = self.detector.detect_in_text(text)
        
        assert len(matches) > 0
        assert matches[0].type == "aws_access_key"
        assert matches[0].severity == "HIGH"
        assert matches[0].confidence == 0.9
    
    def test_github_token_detection(self):
        """Test GitHub token detection."""
        text = "token = 'ghp_1234567890abcdef1234567890abcdef12345678'"
        matches = self.detector.detect_in_text(text)
        
        assert len(matches) > 0
        assert matches[0].type == "github_token"
        assert matches[0].severity == "HIGH"
    
    def test_private_key_detection(self):
        """Test private key detection."""
        text = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"""
        matches = self.detector.detect_in_text(text)
        
        assert len(matches) > 0
        assert matches[0].type == "private_key"
        assert matches[0].severity == "CRITICAL"
    
    def test_no_false_positives(self):
        """Test that common patterns don't trigger false positives."""
        text = "This is just some regular text with no secrets"
        matches = self.detector.detect_in_text(text)
        
        assert len(matches) == 0
    
    def test_file_detection(self):
        """Test detection in file content."""
        content = """
# Configuration file
database_url = "postgresql://user:pass@localhost/db"
aws_key = "AKIA1234567890ABCDEF"
password = "secret123"
"""
        lines = content.split('\n')
        matches = self.detector.detect_in_file("config.py", content, lines)
        
        assert len(matches) >= 2  # Should find AWS key and password
        aws_match = next((m for m in matches if m.type == "aws_access_key"), None)
        assert aws_match is not None
        assert aws_match.start_line == 3


class TestMCPClassifier:
    """Test MCP classification functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.classifier = MCPClassifier()
    
    @pytest.mark.asyncio
    async def test_classify_single_text(self):
        """Test single text classification."""
        with patch.object(self.classifier.mcp_client, 'chat') as mock_chat:
            mock_chat.return_value = {
                "status": "ok",
                "result": [{
                    "is_secret": True,
                    "is_vulnerability": False,
                    "type": "aws_access_key",
                    "severity": "HIGH",
                    "confidence": 0.95,
                    "remediation": "Rotate the key",
                    "reasoning": "Valid AWS key format"
                }]
            }
            
            result = await self.classifier.classify_single_text("AKIA1234567890ABCDEF")
            
            assert result.is_secret is True
            assert result.type == "aws_access_key"
            assert result.severity == "HIGH"
            assert result.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_classify_candidates(self):
        """Test batch classification."""
        candidates = [
            {
                "file_path": "config.py",
                "start_line": 1,
                "context": "aws_key = 'AKIA1234567890ABCDEF'",
                "snippet": "AKIA1234567890ABCDEF",
                "type": "aws_access_key"
            }
        ]
        
        with patch.object(self.classifier.mcp_client, 'chat') as mock_chat:
            mock_chat.return_value = {
                "status": "ok",
                "result": [{
                    "candidate_index": 0,
                    "is_secret": True,
                    "is_vulnerability": False,
                    "type": "aws_access_key",
                    "severity": "HIGH",
                    "confidence": 0.95,
                    "remediation": "Rotate the key",
                    "reasoning": "Valid AWS key format"
                }]
            }
            
            results = await self.classifier.classify_candidates(candidates)
            
            assert len(results) == 1
            assert results[0].is_secret is True
            assert results[0].type == "aws_access_key"
    
    @pytest.mark.asyncio
    async def test_classification_failure_handling(self):
        """Test handling of classification failures."""
        with patch.object(self.classifier.mcp_client, 'chat') as mock_chat:
            mock_chat.side_effect = Exception("MCP server error")
            
            result = await self.classifier.classify_single_text("test")
            
            assert result.is_secret is False
            assert result.confidence == 0.1
            assert "MCP classification failed" in result.reasoning


class TestScanEngine:
    """Test scan engine functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.engine = ScanEngine()
    
    def test_validate_repo_url(self):
        """Test repository URL validation."""
        # Valid URLs
        assert self.engine._validate_repo_url("https://github.com/owner/repo")
        assert self.engine._validate_repo_url("https://github.com/owner/repo/")
        
        # Invalid URLs
        assert not self.engine._validate_repo_url("https://gitlab.com/owner/repo")
        assert not self.engine._validate_repo_url("https://github.com/owner")
        assert not self.engine._validate_repo_url("http://github.com/owner/repo")
        assert not self.engine._validate_repo_url("not-a-url")
    
    def test_calculate_risk_score(self):
        """Test risk score calculation."""
        findings = [
            {"severity": "CRITICAL", "confidence": 0.9},
            {"severity": "HIGH", "confidence": 0.8},
            {"severity": "MEDIUM", "confidence": 0.7},
            {"severity": "LOW", "confidence": 0.6}
        ]
        
        risk_score = self.engine._calculate_risk_score(findings)
        
        assert 0 <= risk_score <= 100
        assert risk_score > 50  # Should be high with critical and high findings
    
    def test_get_context_lines(self):
        """Test context line extraction."""
        lines = ["line1", "line2", "line3", "line4", "line5"]
        context = self.engine._get_context_lines(lines, 3, 3, context=1)
        
        assert "line2" in context
        assert "line3" in context
        assert "line4" in context
        assert ">>>" in context  # Should mark the finding line
    
    def test_merge_findings(self):
        """Test findings merge and deduplication."""
        regex_findings = [
            {"file_path": "file1.py", "start_line": 1, "type": "aws_key", "engine": "regex"}
        ]
        mcp_findings = [
            {"file_path": "file1.py", "start_line": 1, "type": "aws_key", "engine": "mcp"}
        ]
        
        merged = self.engine._merge_findings(regex_findings, mcp_findings)
        
        # Should deduplicate based on file path, line, and type
        assert len(merged) == 2  # Both should be included for now


class TestReportRenderer:
    """Test HTML report rendering."""
    
    def test_render_scan_report(self):
        """Test scan report HTML rendering."""
        from api.report_renderer import render_scan_report
        from api.scanner_models import Scan, Finding
        from datetime import datetime
        
        # Create mock scan and findings
        scan = Scan(
            id="test-scan-id",
            repo_url="https://github.com/test/repo",
            branch="main",
            status="done",
            risk_score=75.5,
            total_files=100,
            scanned_files=100,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            duration_ms=30000
        )
        
        findings = [
            Finding(
                id="finding-1",
                scan_id="test-scan-id",
                type="aws_access_key",
                severity="HIGH",
                confidence=0.95,
                repo="test/repo",
                file_path="config.py",
                start_line=15,
                end_line=15,
                evidence_snippet_hash="hash1",
                engine="regex",
                description="AWS Access Key found",
                remediation_text="Remove hardcoded key"
            )
        ]
        
        html = render_scan_report(scan, findings)
        
        assert "<html" in html
        assert "VaultSentinel" in html
        assert "test/repo" in html
        assert "aws_access_key" in html
        assert "HIGH" in html


if __name__ == "__main__":
    pytest.main([__file__])
