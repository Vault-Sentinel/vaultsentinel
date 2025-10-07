"""MCP client module for VaultSentinel.

This module provides access to the MCP (Model Context Protocol) client
for secure LLM communication.
"""

from .mcp_client import get_mcp_client, MCPClient, MockMCPClient, reset_client
from .mcp_client import MCPClientError, MCPAuthError, MCPRateLimitError, MCPCircuitBreakerError

__all__ = [
    "get_mcp_client",
    "MCPClient", 
    "MockMCPClient",
    "reset_client",
    "MCPClientError",
    "MCPAuthError", 
    "MCPRateLimitError",
    "MCPCircuitBreakerError"
]
