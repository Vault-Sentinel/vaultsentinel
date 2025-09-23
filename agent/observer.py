"""GitHub repository observer for monitoring changes."""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from agent.config import settings


@dataclass
class CommitInfo:
    """Information about a commit."""
    sha: str
    message: str
    author: str
    date: datetime
    files: List[str]


@dataclass
class FileChange:
    """Information about a file change."""
    file_path: str
    status: str  # added, modified, removed
    patch: Optional[str] = None
    content: Optional[str] = None


class GitHubObserver:
    """Observer for monitoring GitHub repository changes."""
    
    def __init__(self):
        """Initialize GitHub observer."""
        self.repo = settings.github_repo
        self.token = settings.github_token
        self.scan_depth = settings.scan_depth_commits
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.last_scan_sha: Optional[str] = None
    
    def get_latest_commits(self, since: Optional[datetime] = None) -> List[CommitInfo]:
        """Get latest commits from the repository.
        
        Args:
            since: Only get commits since this date
            
        Returns:
            List of commit information
        """
        url = f"{self.base_url}/repos/{self.repo}/commits"
        
        params = {
            "per_page": self.scan_depth,
            "sha": "main"  # or "master" depending on default branch
        }
        
        if since:
            params["since"] = since.isoformat()
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            commits_data = response.json()
            commits = []
            
            for commit_data in commits_data:
                commit = CommitInfo(
                    sha=commit_data["sha"],
                    message=commit_data["commit"]["message"],
                    author=commit_data["commit"]["author"]["name"],
                    date=datetime.fromisoformat(commit_data["commit"]["author"]["date"].replace('Z', '+00:00')),
                    files=[]
                )
                
                # Get files changed in this commit
                files = self._get_commit_files(commit.sha)
                commit.files = files
                
                commits.append(commit)
            
            return commits
            
        except requests.RequestException as e:
            print(f"Error fetching commits: {e}")
            return []
    
    def _get_commit_files(self, commit_sha: str) -> List[str]:
        """Get files changed in a specific commit.
        
        Args:
            commit_sha: SHA of the commit
            
        Returns:
            List of file paths
        """
        url = f"{self.base_url}/repos/{self.repo}/commits/{commit_sha}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            commit_data = response.json()
            files = [file["filename"] for file in commit_data.get("files", [])]
            
            return files
            
        except requests.RequestException as e:
            print(f"Error fetching commit files: {e}")
            return []
    
    def get_file_content(self, file_path: str, commit_sha: Optional[str] = None) -> Optional[str]:
        """Get content of a file at a specific commit.
        
        Args:
            file_path: Path to the file
            commit_sha: SHA of the commit (defaults to latest)
            
        Returns:
            File content or None if not found
        """
        url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
        
        params = {}
        if commit_sha:
            params["ref"] = commit_sha
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            file_data = response.json()
            
            if file_data.get("type") == "file":
                import base64
                content = base64.b64decode(file_data["content"]).decode("utf-8")
                return content
            
            return None
            
        except requests.RequestException as e:
            print(f"Error fetching file content: {e}")
            return None
    
    def get_file_changes(self, commit_sha: str) -> List[FileChange]:
        """Get file changes for a specific commit.
        
        Args:
            commit_sha: SHA of the commit
            
        Returns:
            List of file changes
        """
        url = f"{self.base_url}/repos/{self.repo}/commits/{commit_sha}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            commit_data = response.json()
            changes = []
            
            for file_data in commit_data.get("files", []):
                change = FileChange(
                    file_path=file_data["filename"],
                    status=file_data["status"],
                    patch=file_data.get("patch")
                )
                
                # Get full content for added/modified files
                if change.status in ["added", "modified"]:
                    content = self.get_file_content(file_data["filename"], commit_sha)
                    change.content = content
                
                changes.append(change)
            
            return changes
            
        except requests.RequestException as e:
            print(f"Error fetching file changes: {e}")
            return []
    
    def get_recent_changes(self, hours: int = 24) -> List[Tuple[CommitInfo, List[FileChange]]]:
        """Get recent changes in the repository.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of (commit, file_changes) tuples
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        commits = self.get_latest_commits(since=since)
        
        changes = []
        for commit in commits:
            file_changes = self.get_file_changes(commit.sha)
            changes.append((commit, file_changes))
        
        return changes
    
    def get_repository_info(self) -> Dict:
        """Get basic repository information.
        
        Returns:
            Repository information dictionary
        """
        url = f"{self.base_url}/repos/{self.repo}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            repo_data = response.json()
            
            return {
                "name": repo_data["name"],
                "full_name": repo_data["full_name"],
                "default_branch": repo_data["default_branch"],
                "private": repo_data["private"],
                "updated_at": repo_data["updated_at"]
            }
            
        except requests.RequestException as e:
            print(f"Error fetching repository info: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test GitHub API connection.
        
        Returns:
            True if connection is successful
        """
        try:
            repo_info = self.get_repository_info()
            return bool(repo_info)
        except Exception as e:
            print(f"GitHub connection test failed: {e}")
            return False
