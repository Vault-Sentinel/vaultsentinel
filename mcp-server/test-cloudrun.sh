#!/bin/bash
"""Test Cloud Run deployment."""

set -e

# Configuration
SERVICE_URL=${1:-"https://vaultsentinel-mcp-xxxxx-uc.a.run.app"}
MCP_API_KEY=${MCP_API_KEY:-"demo-mcp-key-12345"}

echo "🧪 Testing Cloud Run MCP Server"
echo "==============================="
echo "Service URL: $SERVICE_URL"
echo "API Key: ${MCP_API_KEY:0:10}..."
echo ""

# Test 1: Health Check
echo "1️⃣ Testing health endpoint..."
if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

# Test 2: API Authentication
echo ""
echo "2️⃣ Testing API authentication..."
if curl -f -H "Authorization: Bearer $MCP_API_KEY" "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo "✅ Authentication working"
else
    echo "❌ Authentication failed"
    exit 1
fi

# Test 3: Chat Endpoint
echo ""
echo "3️⃣ Testing chat endpoint..."
RESPONSE=$(curl -s -X POST "$SERVICE_URL/v1/chat" \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation": {
      "messages": [{"role": "user", "content": "Analyze this secret: AWS_ACCESS_KEY_ID_EXAMPLE"}],
      "provider": "gemini"
    }
  }')

if echo "$RESPONSE" | grep -q "request_id"; then
    echo "✅ Chat endpoint working"
    echo "📋 Response: $(echo "$RESPONSE" | jq -r '.request_id // "N/A"')"
else
    echo "❌ Chat endpoint failed"
    echo "Response: $RESPONSE"
    exit 1
fi

# Test 4: Stats Endpoint
echo ""
echo "4️⃣ Testing stats endpoint..."
STATS=$(curl -s -H "Authorization: Bearer $MCP_API_KEY" "$SERVICE_URL/v1/stats")
if echo "$STATS" | grep -q "uptime_seconds"; then
    echo "✅ Stats endpoint working"
    echo "📊 Uptime: $(echo "$STATS" | jq -r '.uptime_seconds // "N/A"') seconds"
else
    echo "❌ Stats endpoint failed"
    echo "Response: $STATS"
    exit 1
fi

echo ""
echo "🎉 All tests passed! Cloud Run deployment is working correctly."
echo ""
echo "🔗 Service URL: $SERVICE_URL"
echo "📚 API docs: $SERVICE_URL/docs"
echo "🔍 Health: $SERVICE_URL/health"
echo ""
echo "💡 To use with VaultSentinel:"
echo "export MCP_BASE_URL=$SERVICE_URL"
echo "export MCP_AUTH_TYPE=api_key"
echo "export MCP_API_KEY=$MCP_API_KEY"
echo "export DEMO_MODE=false"
