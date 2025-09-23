"""Context-based filtering to reduce false positives."""

import re
from typing import List, Dict, Tuple
from agent.config import settings


class ContextFilter:
    """Context-based filter for reducing false positives."""
    
    def __init__(self):
        """Initialize with configuration."""
        self.allowlist_paths = settings.allowlist_paths
        self.denylist_patterns = settings.denylist_patterns
        self.entropy_threshold = settings.detection_entropy_threshold
    
    def score_context(self, file_path: str, line_content: str, secret_kind: str) -> Tuple[float, str]:
        """Score context to determine confidence adjustment.
        
        Args:
            file_path: Path to the file
            line_content: Content of the line containing the secret
            secret_kind: Type of secret detected
            
        Returns:
            Tuple of (confidence_adjustment, reason)
        """
        confidence_adjustment = 0.0
        reasons = []
        
        # Check allowlist paths (reduce confidence for test files)
        if self._is_allowlisted_path(file_path):
            confidence_adjustment -= 0.3
            reasons.append("allowlisted_path")
        
        # Check denylist patterns in filename
        if self._matches_denylist_patterns(file_path):
            confidence_adjustment -= 0.4
            reasons.append("denylist_pattern")
        
        # Check for test-related content
        if self._is_test_content(line_content):
            confidence_adjustment -= 0.2
            reasons.append("test_content")
        
        # Check for example/dummy content
        if self._is_example_content(line_content):
            confidence_adjustment -= 0.3
            reasons.append("example_content")
        
        # Check for configuration files (higher confidence)
        if self._is_config_file(file_path):
            confidence_adjustment += 0.1
            reasons.append("config_file")
        
        # Check for source code files (medium confidence)
        if self._is_source_file(file_path):
            confidence_adjustment += 0.05
            reasons.append("source_file")
        
        # Check for documentation files (lower confidence)
        if self._is_documentation_file(file_path):
            confidence_adjustment -= 0.2
            reasons.append("documentation_file")
        
        # Check for commented secrets (lower confidence)
        if self._is_commented_secret(line_content):
            confidence_adjustment -= 0.1
            reasons.append("commented_secret")
        
        # Check for environment variable patterns (higher confidence)
        if self._is_env_var_pattern(line_content):
            confidence_adjustment += 0.1
            reasons.append("env_var_pattern")
        
        # Check for hardcoded secrets (higher confidence)
        if self._is_hardcoded_secret(line_content):
            confidence_adjustment += 0.15
            reasons.append("hardcoded_secret")
        
        reason = ", ".join(reasons) if reasons else "no_context_indicators"
        
        return confidence_adjustment, reason
    
    def _is_allowlisted_path(self, file_path: str) -> bool:
        """Check if file path is in allowlist."""
        file_path_lower = file_path.lower()
        return any(allowlist_path in file_path_lower for allowlist_path in self.allowlist_paths)
    
    def _matches_denylist_patterns(self, file_path: str) -> bool:
        """Check if file path matches denylist patterns."""
        file_path_lower = file_path.lower()
        return any(pattern in file_path_lower for pattern in self.denylist_patterns)
    
    def _is_test_content(self, line_content: str) -> bool:
        """Check if line contains test-related content."""
        test_indicators = [
            "test", "mock", "fake", "dummy", "sample", "example",
            "placeholder", "TODO", "FIXME", "XXX"
        ]
        line_lower = line_content.lower()
        return any(indicator in line_lower for indicator in test_indicators)
    
    def _is_example_content(self, line_content: str) -> bool:
        """Check if line contains example content."""
        example_indicators = [
            "example", "sample", "demo", "placeholder", "your_",
            "replace_", "change_", "update_"
        ]
        line_lower = line_content.lower()
        return any(indicator in line_lower for indicator in example_indicators)
    
    def _is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file."""
        config_extensions = [".conf", ".config", ".cfg", ".ini", ".yaml", ".yml", ".json", ".toml"]
        config_names = ["config", "settings", "secrets", "credentials", "env"]
        
        file_path_lower = file_path.lower()
        
        # Check extensions
        if any(file_path_lower.endswith(ext) for ext in config_extensions):
            return True
        
        # Check names
        if any(name in file_path_lower for name in config_names):
            return True
        
        return False
    
    def _is_source_file(self, file_path: str) -> bool:
        """Check if file is source code."""
        source_extensions = [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".cs"]
        return any(file_path.endswith(ext) for ext in source_extensions)
    
    def _is_documentation_file(self, file_path: str) -> bool:
        """Check if file is documentation."""
        doc_extensions = [".md", ".txt", ".rst", ".doc", ".docx"]
        doc_names = ["readme", "changelog", "license", "contributing"]
        
        file_path_lower = file_path.lower()
        
        # Check extensions
        if any(file_path_lower.endswith(ext) for ext in doc_extensions):
            return True
        
        # Check names
        if any(name in file_path_lower for name in doc_names):
            return True
        
        return False
    
    def _is_commented_secret(self, line_content: str) -> bool:
        """Check if secret is in a comment."""
        stripped = line_content.strip()
        return stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*")
    
    def _is_env_var_pattern(self, line_content: str) -> bool:
        """Check if line contains environment variable patterns."""
        env_patterns = [
            r"export\s+\w+=",
            r"ENV\s+\w+",
            r"process\.env\.",
            r"os\.environ\.",
            r"getenv\(",
            r"System\.getenv\("
        ]
        
        return any(re.search(pattern, line_content, re.IGNORECASE) for pattern in env_patterns)
    
    def _is_hardcoded_secret(self, line_content: str) -> bool:
        """Check if line contains hardcoded secret patterns."""
        hardcoded_patterns = [
            r'["\']\w+["\']\s*[:=]\s*["\']',  # key: "value" or key = "value"
            r'const\s+\w+\s*=\s*["\']',  # const key = "value"
            r'let\s+\w+\s*=\s*["\']',  # let key = "value"
            r'var\s+\w+\s*=\s*["\']',  # var key = "value"
        ]
        
        return any(re.search(pattern, line_content, re.IGNORECASE) for pattern in hardcoded_patterns)
    
    def apply_context_filter(self, matches: List[Dict]) -> List[Dict]:
        """Apply context filtering to a list of matches.
        
        Args:
            matches: List of match dictionaries
            
        Returns:
            Filtered list of matches with adjusted confidence
        """
        filtered_matches = []
        
        for match in matches:
            # Apply context scoring
            confidence_adjustment, reason = self.score_context(
                match.get("file_path", ""),
                match.get("line_content", ""),
                match.get("secret_kind", "")
            )
            
            # Adjust confidence
            original_confidence = match.get("confidence", 0.0)
            adjusted_confidence = max(0.0, min(1.0, original_confidence + confidence_adjustment))
            
            # Only include if confidence is above threshold
            if adjusted_confidence >= 0.3:  # Minimum confidence threshold
                match["confidence"] = adjusted_confidence
                match["context_reason"] = reason
                filtered_matches.append(match)
        
        return filtered_matches
