"""GitHub connector for VaultSentinel."""

import requests
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from core.interfaces import Connector, DetectionContext
from core.config import get_config

logger = logging.getLogger(__name__)


class GitHubConnector:
    """GitHub connector for fetching repository changes."""
    
    def __init__(self):
        self.config = get_config()
        self.name = "github"
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.config.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def connect(self) -> bool:
        """Test GitHub API connection."""
        try:
            url = f"{self.base_url}/repos/{self.config.github_repo}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"GitHub connection test failed: {e}")
            return False
    
    def fetch_changes(self, since: Optional[str] = None) -> List[DetectionContext]:
        """Fetch recent changes from GitHub repository."""
        contexts = []
        
        try:
            # Get recent commits
            commits = self._get_recent_commits(since)
            
            for commit in commits:
                # Get files changed in this commit
                files = self._get_commit_files(commit["sha"])
                
                for file_info in files:
                    # Skip deleted files
                    if file_info["status"] == "removed":
                        continue
                    
                    # Skip binary files
                    if self._is_binary_file(file_info["filename"]):
                        continue
                    
                    # Get file content
                    content = self._get_file_content(file_info["filename"], commit["sha"])
                    if not content:
                        continue
                    
                    # Create detection context
                    context = DetectionContext(
                        repo=self.config.github_repo,
                        commit_sha=commit["sha"],
                        file_path=file_info["filename"],
                        content=content,
                        metadata={
                            "commit_message": commit["commit"]["message"],
                            "author": commit["commit"]["author"]["name"],
                            "date": commit["commit"]["author"]["date"],
                            "file_status": file_info["status"]
                        }
                    )
                    contexts.append(context)
            
            logger.info(f"Fetched {len(contexts)} contexts from {len(commits)} commits")
            
        except Exception as e:
            logger.error(f"Error fetching GitHub changes: {e}")
        
        return contexts
    
    def _get_recent_commits(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent commits from the repository."""
        url = f"{self.base_url}/repos/{self.config.github_repo}/commits"
        
        params = {
            "per_page": self.config.scan_depth_commits,
            "sha": "main"  # or "master" depending on default branch
        }
        
        if since:
            params["since"] = since
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching commits: {e}")
            return []
    
    def _get_commit_files(self, commit_sha: str) -> List[Dict[str, Any]]:
        """Get files changed in a specific commit."""
        url = f"{self.base_url}/repos/{self.config.github_repo}/commits/{commit_sha}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            commit_data = response.json()
            return commit_data.get("files", [])
        except requests.RequestException as e:
            logger.error(f"Error fetching commit files: {e}")
            return []
    
    def _get_file_content(self, file_path: str, commit_sha: str) -> Optional[str]:
        """Get content of a file at a specific commit."""
        url = f"{self.base_url}/repos/{self.config.github_repo}/contents/{file_path}"
        
        params = {"ref": commit_sha}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            file_data = response.json()
            
            if file_data.get("type") == "file":
                import base64
                content = base64.b64decode(file_data["content"]).decode("utf-8")
                return content
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error fetching file content: {e}")
            return None
    
    def _is_binary_file(self, file_path: str) -> bool:
        """Check if file is likely binary."""
        binary_extensions = [
            '.exe', '.dll', '.so', '.dylib', '.bin', '.img', '.iso',
            '.zip', '.tar', '.gz', '.rar', '.7z', '.pdf', '.doc',
            '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.jpg',
            '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac'
        ]
        
        return any(file_path.lower().endswith(ext) for ext in binary_extensions)
    
    def is_enabled(self) -> bool:
        """Check if connector is enabled."""
        return bool(self.config.github_repo and self.config.github_token)
