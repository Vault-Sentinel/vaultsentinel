"""Configuration management for VaultSentinel."""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # GitHub Configuration
    github_repo: Optional[str] = Field(default=None, env="GITHUB_REPO")
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    
    # Scanning Configuration
    poll_interval_seconds: int = Field(default=120, env="POLL_INTERVAL_SECONDS")
    scan_depth_commits: int = Field(default=10, env="SCAN_DEPTH_COMMITS")
    
    # Slack Configuration
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    
    # Remediation Configuration
    remediation_enabled: bool = Field(default=False, env="REMEDIATION_ENABLED")
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    
    # Detection Configuration
    detection_entropy_threshold: float = Field(default=4.5, env="DETECTION_ENTROPY_THRESHOLD")
    allowlist_paths: List[str] = Field(default=["/tests/", "/examples/", "/fixtures/"], env="ALLOWLIST_PATHS")
    denylist_patterns: List[str] = Field(default=["dummy", "example", "test", "mock"], env="DENYLIST_PATTERNS")
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


def get_redacted_config() -> dict:
    """Get configuration with sensitive values redacted."""
    return {
        "github_repo": settings.github_repo,
        "poll_interval_seconds": settings.poll_interval_seconds,
        "scan_depth_commits": settings.scan_depth_commits,
        "slack_webhook_url": f"{settings.slack_webhook_url[:20]}..." if settings.slack_webhook_url else None,
        "remediation_enabled": settings.remediation_enabled,
        "aws_access_key_id": f"{settings.aws_access_key_id[:8]}..." if settings.aws_access_key_id else None,
        "detection_entropy_threshold": settings.detection_entropy_threshold,
        "allowlist_paths": settings.allowlist_paths,
        "denylist_patterns": settings.denylist_patterns,
        "database_url": settings.database_url,
        "mcp_base_url": settings.mcp_base_url,
        "mcp_auth_type": settings.mcp_auth_type,
        "mcp_api_key": f"{settings.mcp_api_key[:8]}..." if settings.mcp_api_key else None,
        "demo_mode": settings.demo_mode,
    }
