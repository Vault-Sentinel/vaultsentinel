#!/bin/bash
"""Start MCP server with cheapest possible configuration."""

set -e

echo "💰 Starting VaultSentinel MCP Server - ULTRA CHEAP MODE"
echo "======================================================"

# Check for required API keys
if [ -z "$OPENAI_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Error: No LLM API keys provided!"
    echo "Please set at least one of:"
    echo "  export OPENAI_API_KEY=sk-your-openai-key-here"
    echo "  export GEMINI_API_KEY=your-gemini-key-here"
    echo ""
    echo "For cheapest setup, use Gemini:"
    echo "  export GEMINI_API_KEY=AIzaSy-your-key"
    exit 1
fi

# Ultra-cheap configuration
echo "🔧 Applying ULTRA CHEAP configuration..."

# Use Gemini 1.0 Pro (cheapest model)
export GEMINI_MODEL="gemini-1.0-pro"
export OPENAI_MODEL="gpt-3.5-turbo"

# Default to Gemini (cheaper than OpenAI)
if [ -n "$GEMINI_API_KEY" ]; then
    export DEFAULT_LLM_PROVIDER="gemini"
    echo "✅ Using Gemini 1.0 Pro (cheapest model)"
else
    export DEFAULT_LLM_PROVIDER="openai"
    echo "✅ Using OpenAI GPT-3.5-turbo (cheapest OpenAI model)"
fi

# Ultra-aggressive cost optimization
export MAX_TOKENS="50"          # Very short responses
export TEMPERATURE="0.1"       # Consistent, shorter outputs
export ENABLE_CACHING="true"   # Cache everything
export USE_REAL_LLM="true"     # Use real LLM (not simulation)

# Server configuration
export MCP_API_KEY=${MCP_API_KEY:-"demo-mcp-key-12345"}
export MCP_HOST=${MCP_HOST:-"0.0.0.0"}
export MCP_PORT=${MCP_PORT:-"9000"}

echo "📍 Host: $MCP_HOST"
echo "🔌 Port: $MCP_PORT"
echo "🔑 MCP API Key: $MCP_API_KEY"
echo "🤖 Default Provider: $DEFAULT_LLM_PROVIDER"
echo "💰 Max Tokens: $MAX_TOKENS (ultra-short responses)"
echo "🌡️  Temperature: $TEMPERATURE (consistent outputs)"
echo "💾 Caching: $ENABLE_CACHING (avoid duplicate calls)"

if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OpenAI API Key: ${OPENAI_API_KEY:0:10}... (Model: $OPENAI_MODEL)"
else
    echo "❌ OpenAI API Key: Not provided"
fi

if [ -n "$GEMINI_API_KEY" ]; then
    echo "✅ Gemini API Key: ${GEMINI_API_KEY:0:10}... (Model: $GEMINI_MODEL)"
else
    echo "❌ Gemini API Key: Not provided"
fi

echo ""
echo "💰 COST ESTIMATE:"
echo "   - Gemini 1.0 Pro: ~$0.125 per 1000 requests"
echo "   - OpenAI GPT-3.5: ~$0.25 per 1000 requests"
echo "   - With caching: 80%+ cost reduction"
echo ""

# Install required dependencies
echo "📦 Installing LLM dependencies..."
pip install openai google-generativeai

# Export all environment variables
export PYTHONUNBUFFERED=1

# Create logs directory
mkdir -p logs

# Start the enhanced server
echo "🚀 Starting ultra-cheap MCP server..."
python enhanced_server.py
