"""AWS remediation stubs for VaultSentinel."""

import boto3
import logging
from typing import Dict, Optional
from agent.config import settings

logger = logging.getLogger(__name__)


class AWSRemediationStub:
    """AWS remediation stub for rotating/revoking credentials."""
    
    def __init__(self):
        """Initialize AWS remediation stub."""
        self.enabled = settings.remediation_enabled
        self.aws_access_key_id = settings.aws_access_key_id
        self.aws_secret_access_key = settings.aws_secret_access_key
        
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
    
    def disable_access_key(self, access_key_id: str, username: Optional[str] = None) -> Dict:
        """Disable an AWS access key.
        
        Args:
            access_key_id: AWS access key ID to disable
            username: IAM username (optional, will be detected if not provided)
            
        Returns:
            Dictionary with operation result
        """
        if not self.enabled:
            return {
                "success": False,
                "message": "AWS remediation disabled - this is a stub operation",
                "action": "stub"
            }
        
        try:
            # If username not provided, try to find it
            if not username:
                username = self._find_username_for_access_key(access_key_id)
                if not username:
                    return {
                        "success": False,
                        "message": f"Could not find username for access key {access_key_id}",
                        "action": "failed"
                    }
            
            # Disable the access key
            self.iam_client.update_access_key(
                UserName=username,
                AccessKeyId=access_key_id,
                Status='Inactive'
            )
            
            logger.info(f"Successfully disabled access key {access_key_id} for user {username}")
            
            return {
                "success": True,
                "message": f"Access key {access_key_id} disabled for user {username}",
                "action": "disabled",
                "username": username
            }
            
        except Exception as e:
            logger.error(f"Failed to disable access key {access_key_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to disable access key: {str(e)}",
                "action": "failed"
            }
    
    def delete_access_key(self, access_key_id: str, username: Optional[str] = None) -> Dict:
        """Delete an AWS access key.
        
        Args:
            access_key_id: AWS access key ID to delete
            username: IAM username (optional, will be detected if not provided)
            
        Returns:
            Dictionary with operation result
        """
        if not self.enabled:
            return {
                "success": False,
                "message": "AWS remediation disabled - this is a stub operation",
                "action": "stub"
            }
        
        try:
            # If username not provided, try to find it
            if not username:
                username = self._find_username_for_access_key(access_key_id)
                if not username:
                    return {
                        "success": False,
                        "message": f"Could not find username for access key {access_key_id}",
                        "action": "failed"
                    }
            
            # Delete the access key
            self.iam_client.delete_access_key(
                UserName=username,
                AccessKeyId=access_key_id
            )
            
            logger.info(f"Successfully deleted access key {access_key_id} for user {username}")
            
            return {
                "success": True,
                "message": f"Access key {access_key_id} deleted for user {username}",
                "action": "deleted",
                "username": username
            }
            
        except Exception as e:
            logger.error(f"Failed to delete access key {access_key_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete access key: {str(e)}",
                "action": "failed"
            }
    
    def _find_username_for_access_key(self, access_key_id: str) -> Optional[str]:
        """Find the username associated with an access key.
        
        Args:
            access_key_id: AWS access key ID
            
        Returns:
            Username if found, None otherwise
        """
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
                            if key['AccessKeyId'] == access_key_id:
                                return username
                                
                    except Exception:
                        # Skip users we can't access
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find username for access key {access_key_id}: {e}")
            return None
    
    def test_connection(self) -> Dict:
        """Test AWS connection.
        
        Returns:
            Dictionary with test result
        """
        if not self.enabled:
            return {
                "success": False,
                "message": "AWS remediation disabled",
                "action": "stub"
            }
        
        try:
            # Test connection by listing users
            self.iam_client.list_users(MaxItems=1)
            
            return {
                "success": True,
                "message": "AWS connection successful",
                "action": "tested"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"AWS connection failed: {str(e)}",
                "action": "failed"
            }


def get_aws_remediation() -> AWSRemediationStub:
    """Get AWS remediation stub instance.
    
    Returns:
        AWS remediation stub instance
    """
    return AWSRemediationStub()
