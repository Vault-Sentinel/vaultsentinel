#!/bin/bash
"""Start MCP server with real OpenAI and Gemini API keys."""

set -e

echo "🚀 Starting Enhanced VaultSentinel MCP Server with Real LLM"
echo "=========================================================="

# Check for required API keys
if [ -z "$OPENAI_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Error: No LLM API keys provided!"
    echo "Please set at least one of:"
    echo "  export OPENAI_API_KEY=sk-your-openai-key-here"
    echo "  export GEMINI_API_KEY=your-gemini-key-here"
    echo ""
    echo "Example:"
    echo "  export OPENAI_API_KEY=sk-proj-abc123..."
    echo "  export GEMINI_API_KEY=AIzaSyAbc123..."
    exit 1
fi

# Set default values
HOST=${MCP_HOST:-"0.0.0.0"}
PORT=${MCP_PORT:-"9000"}
API_KEY=${MCP_API_KEY:-"demo-mcp-key-12345"}
USE_REAL_LLM=${USE_REAL_LLM:-"true"}
DEFAULT_PROVIDER=${DEFAULT_LLM_PROVIDER:-"openai"}

echo "📍 Host: $HOST"
echo "🔌 Port: $PORT"
echo "🔑 MCP API Key: $API_KEY"
echo "🤖 Use Real LLM: $USE_REAL_LLM"
echo "🎯 Default Provider: $DEFAULT_PROVIDER"

if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OpenAI API Key: ${OPENAI_API_KEY:0:10}..."
else
    echo "❌ OpenAI API Key: Not provided"
fi

if [ -n "$GEMINI_API_KEY" ]; then
    echo "✅ Gemini API Key: ${GEMINI_API_KEY:0:10}..."
else
    echo "❌ Gemini API Key: Not provided"
fi

# Install required dependencies
echo "📦 Installing LLM dependencies..."
pip install openai google-generativeai

# Export environment variables
export MCP_API_KEY="$API_KEY"
export USE_REAL_LLM="$USE_REAL_LLM"
export DEFAULT_LLM_PROVIDER="$DEFAULT_PROVIDER"
export PYTHONUNBUFFERED=1

# Create logs directory
mkdir -p logs

# Start the enhanced server
echo "🚀 Starting enhanced MCP server..."
python enhanced_server.py
