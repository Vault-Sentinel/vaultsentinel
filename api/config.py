"""Configuration management for VaultSentinel API."""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class APISettings(BaseSettings):
    """API-only application settings."""
    
    # Database
    database_url: str = Field(default="sqlite:///./vaultsentinel.db", env="DATABASE_URL")
    
    # MCP Configuration
    mcp_base_url: str = Field(default="http://localhost:9000", env="MCP_BASE_URL")
    mcp_auth_type: str = Field(default="api_key", env="MCP_AUTH_TYPE")
    mcp_api_key: Optional[str] = Field(default=None, env="MCP_API_KEY")
    mcp_oauth_token_url: Optional[str] = Field(default=None, env="MCP_OAUTH_TOKEN_URL")
    mcp_client_id: Optional[str] = Field(default=None, env="MCP_CLIENT_ID")
    mcp_client_secret: Optional[str] = Field(default=None, env="MCP_CLIENT_SECRET")
    mcp_timeout_seconds: int = Field(default=30, env="MCP_TIMEOUT_SECONDS")
    demo_mode: bool = Field(default=False, env="DEMO_MODE")
    
    # MCP Proxy Configuration
    mcp_timeout_ms: int = Field(default=20000, env="MCP_TIMEOUT_MS")
    mcp_retries: int = Field(default=2, env="MCP_RETRIES")
    mcp_auth_header: str = Field(default="Authorization", env="MCP_AUTH_HEADER")
    
    # Web Configuration
    frontend_origin: str = Field(default="http://localhost:3000", env="FRONTEND_ORIGIN")
    backend_origin: str = Field(default="http://localhost:8000", env="BACKEND_ORIGIN")
    node_env: str = Field(default="development", env="NODE_ENV")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Create settings instance
settings = APISettings()


def get_redacted_config() -> dict:
    """Get configuration with sensitive values redacted."""
    return {
        "database_url": settings.database_url,
        "mcp_base_url": settings.mcp_base_url,
        "mcp_auth_type": settings.mcp_auth_type,
        "mcp_api_key": f"{settings.mcp_api_key[:8]}..." if settings.mcp_api_key else None,
        "demo_mode": settings.demo_mode,
        "frontend_origin": settings.frontend_origin,
        "backend_origin": settings.backend_origin,
        "node_env": settings.node_env,
    }
