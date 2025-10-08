#!/bin/bash
"""Start MCP server with proper configuration."""

set -e

echo "🚀 Starting VaultSentinel MCP Server"
echo "=================================="

# Set default values
HOST=${MCP_HOST:-"0.0.0.0"}
PORT=${MCP_PORT:-"9000"}
API_KEY=${MCP_API_KEY:-"demo-mcp-key-12345"}
DEBUG=${MCP_DEBUG:-"false"}

echo "📍 Host: $HOST"
echo "🔌 Port: $PORT"
echo "🔑 API Key: $API_KEY"
echo "🐛 Debug: $DEBUG"

# Export environment variables
export MCP_API_KEY="$API_KEY"
export PYTHONUNBUFFERED=1

# Create logs directory
mkdir -p logs

# Start the server
if [ "$DEBUG" = "true" ]; then
    echo "🐛 Starting in debug mode..."
    python server.py --host "$HOST" --port "$PORT" --debug
else
    echo "🚀 Starting in production mode..."
    python server.py --host "$HOST" --port "$PORT"
fi
