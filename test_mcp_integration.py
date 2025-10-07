#!/usr/bin/env python3
"""Test script for MCP integration."""

import os
import sys
import asyncio
import json
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / "packages"))
sys.path.insert(0, str(Path(__file__).parent))

from api.clients import get_mcp_client, reset_client


async def test_mcp_demo_mode():
    """Test MCP client in demo mode."""
    print("🧪 Testing MCP Demo Mode")
    print("=" * 50)
    
    # Set demo mode
    os.environ["DEMO_MODE"] = "true"
    reset_client()
    
    # Get MCP client
    client = get_mcp_client()
    print(f"✅ Client type: {type(client).__name__}")
    
    # Test chat endpoint
    print("\n📝 Testing chat endpoint...")
    conversation = {
        "messages": [
            {"role": "system", "content": "You are a security expert."},
            {"role": "user", "content": "Analyze this potential secret: AKIAIOSFODNN7EXAMPLE"}
        ],
        "model": "gpt-3.5-turbo"
    }
    
    result = await client.chat(conversation)
    print(f"✅ Chat result: {result['status']}")
    print(f"📋 Request ID: {result['request_id']}")
    print(f"🎯 Result: {result['result']}")
    print(f"📊 Meta: {result['mcp_meta']}")
    
    # Test completion endpoint
    print("\n📝 Testing completion endpoint...")
    result = await client.completion("Classify this secret: sk_test_1234567890abcdef")
    print(f"✅ Completion result: {result['status']}")
    print(f"📋 Request ID: {result['request_id']}")
    print(f"🎯 Result: {result['result']}")
    
    # Test client stats
    print("\n📊 Client Statistics:")
    stats = client.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Demo mode test completed successfully!")


async def test_mcp_classifier():
    """Test MCP classifier integration."""
    print("\n🤖 Testing MCP Classifier Integration")
    print("=" * 50)
    
    try:
        from detection.classifier_iface import LLMClassifier
        
        # Create classifier
        classifier = LLMClassifier(
            api_key="demo_key",
            model="gpt-3.5-turbo",
            provider="openai"
        )
        
        print(f"✅ Classifier created: {classifier.name}")
        print(f"🔧 MCP client available: {classifier.mcp_client is not None}")
        
        # Test classification
        print("\n📝 Testing secret classification...")
        result = classifier.classify(
            "AKIAIOSFODNN7EXAMPLE",
            {"file_path": "config/aws.py", "secret_kind": "aws_access_key"}
        )
        
        print(f"✅ Classification result:")
        print(f"  Confidence: {result.confidence}")
        print(f"  Label: {result.label}")
        print(f"  Reasoning: {result.reasoning}")
        
    except Exception as e:
        print(f"❌ Classifier test failed: {e}")
    
    print("\n✅ Classifier integration test completed!")


async def test_api_endpoint():
    """Test MCP API endpoint."""
    print("\n🌐 Testing MCP API Endpoint")
    print("=" * 50)
    
    try:
        import httpx
        
        # Test API endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/mcp/test",
                json={
                    "text": "AKIAIOSFODNN7EXAMPLE",
                    "context": {
                        "file_path": "config/aws.py",
                        "secret_kind": "aws_access_key"
                    }
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API response: {data['mcp_status']}")
                print(f"📋 Request ID: {data.get('mcp_request_id', 'N/A')}")
                print(f"🎯 Result: {data.get('result', 'N/A')}")
                print(f"📊 Client Stats: {data.get('client_stats', {})}")
            else:
                print(f"❌ API request failed: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print("💡 Make sure the API server is running: python main.py --api-only")
    
    print("\n✅ API endpoint test completed!")


async def main():
    """Main test function."""
    print("🚀 VaultSentinel MCP Integration Test")
    print("=" * 60)
    
    # Test demo mode
    await test_mcp_demo_mode()
    
    # Test classifier integration
    await test_mcp_classifier()
    
    # Test API endpoint (if server is running)
    await test_api_endpoint()
    
    print("\n🎉 All MCP integration tests completed!")
    print("\n💡 Next steps:")
    print("  1. Set up production MCP server: MCP_BASE_URL=https://your-mcp-server.com")
    print("  2. Configure authentication: MCP_AUTH_TYPE=api_key")
    print("  3. Test with real MCP server")
    print("  4. Monitor logs for MCP request IDs")


if __name__ == "__main__":
    asyncio.run(main())
