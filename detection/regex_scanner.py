"""Regex-based secret detection patterns."""

import re
import hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SecretMatch:
    """Represents a detected secret."""
    secret: str
    secret_kind: str
    confidence: float
    masked_preview: str
    fingerprint: str
    line_start: int
    line_end: int


class RegexScanner:
    """Regex-based secret scanner."""
    
    def __init__(self):
        """Initialize with detection patterns."""
        self.patterns = {
            "aws_access_key": {
                "regex": r"AKIA[0-9A-Z]{16}",
                "confidence": 0.9,
                "mask_func": self._mask_aws_key
            },
            "aws_secret_key": {
                "regex": r"[A-Za-z0-9/+=]{40}",
                "confidence": 0.8,
                "mask_func": self._mask_generic
            },
            "gcp_service_account": {
                "regex": r"\"type\":\s*\"service_account\"",
                "confidence": 0.7,
                "mask_func": self._mask_generic
            },
            "slack_webhook": {
                "regex": r"https://hooks\.slack\.com/services/[A-Za-z0-9_/]+",
                "confidence": 0.9,
                "mask_func": self._mask_url
            },
            "github_token": {
                "regex": r"gh[ops]_[A-Za-z0-9_]{36}",
                "confidence": 0.9,
                "mask_func": self._mask_generic
            },
            "bearer_token": {
                "regex": r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
                "confidence": 0.7,
                "mask_func": self._mask_bearer
            },
            "jwt_token": {
                "regex": r"eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
                "confidence": 0.8,
                "mask_func": self._mask_jwt
            },
            "rsa_private_key": {
                "regex": r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----",
                "confidence": 0.95,
                "mask_func": self._mask_private_key
            },
            "postgres_url": {
                "regex": r"postgres://[^:\s]+:[^@\s]+@[^/\s]+/[^\s]+",
                "confidence": 0.8,
                "mask_func": self._mask_db_url
            },
            "mysql_url": {
                "regex": r"mysql://[^:\s]+:[^@\s]+@[^/\s]+/[^\s]+",
                "confidence": 0.8,
                "mask_func": self._mask_db_url
            },
            "mongodb_url": {
                "regex": r"mongodb(?:\+srv)?://[^:\s]+:[^@\s]+@[^/\s]+/[^\s]+",
                "confidence": 0.8,
                "mask_func": self._mask_db_url
            }
        }
    
    def scan_text(self, text: str, file_path: str = "") -> List[SecretMatch]:
        """Scan text for secrets using regex patterns."""
        matches = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for secret_kind, pattern_info in self.patterns.items():
                regex = re.compile(pattern_info["regex"], re.IGNORECASE)
                for match in regex.finditer(line):
                    secret = match.group(0)
                    confidence = pattern_info["confidence"]
                    masked_preview = pattern_info["mask_func"](secret)
                    fingerprint = self._compute_fingerprint(secret)
                    
                    matches.append(SecretMatch(
                        secret=secret,
                        secret_kind=secret_kind,
                        confidence=confidence,
                        masked_preview=masked_preview,
                        fingerprint=fingerprint,
                        line_start=line_num,
                        line_end=line_num
                    ))
        
        return matches
    
    def _compute_fingerprint(self, secret: str) -> str:
        """Compute SHA256 fingerprint for deduplication."""
        return hashlib.sha256(secret.encode()).hexdigest()
    
    def _mask_aws_key(self, secret: str) -> str:
        """Mask AWS access key."""
        if len(secret) >= 4:
            return secret[:4] + "*" * (len(secret) - 4)
        return "*" * len(secret)
    
    def _mask_generic(self, secret: str) -> str:
        """Generic masking."""
        if len(secret) <= 8:
            return "*" * len(secret)
        return secret[:4] + "*" * (len(secret) - 8) + secret[-4:]
    
    def _mask_url(self, secret: str) -> str:
        """Mask URL secrets."""
        if "://" in secret:
            parts = secret.split("://", 1)
            if len(parts) == 2:
                return parts[0] + "://***"
        return "*" * len(secret)
    
    def _mask_bearer(self, secret: str) -> str:
        """Mask bearer token."""
        if secret.startswith("Bearer "):
            return "Bearer " + "*" * (len(secret) - 7)
        return "*" * len(secret)
    
    def _mask_jwt(self, secret: str) -> str:
        """Mask JWT token."""
        parts = secret.split('.')
        if len(parts) >= 3:
            return parts[0] + "." + "*" * len(parts[1]) + "." + "*" * len(parts[2])
        return "*" * len(secret)
    
    def _mask_private_key(self, secret: str) -> str:
        """Mask private key."""
        return "-----BEGIN PRIVATE KEY-----***"
    
    def _mask_db_url(self, secret: str) -> str:
        """Mask database URL."""
        if "://" in secret and "@" in secret:
            # Extract just the protocol and host
            protocol_part = secret.split("://")[0]
            host_part = secret.split("@")[-1].split("/")[0]
            return f"{protocol_part}://***@{host_part}/***"
        return "*" * len(secret)
