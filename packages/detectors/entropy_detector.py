"""Entropy-based secret detector."""

import math
import re
import hashlib
import logging
from typing import List, Iterable, Tuple

from core.interfaces import Detector, DetectionContext
from core.models import Finding, SecretKind
from core.config import get_config

logger = logging.getLogger(__name__)


class EntropyDetector:
    """Entropy-based secret detector."""
    
    def __init__(self):
        self.config = get_config()
        self.name = "entropy"
        self.entropy_threshold = self.config.detection_entropy_threshold
        self.min_length = 20
    
    def detect(self, context: DetectionContext) -> Iterable[Finding]:
        """Detect high entropy strings in the given context."""
        findings = []
        lines = context.content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Find high entropy strings in this line
            entropy_matches = self._detect_high_entropy_strings(line)
            
            for secret, entropy, start_pos, end_pos in entropy_matches:
                # Skip if already detected by regex patterns
                if self._is_likely_regex_detected(secret):
                    continue
                
                # Skip common false positives
                if self._is_false_positive(secret):
                    continue
                
                # Calculate confidence based on entropy
                confidence = min(0.9, entropy / 6.0)  # Normalize to 0-0.9 range
                
                if confidence >= 0.3:  # Minimum confidence threshold
                    fingerprint = self._compute_fingerprint(secret)
                    masked_preview = self._mask_secret(secret)
                    
                    finding = Finding(
                        fingerprint=fingerprint,
                        kind=SecretKind.HIGH_ENTROPY_STRING,
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
                    logger.debug(f"Detected high entropy string in {context.file_path}:{line_num}")
        
        return findings
    
    def _detect_high_entropy_strings(self, text: str) -> List[Tuple[str, float, int, int]]:
        """Detect high entropy strings in text."""
        # Find potential secret strings (alphanumeric + common symbols)
        pattern = r'[A-Za-z0-9+/=_-]{' + str(self.min_length) + ',}'
        matches = []
        
        for match in re.finditer(pattern, text):
            candidate = match.group(0)
            entropy = self._calculate_entropy(candidate)
            
            if entropy >= self.entropy_threshold:
                matches.append((candidate, entropy, match.start(), match.end()))
        
        return matches
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not text:
            return 0.0
        
        # Count character frequencies
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        text_len = len(text)
        
        for count in char_counts.values():
            probability = count / text_len
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _is_likely_regex_detected(self, secret: str) -> bool:
        """Check if secret is likely detected by regex patterns."""
        # Common regex patterns that would catch this
        regex_patterns = [
            r"AKIA[0-9A-Z]{16}",  # AWS access key
            r"gh[ops]_[A-Za-z0-9_]{36}",  # GitHub token
            r"https://hooks\.slack\.com/services/",  # Slack webhook
            r"eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",  # JWT
            r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----",  # RSA key
        ]
        
        for pattern in regex_patterns:
            if re.match(pattern, secret, re.IGNORECASE):
                return True
        
        return False
    
    def _is_false_positive(self, secret: str) -> bool:
        """Check if secret is a false positive."""
        # Common false positive patterns
        false_positive_patterns = [
            r'^[0-9]+$',  # Pure numbers
            r'^[A-Z]+$',  # Pure uppercase
            r'^[a-z]+$',  # Pure lowercase
            r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$',  # Dates
            r'^[0-9]{2}:[0-9]{2}:[0-9]{2}$',  # Times
            r'^[0-9]+\.[0-9]+\.[0-9]+$',  # Version numbers
            r'^[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12}$',  # UUIDs
        ]
        
        for pattern in false_positive_patterns:
            if re.match(pattern, secret):
                return True
        
        # Check for repeated patterns (low entropy indicators)
        if len(set(secret)) < len(secret) * 0.3:  # Less than 30% unique characters
            return True
        
        return False
    
    def _compute_fingerprint(self, secret: str) -> str:
        """Compute SHA256 fingerprint for deduplication."""
        return hashlib.sha256(secret.encode()).hexdigest()
    
    def _mask_secret(self, secret: str) -> str:
        """Mask a secret for display."""
        if len(secret) <= 8:
            return "*" * len(secret)
        return secret[:4] + "*" * (len(secret) - 8) + secret[-4:]
    
    def is_enabled(self) -> bool:
        """Check if detector is enabled."""
        return True
