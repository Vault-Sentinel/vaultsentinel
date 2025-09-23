"""Configuration management for VaultSentinel."""

import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """VaultSentinel configuration."""
    
    # GitHub Configuration
    github_repo: str = ""
    github_token: str = ""
    
    # Scanning Configuration
    poll_interval_seconds: int = 120
    scan_depth_commits: int = 10
    
    # Slack Configuration
    slack_webhook_url: str = ""
    
    # Remediation Configuration
    remediation_enabled: bool = False
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Detection Configuration
    detection_entropy_threshold: float = 4.5
    allowlist_paths: List[str] = field(default_factory=lambda: ["/tests/", "/examples/", "/fixtures/"])
    denylist_patterns: List[str] = field(default_factory=lambda: ["dummy", "example", "test", "mock"])
    
    # Database Configuration
    database_url: str = "sqlite:///./vaultsentinel.db"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Security Configuration
    mask_secrets: bool = True
    max_secret_length: int = 100
    
    # LLM Configuration
    llm_classifier_enabled: bool = False
    llm_provider: str = "openai"  # openai, gemini, both
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    gemini_model: str = "gemini-1.5-flash"
    llm_confidence_threshold: float = 0.7
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        return cls(
            github_repo=os.getenv("GITHUB_REPO", ""),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "120")),
            scan_depth_commits=int(os.getenv("SCAN_DEPTH_COMMITS", "10")),
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
            remediation_enabled=os.getenv("REMEDIATION_ENABLED", "false").lower() == "true",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            detection_entropy_threshold=float(os.getenv("DETECTION_ENTROPY_THRESHOLD", "4.5")),
            allowlist_paths=os.getenv("ALLOWLIST_PATHS", "/tests/,/examples/,/fixtures/").split(","),
            denylist_patterns=os.getenv("DENYLIST_PATTERNS", "dummy,example,test,mock").split(","),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./vaultsentinel.db"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "json"),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
            llm_classifier_enabled=os.getenv("LLM_CLASSIFIER_ENABLED", "false").lower() == "true",
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            llm_confidence_threshold=float(os.getenv("LLM_CONFIDENCE_THRESHOLD", "0.7")),
        )
    
    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Create config from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with sensitive values redacted."""
        return {
            "github_repo": self.github_repo,
            "poll_interval_seconds": self.poll_interval_seconds,
            "scan_depth_commits": self.scan_depth_commits,
            "slack_webhook_url": f"{self.slack_webhook_url[:20]}..." if self.slack_webhook_url else None,
            "remediation_enabled": self.remediation_enabled,
            "aws_access_key_id": f"{self.aws_access_key_id[:8]}..." if self.aws_access_key_id else None,
            "detection_entropy_threshold": self.detection_entropy_threshold,
            "allowlist_paths": self.allowlist_paths,
            "denylist_patterns": self.denylist_patterns,
            "database_url": self.database_url,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "llm_classifier_enabled": self.llm_classifier_enabled,
            "llm_provider": self.llm_provider,
            "openai_model": self.openai_model,
            "gemini_model": self.gemini_model,
            "llm_confidence_threshold": self.llm_confidence_threshold,
            "openai_api_key": f"{self.openai_api_key[:8]}..." if self.openai_api_key else None,
            "gemini_api_key": f"{self.gemini_api_key[:8]}..." if self.gemini_api_key else None,
        }
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.github_repo:
            errors.append("GITHUB_REPO is required")
        
        if not self.github_token:
            errors.append("GITHUB_TOKEN is required")
        
        if not self.slack_webhook_url:
            errors.append("SLACK_WEBHOOK_URL is required")
        
        if self.remediation_enabled and not (self.aws_access_key_id and self.aws_secret_access_key):
            errors.append("AWS credentials required when remediation is enabled")
        
        if self.poll_interval_seconds < 60:
            errors.append("POLL_INTERVAL_SECONDS must be at least 60 seconds")
        
        if self.scan_depth_commits < 1:
            errors.append("SCAN_DEPTH_COMMITS must be at least 1")
        
        return errors


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
