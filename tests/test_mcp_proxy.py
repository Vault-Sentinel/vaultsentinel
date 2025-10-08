"""Unit tests for MCP proxy functionality."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from api.app import app
from api.clients.mcp_client import MCPClient, MockMCPClient


class TestMCPClient:
    """Test MCP client functionality."""
    
    def test_mcp_client_initialization(self):
        """Test MCP client initialization."""
        client = MCPClient("http://test.com", 30)
        assert client.base_url == "http://test.com"
        assert client.timeout == 30
        assert client._consecutive_errors == 0
        assert client._circuit_opened_at is None
    
    def test_circuit_breaker_logic(self):
        """Test circuit breaker functionality."""
        client = MCPClient("http://test.com", 30)
        
        # Initially circuit should be closed
        assert not client._is_circuit_open()
        
        # Record failures to open circuit
        for _ in range(5):
            client._record_failure()
        
        # Circuit should now be open
        assert client._is_circuit_open()
        
        # Record success should reset circuit
        client._record_success()
        assert not client._is_circuit_open()
        assert client._consecutive_errors == 0
    
    def test_redact_secrets(self):
        """Test secret redaction in logs."""
        client = MCPClient("http://test.com", 30)
        
        # Test API key redaction
        text = 'api_key="sk-1234567890abcdef"'
        redacted = client._redact_secrets(text)
        assert "***REDACTED***" in redacted
        assert "sk-1234567890abcdef" not in redacted
        
        # Test token redaction
        text = 'token=ghp_abcdef1234567890'
        redacted = client._redact_secrets(text)
        assert "***REDACTED***" in redacted
        assert "ghp_abcdef1234567890" not in redacted
    
    @pytest.mark.asyncio
    async def test_chat_success(self):
        """Test successful chat request."""
        client = MCPClient("http://test.com", 30)
        
        # Mock successful response
        mock_response = {
            "choices": [{"text": "Test response"}],
            "request_id": "test-123"
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.chat({"messages": [{"role": "user", "content": "test"}]})
            
            assert result["status"] == "ok"
            assert result["result"] == mock_response["choices"]
            assert result["request_id"] == "test-123"
    
    @pytest.mark.asyncio
    async def test_chat_failure(self):
        """Test chat request failure."""
        client = MCPClient("http://test.com", 30)
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("Network error")
            
            result = await client.chat({"messages": [{"role": "user", "content": "test"}]})
            
            assert result["status"] == "error"
            assert result["result"] is None
            assert "error" in result["mcp_meta"]


class TestMockMCPClient:
    """Test mock MCP client functionality."""
    
    def test_mock_client_initialization(self):
        """Test mock client initialization."""
        client = MockMCPClient("http://test.com", 30)
        assert client.base_url == "http://test.com"
        assert client.timeout == 30
        assert "chat" in client._demo_responses
        assert "completion" in client._demo_responses
    
    @pytest.mark.asyncio
    async def test_mock_chat(self):
        """Test mock chat functionality."""
        client = MockMCPClient("http://test.com", 30)
        
        conversation = {
            "messages": [{"role": "user", "content": "test secret"}],
            "provider": "gemini"
        }
        
        result = await client.chat(conversation)
        
        assert result["status"] == "ok"
        assert "result" in result
        assert "request_id" in result
        assert "mcp_meta" in result
    
    @pytest.mark.asyncio
    async def test_mock_completion(self):
        """Test mock completion functionality."""
        client = MockMCPClient("http://test.com", 30)
        
        result = await client.completion("classify this text")
        
        assert result["status"] == "ok"
        assert "result" in result
        assert "request_id" in result
        assert "mcp_meta" in result


class TestMCPProxyRoutes:
    """Test MCP proxy API routes."""
    
    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)
    
    def test_mcp_health_success(self):
        """Test successful MCP health check."""
        with patch('api.app.get_mcp_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request = AsyncMock(return_value={"status": "ok"})
            mock_get_client.return_value = mock_client
            
            response = self.client.get("/api/mcp/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "request_id" in data
    
    def test_mcp_health_failure(self):
        """Test MCP health check failure."""
        with patch('api.app.get_mcp_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request = AsyncMock(side_effect=Exception("Connection failed"))
            mock_get_client.return_value = mock_client
            
            response = self.client.get("/api/mcp/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "error" in data["details"]
    
    def test_mcp_chat_success(self):
        """Test successful MCP chat request."""
        with patch('api.app.get_mcp_client') as mock_get_client:
            mock_client = Mock()
            mock_response = {
                "status": "ok",
                "result": [{"text": "Test response"}],
                "request_id": "test-123"
            }
            mock_client.chat = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            chat_data = {
                "messages": [{"role": "user", "content": "test message"}],
                "provider": "gemini"
            }
            
            response = self.client.post("/api/mcp/chat", json=chat_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["result"] == mock_response["result"]
            assert data["request_id"] == "test-123"
    
    def test_mcp_chat_failure(self):
        """Test MCP chat request failure."""
        with patch('api.app.get_mcp_client') as mock_get_client:
            mock_client = Mock()
            mock_client.chat = AsyncMock(side_effect=Exception("Chat failed"))
            mock_get_client.return_value = mock_client
            
            chat_data = {
                "messages": [{"role": "user", "content": "test message"}],
                "provider": "gemini"
            }
            
            response = self.client.post("/api/mcp/chat", json=chat_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "error" in data["result"]
    
    def test_mcp_chat_validation(self):
        """Test MCP chat request validation."""
        # Test missing messages
        response = self.client.post("/api/mcp/chat", json={})
        assert response.status_code == 422
        
        # Test invalid message format
        invalid_data = {
            "messages": [{"role": "invalid", "content": "test"}],
            "provider": "gemini"
        }
        response = self.client.post("/api/mcp/chat", json=invalid_data)
        assert response.status_code == 422


class TestMCPIntegration:
    """Test MCP integration scenarios."""
    
    def test_cors_headers(self):
        """Test CORS headers are set correctly."""
        client = TestClient(app)
        
        # Test preflight request
        response = client.options("/api/mcp/health")
        assert response.status_code == 200
        
        # Test actual request
        response = client.get("/api/mcp/health")
        assert response.status_code == 200
    
    def test_request_id_generation(self):
        """Test request ID generation."""
        client = TestClient(app)
        
        with patch('api.app.get_mcp_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request = AsyncMock(return_value={"status": "ok"})
            mock_get_client.return_value = mock_client
            
            response = self.client.get("/api/mcp/health")
            data = response.json()
            
            # Request ID should be present and non-empty
            assert "request_id" in data
            assert data["request_id"] is not None
            assert len(data["request_id"]) > 0
    
    def test_error_handling(self):
        """Test error handling in proxy routes."""
        client = TestClient(app)
        
        with patch('api.app.get_mcp_client') as mock_get_client:
            mock_get_client.side_effect = Exception("Client creation failed")
            
            response = self.client.get("/api/mcp/health")
            data = response.json()
            
            assert data["status"] == "error"
            assert "error" in data["details"]


if __name__ == "__main__":
    pytest.main([__file__])
