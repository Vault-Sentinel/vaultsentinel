"""Scan job execution engine."""

import os
import uuid
import tempfile
import subprocess
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import fnmatch
import re

from api.scanner_models import Scan, Finding, get_db
from detection.regex_detectors import RegexDetector, create_evidence_hash
from detection.mcp_classifier import MCPClassifier
from api.gcs_storage import gcs_storage

logger = logging.getLogger(__name__)


class ScanEngine:
    """Main scan execution engine."""
    
    def __init__(self):
        """Initialize scan engine."""
        self.regex_detector = RegexDetector()
        self.mcp_classifier = MCPClassifier()
    
    async def execute_scan(self, scan_id: str, scan_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a scan job."""
        db = next(get_db())
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")
        
        try:
            # Update scan status
            scan.status = "running"
            scan.started_at = datetime.utcnow()
            db.commit()
            
            # Clone repository
            repo_path = await self._clone_repository(scan_config)
            
            # Select files to scan
            files_to_scan = await self._select_files(repo_path, scan_config)
            scan.total_files = len(files_to_scan)
            db.commit()
            
            # Run regex detection
            regex_findings = await self._run_regex_detection(files_to_scan, scan_config)
            
            # Run MCP classification on candidates
            mcp_findings = await self._run_mcp_classification(regex_findings, scan_config)
            
            # Merge and deduplicate findings
            all_findings = self._merge_findings(regex_findings, mcp_findings)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(all_findings)
            
            # Store findings in GCS
            await gcs_storage.store_findings(scan_id, all_findings)
            
            # Store scan metadata in GCS
            scan_metadata = {
                "scan_id": scan_id,
                "repo_url": scan_config["repo_url"],
                "branch": scan_config.get("branch", "main"),
                "status": "done",
                "risk_score": risk_score,
                "total_files": len(files_to_scan),
                "scanned_files": len(files_to_scan),
                "findings_count": len(all_findings),
                "duration_ms": int((datetime.utcnow() - scan.started_at).total_seconds() * 1000),
                "engines": {
                    "regex": True,
                    "mcp": True,
                    "semgrep": False
                }
            }
            await gcs_storage.store_scan_metadata(scan_id, scan_metadata)
            
            # Store repository files in GCS for future reference
            await gcs_storage.store_repository_files(scan_id, repo_path)
            
            # Persist findings to database (for API queries)
            await self._persist_findings(scan_id, all_findings, db)
            
            # Update scan completion
            scan.status = "done"
            scan.finished_at = datetime.utcnow()
            scan.duration_ms = int((scan.finished_at - scan.started_at).total_seconds() * 1000)
            scan.risk_score = risk_score
            scan.scanned_files = len(files_to_scan)
            scan.engines_json = {
                "regex": True,
                "mcp": True,
                "semgrep": False  # Future enhancement
            }
            db.commit()
            
            # Cleanup
            await self._cleanup_repo(repo_path)
            await gcs_storage.cleanup_temp_files(scan_id)
            
            return {
                "status": "done",
                "findings_count": len(all_findings),
                "risk_score": risk_score,
                "duration_ms": scan.duration_ms
            }
            
        except Exception as e:
            logger.error(f"Scan execution failed: {e}")
            scan.status = "error"
            scan.error_message = str(e)
            scan.finished_at = datetime.utcnow()
            db.commit()
            
            # Cleanup on error
            if 'repo_path' in locals():
                await self._cleanup_repo(repo_path)
            
            raise
    
    async def _clone_repository(self, scan_config: Dict[str, Any]) -> str:
        """Clone repository to temporary directory."""
        repo_url = scan_config["repo_url"]
        branch = scan_config.get("branch", "main")
        
        # Validate repo URL
        if not self._validate_repo_url(repo_url):
            raise ValueError("Invalid repository URL. Only GitHub repositories are supported.")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="vaultsentinel_scan_")
        
        try:
            # Clone repository
            cmd = [
                "git", "clone",
                "--depth", "1",
                "--branch", branch,
                "--single-branch",
                repo_url,
                temp_dir
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                # Parse git error messages to provide better user feedback
                error_msg = result.stderr.lower()
                if "authentication failed" in error_msg or "permission denied" in error_msg:
                    raise RuntimeError("This repository is private and requires authentication. VaultSentinel can only scan public repositories.")
                elif "not found" in error_msg or "does not exist" in error_msg:
                    raise RuntimeError("Repository not found. Please check the repository URL and ensure it exists.")
                elif "invalid" in error_msg and "branch" in error_msg:
                    raise RuntimeError(f"Branch '{branch}' not found in the repository. Please check the branch name.")
                elif "timeout" in error_msg:
                    raise RuntimeError("Repository access timed out. The repository might be too large or temporarily unavailable.")
                else:
                    raise RuntimeError(f"Failed to access repository: {result.stderr}")
            
            logger.info(f"Successfully cloned {repo_url} to {temp_dir}")
            return temp_dir
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Repository access timed out. The repository might be too large or the network connection is slow.")
        except Exception as e:
            if "private" in str(e).lower() or "authentication" in str(e).lower():
                raise RuntimeError("This repository is private and requires authentication. VaultSentinel can only scan public repositories.")
            raise RuntimeError(f"Failed to access repository: {e}")
    
    def _validate_repo_url(self, repo_url: str) -> bool:
        """Validate repository URL."""
        # Only allow GitHub repositories
        github_pattern = r'^https://github\.com/[^/]+/[^/]+/?$'
        return bool(re.match(github_pattern, repo_url))
    
    async def _select_files(self, repo_path: str, scan_config: Dict[str, Any]) -> List[str]:
        """Select files to scan based on include/exclude patterns."""
        include_patterns = scan_config.get("include", ["**/*"])
        exclude_patterns = scan_config.get("exclude", [
            "**/node_modules/**",
            "**/dist/**",
            "**/.git/**",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/*.pyo"
        ])
        max_files = scan_config.get("max_files", 2000)
        max_bytes_per_file = scan_config.get("max_bytes_per_file", 200000)
        
        files_to_scan = []
        repo_path_obj = Path(repo_path)
        
        for include_pattern in include_patterns:
            # Use pathlib.glob() for proper pattern matching
            for file_path in repo_path_obj.glob(include_pattern):
                if file_path.is_file():
                    relative_path = file_path.relative_to(repo_path_obj)
                    file_path_str = str(relative_path)
                    
                    # Check if file matches exclude pattern
                    excluded = False
                    for exclude_pattern in exclude_patterns:
                        if fnmatch.fnmatch(file_path_str, exclude_pattern):
                            excluded = True
                            break
                    
                    if excluded:
                        continue
                    
                    # Check file size
                    try:
                        file_size = file_path.stat().st_size
                        if file_size > max_bytes_per_file:
                            continue
                    except OSError:
                        continue
                    
                    files_to_scan.append(str(file_path))
                    
                    # Respect max files limit
                    if len(files_to_scan) >= max_files:
                        break
            
            if len(files_to_scan) >= max_files:
                break
        
        logger.info(f"Selected {len(files_to_scan)} files for scanning")
        return files_to_scan
    
    async def _run_regex_detection(self, files_to_scan: List[str], scan_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run regex detection on files."""
        findings = []
        
        for file_path in files_to_scan:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                # Run regex detection
                matches = self.regex_detector.detect_in_file(file_path, content, lines)
                
                for match in matches:
                    finding = {
                        "type": match.type,
                        "severity": match.severity,
                        "confidence": match.confidence,
                        "file_path": match.file_path,
                        "start_line": match.start_line,
                        "end_line": match.end_line,
                        "evidence_snippet_hash": create_evidence_hash(
                            match.match_text, match.start_line, match.end_line
                        ),
                        "engine": "regex",
                        "description": match.description,
                        "remediation_text": match.remediation,
                        "context": self._get_context_lines(lines, match.start_line, match.end_line)
                    }
                    findings.append(finding)
                    
            except Exception as e:
                logger.error(f"Error scanning file {file_path}: {e}")
                continue
        
        logger.info(f"Regex detection found {len(findings)} potential secrets")
        return findings
    
    async def _run_mcp_classification(self, regex_findings: List[Dict[str, Any]], scan_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run MCP classification on regex findings."""
        if not regex_findings:
            return []
        
        # Prepare candidates for MCP classification
        candidates = []
        for finding in regex_findings:
            candidate = {
                "file_path": finding["file_path"],
                "start_line": finding["start_line"],
                "context": finding["context"],
                "snippet": finding.get("snippet", ""),
                "type": finding["type"]
            }
            candidates.append(candidate)
        
        # Run MCP classification
        try:
            classifications = await self.mcp_classifier.classify_candidates(candidates)
            
            # Merge MCP results with regex findings
            mcp_findings = []
            for i, (finding, classification) in enumerate(zip(regex_findings, classifications)):
                if classification.is_secret or classification.is_vulnerability:
                    mcp_finding = finding.copy()
                    mcp_finding.update({
                        "severity": classification.severity,
                        "confidence": classification.confidence,
                        "description": f"{finding['description']} (MCP verified)",
                        "remediation_text": classification.remediation,
                        "engine": "mcp",
                        "mcp_reasoning": classification.reasoning
                    })
                    mcp_findings.append(mcp_finding)
            
            logger.info(f"MCP classification processed {len(candidates)} candidates, found {len(mcp_findings)} verified secrets")
            return mcp_findings
            
        except Exception as e:
            logger.error(f"MCP classification failed: {e}")
            return []
    
    def _merge_findings(self, regex_findings: List[Dict[str, Any]], mcp_findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge and deduplicate findings."""
        # For now, prioritize MCP findings over regex findings
        # In the future, we could implement more sophisticated deduplication
        all_findings = mcp_findings + regex_findings
        
        # Simple deduplication based on file path and line
        seen = set()
        unique_findings = []
        
        for finding in all_findings:
            key = (finding["file_path"], finding["start_line"], finding["type"])
            if key not in seen:
                seen.add(key)
                unique_findings.append(finding)
        
        return unique_findings
    
    def _calculate_risk_score(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate risk score based on findings."""
        if not findings:
            return 0.0
        
        severity_weights = {
            "CRITICAL": 10.0,
            "HIGH": 7.0,
            "MEDIUM": 4.0,
            "LOW": 1.0
        }
        
        total_weight = 0.0
        for finding in findings:
            severity = finding.get("severity", "LOW")
            confidence = finding.get("confidence", 0.5)
            weight = severity_weights.get(severity, 1.0)
            total_weight += weight * confidence
        
        # Normalize to 0-100 scale
        max_possible_weight = len(findings) * 10.0
        risk_score = min(100.0, (total_weight / max_possible_weight) * 100.0) if max_possible_weight > 0 else 0.0
        
        return round(risk_score, 2)
    
    async def _persist_findings(self, scan_id: str, findings: List[Dict[str, Any]], db) -> None:
        """Persist findings to database."""
        for finding in findings:
            db_finding = Finding(
                scan_id=scan_id,
                type=finding["type"],
                severity=finding["severity"],
                confidence=finding["confidence"],
                repo=finding.get("repo", "unknown"),
                file_path=finding["file_path"],
                start_line=finding["start_line"],
                end_line=finding["end_line"],
                evidence_snippet_hash=finding["evidence_snippet_hash"],
                engine=finding["engine"],
                description=finding["description"],
                remediation_text=finding.get("remediation_text", "")
            )
            db.add(db_finding)
        
        db.commit()
        logger.info(f"Persisted {len(findings)} findings to database")
    
    def _get_context_lines(self, lines: List[str], start_line: int, end_line: int, context: int = 3) -> str:
        """Get context lines around a finding."""
        start_idx = max(0, start_line - 1 - context)
        end_idx = min(len(lines), end_line + context)
        
        context_lines = []
        for i in range(start_idx, end_idx):
            line_num = i + 1
            prefix = ">>> " if start_line <= line_num <= end_line else "    "
            context_lines.append(f"{prefix}{line_num:4d}: {lines[i]}")
        
        return "\n".join(context_lines)
    
    async def _cleanup_repo(self, repo_path: str) -> None:
        """Clean up repository directory."""
        try:
            import shutil
            shutil.rmtree(repo_path)
            logger.info(f"Cleaned up repository directory: {repo_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup repository directory {repo_path}: {e}")
