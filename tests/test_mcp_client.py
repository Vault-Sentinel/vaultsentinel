"""Unit tests for MCP client."""

import pytest
import asyncio
import json
import os
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import Response, RequestError, HTTPStatusError

from api.clients.mcp_client import (
    MCPClient, 
    MockMCPClient, 
    MCPClientError, 
    MCPAuthError, 
    MCPRateLimitError,
    MCPCircuitBreakerError,
    get_mcp_client,
    reset_client
)


class TestMCPClient:
    """Test MCP client functionality."""
    
    @pytest.fixture
    def client(self):
        """Create MCP client instance."""
        return MCPClient(base_url="http://localhost:9000", timeout=30)
    
    @pytest.fixture
    def mock_response(self):
        """Create mock successful response."""
        return {
            "choices": [{"text": "Test response"}],
            "request_id": "test-123",
            "meta": {"model": "gpt-3.5-turbo", "usage": {"total_tokens": 50}}
        }
    
    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.base_url == "http://localhost:9000"
        assert client.timeout == 30
        assert client._consecutive_errors == 0
        assert client._circuit_opened_at is None
    
    def test_circuit_breaker_closed_initially(self, client):
        """Test circuit breaker is closed initially."""
        assert not client._is_circuit_open()
    
    def test_circuit_breaker_opens_after_failures(self, client):
        """Test circuit breaker opens after consecutive failures."""
        # Simulate consecutive failures
        for _ in range(5):
            client._record_failure()
        
        assert client._is_circuit_open()
        assert client._consecutive_errors == 5
    
    def test_circuit_breaker_resets_after_success(self, client):
        """Test circuit breaker resets after successful request."""
        # Open circuit breaker
        for _ in range(5):
            client._record_failure()
        assert client._is_circuit_open()
        
        # Record success
        client._record_success()
        assert not client._is_circuit_open()
        assert client._consecutive_errors == 0
    
    def test_redact_secrets(self, client):
        """Test secret redaction in logs."""
        text = 'api_key="sk-1234567890abcdef"'
        redacted = client._redact_secrets(text)
        assert "***REDACTED***" in redacted
        assert "sk-1234567890abcdef" not in redacted
    
    @pytest.mark.asyncio
    async def test_successful_chat_request(self, client, mock_response):
        """Test successful chat request."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response_obj = Response(200, json=mock_response)
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response_obj)
            
            conversation = {"messages": [{"role": "user", "content": "test"}]}
            result = await client.chat(conversation)
            
            assert result["status"] == "ok"
            assert result["request_id"] == "test-123"
            assert "result" in result
            assert "mcp_meta" in result
    
    @pytest.mark.asyncio
    async def test_successful_completion_request(self, client, mock_response):
        """Test successful completion request."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response_obj = Response(200, json=mock_response)
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response_obj)
            
            result = await client.completion("test prompt", {"temperature": 0.1})
            
            assert result["status"] == "ok"
            assert result["request_id"] == "test-123"
            assert "result" in result
            assert "mcp_meta" in result
    
    @pytest.mark.asyncio
    async def test_retry_on_500_error(self, client):
        """Test retry behavior on 500 error."""
        with patch('httpx.AsyncClient') as mock_client:
            # First call returns 500, second call succeeds
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=[
                    Response(500, json={"error": "Internal server error"}),
                    Response(200, json={"choices": [{"text": "Success"}]})
                ]
            )
            
            conversation = {"messages": [{"role": "user", "content": "test"}]}
            result = await client.chat(conversation)
            
            assert result["status"] == "ok"
            # Should have made 2 requests (1 retry)
            assert mock_client.return_value.__aenter__.return_value.request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, client):
        """Test rate limit handling with Retry-After header."""
        with patch('httpx.AsyncClient') as mock_client:
            # First call returns 429 with Retry-After, second call succeeds
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=[
                    Response(429, headers={"Retry-After": "1"}, json={"error": "Rate limited"}),
                    Response(200, json={"choices": [{"text": "Success"}]})
                ]
            )
            
            conversation = {"messages": [{"role": "user", "content": "test"}]}
            result = await client.chat(conversation)
            
            assert result["status"] == "ok"
            # Should have made 2 requests
            assert mock_client.return_value.__aenter__.return_value.request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_auth_error_no_retry(self, client):
        """Test that auth errors don't retry."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=Response(401, json={"error": "Unauthorized"})
            )
            
            conversation = {"messages": [{"role": "user", "content": "test"}]}
            
            with pytest.raises(MCPAuthError):
                await client.chat(conversation)
            
            # Should only make 1 request (no retry)
            assert mock_client.return_value.__aenter__.return_value.request.call_count == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_requests(self, client):
        """Test that circuit breaker blocks requests when open."""
        # Open circuit breaker
        for _ in range(5):
            client._record_failure()
        
        conversation = {"messages": [{"role": "user", "content": "test"}]}
        
        with pytest.raises(MCPCircuitBreakerError):
            await client.chat(conversation)
    
    @pytest.mark.asyncio
    async def test_oauth_token_retrieval(self, client):
        """Test OAuth2 token retrieval."""
        with patch.dict(os.environ, {
            'MCP_AUTH_TYPE': 'oauth2',
            'MCP_OAUTH_TOKEN_URL': 'https://auth.example.com/token',
            'MCP_CLIENT_ID': 'test_client',
            'MCP_CLIENT_SECRET': 'test_secret'
        }):
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Response(200, json={"access_token": "test_token"})
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                token = await client._get_oauth_token()
                assert token == "test_token"
                assert client._token == "test_token"
    
    def test_get_stats(self, client):
        """Test client statistics."""
        stats = client.get_stats()
        
        assert "consecutive_errors" in stats
        assert "circuit_open" in stats
        assert "request_count" in stats
        assert "base_url" in stats
        assert "timeout" in stats
    
    @pytest.mark.asyncio
    async def test_request_with_headers(self, client):
        """Test request includes proper headers."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response_obj = Response(200, json={"choices": [{"text": "test"}]})
            mock_request = AsyncMock(return_value=mock_response_obj)
            mock_client.return_value.__aenter__.return_value.request = mock_request
            
            conversation = {"messages": [{"role": "user", "content": "test"}]}
            await client.chat(conversation)
            
            # Check that request was called with proper headers
            call_args = mock_request.call_args
            assert call_args[1]["headers"]["X-Request-ID"] is not None
    
    @pytest.mark.asyncio
    async def test_error_response_handling(self, client):
        """Test handling of error responses."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response_obj = Response(200, json={"error": "Something went wrong"})
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response_obj)
            
            conversation = {"messages": [{"role": "user", "content": "test"}]}
            result = await client.chat(conversation)
            
            assert result["status"] == "error"
            assert result["result"] is None


class TestMockMCPClient:
    """Test Mock MCP client functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock MCP client."""
        return MockMCPClient()
    
    @pytest.mark.asyncio
    async def test_mock_chat_response(self, mock_client):
        """Test mock chat response."""
        conversation = {"messages": [{"role": "user", "content": "test"}]}
        result = await mock_client.chat(conversation)
        
        assert result["status"] == "ok"
        assert "request_id" in result
        assert "result" in result
        assert "mcp_meta" in result
        assert result["result"][0]["confidence"] == 0.85
    
    @pytest.mark.asyncio
    async def test_mock_completion_response(self, mock_client):
        """Test mock completion response."""
        result = await mock_client.completion("test prompt")
        
        assert result["status"] == "ok"
        assert "request_id" in result
        assert "result" in result
        assert "mcp_meta" in result
        assert result["result"]["confidence"] == 0.90
    
    @pytest.mark.asyncio
    async def test_mock_response_variation(self, mock_client):
        """Test that mock responses vary based on content."""
        # Test with "secret" in conversation
        conversation = {"messages": [{"role": "user", "content": "This is a secret key"}]}
        result = await mock_client.chat(conversation)
        
        assert result["result"][0]["confidence"] == 0.95
        assert "high confidence" in result["result"][0]["reasoning"]
        
        # Test without "secret" in conversation
        conversation = {"messages": [{"role": "user", "content": "This is just normal text"}]}
        result = await mock_client.chat(conversation)
        
        assert result["result"][0]["confidence"] == 0.65
        assert "low confidence" in result["result"][0]["reasoning"]


class TestMCPClientFactory:
    """Test MCP client factory functions."""
    
    def test_get_mcp_client_demo_mode(self):
        """Test getting MCP client in demo mode."""
        with patch.dict(os.environ, {'DEMO_MODE': 'true'}):
            reset_client()
            client = get_mcp_client()
            assert isinstance(client, MockMCPClient)
    
    def test_get_mcp_client_production_mode(self):
        """Test getting MCP client in production mode."""
        with patch.dict(os.environ, {'DEMO_MODE': 'false'}):
            reset_client()
            client = get_mcp_client()
            assert isinstance(client, MCPClient)
    
    def test_reset_client(self):
        """Test client reset functionality."""
        # Get initial client
        client1 = get_mcp_client()
        
        # Reset and get new client
        reset_client()
        client2 = get_mcp_client()
        
        # Should be different instances
        assert client1 is not client2


class TestMCPClientIntegration:
    """Integration tests for MCP client."""
    
    @pytest.mark.asyncio
    async def test_full_chat_workflow(self):
        """Test complete chat workflow."""
        client = MCPClient(base_url="http://localhost:9000")
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Response(200, json={
                "choices": [{"text": "This is a test response"}],
                "request_id": "integration-test-123",
                "meta": {"model": "gpt-3.5-turbo", "usage": {"total_tokens": 25}}
            })
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)
            
            conversation = {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                "model": "gpt-3.5-turbo",
                "temperature": 0.7
            }
            
            result = await client.chat(conversation)
            
            assert result["status"] == "ok"
            assert result["request_id"] == "integration-test-123"
            assert "result" in result
            assert "mcp_meta" in result
            assert result["mcp_meta"]["model"] == "gpt-3.5-turbo"
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling in complete workflow."""
        client = MCPClient(base_url="http://localhost:9000")
        
        with patch('httpx.AsyncClient') as mock_client:
            # Simulate network error
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=RequestError("Network error")
            )
            
            conversation = {"messages": [{"role": "user", "content": "test"}]}
            result = await client.chat(conversation)
            
            assert result["status"] == "error"
            assert "error" in result["mcp_meta"]


if __name__ == "__main__":
    pytest.main([__file__])
