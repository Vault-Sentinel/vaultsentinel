"""Main VaultSentinel service orchestration."""

import logging
import time
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from agent.observer import GitHubObserver
from agent.thinker import Thinker
from agent.actor import Actor
from agent.config import settings, get_redacted_config
from api.models import get_db, ScanRun

logger = logging.getLogger(__name__)


class VaultSentinelService:
    """Main VaultSentinel service."""
    
    def __init__(self):
        """Initialize VaultSentinel service."""
        self.observer = GitHubObserver()
        self.db_session = next(get_db())
        self.thinker = Thinker(self.db_session)
        self.actor = Actor(self.db_session)
        self.running = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def start(self):
        """Start the VaultSentinel service."""
        logger.info("Starting VaultSentinel service...")
        logger.info(f"Configuration: {get_redacted_config()}")
        
        # Test connections
        self._test_connections()
        
        self.running = True
        
        try:
            while self.running:
                self._run_scan_cycle()
                time.sleep(settings.poll_interval_seconds)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Service error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the VaultSentinel service."""
        logger.info("Stopping VaultSentinel service...")
        self.running = False
        self.db_session.close()
    
    def run_once(self) -> Dict:
        """Run a single scan cycle.
        
        Returns:
            Dictionary with scan results
        """
        logger.info("Running single scan cycle...")
        return self._run_scan_cycle()
    
    def _run_scan_cycle(self) -> Dict:
        """Run a single scan cycle.
        
        Returns:
            Dictionary with scan results
        """
        scan_start = datetime.utcnow()
        scan_run_id = None
        
        try:
            # Create scan run record
            scan_run = ScanRun(
                repo=settings.github_repo,
                status="OK",
                started_at=scan_start
            )
            self.db_session.add(scan_run)
            self.db_session.commit()
            scan_run_id = scan_run.id
            
            # Get recent changes
            logger.info("Fetching recent changes from GitHub...")
            changes = self.observer.get_recent_changes(hours=24)
            
            if not changes:
                logger.info("No recent changes found")
                return {
                    "scan_run_id": scan_run_id,
                    "commits_processed": 0,
                    "findings_detected": 0,
                    "alerts_sent": 0,
                    "remediation_actions": 0,
                    "errors": []
                }
            
            total_findings = []
            total_commits = 0
            
            # Process each commit
            for commit, file_changes in changes:
                logger.info(f"Processing commit {commit.sha[:8]}...")
                
                # Convert file changes to format expected by thinker
                file_changes_dict = []
                for file_change in file_changes:
                    file_changes_dict.append({
                        "file_path": file_change.file_path,
                        "status": file_change.status,
                        "content": file_change.content or "",
                        "patch": file_change.patch
                    })
                
                # Process commit with thinker
                findings = self.thinker.process_commit(commit.sha, file_changes_dict)
                total_findings.extend(findings)
                total_commits += 1
                
                logger.info(f"Found {len(findings)} secrets in commit {commit.sha[:8]}")
            
            # Execute actions with actor
            if total_findings:
                logger.info(f"Executing actions for {len(total_findings)} findings...")
                action_results = self.actor.process_findings(total_findings)
                
                # Update scan run with results
                scan_run.new_findings_count = len(total_findings)
                scan_run.ended_at = datetime.utcnow()
                self.db_session.commit()
                
                logger.info(f"Scan completed: {len(total_findings)} findings, "
                          f"{action_results['slack_alerts_sent']} alerts sent, "
                          f"{action_results['remediation_actions']} remediation actions")
                
                return {
                    "scan_run_id": scan_run_id,
                    "commits_processed": total_commits,
                    "findings_detected": len(total_findings),
                    "alerts_sent": action_results["slack_alerts_sent"],
                    "remediation_actions": action_results["remediation_actions"],
                    "errors": action_results["errors"]
                }
            else:
                logger.info("No secrets detected in recent changes")
                scan_run.ended_at = datetime.utcnow()
                self.db_session.commit()
                
                return {
                    "scan_run_id": scan_run_id,
                    "commits_processed": total_commits,
                    "findings_detected": 0,
                    "alerts_sent": 0,
                    "remediation_actions": 0,
                    "errors": []
                }
                
        except Exception as e:
            logger.error(f"Scan cycle error: {e}")
            
            # Update scan run with error
            if scan_run_id:
                scan_run = self.db_session.query(ScanRun).filter(ScanRun.id == scan_run_id).first()
                if scan_run:
                    scan_run.status = "ERROR"
                    scan_run.ended_at = datetime.utcnow()
                    self.db_session.commit()
            
            return {
                "scan_run_id": scan_run_id,
                "commits_processed": 0,
                "findings_detected": 0,
                "alerts_sent": 0,
                "remediation_actions": 0,
                "errors": [str(e)]
            }
    
    def _test_connections(self):
        """Test all external connections."""
        logger.info("Testing external connections...")
        
        # Test GitHub connection
        if not self.observer.test_connection():
            logger.error("GitHub connection test failed")
            raise Exception("GitHub connection test failed")
        logger.info("GitHub connection: OK")
        
        # Test Slack connection
        connection_results = self.actor.test_connections()
        if not connection_results["slack"]:
            logger.error("Slack connection test failed")
            raise Exception("Slack connection test failed")
        logger.info("Slack connection: OK")
        
        if connection_results["aws"]:
            logger.info("AWS connection: OK")
        else:
            logger.warning("AWS connection: Not available (remediation will be stubbed)")
        
        if connection_results["errors"]:
            for error in connection_results["errors"]:
                logger.warning(f"Connection warning: {error}")
    
    def get_status(self) -> Dict:
        """Get service status.
        
        Returns:
            Dictionary with service status
        """
        return {
            "running": self.running,
            "config": get_redacted_config(),
            "last_scan": self._get_last_scan_time(),
            "connections": self.actor.test_connections()
        }
    
    def _get_last_scan_time(self) -> Optional[str]:
        """Get the time of the last scan.
        
        Returns:
            ISO timestamp of last scan or None
        """
        try:
            last_scan = self.db_session.query(ScanRun).order_by(ScanRun.started_at.desc()).first()
            if last_scan:
                return last_scan.started_at.isoformat()
            return None
        except Exception:
            return None
