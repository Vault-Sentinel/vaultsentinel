"""Script to seed a repository with test secrets for demonstration."""

import os
import tempfile
import subprocess
from pathlib import Path

def create_test_repo():
    """Create a test repository with seeded secrets."""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="vaultsentinel_test_")
    
    # Initialize git repository
    os.chdir(temp_dir)
    subprocess.run(["git", "init"], check=True)
    
    # Create test files with secrets
    test_files = {
        "config.py": """
# Configuration file with secrets
AWS_ACCESS_KEY_ID = "AKIA1234567890ABCDEF"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
DATABASE_URL = "postgres://user:password@localhost:5432/mydb"
""",
        "secrets.json": """
{
    "slack_webhook": "https://hooks.slack.com/services/T123/B456/xyz789",
    "github_token": "ghp_1234567890abcdef1234567890abcdef12345678",
    "jwt_secret": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
}
""",
        "tests/test_config.py": """
# Test file with mock secrets
TEST_AWS_KEY = "AKIA0000000000000000"
MOCK_DATABASE_URL = "postgres://test:test@localhost:5432/testdb"
""",
        "examples/demo.py": """
# Example file with placeholder secrets
API_KEY = "your_api_key_here"
SECRET_TOKEN = "replace_with_real_token"
"""
    }
    
    # Create files
    for file_path, content in test_files.items():
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
    
    # Add and commit files
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Add test files with secrets"], check=True)
    
    print(f"Test repository created at: {temp_dir}")
    print("Repository contains the following test secrets:")
    print("- AWS Access Key ID: AKIA1234567890ABCDEF")
    print("- AWS Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
    print("- Database URL: postgres://user:password@localhost:5432/mydb")
    print("- Slack Webhook: https://hooks.slack.com/services/T123/B456/xyz789")
    print("- GitHub Token: ghp_1234567890abcdef1234567890abcdef12345678")
    print("- JWT Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    
    return temp_dir

if __name__ == "__main__":
    create_test_repo()
