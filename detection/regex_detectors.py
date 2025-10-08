"""Regex-based secret detectors for common patterns."""

import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RegexMatch:
    """A regex match result."""
    pattern_name: str
    type: str
    severity: str
    confidence: float
    start_line: int
    end_line: int
    match_text: str
    file_path: str
    description: str
    remediation: str


class RegexDetector:
    """Regex-based secret detector."""
    
    def __init__(self):
        """Initialize with compiled regex patterns."""
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> List[Dict[str, Any]]:
        """Compile regex patterns for common secrets."""
        return [
            {
                "name": "aws_access_key",
                "pattern": re.compile(r'AKIA[0-9A-Z]{16}', re.IGNORECASE),
                "type": "aws_access_key",
                "severity": "HIGH",
                "confidence": 0.9,
                "description": "AWS Access Key ID",
                "remediation": "Rotate the AWS access key immediately and update all references."
            },
            {
                "name": "aws_secret_key",
                "pattern": re.compile(r'(?i)aws(.{0,20})?(secret|access).{0,20}[\'\"][0-9a-zA-Z\/+=]{40}[\'\"]', re.IGNORECASE),
                "type": "aws_secret_key",
                "severity": "CRITICAL",
                "confidence": 0.95,
                "description": "AWS Secret Access Key",
                "remediation": "Rotate the AWS secret key immediately and update all references."
            },
            {
                "name": "google_api_key",
                "pattern": re.compile(r'AIza[0-9A-Za-z\-_]{35}', re.IGNORECASE),
                "type": "google_api_key",
                "severity": "HIGH",
                "confidence": 0.9,
                "description": "Google API Key",
                "remediation": "Regenerate the Google API key and update all references."
            },
            {
                "name": "slack_token",
                "pattern": re.compile(r'xox[baprs]-[0-9a-zA-Z]{10,48}', re.IGNORECASE),
                "type": "slack_token",
                "severity": "HIGH",
                "confidence": 0.9,
                "description": "Slack Token",
                "remediation": "Revoke the Slack token and generate a new one."
            },
            {
                "name": "github_token",
                "pattern": re.compile(r'ghp_[0-9a-zA-Z]{36}', re.IGNORECASE),
                "type": "github_token",
                "severity": "HIGH",
                "confidence": 0.9,
                "description": "GitHub Personal Access Token",
                "remediation": "Revoke the GitHub token and generate a new one."
            },
            {
                "name": "private_key",
                "pattern": re.compile(r'-----BEGIN (?:RSA|EC|DSA|OPENSSH) PRIVATE KEY-----', re.IGNORECASE),
                "type": "private_key",
                "severity": "CRITICAL",
                "confidence": 0.95,
                "description": "Private Key",
                "remediation": "Remove the private key from the repository and use secure key management."
            },
            {
                "name": "password_env",
                "pattern": re.compile(r'(?i)password\s*[:=]\s*[\'\"][^\'\"]{6,}[\'\"]', re.IGNORECASE),
                "type": "password",
                "severity": "MEDIUM",
                "confidence": 0.7,
                "description": "Password in Environment Variable",
                "remediation": "Use environment variables or secure secret management instead of hardcoded passwords."
            },
            {
                "name": "stripe_key",
                "pattern": re.compile(r'sk_live_[0-9a-zA-Z]{24}', re.IGNORECASE),
                "type": "stripe_key",
                "severity": "CRITICAL",
                "confidence": 0.95,
                "description": "Stripe Live Secret Key",
                "remediation": "Regenerate the Stripe key and update all references."
            },
            {
                "name": "twilio_token",
                "pattern": re.compile(r'[0-9a-fA-F]{32}', re.IGNORECASE),
                "type": "twilio_token",
                "severity": "HIGH",
                "confidence": 0.8,
                "description": "Twilio Token",
                "remediation": "Regenerate the Twilio token and update all references."
            },
            {
                "name": "jwt_secret",
                "pattern": re.compile(r'(?i)jwt.{0,20}secret.{0,20}[\'\"][^\'\"]{16,}[\'\"]', re.IGNORECASE),
                "type": "jwt_secret",
                "severity": "HIGH",
                "confidence": 0.8,
                "description": "JWT Secret",
                "remediation": "Use a strong, randomly generated JWT secret and store it securely."
            }
        ]
    
    def detect_in_file(self, file_path: str, content: str, lines: List[str]) -> List[RegexMatch]:
        """Detect secrets in a file."""
        matches = []
        
        for pattern_info in self.patterns:
            pattern = pattern_info["pattern"]
            for match in pattern.finditer(content):
                # Find line numbers
                start_line = content[:match.start()].count('\n') + 1
                end_line = content[:match.end()].count('\n') + 1
                
                # Get context lines
                context_start = max(0, start_line - 2)
                context_end = min(len(lines), end_line + 2)
                context_lines = lines[context_start:context_end]
                
                # Create match object
                regex_match = RegexMatch(
                    pattern_name=pattern_info["name"],
                    type=pattern_info["type"],
                    severity=pattern_info["severity"],
                    confidence=pattern_info["confidence"],
                    start_line=start_line,
                    end_line=end_line,
                    match_text=match.group(),
                    file_path=file_path,
                    description=pattern_info["description"],
                    remediation=pattern_info["remediation"]
                )
                
                matches.append(regex_match)
        
        return matches
    
    def detect_in_text(self, text: str) -> List[RegexMatch]:
        """Detect secrets in text (for MCP classify page)."""
        matches = []
        
        for pattern_info in self.patterns:
            pattern = pattern_info["pattern"]
            for match in pattern.finditer(text):
                regex_match = RegexMatch(
                    pattern_name=pattern_info["name"],
                    type=pattern_info["type"],
                    severity=pattern_info["severity"],
                    confidence=pattern_info["confidence"],
                    start_line=1,
                    end_line=1,
                    match_text=match.group(),
                    file_path="<input>",
                    description=pattern_info["description"],
                    remediation=pattern_info["remediation"]
                )
                
                matches.append(regex_match)
        
        return matches
    
    def get_pattern_summary(self) -> Dict[str, Any]:
        """Get summary of all patterns."""
        return {
            "total_patterns": len(self.patterns),
            "patterns": [
                {
                    "name": p["name"],
                    "type": p["type"],
                    "severity": p["severity"],
                    "confidence": p["confidence"]
                }
                for p in self.patterns
            ]
        }


def create_evidence_hash(content: str, start_line: int, end_line: int) -> str:
    """Create a hash for evidence deduplication."""
    evidence = f"{content}:{start_line}:{end_line}"
    return hashlib.sha256(evidence.encode()).hexdigest()
