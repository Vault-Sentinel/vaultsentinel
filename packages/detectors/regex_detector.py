"""Regex-based secret detector."""

import re
import hashlib
import logging
from typing import List, Iterable

from core.interfaces import Detector, DetectionContext
from core.models import Finding, SecretKind
from core.config import get_config

logger = logging.getLogger(__name__)


class RegexDetector:
    """Regex-based secret detector."""
    
    def __init__(self):
        self.config = get_config()
        self.name = "regex"
        
        # Define detection patterns
        self.patterns = {
            SecretKind.AWS_ACCESS_KEY: {
                "regex": r"AKIA[0-9A-Z]{16}",
                "confidence": 0.9,
                "mask_func": self._mask_aws_key
            },
            SecretKind.AWS_SECRET_KEY: {
                "regex": r"[A-Za-z0-9/+=]{40}",
                "confidence": 0.8,
                "mask_func": self._mask_generic
            },
            SecretKind.GITHUB_TOKEN: {
                "regex": r"gh[ops]_[A-Za-z0-9_]{36}",
                "confidence": 0.9,
                "mask_func": self._mask_generic
            },
            SecretKind.SLACK_WEBHOOK: {
                "regex": r"https://hooks\.slack\.com/services/[A-Za-z0-9_/]+",
                "confidence": 0.9,
                "mask_func": self._mask_url
            },
            SecretKind.JWT_TOKEN: {
                "regex": r"eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
                "confidence": 0.8,
                "mask_func": self._mask_jwt
            },
            SecretKind.RSA_PRIVATE_KEY: {
                "regex": r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----",
                "confidence": 0.95,
                "mask_func": self._mask_private_key
            },
            SecretKind.DATABASE_URL: {
                "regex": r"(postgres|mysql|mongodb)(?:\+srv)?://[^:\s]+:[^@\s]+@[^/\s]+/[^\s]+",
                "confidence": 0.8,
                "mask_func": self._mask_db_url
            },
            SecretKind.BEARER_TOKEN: {
                "regex": r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
                "confidence": 0.7,
                "mask_func": self._mask_bearer
            }
        }
    
    def detect(self, context: DetectionContext) -> Iterable[Finding]:
        """Detect secrets in the given context."""
        findings = []
        lines = context.content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for secret_kind, pattern_info in self.patterns.items():
                regex = re.compile(pattern_info["regex"], re.IGNORECASE)
                for match in regex.finditer(line):
                    secret = match.group(0)
                    confidence = pattern_info["confidence"]
                    masked_preview = pattern_info["mask_func"](secret)
                    fingerprint = self._compute_fingerprint(secret)
                    
                    finding = Finding(
                        fingerprint=fingerprint,
                        kind=secret_kind,
                        confidence=confidence,
                        location=f"{context.file_path}:{line_num}",
                        preview_masked=masked_preview,
                        repo=context.repo,
                        commit_sha=context.commit_sha,
                        file_path=context.file_path,
                        line_start=line_num,
                        line_end=line_num
                    )
                    
                    findings.append(finding)
                    logger.debug(f"Detected {secret_kind.value} in {context.file_path}:{line_num}")
        
        return findings
    
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
    
    def is_enabled(self) -> bool:
        """Check if detector is enabled."""
        return True
