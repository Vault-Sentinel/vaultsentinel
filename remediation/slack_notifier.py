"""Slack notification system for VaultSentinel."""

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
from agent.config import settings


class SlackNotifier:
    """Slack notification system."""
    
    def __init__(self):
        """Initialize Slack notifier."""
        self.webhook_url = settings.slack_webhook_url
        self.retry_attempts = 3
        self.retry_delay = 1  # seconds
    
    def send_alert(self, finding: Dict) -> bool:
        """Send a single finding alert to Slack.
        
        Args:
            finding: Finding dictionary
            
        Returns:
            True if alert was sent successfully
        """
        message = self._format_finding_message(finding)
        return self._send_message(message)
    
    def send_batch_alert(self, findings: List[Dict]) -> bool:
        """Send a batch of findings to Slack.
        
        Args:
            findings: List of finding dictionaries
            
        Returns:
            True if alert was sent successfully
        """
        if not findings:
            return True
        
        message = self._format_batch_message(findings)
        return self._send_message(message)
    
    def _format_finding_message(self, finding: Dict) -> Dict:
        """Format a single finding into Slack message.
        
        Args:
            finding: Finding dictionary
            
        Returns:
            Formatted Slack message
        """
        confidence_percent = int(finding["confidence"] * 100)
        confidence_emoji = "🔴" if confidence_percent >= 80 else "🟡" if confidence_percent >= 50 else "🟢"
        
        # Determine action status
        action_status = "manual" if not settings.remediation_enabled else "stub"
        
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
                        "text": f"*Repository:*\n{finding['repo']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Confidence:*\n{confidence_percent}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{finding['secret_kind']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{finding['status']}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Commit:*\n`{finding['commit_sha'][:8]}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*File:*\n`{finding['file_path']}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Lines:*\n{finding['line_start']}-{finding['line_end']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Preview:*\n`{finding['masked_preview']}`"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Action Required:* {action_status}\n*First Seen:* {finding['first_seen_at']}"
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
                        "url": f"http://localhost:8000/findings/{finding['id']}",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Acknowledge"
                        },
                        "value": finding['id'],
                        "action_id": "acknowledge_finding"
                    }
                ]
            }
        ]
        
        return {
            "blocks": blocks,
            "text": f"VaultSentinel detected a {finding['secret_kind']} with {confidence_percent}% confidence"
        }
    
    def _format_batch_message(self, findings: List[Dict]) -> Dict:
        """Format multiple findings into a batch Slack message.
        
        Args:
            findings: List of finding dictionaries
            
        Returns:
            Formatted Slack message
        """
        total_findings = len(findings)
        high_confidence = sum(1 for f in findings if f["confidence"] >= 0.8)
        medium_confidence = sum(1 for f in findings if 0.5 <= f["confidence"] < 0.8)
        low_confidence = sum(1 for f in findings if f["confidence"] < 0.5)
        
        # Group by secret kind
        kinds = {}
        for finding in findings:
            kind = finding["secret_kind"]
            kinds[kind] = kinds.get(kind, 0) + 1
        
        kind_summary = ", ".join([f"{kind}: {count}" for kind, count in kinds.items()])
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 VaultSentinel Batch Alert - {total_findings} Secrets Detected"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Findings:*\n{total_findings}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*High Confidence:*\n{high_confidence}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Medium Confidence:*\n{medium_confidence}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Low Confidence:*\n{low_confidence}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Secret Types:* {kind_summary}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View All Findings"
                        },
                        "url": "http://localhost:8000/findings",
                        "style": "primary"
                    }
                ]
            }
        ]
        
        return {
            "blocks": blocks,
            "text": f"VaultSentinel detected {total_findings} secrets across the repository"
        }
    
    def _send_message(self, message: Dict) -> bool:
        """Send message to Slack webhook.
        
        Args:
            message: Slack message dictionary
            
        Returns:
            True if message was sent successfully
        """
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
                print(f"Slack notification attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    import time
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    print(f"All Slack notification attempts failed: {e}")
                    return False
        
        return False
    
    def test_connection(self) -> bool:
        """Test Slack webhook connection.
        
        Returns:
            True if connection is successful
        """
        test_message = {
            "text": "VaultSentinel connection test",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "✅ VaultSentinel Slack integration is working!"
                    }
                }
            ]
        }
        
        return self._send_message(test_message)
