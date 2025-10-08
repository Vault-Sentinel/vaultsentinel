"""Integration tests for MCP client with mock server."""

import pytest
import asyncio
import json
import os
from unittest.mock import patch
from httpx import Response
import respx
from fastapi.testclient import TestClient

from api.clients import get_mcp_client, reset_client, MCPClient
from api.app import app


class TestMCPIntegration:
    """Integration tests for MCP client with mock server."""
    
    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Setup for each test."""
        # Reset client before each test
        reset_client()
        yield
        # Cleanup after each test
        reset_client()
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_mcp_chat_endpoint_success(self):
        """Test MCP chat endpoint with successful response."""
        # Mock MCP server response
        mock_response = {
            "choices": [{"text": "This is a test response from MCP server"}],
            "request_id": "mcp-test-123",
            "meta": {
                "model": "gpt-3.5-turbo",
                "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}
            }
        }
        
        # Mock the MCP server endpoint
        respx.post("http://localhost:9000/v1/chat").mock(
            return_value=Response(200, json=mock_response)
        )
        
        # Test the MCP client directly
        client = MCPClient(base_url="http://localhost:9000")
        conversation = {
            "messages": [{"role": "user", "content": "Hello, MCP server!"}],
            "model": "gpt-3.5-turbo"
        }
        
        result = await client.chat(conversation)
        
        assert result["status"] == "ok"
        assert result["request_id"] == "mcp-test-123"
        assert "result" in result
        assert "mcp_meta" in result
        assert result["mcp_meta"]["model"] == "gpt-3.5-turbo"
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_mcp_completion_endpoint_success(self):
        """Test MCP completion endpoint with successful response."""
        mock_response = {
            "result": {"text": "Completion response from MCP server"},
            "request_id": "mcp-completion-123",
            "meta": {"model": "gpt-4", "usage": {"total_tokens": 25}}
        }
        
        respx.post("http://localhost:9000/v1/complete").mock(
            return_value=Response(200, json=mock_response)
        )
        
        client = MCPClient(base_url="http://localhost:9000")
        result = await client.completion("Test prompt", {"temperature": 0.7})
        
        assert result["status"] == "ok"
        assert result["request_id"] == "mcp-completion-123"
        assert "result" in result
        assert result["mcp_meta"]["model"] == "gpt-4"
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_mcp_retry_on_server_error(self):
        """Test MCP client retries on server error."""
        # First call returns 500, second call succeeds
        mock_response = {
            "choices": [{"text": "Success after retry"}],
            "request_id": "mcp-retry-123"
        }
        
        respx.post("http://localhost:9000/v1/chat").mock(
            side_effect=[
                Response(500, json={"error": "Internal server error"}),
                Response(200, json=mock_response)
            ]
        )
        
        client = MCPClient(base_url="http://localhost:9000")
        conversation = {"messages": [{"role": "user", "content": "Test retry"}]}
        
        result = await client.chat(conversation)
        
        assert result["status"] == "ok"
        assert result["request_id"] == "mcp-retry-123"
        # Should have made 2 requests (1 retry)
        assert len(respx.calls) == 2
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_mcp_rate_limit_handling(self):
        """Test MCP client handles rate limits with Retry-After header."""
        mock_response = {
            "choices": [{"text": "Success after rate limit"}],
            "request_id": "mcp-rate-limit-123"
        }
        
        respx.post("http://localhost:9000/v1/chat").mock(
            side_effect=[
                Response(429, headers={"Retry-After": "1"}, json={"error": "Rate limited"}),
                Response(200, json=mock_response)
            ]
        )
        
        client = MCPClient(base_url="http://localhost:9000")
        conversation = {"messages": [{"role": "user", "content": "Test rate limit"}]}
        
        result = await client.chat(conversation)
        
        assert result["status"] == "ok"
        assert result["request_id"] == "mcp-rate-limit-123"
        # Should have made 2 requests
        assert len(respx.calls) == 2
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_mcp_auth_error_no_retry(self):
        """Test MCP client doesn't retry on auth errors."""
        respx.post("http://localhost:9000/v1/chat").mock(
            return_value=Response(401, json={"error": "Unauthorized"})
        )
        
        client = MCPClient(base_url="http://localhost:9000")
        conversation = {"messages": [{"role": "user", "content": "Test auth error"}]}
        
        with pytest.raises(Exception):  # Should raise auth error
            await client.chat(conversation)
        
        # Should only make 1 request (no retry)
        assert len(respx.calls) == 1
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_mcp_oauth_authentication(self):
        """Test MCP client with OAuth2 authentication."""
        # Mock OAuth token endpoint
        token_response = {"access_token": "test-oauth-token", "token_type": "Bearer"}
        respx.post("https://auth.example.com/token").mock(
            return_value=Response(200, json=token_response)
        )
        
        # Mock MCP server endpoint
        mock_response = {
            "choices": [{"text": "OAuth authenticated response"}],
            "request_id": "mcp-oauth-123"
        }
        respx.post("http://localhost:9000/v1/chat").mock(
            return_value=Response(200, json=mock_response)
        )
        
        with patch.dict(os.environ, {
            'MCP_AUTH_TYPE': 'oauth2',
            'MCP_OAUTH_TOKEN_URL': 'https://auth.example.com/token',
            'MCP_CLIENT_ID': 'test_client',
            'MCP_CLIENT_SECRET': 'test_secret'
        }):
            client = MCPClient(base_url="http://localhost:9000")
            conversation = {"messages": [{"role": "user", "content": "Test OAuth"}]}
            
            result = await client.chat(conversation)
            
            assert result["status"] == "ok"
            assert result["request_id"] == "mcp-oauth-123"
            
            # Check that OAuth token was requested
            assert len([call for call in respx.calls if "auth.example.com" in str(call.request.url)]) == 1
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_mcp_circuit_breaker_integration(self):
        """Test circuit breaker in integration scenario."""
        # Mock multiple failures to trigger circuit breaker
        respx.post("http://localhost:9000/v1/chat").mock(
            return_value=Response(500, json={"error": "Server error"})
        )
        
        client = MCPClient(base_url="http://localhost:9000")
        conversation = {"messages": [{"role": "user", "content": "Test circuit breaker"}]}
        
        # Make multiple requests to trigger circuit breaker
        for _ in range(6):  # More than the threshold
            try:
                await client.chat(conversation)
            except Exception:
                pass  # Expected to fail
        
        # Circuit breaker should now be open
        assert client._is_circuit_open()
        
        # Next request should be blocked by circuit breaker
        with pytest.raises(Exception):  # Circuit breaker error
            await client.chat(conversation)
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_mcp_api_endpoint_integration(self):
        """Test MCP API endpoint integration."""
        # Mock MCP server response
        mock_response = {
            "choices": [{"text": "API test response"}],
            "request_id": "api-test-123",
            "meta": {"model": "gpt-3.5-turbo", "usage": {"total_tokens": 20}}
        }
        
        respx.post("http://localhost:9000/v1/chat").mock(
            return_value=Response(200, json=mock_response)
        )
        
        # Test API endpoint
        with TestClient(app) as client:
            response = client.post("/mcp/test", json={
                "text": "AKIAIOSFODNN7EXAMPLE",
                "context": {"file_path": "config/aws.py", "secret_kind": "aws_access_key"}
            })
            
            assert response.status_code == 200
            data = response.json()
            
            assert "mcp_request_id" in data
            assert "mcp_status" in data
            assert "result" in data
            assert "mcp_meta" in data
            assert "client_stats" in data
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_mcp_demo_mode_integration(self):
        """Test MCP client in demo mode."""
        with patch.dict(os.environ, {'DEMO_MODE': 'true'}):
            reset_client()
            client = get_mcp_client()
            
            # Should be using MockMCPClient
            from api.clients.mcp_client import MockMCPClient
            assert isinstance(client, MockMCPClient)
            
            # Test mock response
            conversation = {"messages": [{"role": "user", "content": "Test demo mode"}]}
            result = await client.chat(conversation)
            
            assert result["status"] == "ok"
            assert "request_id" in result
            assert "result" in result
            assert "mcp_meta" in result
            assert result["mcp_meta"]["model"] == "demo-gpt-3.5-turbo"
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_mcp_error_handling_integration(self):
        """Test comprehensive error handling in integration."""
        # Mock various error scenarios
        respx.post("http://localhost:9000/v1/chat").mock(
            side_effect=[
                Response(500, json={"error": "Server error"}),
                Response(429, headers={"Retry-After": "1"}, json={"error": "Rate limited"}),
                Response(200, json={"choices": [{"text": "Success after errors"}]})
            ]
        )
        
        client = MCPClient(base_url="http://localhost:9000")
        conversation = {"messages": [{"role": "user", "content": "Test error handling"}]}
        
        result = await client.chat(conversation)
        
        assert result["status"] == "ok"
        assert "result" in result
        # Should have made 3 requests (2 retries)
        assert len(respx.calls) == 3
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_mcp_telemetry_integration(self):
        """Test telemetry and logging in integration."""
        mock_response = {
            "choices": [{"text": "Telemetry test response"}],
            "request_id": "telemetry-test-123"
        }
        
        respx.post("http://localhost:9000/v1/chat").mock(
            return_value=Response(200, json=mock_response)
        )
        
        client = MCPClient(base_url="http://localhost:9000")
        conversation = {"messages": [{"role": "user", "content": "Test telemetry"}]}
        
        result = await client.chat(conversation)
        
        assert result["status"] == "ok"
        assert "mcp_meta" in result
        assert "latency_ms" in result["mcp_meta"]
        assert "attempt" in result["mcp_meta"]
        assert "status_code" in result["mcp_meta"]
        
        # Test client stats
        stats = client.get_stats()
        assert "request_count" in stats
        assert "consecutive_errors" in stats
        assert "circuit_open" in stats


class TestMCPClassifierIntegration:
    """Integration tests for MCP classifier."""
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_classifier_with_mcp_client(self):
        """Test LLM classifier using MCP client."""
        # Mock MCP server response
        mock_response = {
            "choices": [{"text": '{"is_secret": true, "confidence": 0.9, "secret_type": "aws_access_key", "reasoning": "High confidence AWS key"}'}],
            "request_id": "classifier-test-123"
        }
        
        respx.post("http://localhost:9000/v1/chat").mock(
            return_value=Response(200, json=mock_response)
        )
        
        # Test classifier
        from detection.classifier_iface import LLMClassifier
        
        classifier = LLMClassifier(
            api_key="test_key",
            model="gpt-3.5-turbo",
            provider="openai"
        )
        
        # Test classification
        result = await classifier.classify(
            "AKIAIOSFODNN7EXAMPLE",
            {"file_path": "config/aws.py", "secret_kind": "aws_access_key"}
        )
        
        assert result.confidence == 0.9
        assert result.label == "aws_access_key"
        assert "High confidence" in result.reasoning
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_classifier_fallback_on_error(self):
        """Test classifier falls back to rule-based on MCP error."""
        # Mock MCP server error
        respx.post("http://localhost:9000/v1/chat").mock(
            return_value=Response(500, json={"error": "Server error"})
        )
        
        from detection.classifier_iface import LLMClassifier
        
        classifier = LLMClassifier(
            api_key="test_key",
            model="gpt-3.5-turbo",
            provider="openai"
        )
        
        # Test classification with error
        result = await classifier.classify(
            "AKIAIOSFODNN7EXAMPLE",
            {"file_path": "config/aws.py", "secret_kind": "aws_access_key"}
        )
        
        # Should fall back to rule-based classifier
        assert result.confidence > 0.0
        assert result.label == "aws_access_key"


if __name__ == "__main__":
    pytest.main([__file__])
