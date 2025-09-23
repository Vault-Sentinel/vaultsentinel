"""Thinker pipeline for orchestrating detection and filtering."""

import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from detection.regex_scanner import RegexScanner, SecretMatch
from detection.entropy import detect_high_entropy_strings, is_likely_secret, filter_common_false_positives
from detection.context_filter import ContextFilter
from detection.classifier_iface import get_classifier
from api.models import Finding, ScanRun
from agent.config import settings


class Thinker:
    """Thinker pipeline for orchestrating detection and filtering."""
    
    def __init__(self, db_session: Session):
        """Initialize thinker with database session."""
        self.db = db_session
        self.regex_scanner = RegexScanner()
        self.context_filter = ContextFilter()
        self.classifier = get_classifier("rule")  # Use rule-based classifier by default
    
    def process_commit(self, commit_sha: str, file_changes: List[Dict]) -> List[Dict]:
        """Process a commit and its file changes.
        
        Args:
            commit_sha: SHA of the commit
            file_changes: List of file change dictionaries
            
        Returns:
            List of detected findings
        """
        findings = []
        
        for file_change in file_changes:
            file_path = file_change["file_path"]
            content = file_change.get("content", "")
            status = file_change.get("status", "modified")
            
            # Skip deleted files
            if status == "removed":
                continue
            
            # Skip binary files
            if self._is_binary_file(file_path):
                continue
            
            # Process file content
            file_findings = self._process_file_content(
                content, file_path, commit_sha
            )
            
            findings.extend(file_findings)
        
        # Deduplicate findings
        deduplicated_findings = self._deduplicate_findings(findings)
        
        # Persist new findings
        persisted_findings = self._persist_findings(deduplicated_findings, commit_sha)
        
        return persisted_findings
    
    def _process_file_content(self, content: str, file_path: str, commit_sha: str) -> List[Dict]:
        """Process file content for secrets.
        
        Args:
            content: File content
            file_path: Path to the file
            commit_sha: SHA of the commit
            
        Returns:
            List of detected findings
        """
        findings = []
        
        # Regex-based detection
        regex_matches = self.regex_scanner.scan_text(content, file_path)
        
        for match in regex_matches:
            finding = {
                "secret": match.secret,
                "secret_kind": match.secret_kind,
                "confidence": match.confidence,
                "masked_preview": match.masked_preview,
                "fingerprint": match.fingerprint,
                "file_path": file_path,
                "commit_sha": commit_sha,
                "line_start": match.line_start,
                "line_end": match.line_end,
                "line_content": content.split('\n')[match.line_start - 1] if match.line_start <= len(content.split('\n')) else ""
            }
            findings.append(finding)
        
        # Entropy-based detection
        entropy_matches = detect_high_entropy_strings(content, settings.detection_entropy_threshold)
        
        for secret, entropy, start_pos, end_pos in entropy_matches:
            # Skip if already detected by regex
            if any(match.secret == secret for match in regex_matches):
                continue
            
            # Skip common false positives
            if filter_common_false_positives(secret):
                continue
            
            # Check if likely a secret
            is_secret, confidence = is_likely_secret(secret, settings.detection_entropy_threshold)
            
            if is_secret:
                # Find line numbers
                lines = content[:start_pos].count('\n')
                line_content = content.split('\n')[lines] if lines < len(content.split('\n')) else ""
                
                finding = {
                    "secret": secret,
                    "secret_kind": "high_entropy_string",
                    "confidence": confidence,
                    "masked_preview": self._mask_secret(secret),
                    "fingerprint": hashlib.sha256(secret.encode()).hexdigest(),
                    "file_path": file_path,
                    "commit_sha": commit_sha,
                    "line_start": lines + 1,
                    "line_end": lines + 1,
                    "line_content": line_content
                }
                findings.append(finding)
        
        # Apply context filtering
        filtered_findings = self.context_filter.apply_context_filter(findings)
        
        # Apply classifier
        classified_findings = []
        for finding in filtered_findings:
            classification = self.classifier.classify(
                finding["secret"],
                {
                    "secret_kind": finding["secret_kind"],
                    "file_path": finding["file_path"],
                    "line_content": finding["line_content"]
                }
            )
            
            # Update confidence based on classification
            finding["confidence"] = max(finding["confidence"], classification.confidence)
            finding["classification_reason"] = classification.reasoning
            
            classified_findings.append(finding)
        
        return classified_findings
    
    def _is_binary_file(self, file_path: str) -> bool:
        """Check if file is likely binary.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is likely binary
        """
        binary_extensions = [
            '.exe', '.dll', '.so', '.dylib', '.bin', '.img', '.iso',
            '.zip', '.tar', '.gz', '.rar', '.7z', '.pdf', '.doc',
            '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.jpg',
            '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac'
        ]
        
        return any(file_path.lower().endswith(ext) for ext in binary_extensions)
    
    def _mask_secret(self, secret: str) -> str:
        """Mask a secret for display.
        
        Args:
            secret: Secret to mask
            
        Returns:
            Masked secret
        """
        if len(secret) <= 8:
            return "*" * len(secret)
        return secret[:4] + "*" * (len(secret) - 8) + secret[-4:]
    
    def _deduplicate_findings(self, findings: List[Dict]) -> List[Dict]:
        """Deduplicate findings based on fingerprint and file path.
        
        Args:
            findings: List of findings
            
        Returns:
            Deduplicated list of findings
        """
        seen = set()
        deduplicated = []
        
        for finding in findings:
            key = (finding["fingerprint"], finding["file_path"])
            if key not in seen:
                seen.add(key)
                deduplicated.append(finding)
        
        return deduplicated
    
    def _persist_findings(self, findings: List[Dict], commit_sha: str) -> List[Dict]:
        """Persist findings to database.
        
        Args:
            findings: List of findings to persist
            commit_sha: SHA of the commit
            
        Returns:
            List of persisted findings
        """
        persisted_findings = []
        
        for finding in findings:
            # Check if finding already exists
            existing = self.db.query(Finding).filter(
                Finding.secret_fingerprint == finding["fingerprint"],
                Finding.file_path == finding["file_path"]
            ).first()
            
            if existing:
                # Update last seen time
                existing.last_seen_at = datetime.utcnow()
                self.db.commit()
                continue
            
            # Create new finding
            new_finding = Finding(
                repo=settings.github_repo,
                commit_sha=commit_sha,
                file_path=finding["file_path"],
                line_start=finding["line_start"],
                line_end=finding["line_end"],
                secret_fingerprint=finding["fingerprint"],
                secret_kind=finding["secret_kind"],
                confidence=finding["confidence"],
                masked_preview=finding["masked_preview"],
                status="NEW"
            )
            
            self.db.add(new_finding)
            self.db.commit()
            
            # Convert to dict for return
            persisted_findings.append(new_finding.to_dict())
        
        return persisted_findings
    
    def create_scan_run(self, commit_sha: str, new_findings_count: int) -> str:
        """Create a scan run record.
        
        Args:
            commit_sha: SHA of the commit
            new_findings_count: Number of new findings
            
        Returns:
            Scan run ID
        """
        scan_run = ScanRun(
            repo=settings.github_repo,
            commit_range=commit_sha,
            new_findings_count=new_findings_count,
            status="OK"
        )
        
        self.db.add(scan_run)
        self.db.commit()
        
        return scan_run.id
