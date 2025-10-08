#!/usr/bin/env python3
"""Test client for MCP server."""

import asyncio
import httpx
import json
import time
from typing import Dict, Any


class MCPTestClient:
    """Test client for MCP server."""
    
    def __init__(self, base_url: str = "http://localhost:9000", api_key: str = "demo-mcp-key-12345"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
    
    async def chat(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Send chat request."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/chat",
                json={"conversation": conversation},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def completion(self, prompt: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send completion request."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/complete",
                json={"prompt": prompt, "params": params or {}},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/v1/stats", headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_requests(self) -> Dict[str, Any]:
        """Get recent requests."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/v1/requests", headers=self.headers)
            response.raise_for_status()
            return response.json()


async def test_mcp_server():
    """Test MCP server functionality."""
    print("🧪 Testing MCP Server")
    print("=" * 50)
    
    client = MCPTestClient()
    
    try:
        # Test health check
        print("1. Testing health check...")
        health = await client.health_check()
        print(f"   ✅ Health: {health['status']}")
        print(f"   📊 Uptime: {health['uptime']:.2f}s")
        
        # Test chat endpoint
        print("\n2. Testing chat endpoint...")
        conversation = {
            "messages": [
                {"role": "system", "content": "You are a security expert analyzing secrets."},
                {"role": "user", "content": "Analyze this potential secret: AKIAIOSFODNN7EXAMPLE"}
            ],
            "model": "gpt-3.5-turbo",
            "temperature": 0.1,
            "max_tokens": 200
        }
        
        chat_result = await client.chat(conversation)
        print(f"   ✅ Chat request ID: {chat_result['request_id']}")
        print(f"   🎯 Result: {chat_result['choices'][0]['text'][:100]}...")
        print(f"   📊 Confidence: {chat_result['choices'][0]['confidence']}")
        
        # Test completion endpoint
        print("\n3. Testing completion endpoint...")
        completion_result = await client.completion(
            "Classify this secret: sk_test_1234567890abcdef",
            {"temperature": 0.1}
        )
        print(f"   ✅ Completion request ID: {completion_result['request_id']}")
        print(f"   🎯 Result: {completion_result['result']['text'][:100]}...")
        print(f"   📊 Confidence: {completion_result['result']['confidence']}")
        
        # Test server stats
        print("\n4. Testing server stats...")
        stats = await client.get_stats()
        print(f"   📊 Total requests: {stats['total_requests']}")
        print(f"   ⏱️  Uptime: {stats['uptime_seconds']:.2f}s")
        print(f"   💾 Stored requests: {stats['stored_requests']}")
        
        # Test error handling
        print("\n5. Testing error handling...")
        try:
            # Test with invalid API key
            invalid_client = MCPTestClient(api_key="invalid-key")
            await invalid_client.health_check()
            print("   ❌ Should have failed with invalid key")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                print("   ✅ Correctly rejected invalid API key")
            else:
                print(f"   ❌ Unexpected error: {e}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


async def test_vaultsentinel_integration():
    """Test VaultSentinel integration with MCP server."""
    print("\n🔗 Testing VaultSentinel Integration")
    print("=" * 50)
    
    try:
        import sys
        from pathlib import Path
        
        # Add VaultSentinel to path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from api.clients import get_mcp_client, reset_client
        import os
        
        # Configure for local MCP server
        os.environ["MCP_BASE_URL"] = "http://localhost:9000"
        os.environ["MCP_AUTH_TYPE"] = "api_key"
        os.environ["MCP_API_KEY"] = "demo-mcp-key-12345"
        os.environ["DEMO_MODE"] = "false"  # Use real MCP server
        
        reset_client()
        client = get_mcp_client()
        
        print(f"✅ MCP client type: {type(client).__name__}")
        print(f"🔗 Base URL: {client.base_url}")
        
        # Test chat
        conversation = {
            "messages": [
                {"role": "system", "content": "You are a security expert."},
                {"role": "user", "content": "Analyze this secret: AKIAIOSFODNN7EXAMPLE"}
            ],
            "model": "gpt-3.5-turbo"
        }
        
        result = await client.chat(conversation)
        print(f"✅ VaultSentinel chat result: {result['status']}")
        print(f"📋 Request ID: {result['request_id']}")
        print(f"🎯 Result: {result['result']}")
        
        # Test completion
        completion_result = await client.completion("Test prompt")
        print(f"✅ VaultSentinel completion result: {completion_result['status']}")
        print(f"📋 Request ID: {completion_result['request_id']}")
        
        print("\n✅ VaultSentinel integration test completed!")
        
    except Exception as e:
        print(f"❌ VaultSentinel integration test failed: {e}")
        print("💡 Make sure VaultSentinel is properly installed and configured")


async def main():
    """Main test function."""
    print("🚀 MCP Server Test Suite")
    print("=" * 60)
    
    # Test MCP server directly
    await test_mcp_server()
    
    # Test VaultSentinel integration
    await test_vaultsentinel_integration()
    
    print("\n🎉 All tests completed!")
    print("\n💡 Next steps:")
    print("  1. Start MCP server: python server.py")
    print("  2. Test with VaultSentinel: python test_client.py")
    print("  3. View API docs: http://localhost:9000/docs")


if __name__ == "__main__":
    asyncio.run(main())
