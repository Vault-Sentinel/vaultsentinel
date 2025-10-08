#!/usr/bin/env python3
"""Enhanced MCP Server with Real OpenAI and Gemini Integration.

This MCP server can use real OpenAI and Gemini API keys for actual LLM processing.
"""

import os
import json
import uuid
import time
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# LLM Provider imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VaultSentinel Enhanced MCP Server",
    description="MCP server with real OpenAI and Gemini integration",
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

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MCP_API_KEY = os.getenv("MCP_API_KEY", "demo-mcp-key-12345")
DEFAULT_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
USE_REAL_LLM = os.getenv("USE_REAL_LLM", "false").lower() == "true"

# Model Configuration (Cost Optimization)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "100"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"

# Initialize LLM clients
openai_client = None
gemini_client = None

if OPENAI_AVAILABLE and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    openai_client = openai
    logger.info("✅ OpenAI client initialized")

if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_client = genai
    logger.info("✅ Gemini client initialized")

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
    llm_providers: Dict[str, bool]

# Storage for requests/responses
class RequestStorage:
    def __init__(self):
        self.requests = {}
        self.responses = {}
        self.cache = {}  # Simple in-memory cache for cost optimization
    
    def store_request(self, request_id: str, data: Dict[str, Any]):
        self.requests[request_id] = {
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
    
    def store_response(self, request_id: str, response: Dict[str, Any]):
        self.responses[request_id] = response
    
    def get_requests(self) -> Dict[str, Any]:
        return self.requests
    
    def get_responses(self) -> Dict[str, Any]:
        return self.responses
    
    def get_cache_key(self, prompt: str, model: str, provider: str) -> str:
        """Generate cache key for prompt."""
        import hashlib
        content = f"{prompt}_{model}_{provider}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available."""
        if ENABLE_CACHING and cache_key in self.cache:
            cached = self.cache[cache_key]
            # Check if cache is still valid (1 hour TTL)
            if time.time() - cached["timestamp"] < 3600:
                logger.info(f"Using cached response for key: {cache_key[:8]}...")
                return cached["response"]
        return None
    
    def cache_response(self, cache_key: str, response: Dict[str, Any]):
        """Cache response for future use."""
        if ENABLE_CACHING:
            self.cache[cache_key] = {
                "response": response,
                "timestamp": time.time()
            }
            logger.info(f"Cached response for key: {cache_key[:8]}...")

storage = RequestStorage()
startup_time = time.time()
request_count = 0

# Authentication
def verify_auth(request: Request) -> str:
    """Verify API key authentication."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    if token != MCP_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return token

def generate_request_id() -> str:
    """Generate a unique request ID."""
    return f"mcp-{uuid.uuid4()}"

async def call_openai(messages: List[Dict[str, str]], model: str = None, temperature: float = None) -> Dict[str, Any]:
    """Call OpenAI API with cost optimization."""
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not available")
    
    # Use configured defaults for cost optimization
    model = model or OPENAI_MODEL
    temperature = temperature or TEMPERATURE
    
    try:
        response = await openai_client.ChatCompletion.acreate(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=MAX_TOKENS  # Cost optimization: limit response length
        )
        
        content = response.choices[0].message.content
        
        # Parse the response to extract secret classification
        try:
            # Try to parse as JSON first
            parsed = json.loads(content)
            return {
                "text": content,
                "confidence": parsed.get("confidence", 0.8),
                "secret_type": parsed.get("secret_type", "unknown")
            }
        except json.JSONDecodeError:
            # If not JSON, create a structured response
            return {
                "text": json.dumps({
                    "is_secret": "secret" in content.lower() or "key" in content.lower(),
                    "confidence": 0.8,
                    "secret_type": "unknown",
                    "reasoning": content
                }),
                "confidence": 0.8,
                "secret_type": "unknown"
            }
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

async def call_gemini(prompt: str, model: str = None) -> Dict[str, Any]:
    """Call Gemini API with cost optimization."""
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini client not available")
    
    # Use configured default for cost optimization
    model = model or GEMINI_MODEL
    
    try:
        model_instance = gemini_client.GenerativeModel(model)
        response = await model_instance.generate_content_async(
            prompt,
            generation_config={
                "max_output_tokens": MAX_TOKENS,  # Cost optimization: limit response length
                "temperature": TEMPERATURE,  # Cost optimization: lower temperature
            }
        )
        
        content = response.text
        
        # Parse the response to extract secret classification
        try:
            parsed = json.loads(content)
            return {
                "text": content,
                "confidence": parsed.get("confidence", 0.8),
                "secret_type": parsed.get("secret_type", "unknown")
            }
        except json.JSONDecodeError:
            return {
                "text": json.dumps({
                    "is_secret": "secret" in content.lower() or "key" in content.lower(),
                    "confidence": 0.8,
                    "secret_type": "unknown",
                    "reasoning": content
                }),
                "confidence": 0.8,
                "secret_type": "unknown"
            }
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

def simulate_llm_processing(prompt: str, model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
    """Simulate LLM processing for testing (fallback)."""
    time.sleep(0.1)
    
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
        uptime=time.time() - startup_time,
        llm_providers={
            "openai": openai_client is not None,
            "gemini": gemini_client is not None,
            "use_real_llm": USE_REAL_LLM
        }
    )

@app.post("/v1/chat")
async def chat_completion(
    request: ChatRequest,
    token: str = Depends(verify_auth)
):
    """Chat completion endpoint with real LLM integration."""
    global request_count
    request_count += 1
    
    request_id = generate_request_id()
    
    logger.info(f"Chat request {request_id} from token {token[:10]}...")
    storage.store_request(request_id, request.conversation)
    
    try:
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
        
        # Determine which LLM provider to use
        provider = request.conversation.get("provider", DEFAULT_PROVIDER)
        
        # Check cache first for cost optimization
        cache_key = storage.get_cache_key(user_message, model, provider)
        cached_result = storage.get_cached_response(cache_key)
        
        if cached_result:
            result = cached_result
            logger.info(f"Using cached response for {provider} model {model}")
        elif USE_REAL_LLM:
            if provider == "openai" and openai_client:
                result = await call_openai(messages, model, temperature)
            elif provider == "gemini" and gemini_client:
                result = await call_gemini(user_message, model)
            else:
                # Fallback to simulation
                result = simulate_llm_processing(user_message, model)
            
            # Cache the result for future use
            storage.cache_response(cache_key, result)
        else:
            # Use simulation mode
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
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(result["text"].split()),
                    "total_tokens": len(user_message.split()) + len(result["text"].split())
                },
                "processing_time_ms": 100,
                "timestamp": datetime.utcnow().isoformat(),
                "provider": provider,
                "use_real_llm": USE_REAL_LLM
            }
        }
        
        storage.store_response(request_id, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/complete")
async def text_completion(
    request: CompletionRequest,
    token: str = Depends(verify_auth)
):
    """Text completion endpoint with real LLM integration."""
    global request_count
    request_count += 1
    
    request_id = generate_request_id()
    
    logger.info(f"Completion request {request_id} from token {token[:10]}...")
    storage.store_request(request_id, {"prompt": request.prompt, "params": request.params})
    
    try:
        model = request.params.get("model", "gpt-3.5-turbo")
        temperature = request.params.get("temperature", 0.1)
        provider = request.params.get("provider", DEFAULT_PROVIDER)
        
        if USE_REAL_LLM:
            if provider == "openai" and openai_client:
                # Convert to chat format for OpenAI
                messages = [{"role": "user", "content": request.prompt}]
                result = await call_openai(messages, model, temperature)
            elif provider == "gemini" and gemini_client:
                result = await call_gemini(request.prompt, model)
            else:
                result = simulate_llm_processing(request.prompt, model)
        else:
            result = simulate_llm_processing(request.prompt, model)
        
        response = {
            "request_id": request_id,
            "result": {
                "text": result["text"],
                "confidence": result["confidence"],
                "secret_type": result["secret_type"]
            },
            "meta": {
                "model": model,
                "usage": {
                    "prompt_tokens": len(request.prompt.split()),
                    "completion_tokens": len(result["text"].split()),
                    "total_tokens": len(request.prompt.split()) + len(result["text"].split())
                },
                "processing_time_ms": 100,
                "timestamp": datetime.utcnow().isoformat(),
                "provider": provider,
                "use_real_llm": USE_REAL_LLM
            }
        }
        
        storage.store_response(request_id, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Text completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/stats")
async def get_stats(token: str = Depends(verify_auth)):
    """Get server statistics."""
    return {
        "uptime_seconds": time.time() - startup_time,
        "total_requests": request_count,
        "stored_requests": len(storage.requests),
        "stored_responses": len(storage.responses),
        "timestamp": datetime.utcnow().isoformat(),
        "llm_providers": {
            "openai": openai_client is not None,
            "gemini": gemini_client is not None,
            "use_real_llm": USE_REAL_LLM
        }
    }

@app.get("/v1/requests")
async def get_requests(token: str = Depends(verify_auth)):
    """Get recent requests and responses."""
    return {
        "requests": storage.get_requests(),
        "responses": storage.get_responses()
    }

if __name__ == "__main__":
    # Cloud Run compatibility
    port = int(os.getenv("PORT", 9000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print("🚀 Starting Enhanced VaultSentinel MCP Server")
    print("=" * 50)
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔑 MCP API Key: {MCP_API_KEY}")
    print(f"🤖 OpenAI Available: {openai_client is not None}")
    print(f"🤖 Gemini Available: {gemini_client is not None}")
    print(f"🔧 Use Real LLM: {USE_REAL_LLM}")
    print(f"🌐 Health check: http://{host}:{port}/health")
    print(f"📚 API docs: http://{host}:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)
