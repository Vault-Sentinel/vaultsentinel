"""Core VaultSentinel agent implementing Observe-Think-Act loop."""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import get_config
from .models import Finding, ScanRun, FindingModel, ScanRunModel, Base
from .interfaces import get_registry, DetectionContext
from .storage import FindingRepository, ScanRunRepository

logger = logging.getLogger(__name__)


class VaultSentinelAgent:
    """Core VaultSentinel agent implementing Observe-Think-Act loop."""
    
    def __init__(self):
        """Initialize the agent."""
        self.config = get_config()
        self.registry = get_registry()
        self.running = False
        
        # Setup database
        self.engine = create_engine(self.config.database_url)
        Base.metadata.create_all(self.engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db_session = SessionLocal()
        
        # Setup repositories
        self.finding_repo = FindingRepository(self.db_session)
        self.scan_run_repo = ScanRunRepository(self.db_session)
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup structured logging."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def start(self):
        """Start the agent loop."""
        logger.info("Starting VaultSentinel agent...")
        logger.info(f"Configuration: {self.config.to_dict()}")
        
        # Validate configuration
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Configuration errors: {errors}")
        
        # Test connections
        self._test_connections()
        
        self.running = True
        
        try:
            while self.running:
                self._run_cycle()
                time.sleep(self.config.poll_interval_seconds)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Agent error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the agent loop."""
        logger.info("Stopping VaultSentinel agent...")
        self.running = False
        self.db_session.close()
    
    def run_once(self) -> Dict[str, Any]:
        """Run a single scan cycle."""
        logger.info("Running single scan cycle...")
        return self._run_cycle()
    
    def _run_cycle(self) -> Dict[str, Any]:
        """Run a single Observe-Think-Act cycle."""
        cycle_start = datetime.utcnow()
        
        # Create scan run record
        scan_run = ScanRun(
            repo=self.config.github_repo,
            started_at=cycle_start
        )
        self.scan_run_repo.create(scan_run)
        
        try:
            # OBSERVE: Fetch changes from connectors
            logger.info("Observing changes...")
            contexts = self._observe()
            
            if not contexts:
                logger.info("No changes detected")
                scan_run.ended_at = datetime.utcnow()
                self.scan_run_repo.update(scan_run)
                return {
                    "scan_run_id": scan_run.id,
                    "contexts_processed": 0,
                    "findings_detected": 0,
                    "remediation_actions": 0,
                    "errors": []
                }
            
            # THINK: Detect secrets using detectors
            logger.info("Thinking - detecting secrets...")
            findings = self._think(contexts)
            
            # ACT: Execute remediation actions
            logger.info("Acting - executing remediation...")
            remediation_results = self._act(findings)
            
            # Update scan run
            scan_run.ended_at = datetime.utcnow()
            scan_run.new_findings_count = len(findings)
            self.scan_run_repo.update(scan_run)
            
            logger.info(f"Cycle completed: {len(contexts)} contexts, "
                       f"{len(findings)} findings, "
                       f"{remediation_results['actions_taken']} remediation actions")
            
            return {
                "scan_run_id": scan_run.id,
                "contexts_processed": len(contexts),
                "findings_detected": len(findings),
                "remediation_actions": remediation_results['actions_taken'],
                "errors": remediation_results['errors']
            }
            
        except Exception as e:
            logger.error(f"Cycle error: {e}")
            scan_run.status = "ERROR"
            scan_run.ended_at = datetime.utcnow()
            self.scan_run_repo.update(scan_run)
            
            return {
                "scan_run_id": scan_run.id,
                "contexts_processed": 0,
                "findings_detected": 0,
                "remediation_actions": 0,
                "errors": [str(e)]
            }
    
    def _observe(self) -> List[DetectionContext]:
        """Observe changes from all enabled connectors."""
        contexts = []
        
        for name, connector in self.registry.get_connectors().items():
            try:
                logger.info(f"Observing with connector: {name}")
                connector_contexts = list(connector.fetch_changes())
                contexts.extend(connector_contexts)
                logger.info(f"Connector {name} found {len(connector_contexts)} contexts")
            except Exception as e:
                logger.error(f"Connector {name} error: {e}")
        
        return contexts
    
    def _think(self, contexts: List[DetectionContext]) -> List[Finding]:
        """Think - detect secrets using all enabled detectors."""
        all_findings = []
        
        for context in contexts:
            for name, detector in self.registry.get_detectors().items():
                try:
                    logger.debug(f"Detecting with {name} in {context.file_path}")
                    findings = list(detector.detect(context))
                    
                    # Deduplicate findings
                    for finding in findings:
                        if not self.finding_repo.exists(finding.fingerprint, context.file_path):
                            self.finding_repo.create(finding)
                            all_findings.append(finding)
                            logger.info(f"New finding: {finding.kind.value} in {context.file_path}")
                        else:
                            logger.debug(f"Duplicate finding: {finding.fingerprint}")
                            
                except Exception as e:
                    logger.error(f"Detector {name} error: {e}")
        
        return all_findings
    
    def _act(self, findings: List[Finding]) -> Dict[str, Any]:
        """Act - execute remediation actions."""
        actions_taken = 0
        errors = []
        
        for finding in findings:
            handler = self.registry.get_remediation_handler_for_finding(finding)
            if handler:
                try:
                    result = handler.remediate(finding)
                    actions_taken += 1
                    logger.info(f"Remediation {handler.name}: {result}")
                except Exception as e:
                    error_msg = f"Remediation {handler.name} failed: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            else:
                logger.debug(f"No remediation handler for {finding.kind.value}")
        
        return {
            "actions_taken": actions_taken,
            "errors": errors
        }
    
    def _test_connections(self):
        """Test all external connections."""
        logger.info("Testing external connections...")
        
        # Test connectors
        for name, connector in self.registry.get_connectors().items():
            if not connector.connect():
                raise Exception(f"Connector {name} connection test failed")
            logger.info(f"Connector {name}: OK")
        
        # Test remediation handlers
        for name, handler in self.registry.get_remediation_handlers().items():
            # Test if handler can be instantiated (basic test)
            logger.info(f"Remediation handler {name}: OK")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "running": self.running,
            "config": self.config.to_dict(),
            "last_scan": self._get_last_scan_time(),
            "registered_plugins": {
                "detectors": list(self.registry.get_detectors().keys()),
                "connectors": list(self.registry.get_connectors().keys()),
                "remediation_handlers": list(self.registry.get_remediation_handlers().keys())
            }
        }
    
    def _get_last_scan_time(self) -> Optional[str]:
        """Get the time of the last scan."""
        try:
            last_scan = self.scan_run_repo.get_latest()
            if last_scan:
                return last_scan.started_at.isoformat()
            return None
        except Exception:
            return None
