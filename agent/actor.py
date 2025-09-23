"""Actor for executing actions based on findings."""

import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from remediation.slack_notifier import SlackNotifier
from remediation.aws_stub import get_aws_remediation
from api.models import Finding
from agent.config import settings

logger = logging.getLogger(__name__)


class Actor:
    """Actor for executing actions based on findings."""
    
    def __init__(self, db_session: Session):
        """Initialize actor with database session."""
        self.db = db_session
        self.slack_notifier = SlackNotifier()
        self.aws_remediation = get_aws_remediation()
    
    def process_findings(self, findings: List[Dict]) -> Dict:
        """Process a list of findings and execute actions.
        
        Args:
            findings: List of finding dictionaries
            
        Returns:
            Dictionary with action results
        """
        results = {
            "slack_alerts_sent": 0,
            "remediation_actions": 0,
            "errors": []
        }
        
        if not findings:
            return results
        
        # Send Slack alerts
        try:
            if len(findings) == 1:
                success = self.slack_notifier.send_alert(findings[0])
                if success:
                    results["slack_alerts_sent"] = 1
                else:
                    results["errors"].append("Failed to send Slack alert")
            else:
                success = self.slack_notifier.send_batch_alert(findings)
                if success:
                    results["slack_alerts_sent"] = len(findings)
                else:
                    results["errors"].append("Failed to send batch Slack alert")
        except Exception as e:
            logger.error(f"Error sending Slack alerts: {e}")
            results["errors"].append(f"Slack alert error: {str(e)}")
        
        # Execute remediation actions
        for finding in findings:
            try:
                remediation_result = self._execute_remediation(finding)
                if remediation_result["success"]:
                    results["remediation_actions"] += 1
                else:
                    results["errors"].append(f"Remediation failed: {remediation_result['message']}")
            except Exception as e:
                logger.error(f"Error executing remediation for finding {finding.get('id', 'unknown')}: {e}")
                results["errors"].append(f"Remediation error: {str(e)}")
        
        return results
    
    def _execute_remediation(self, finding: Dict) -> Dict:
        """Execute remediation action for a finding.
        
        Args:
            finding: Finding dictionary
            
        Returns:
            Dictionary with remediation result
        """
        secret_kind = finding.get("secret_kind", "")
        secret = finding.get("secret", "")
        
        # Only attempt remediation for AWS access keys
        if secret_kind == "aws_access_key":
            return self._remediate_aws_access_key(secret, finding)
        elif secret_kind == "aws_secret_key":
            return self._remediate_aws_secret_key(secret, finding)
        else:
            return {
                "success": False,
                "message": f"No remediation available for {secret_kind}",
                "action": "none"
            }
    
    def _remediate_aws_access_key(self, access_key: str, finding: Dict) -> Dict:
        """Remediate AWS access key.
        
        Args:
            access_key: AWS access key ID
            finding: Finding dictionary
            
        Returns:
            Dictionary with remediation result
        """
        logger.info(f"Attempting to remediate AWS access key: {access_key[:8]}...")
        
        # Try to disable the access key
        result = self.aws_remediation.disable_access_key(access_key)
        
        # Update finding with remediation result
        self._update_finding_remediation(finding, result)
        
        return result
    
    def _remediate_aws_secret_key(self, secret_key: str, finding: Dict) -> Dict:
        """Remediate AWS secret key.
        
        Args:
            secret_key: AWS secret access key
            finding: Finding dictionary
            
        Returns:
            Dictionary with remediation result
        """
        logger.info(f"Attempting to remediate AWS secret key: {secret_key[:8]}...")
        
        # For secret keys, we can't directly remediate without the access key ID
        # This is a limitation of the current implementation
        result = {
            "success": False,
            "message": "Cannot remediate secret key without access key ID",
            "action": "manual_required"
        }
        
        # Update finding with remediation result
        self._update_finding_remediation(finding, result)
        
        return result
    
    def _update_finding_remediation(self, finding: Dict, remediation_result: Dict):
        """Update finding with remediation result.
        
        Args:
            finding: Finding dictionary
            remediation_result: Result from remediation action
        """
        try:
            finding_id = finding.get("id")
            if not finding_id:
                return
            
            # Get finding from database
            db_finding = self.db.query(Finding).filter(Finding.id == finding_id).first()
            if not db_finding:
                return
            
            # Update notes with remediation result
            remediation_note = f"Remediation: {remediation_result['action']} - {remediation_result['message']}"
            
            if db_finding.notes:
                db_finding.notes += f"\n{remediation_note}"
            else:
                db_finding.notes = remediation_note
            
            # Update status based on remediation result
            if remediation_result["success"]:
                db_finding.status = "RESOLVED"
            else:
                db_finding.status = "ACKNOWLEDGED"
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating finding remediation: {e}")
    
    def test_connections(self) -> Dict:
        """Test all external connections.
        
        Returns:
            Dictionary with test results
        """
        results = {
            "slack": False,
            "aws": False,
            "errors": []
        }
        
        # Test Slack connection
        try:
            results["slack"] = self.slack_notifier.test_connection()
        except Exception as e:
            results["errors"].append(f"Slack test failed: {str(e)}")
        
        # Test AWS connection
        try:
            aws_result = self.aws_remediation.test_connection()
            results["aws"] = aws_result["success"]
            if not aws_result["success"]:
                results["errors"].append(f"AWS test failed: {aws_result['message']}")
        except Exception as e:
            results["errors"].append(f"AWS test failed: {str(e)}")
        
        return results
