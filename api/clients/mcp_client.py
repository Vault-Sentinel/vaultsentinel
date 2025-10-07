"""MCP (Model Context Protocol) client for VaultSentinel.

This module provides a secure, robust client for communicating with MCP servers,
including authentication, retries, circuit breaker, and telemetry.
"""

import os
import time
import uuid
import logging
import asyncio
from typing import Optional, Dict, Any, List
import httpx
from functools import wraps

logger = logging.getLogger(__name__)

# Configuration from environment
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:9000")
AUTH_TYPE = os.getenv("MCP_AUTH_TYPE", "api_key")
API_KEY = os.getenv("MCP_API_KEY")
OAUTH_TOKEN_URL = os.getenv("MCP_OAUTH_TOKEN_URL")
CLIENT_ID = os.getenv("MCP_CLIENT_ID")
CLIENT_SECRET = os.getenv("MCP_CLIENT_SECRET")
DEFAULT_TIMEOUT = int(os.getenv("MCP_TIMEOUT_SECONDS", "30"))
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# Circuit breaker configuration
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60  # seconds


class MCPClientError(Exception):
    """Base exception for MCP client errors."""
    pass


class MCPAuthError(MCPClientError):
    """Authentication error."""
    pass


class MCPRateLimitError(MCPClientError):
    """Rate limit error."""
    pass


class MCPCircuitBreakerError(MCPClientError):
    """Circuit breaker is open."""
    pass


class MCPClient:
    """MCP client with authentication, retries, and circuit breaker."""
    
    def __init__(self, base_url: str = MCP_BASE_URL, timeout: int = DEFAULT_TIMEOUT):
        """Initialize MCP client."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._token = None
        self._consecutive_errors = 0
        self._circuit_opened_at = None
        self._request_count = 0
        
    async def _get_oauth_token(self) -> str:
        """Get OAuth2 token using client credentials flow."""
        if self._token:
            return self._token
            
        if not OAUTH_TOKEN_URL or not CLIENT_ID or not CLIENT_SECRET:
            raise MCPAuthError("OAuth2 credentials not configured")
            
        data = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(OAUTH_TOKEN_URL, data=data)
                response.raise_for_status()
                token_data = response.json()
                self._token = token_data.get("access_token")
                
                if not self._token:
                    raise MCPAuthError("No access token in OAuth response")
                    
                return self._token
                
        except httpx.RequestError as e:
            raise MCPAuthError(f"OAuth token request failed: {e}")
        except Exception as e:
            raise MCPAuthError(f"OAuth token error: {e}")
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self._circuit_opened_at is None:
            return False
        # Check if enough time has passed to reset circuit
        return (time.time() - self._circuit_opened_at) < CIRCUIT_BREAKER_TIMEOUT
    
    def _record_success(self):
        """Record successful request and reset circuit breaker."""
        self._consecutive_errors = 0
        self._circuit_opened_at = None
    
    def _record_failure(self):
        """Record failed request and potentially open circuit breaker."""
        self._consecutive_errors += 1
        if self._consecutive_errors >= CIRCUIT_BREAKER_THRESHOLD:
            self._circuit_opened_at = time.time()
            logger.error(
                "Circuit breaker opened after %d consecutive errors",
                self._consecutive_errors
            )
    
    def _redact_secrets(self, text: str) -> str:
        """Redact potential secrets from log messages."""
        if not text:
            return text
            
        # Common secret patterns to redact
        secret_patterns = [
            (r'api[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'api_key=***REDACTED***'),
            (r'token["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'token=***REDACTED***'),
            (r'secret["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'secret=***REDACTED***'),
            (r'password["\s]*[:=]["\s]*([^\s]{8,})', r'password=***REDACTED***'),
        ]
        
        import re
        redacted = text
        for pattern, replacement in secret_patterns:
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
        
        return redacted
    
    async def _request(
        self, 
        method: str, 
        path: str, 
        json: dict = None, 
        headers: dict = None, 
        retries: int = 3
    ) -> dict:
        """Make HTTP request with retries and circuit breaker."""
        if self._is_circuit_open():
            raise MCPCircuitBreakerError("Circuit breaker is open due to prior failures")
        
        url = f"{self.base_url}{path}"
        headers = headers or {}
        
        # Add authentication
        if AUTH_TYPE == "api_key" and API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"
        elif AUTH_TYPE == "oauth2":
            try:
                token = await self._get_oauth_token()
                headers["Authorization"] = f"Bearer {token}"
            except MCPAuthError as e:
                logger.error("OAuth authentication failed: %s", str(e))
                raise
        elif AUTH_TYPE == "none":
            pass  # No authentication
        else:
            logger.warning("Unknown auth type: %s", AUTH_TYPE)
        
        # Add request ID for tracing
        request_id = str(uuid.uuid4())
        headers["X-Request-ID"] = request_id
        
        backoff = 0.5
        last_exception = None
        
        for attempt in range(1, retries + 1):
            start_time = time.time()
            self._request_count += 1
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, url, json=json, headers=headers)
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Log request (redacted)
                logger.info(
                    "MCP request %s %s - status: %d, latency: %dms, attempt: %d",
                    method, path, response.status_code, latency_ms, attempt
                )
                
                # Handle different status codes
                if response.status_code >= 500:
                    # Server error - retry
                    self._record_failure()
                    raise MCPClientError(f"Server error: {response.status_code}")
                
                elif response.status_code == 429:
                    # Rate limit - respect Retry-After header
                    retry_after = response.headers.get("Retry-After")
                    wait_time = int(retry_after) if retry_after and retry_after.isdigit() else backoff
                    
                    logger.warning(
                        "Rate limited, waiting %ds before retry (attempt %d/%d)",
                        wait_time, attempt, retries
                    )
                    
                    if attempt < retries:
                        await asyncio.sleep(wait_time)
                        backoff *= 2
                        continue
                    else:
                        raise MCPRateLimitError("Rate limit exceeded")
                
                elif response.status_code in (401, 403):
                    # Auth error - don't retry
                    self._record_failure()
                    logger.error("Authentication failed: %s", response.status_code)
                    raise MCPAuthError(f"Authentication failed: {response.status_code}")
                
                elif response.status_code >= 400:
                    # Client error - don't retry
                    self._record_failure()
                    raise MCPClientError(f"Client error: {response.status_code}")
                
                # Success
                self._record_success()
                response_data = response.json()
                
                # Add telemetry
                response_data["mcp_meta"] = {
                    "request_id": request_id,
                    "latency_ms": latency_ms,
                    "attempt": attempt,
                    "status_code": response.status_code
                }
                
                return response_data
                
            except (httpx.RequestError, MCPClientError) as e:
                last_exception = e
                self._record_failure()
                
                logger.warning(
                    "MCP request attempt %d failed: %s",
                    attempt, self._redact_secrets(str(e))
                )
                
                if attempt == retries:
                    break
                
                # Exponential backoff with jitter
                jitter = 0.1 * (2 ** (attempt - 1)) * (0.5 + 0.5 * (hash(str(time.time())) % 100) / 100)
                await asyncio.sleep(backoff + jitter)
                backoff *= 2
        
        # All retries failed
        if last_exception:
            raise last_exception
        else:
            raise MCPClientError("All retry attempts failed")
    
    async def chat(self, conversation: Dict[str, Any], timeout: Optional[int] = None) -> Dict[str, Any]:
        """Send chat completion request to MCP server."""
        body = {"conversation": conversation}
        
        try:
            response = await self._request("POST", "/v1/chat", json=body)
            
            # Normalize response format
            return {
                "request_id": response.get("request_id") or str(uuid.uuid4()),
                "status": "ok" if response.get("choices") or response.get("result") else "error",
                "result": response.get("choices") or response.get("result") or response,
                "mcp_meta": response.get("mcp_meta", {})
            }
            
        except Exception as e:
            logger.error("Chat request failed: %s", self._redact_secrets(str(e)))
            return {
                "request_id": str(uuid.uuid4()),
                "status": "error",
                "result": None,
                "mcp_meta": {"error": str(e)}
            }
    
    async def completion(self, prompt: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send completion request to MCP server."""
        body = {
            "prompt": prompt,
            "params": params or {}
        }
        
        try:
            response = await self._request("POST", "/v1/complete", json=body)
            
            # Normalize response format
            return {
                "request_id": response.get("request_id") or str(uuid.uuid4()),
                "status": "ok" if response.get("choices") or response.get("result") else "error",
                "result": response.get("choices") or response.get("result") or response,
                "mcp_meta": response.get("mcp_meta", {})
            }
            
        except Exception as e:
            logger.error("Completion request failed: %s", self._redact_secrets(str(e)))
            return {
                "request_id": str(uuid.uuid4()),
                "status": "error",
                "result": None,
                "mcp_meta": {"error": str(e)}
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "consecutive_errors": self._consecutive_errors,
            "circuit_open": self._is_circuit_open(),
            "circuit_opened_at": self._circuit_opened_at,
            "request_count": self._request_count,
            "base_url": self.base_url,
            "timeout": self.timeout
        }


class MockMCPClient(MCPClient):
    """Mock MCP client for demo mode."""
    
    def __init__(self, base_url: str = "http://localhost:9000", timeout: int = 30):
        """Initialize mock client."""
        super().__init__(base_url, timeout)
        self._demo_responses = self._load_demo_responses()
    
    def _load_demo_responses(self) -> Dict[str, Any]:
        """Load deterministic demo responses."""
        return {
            "chat": {
                "request_id": "demo-chat-001",
                "status": "ok",
                "result": [
                    {
                        "text": "This is a deterministic demo response for secret classification.",
                        "confidence": 0.85,
                        "reasoning": "Demo mode - simulated LLM analysis"
                    }
                ],
                "mcp_meta": {
                    "model": "demo-gpt-3.5-turbo",
                    "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75}
                }
            },
            "completion": {
                "request_id": "demo-completion-001", 
                "status": "ok",
                "result": {
                    "text": "This is a deterministic demo completion response.",
                    "confidence": 0.90
                },
                "mcp_meta": {
                    "model": "demo-gpt-4",
                    "usage": {"prompt_tokens": 30, "completion_tokens": 15, "total_tokens": 45}
                }
            }
        }
    
    async def chat(self, conversation: Dict[str, Any], timeout: Optional[int] = None) -> Dict[str, Any]:
        """Return deterministic demo response for chat."""
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        response = self._demo_responses["chat"].copy()
        response["request_id"] = f"demo-{uuid.uuid4()}"
        
        # Add some variation based on conversation content
        if "secret" in str(conversation).lower():
            response["result"][0]["confidence"] = 0.95
            response["result"][0]["reasoning"] = "Demo mode - high confidence secret detection"
        else:
            response["result"][0]["confidence"] = 0.65
            response["result"][0]["reasoning"] = "Demo mode - low confidence, likely not a secret"
        
        return response
    
    async def completion(self, prompt: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Return deterministic demo response for completion."""
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        response = self._demo_responses["completion"].copy()
        response["request_id"] = f"demo-{uuid.uuid4()}"
        
        # Add some variation based on prompt content
        if "classify" in prompt.lower():
            response["result"]["confidence"] = 0.88
            response["result"]["text"] = "Demo mode - classification result: likely secret"
        else:
            response["result"]["confidence"] = 0.75
            response["result"]["text"] = "Demo mode - general completion response"
        
        return response


# Global client instance
_client_instance: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get the global MCP client instance."""
    global _client_instance
    if _client_instance is None:
        if DEMO_MODE:
            _client_instance = MockMCPClient()
            logger.info("Using MockMCPClient for demo mode")
        else:
            _client_instance = MCPClient()
            logger.info("Using MCPClient for production mode")
    return _client_instance


def reset_client():
    """Reset the global client instance (useful for testing)."""
    global _client_instance
    _client_instance = None
