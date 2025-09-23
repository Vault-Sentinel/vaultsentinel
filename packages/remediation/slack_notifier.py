"""Slack notification handler for VaultSentinel."""

import requests
import logging
from typing import Dict, Any, List
from datetime import datetime

from core.interfaces import RemediationHandler
from core.models import Finding, SecretKind
from core.config import get_config

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Slack notification handler."""
    
    def __init__(self):
        self.config = get_config()
        self.name = "slack"
        self.webhook_url = self.config.slack_webhook_url
        self.retry_attempts = 3
        self.retry_delay = 1  # seconds
    
    def can_handle(self, finding: Finding) -> bool:
        """Check if this handler can handle the finding."""
        # Slack can handle any finding type
        return True
    
    def remediate(self, finding: Finding) -> Dict[str, Any]:
        """Send Slack notification for the finding."""
        try:
            message = self._format_finding_message(finding)
            success = self._send_message(message)
            
            if success:
                return {
                    "success": True,
                    "action": "slack_notification_sent",
                    "message": f"Slack notification sent for {finding.kind.value}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "action": "slack_notification_failed",
                    "message": "Failed to send Slack notification",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            return {
                "success": False,
                "action": "slack_notification_error",
                "message": f"Slack notification error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _format_finding_message(self, finding: Finding) -> Dict[str, Any]:
        """Format a finding into Slack message."""
        confidence_percent = int(finding.confidence * 100)
        confidence_emoji = "🔴" if confidence_percent >= 80 else "🟡" if confidence_percent >= 50 else "🟢"
        
        # Create blocks for rich formatting
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{confidence_emoji} VaultSentinel Secret Detected"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Repository:*\n{finding.repo}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Confidence:*\n{confidence_percent}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{finding.kind.value}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{finding.status.value}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Commit:*\n`{finding.commit_sha[:8]}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*File:*\n`{finding.file_path}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Lines:*\n{finding.line_start}-{finding.line_end}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Preview:*\n`{finding.preview_masked}`"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Action Required:* Manual review\n*First Seen:* {finding.first_seen_at.strftime('%Y-%m-%d %H:%M:%S')}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Details"
                        },
                        "url": f"http://localhost:8000/findings/{finding.id}",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Acknowledge"
                        },
                        "value": finding.id,
                        "action_id": "acknowledge_finding"
                    }
                ]
            }
        ]
        
        return {
            "blocks": blocks,
            "text": f"VaultSentinel detected a {finding.kind.value} with {confidence_percent}% confidence"
        }
    
    def _send_message(self, message: Dict[str, Any]) -> bool:
        """Send message to Slack webhook."""
        for attempt in range(self.retry_attempts):
            try:
                response = requests.post(
                    self.webhook_url,
                    json=message,
                    timeout=10
                )
                response.raise_for_status()
                return True
                
            except requests.RequestException as e:
                logger.error(f"Slack notification attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    import time
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"All Slack notification attempts failed: {e}")
                    return False
        
        return False
    
    def is_enabled(self) -> bool:
        """Check if handler is enabled."""
        return bool(self.webhook_url)
