#!/usr/bin/env python3
"""Local MCP Server for VaultSentinel Testing.

This is a simple MCP server implementation that can be used for testing
the VaultSentinel MCP client integration.
"""

import os
import json
import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VaultSentinel MCP Server",
    description="Local MCP server for testing VaultSentinel integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class ChatRequest(BaseModel):
    conversation: Dict[str, Any]

class CompletionRequest(BaseModel):
    prompt: str
    params: Dict[str, Any] = {}

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime: float

# Global state
startup_time = time.time()
request_count = 0

# Simple in-memory storage for demo
class MCPStorage:
    def __init__(self):
        self.requests = []
        self.responses = {}
    
    def store_request(self, request_id: str, request_data: Dict[str, Any]):
        self.requests.append({
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": request_data
        })
    
    def store_response(self, request_id: str, response_data: Dict[str, Any]):
        self.responses[request_id] = response_data

storage = MCPStorage()

# Authentication middleware
def verify_auth(request: Request):
    """Verify authentication for MCP requests."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    # Simple token validation (in production, use proper JWT validation)
    valid_tokens = [
        os.getenv("MCP_API_KEY", "demo-mcp-key-12345"),
        "demo-mcp-key-12345",
        "test-token-12345"
    ]
    
    if token not in valid_tokens:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return token

# Utility functions
def generate_request_id() -> str:
    """Generate a unique request ID."""
    return f"mcp-{uuid.uuid4()}"

def simulate_llm_processing(prompt: str, model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
    """Simulate LLM processing for testing."""
    # Simulate processing time
    time.sleep(0.1)
    
    # Generate deterministic response based on content
    if "secret" in prompt.lower() or "key" in prompt.lower():
        return {
            "text": json.dumps({
                "is_secret": True,
                "confidence": 0.95,
                "secret_type": "aws_access_key",
                "reasoning": "High confidence secret detection - appears to be AWS access key"
            }),
            "confidence": 0.95,
            "secret_type": "aws_access_key"
        }
    elif "password" in prompt.lower():
        return {
            "text": json.dumps({
                "is_secret": True,
                "confidence": 0.88,
                "secret_type": "password",
                "reasoning": "Medium confidence password detection"
            }),
            "confidence": 0.88,
            "secret_type": "password"
        }
    else:
        return {
            "text": json.dumps({
                "is_secret": False,
                "confidence": 0.65,
                "secret_type": "unknown",
                "reasoning": "Low confidence - likely not a secret"
            }),
            "confidence": 0.65,
            "secret_type": "unknown"
        }

# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        uptime=time.time() - startup_time
    )

@app.post("/v1/chat")
async def chat_completion(
    request: ChatRequest,
    token: str = Depends(verify_auth)
):
    """Chat completion endpoint."""
    global request_count
    request_count += 1
    
    request_id = generate_request_id()
    
    # Log request
    logger.info(f"Chat request {request_id} from token {token[:10]}...")
    
    # Store request
    storage.store_request(request_id, request.conversation)
    
    try:
        # Extract messages and model
        messages = request.conversation.get("messages", [])
        model = request.conversation.get("model", "gpt-3.5-turbo")
        temperature = request.conversation.get("temperature", 0.1)
        max_tokens = request.conversation.get("max_tokens", 200)
        
        # Find user message
        user_message = None
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Simulate LLM processing
        result = simulate_llm_processing(user_message, model)
        
        # Create response
        response = {
            "request_id": request_id,
            "choices": [
                {
                    "text": result["text"],
                    "confidence": result["confidence"],
                    "secret_type": result["secret_type"]
                }
            ],
            "meta": {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "usage": {
                    "prompt_tokens": len(user_message.split()) * 2,
                    "completion_tokens": len(result["text"].split()),
                    "total_tokens": len(user_message.split()) * 2 + len(result["text"].split())
                },
                "processing_time_ms": 100,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Store response
        storage.store_response(request_id, response)
        
        logger.info(f"Chat response {request_id} completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Chat request {request_id} failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/v1/complete")
async def text_completion(
    request: CompletionRequest,
    token: str = Depends(verify_auth)
):
    """Text completion endpoint."""
    global request_count
    request_count += 1
    
    request_id = generate_request_id()
    
    # Log request
    logger.info(f"Completion request {request_id} from token {token[:10]}...")
    
    # Store request
    storage.store_request(request_id, {
        "prompt": request.prompt,
        "params": request.params
    })
    
    try:
        # Simulate LLM processing
        result = simulate_llm_processing(request.prompt)
        
        # Create response
        response = {
            "request_id": request_id,
            "result": {
                "text": result["text"],
                "confidence": result["confidence"],
                "secret_type": result["secret_type"]
            },
            "meta": {
                "model": "gpt-3.5-turbo",
                "usage": {
                    "prompt_tokens": len(request.prompt.split()),
                    "completion_tokens": len(result["text"].split()),
                    "total_tokens": len(request.prompt.split()) + len(result["text"].split())
                },
                "processing_time_ms": 100,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Store response
        storage.store_response(request_id, response)
        
        logger.info(f"Completion response {request_id} completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Completion request {request_id} failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/v1/stats")
async def get_stats(token: str = Depends(verify_auth)):
    """Get server statistics."""
    return {
        "uptime_seconds": time.time() - startup_time,
        "total_requests": request_count,
        "stored_requests": len(storage.requests),
        "stored_responses": len(storage.responses),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/v1/requests")
async def get_requests(token: str = Depends(verify_auth)):
    """Get recent requests (for debugging)."""
    return {
        "requests": storage.requests[-10:],  # Last 10 requests
        "responses": dict(list(storage.responses.items())[-10:])  # Last 10 responses
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "request_id": request.headers.get("X-Request-ID", "unknown"),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "Internal server error",
        "status_code": 500,
        "request_id": request.headers.get("X-Request-ID", "unknown"),
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VaultSentinel MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting VaultSentinel MCP Server")
    print(f"📍 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🔑 API Key: {os.getenv('MCP_API_KEY', 'demo-mcp-key-12345')}")
    print(f"🌐 Health check: http://{args.host}:{args.port}/health")
    print(f"📚 API docs: http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        reload=args.debug,
        log_level="info" if not args.debug else "debug"
    )
