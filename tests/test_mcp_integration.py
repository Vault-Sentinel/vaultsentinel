"""Integration tests for MCP proxy functionality."""

import pytest
import asyncio
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from api.app import app
from api.clients.mcp_client import get_mcp_client, reset_client


class TestMCPIntegration:
    """Integration tests for MCP proxy."""
    
    def setup_method(self):
        """Setup test environment."""
        self.client = TestClient(app)
        # Reset client to ensure clean state
        reset_client()
    
    def teardown_method(self):
        """Cleanup after tests."""
        reset_client()
    
    def test_health_endpoint_integration(self):
        """Test health endpoint with real client integration."""
        # Mock environment variables
        with patch.dict(os.environ, {
            'MCP_BASE_URL': 'https://test-mcp.example.com',
            'MCP_API_KEY': 'test-key',
            'MCP_AUTH_TYPE': 'api_key',
            'DEMO_MODE': 'true'
        }):
            # Reset client to pick up new environment
            reset_client()
            
            response = self.client.get("/api/mcp/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "request_id" in data
    
    def test_chat_endpoint_integration(self):
        """Test chat endpoint with real client integration."""
        # Mock environment variables
        with patch.dict(os.environ, {
            'MCP_BASE_URL': 'https://test-mcp.example.com',
            'MCP_API_KEY': 'test-key',
            'MCP_AUTH_TYPE': 'api_key',
            'DEMO_MODE': 'true'
        }):
            # Reset client to pick up new environment
            reset_client()
            
            chat_data = {
                "messages": [
                    {"role": "user", "content": "Analyze this potential secret: AKIA1234567890"}
                ],
                "provider": "gemini"
            }
            
            response = self.client.post("/api/mcp/chat", json=chat_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "request_id" in data
            assert "result" in data or "error" in data
    
    def test_demo_mode_integration(self):
        """Test demo mode integration."""
        with patch.dict(os.environ, {
            'MCP_BASE_URL': 'https://test-mcp.example.com',
            'MCP_API_KEY': 'test-key',
            'MCP_AUTH_TYPE': 'api_key',
            'DEMO_MODE': 'true'
        }):
            reset_client()
            
            # Test health in demo mode
            response = self.client.get("/api/mcp/health")
            assert response.status_code == 200
            
            # Test chat in demo mode
            chat_data = {
                "messages": [{"role": "user", "content": "test"}],
                "provider": "gemini"
            }
            response = self.client.post("/api/mcp/chat", json=chat_data)
            assert response.status_code == 200
    
    def test_production_mode_integration(self):
        """Test production mode integration (with mocked external calls)."""
        with patch.dict(os.environ, {
            'MCP_BASE_URL': 'https://vaultsentinel-mcp-923046029861.us-west1.run.app',
            'MCP_API_KEY': 'mcp-prod-test-key',
            'MCP_AUTH_TYPE': 'api_key',
            'DEMO_MODE': 'false'
        }):
            reset_client()
            
            # Mock the actual HTTP requests to external MCP server
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": "ok", "version": "1.0.0"}
                
                mock_client_instance = Mock()
                mock_client_instance.request.return_value = mock_response
                mock_client.return_value.__aenter__.return_value = mock_client_instance
                
                # Test health endpoint
                response = self.client.get("/api/mcp/health")
                assert response.status_code == 200
                
                # Test chat endpoint
                chat_data = {
                    "messages": [{"role": "user", "content": "test"}],
                    "provider": "gemini"
                }
                mock_response.json.return_value = {
                    "choices": [{"text": "Test response"}],
                    "request_id": "test-123"
                }
                
                response = self.client.post("/api/mcp/chat", json=chat_data)
                assert response.status_code == 200
    
    def test_error_handling_integration(self):
        """Test error handling in integration scenarios."""
        with patch.dict(os.environ, {
            'MCP_BASE_URL': 'https://test-mcp.example.com',
            'MCP_API_KEY': 'test-key',
            'MCP_AUTH_TYPE': 'api_key',
            'DEMO_MODE': 'false'
        }):
            reset_client()
            
            # Mock network failure
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.side_effect = Exception("Network error")
                
                response = self.client.get("/api/mcp/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "error"
    
    def test_cors_integration(self):
        """Test CORS headers in integration."""
        # Test preflight request
        response = self.client.options(
            "/api/mcp/health",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        
        # Test actual request with origin
        response = self.client.get(
            "/api/mcp/health",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
    
    def test_request_validation_integration(self):
        """Test request validation in integration."""
        # Test invalid chat request
        invalid_data = {
            "messages": "invalid",  # Should be array
            "provider": "gemini"
        }
        response = self.client.post("/api/mcp/chat", json=invalid_data)
        assert response.status_code == 422
        
        # Test missing required fields
        response = self.client.post("/api/mcp/chat", json={})
        assert response.status_code == 422
    
    def test_provider_selection_integration(self):
        """Test provider selection in integration."""
        with patch.dict(os.environ, {
            'MCP_BASE_URL': 'https://test-mcp.example.com',
            'MCP_API_KEY': 'test-key',
            'MCP_AUTH_TYPE': 'api_key',
            'DEMO_MODE': 'true'
        }):
            reset_client()
            
            # Test with Gemini provider
            chat_data = {
                "messages": [{"role": "user", "content": "test"}],
                "provider": "gemini"
            }
            response = self.client.post("/api/mcp/chat", json=chat_data)
            assert response.status_code == 200
            
            # Test with OpenAI provider
            chat_data["provider"] = "openai"
            response = self.client.post("/api/mcp/chat", json=chat_data)
            assert response.status_code == 200
    
    def test_concurrent_requests_integration(self):
        """Test concurrent request handling."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = self.client.get("/api/mcp/health")
            results.append(response.status_code)
        
        # Start multiple concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5
    
    def test_timeout_handling_integration(self):
        """Test timeout handling in integration."""
        with patch.dict(os.environ, {
            'MCP_BASE_URL': 'https://test-mcp.example.com',
            'MCP_API_KEY': 'test-key',
            'MCP_AUTH_TYPE': 'api_key',
            'MCP_TIMEOUT_SECONDS': '1',  # Very short timeout
            'DEMO_MODE': 'false'
        }):
            reset_client()
            
            # Mock slow response
            with patch('httpx.AsyncClient') as mock_client:
                async def slow_request(*args, **kwargs):
                    await asyncio.sleep(2)  # Longer than timeout
                    return Mock(status_code=200, json=lambda: {"status": "ok"})
                
                mock_client_instance = Mock()
                mock_client_instance.request = slow_request
                mock_client.return_value.__aenter__.return_value = mock_client_instance
                
                response = self.client.get("/api/mcp/health")
                # Should handle timeout gracefully
                assert response.status_code == 200


class TestMCPEndToEnd:
    """End-to-end tests for MCP integration."""
    
    def test_full_workflow(self):
        """Test complete MCP workflow."""
        client = TestClient(app)
        
        with patch.dict(os.environ, {
            'MCP_BASE_URL': 'https://test-mcp.example.com',
            'MCP_API_KEY': 'test-key',
            'MCP_AUTH_TYPE': 'api_key',
            'DEMO_MODE': 'true'
        }):
            reset_client()
            
            # 1. Check health
            response = self.client.get("/api/mcp/health")
            assert response.status_code == 200
            health_data = response.json()
            assert health_data["status"] in ["ok", "error"]
            
            # 2. Send chat request
            chat_data = {
                "messages": [
                    {"role": "user", "content": "Analyze this secret: AKIA1234567890"}
                ],
                "provider": "gemini"
            }
            response = self.client.post("/api/mcp/chat", json=chat_data)
            assert response.status_code == 200
            chat_data = response.json()
            assert chat_data["status"] in ["ok", "error"]
            
            # 3. Verify request IDs are different
            health_id = health_data.get("request_id")
            chat_id = chat_data.get("request_id")
            assert health_id != chat_id
    
    def test_error_recovery(self):
        """Test error recovery scenarios."""
        client = TestClient(app)
        
        with patch.dict(os.environ, {
            'MCP_BASE_URL': 'https://test-mcp.example.com',
            'MCP_API_KEY': 'test-key',
            'MCP_AUTH_TYPE': 'api_key',
            'DEMO_MODE': 'false'
        }):
            reset_client()
            
            # Mock first request to fail, second to succeed
            call_count = 0
            
            def mock_request(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("First call fails")
                else:
                    return Mock(status_code=200, json=lambda: {"status": "ok"})
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client_instance = Mock()
                mock_client_instance.request = mock_request
                mock_client.return_value.__aenter__.return_value = mock_client_instance
                
                # First request should fail
                response = self.client.get("/api/mcp/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "error"
                
                # Second request should succeed
                response = self.client.get("/api/mcp/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "ok"


if __name__ == "__main__":
    pytest.main([__file__])
