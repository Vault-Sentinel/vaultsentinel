#!/usr/bin/env python3
"""Log redaction utility for VaultSentinel.

This script helps redact sensitive information from logs to prevent
secret leakage in log files and telemetry.
"""

import re
import sys
import argparse
from typing import List, Dict, Any
from pathlib import Path


class LogRedactor:
    """Utility for redacting sensitive information from logs."""
    
    def __init__(self):
        """Initialize log redactor with common secret patterns."""
        self.secret_patterns = [
            # API Keys
            (r'api[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'api_key=***REDACTED***'),
            (r'token["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'token=***REDACTED***'),
            (r'secret["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'secret=***REDACTED***'),
            (r'password["\s]*[:=]["\s]*([^\s]{8,})', r'password=***REDACTED***'),
            
            # AWS Keys
            (r'AKIA[0-9A-Z]{16}', r'AKIA***REDACTED***'),
            (r'aws[_-]?access[_-]?key[_-]?id["\s]*[:=]["\s]*([A-Z0-9]{20})', r'aws_access_key_id=***REDACTED***'),
            (r'aws[_-]?secret[_-]?access[_-]?key["\s]*[:=]["\s]*([A-Za-z0-9/+=]{40})', r'aws_secret_access_key=***REDACTED***'),
            
            # GitHub Tokens
            (r'ghp_[a-zA-Z0-9]{36}', r'ghp_***REDACTED***'),
            (r'gho_[a-zA-Z0-9]{36}', r'gho_***REDACTED***'),
            (r'ghu_[a-zA-Z0-9]{36}', r'ghu_***REDACTED***'),
            (r'ghs_[a-zA-Z0-9]{36}', r'ghs_***REDACTED***'),
            (r'github[_-]?token["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'github_token=***REDACTED***'),
            
            # Slack Tokens
            (r'xoxb-[a-zA-Z0-9-]+', r'xoxb-***REDACTED***'),
            (r'xoxp-[a-zA-Z0-9-]+', r'xoxp-***REDACTED***'),
            (r'xoxa-[a-zA-Z0-9-]+', r'xoxa-***REDACTED***'),
            (r'xoxr-[a-zA-Z0-9-]+', r'xoxr-***REDACTED***'),
            (r'slack[_-]?token["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'slack_token=***REDACTED***'),
            
            # Stripe Keys
            (r'sk_test_[a-zA-Z0-9]{24}', r'sk_test_***REDACTED***'),
            (r'sk_live_[a-zA-Z0-9]{24}', r'sk_live_***REDACTED***'),
            (r'pk_test_[a-zA-Z0-9]{24}', r'pk_test_***REDACTED***'),
            (r'pk_live_[a-zA-Z0-9]{24}', r'pk_live_***REDACTED***'),
            (r'stripe[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'stripe_key=***REDACTED***'),
            
            # JWT Tokens
            (r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', r'JWT***REDACTED***'),
            
            # Database URLs
            (r'(postgresql|mysql|mongodb)://[^:]+:[^@]+@[^\s]+', r'\1://***REDACTED***@***REDACTED***'),
            
            # Private Keys
            (r'-----BEGIN [A-Z ]+PRIVATE KEY-----', r'-----BEGIN ***REDACTED***PRIVATE KEY-----'),
            
            # Generic tokens
            (r'bearer["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'bearer=***REDACTED***'),
            (r'authorization["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'authorization=***REDACTED***'),
        ]
        
        # Compile patterns for better performance
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in self.secret_patterns
        ]
    
    def redact_text(self, text: str) -> str:
        """Redact sensitive information from text."""
        if not text:
            return text
        
        redacted = text
        for pattern, replacement in self.compiled_patterns:
            redacted = pattern.sub(replacement, redacted)
        
        return redacted
    
    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive information from dictionary."""
        if not isinstance(data, dict):
            return data
        
        redacted = {}
        for key, value in data.items():
            if isinstance(value, str):
                redacted[key] = self.redact_text(value)
            elif isinstance(value, dict):
                redacted[key] = self.redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = [self.redact_text(str(item)) if isinstance(item, str) else item for item in value]
            else:
                redacted[key] = value
        
        return redacted
    
    def redact_file(self, input_file: Path, output_file: Path = None) -> None:
        """Redact sensitive information from a file."""
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        redacted_content = self.redact_text(content)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(redacted_content)
            print(f"Redacted content written to: {output_file}")
        else:
            print(redacted_content)
    
    def check_for_secrets(self, text: str) -> List[str]:
        """Check for potential secrets in text."""
        found_secrets = []
        
        for pattern, _ in self.compiled_patterns:
            matches = pattern.findall(text)
            if matches:
                found_secrets.extend(matches)
        
        return found_secrets


def main():
    """Main entry point for log redaction utility."""
    parser = argparse.ArgumentParser(description="Redact sensitive information from logs")
    parser.add_argument("input_file", type=Path, help="Input file to redact")
    parser.add_argument("-o", "--output", type=Path, help="Output file (default: stdout)")
    parser.add_argument("--check", action="store_true", help="Check for secrets without redacting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    redactor = LogRedactor()
    
    if args.check:
        # Check for secrets
        with open(args.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        secrets = redactor.check_for_secrets(content)
        if secrets:
            print(f"⚠️  Found {len(secrets)} potential secrets:")
            for secret in set(secrets):  # Remove duplicates
                print(f"  - {secret[:20]}...")
        else:
            print("✅ No secrets found")
    else:
        # Redact content
        try:
            redactor.redact_file(args.input_file, args.output)
            if args.verbose:
                print(f"✅ Redaction completed for {args.input_file}")
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
