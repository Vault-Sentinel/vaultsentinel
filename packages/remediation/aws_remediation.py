"""AWS remediation handler for VaultSentinel."""

import boto3
import logging
from typing import Dict, Any, Optional

from core.interfaces import RemediationHandler
from core.models import Finding, SecretKind
from core.config import get_config

logger = logging.getLogger(__name__)


class AWSRemediationHandler:
    """AWS remediation handler for rotating/revoking credentials."""
    
    def __init__(self):
        self.config = get_config()
        self.name = "aws"
        self.enabled = self.config.remediation_enabled
        self.aws_access_key_id = self.config.aws_access_key_id
        self.aws_secret_access_key = self.config.aws_secret_access_key
        
        if self.enabled and self.aws_access_key_id and self.aws_secret_access_key:
            try:
                self.iam_client = boto3.client(
                    'iam',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key
                )
                logger.info("AWS remediation enabled with provided credentials")
            except Exception as e:
                logger.error(f"Failed to initialize AWS client: {e}")
                self.enabled = False
        else:
            self.iam_client = None
            logger.info("AWS remediation disabled - no credentials provided")
    
    def can_handle(self, finding: Finding) -> bool:
        """Check if this handler can handle the finding."""
        return finding.kind in [SecretKind.AWS_ACCESS_KEY, SecretKind.AWS_SECRET_KEY]
    
    def remediate(self, finding: Finding) -> Dict[str, Any]:
        """Attempt to remediate the finding."""
        if not self.enabled:
            return {
                "success": False,
                "action": "stub",
                "message": "AWS remediation disabled - this is a stub operation",
                "timestamp": None
            }
        
        try:
            if finding.kind == SecretKind.AWS_ACCESS_KEY:
                return self._remediate_access_key(finding)
            elif finding.kind == SecretKind.AWS_SECRET_KEY:
                return self._remediate_secret_key(finding)
            else:
                return {
                    "success": False,
                    "action": "unsupported",
                    "message": f"Cannot remediate {finding.kind.value}",
                    "timestamp": None
                }
                
        except Exception as e:
            logger.error(f"AWS remediation error: {e}")
            return {
                "success": False,
                "action": "error",
                "message": f"AWS remediation error: {str(e)}",
                "timestamp": None
            }
    
    def _remediate_access_key(self, finding: Finding) -> Dict[str, Any]:
        """Remediate AWS access key."""
        # Extract access key from finding (this is a simplified approach)
        # In a real implementation, you'd need to extract the actual key
        access_key = finding.preview_masked.replace("*", "")  # This won't work in practice
        
        if not access_key or len(access_key) < 16:
            return {
                "success": False,
                "action": "invalid_key",
                "message": "Cannot extract valid access key from finding",
                "timestamp": None
            }
        
        try:
            # Try to disable the access key
            username = self._find_username_for_access_key(access_key)
            if not username:
                return {
                    "success": False,
                    "action": "user_not_found",
                    "message": f"Cannot find username for access key {access_key[:8]}...",
                    "timestamp": None
                }
            
            # Disable the access key
            self.iam_client.update_access_key(
                UserName=username,
                AccessKeyId=access_key,
                Status='Inactive'
            )
            
            logger.info(f"Successfully disabled access key {access_key[:8]}... for user {username}")
            
            return {
                "success": True,
                "action": "access_key_disabled",
                "message": f"Access key {access_key[:8]}... disabled for user {username}",
                "timestamp": None
            }
            
        except Exception as e:
            logger.error(f"Failed to disable access key {access_key[:8]}...: {e}")
            return {
                "success": False,
                "action": "disable_failed",
                "message": f"Failed to disable access key: {str(e)}",
                "timestamp": None
            }
    
    def _remediate_secret_key(self, finding: Finding) -> Dict[str, Any]:
        """Remediate AWS secret key."""
        # For secret keys, we can't directly remediate without the access key ID
        return {
            "success": False,
            "action": "manual_required",
            "message": "Cannot remediate secret key without access key ID - manual intervention required",
            "timestamp": None
        }
    
    def _find_username_for_access_key(self, access_key: str) -> Optional[str]:
        """Find the username associated with an access key."""
        try:
            # List all users and their access keys
            paginator = self.iam_client.get_paginator('list_users')
            
            for page in paginator.paginate():
                for user in page['Users']:
                    username = user['UserName']
                    
                    # Get access keys for this user
                    try:
                        access_keys = self.iam_client.list_access_keys(UserName=username)
                        
                        for key in access_keys['AccessKeyMetadata']:
                            if key['AccessKeyId'] == access_key:
                                return username
                                
                    except Exception:
                        # Skip users we can't access
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find username for access key {access_key[:8]}...: {e}")
            return None
    
    def is_enabled(self) -> bool:
        """Check if handler is enabled."""
        return self.enabled
