#!/usr/bin/env python3
"""Pre-commit hook for secret detection.

This script checks for potential secrets in staged files before commit.
"""

import sys
import subprocess
from pathlib import Path
from scripts.redact_logs import LogRedactor


def get_staged_files() -> list:
    """Get list of staged files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []


def check_file_for_secrets(file_path: Path) -> list:
    """Check a file for potential secrets."""
    if not file_path.exists():
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        redactor = LogRedactor()
        return redactor.check_for_secrets(content)
    except Exception:
        return []


def main():
    """Main entry point for pre-commit hook."""
    print("🔍 Checking for secrets in staged files...")
    
    staged_files = get_staged_files()
    if not staged_files:
        print("✅ No staged files to check")
        return 0
    
    total_secrets = 0
    files_with_secrets = []
    
    for file_path_str in staged_files:
        if not file_path_str:
            continue
        
        file_path = Path(file_path_str)
        if not file_path.exists():
            continue
        
        # Skip binary files and common non-text files
        if file_path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz'}:
            continue
        
        secrets = check_file_for_secrets(file_path)
        if secrets:
            total_secrets += len(secrets)
            files_with_secrets.append((file_path, secrets))
            print(f"⚠️  {file_path}: Found {len(secrets)} potential secrets")
    
    if files_with_secrets:
        print(f"\n❌ Found {total_secrets} potential secrets in {len(files_with_secrets)} files:")
        for file_path, secrets in files_with_secrets:
            print(f"  📄 {file_path}:")
            for secret in set(secrets):  # Remove duplicates
                print(f"    - {secret[:30]}...")
        
        print("\n💡 To fix this:")
        print("  1. Remove or redact the secrets from your files")
        print("  2. Use environment variables or secret management")
        print("  3. Add files to .gitignore if they contain test secrets")
        print("  4. Use scripts/redact_logs.py to redact log files")
        
        return 1
    
    print("✅ No secrets found in staged files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
