"""Google Cloud Storage service for VaultSentinel scanner."""

import json
import tempfile
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from google.cloud import storage
from google.cloud.exceptions import NotFound
import os

logger = logging.getLogger(__name__)


class GCSStorageService:
    """Google Cloud Storage service for scanner data."""
    
    def __init__(self, bucket_name: Optional[str] = None):
        """Initialize GCS service."""
        self.bucket_name = bucket_name or os.getenv("GCS_BUCKET_NAME", "vaultsentinel-scans")
        self.enabled = os.getenv("GCS_ENABLED", "false").lower() == "true"
        
        if not self.enabled:
            logger.info("GCS storage disabled - using local storage only")
            self.client = None
            self.bucket = None
            return
        
        try:
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
            
            # Ensure bucket exists
            self._ensure_bucket_exists()
        except Exception as e:
            logger.warning(f"Failed to initialize GCS client: {e}")
            logger.info("Falling back to local storage only")
            self.enabled = False
            self.client = None
            self.bucket = None
    
    def _ensure_bucket_exists(self):
        """Ensure the GCS bucket exists."""
        try:
            self.bucket.reload()
            logger.info(f"Using existing bucket: {self.bucket_name}")
        except NotFound:
            logger.info(f"Creating new bucket: {self.bucket_name}")
            self.bucket = self.client.create_bucket(self.bucket_name)
    
    async def store_scan_metadata(self, scan_id: str, metadata: Dict[str, Any]) -> str:
        """Store scan metadata in GCS."""
        if not self.enabled:
            logger.info(f"GCS disabled - skipping metadata storage for scan {scan_id}")
            return f"local/{scan_id}/metadata.json"
        
        blob_name = f"scans/{scan_id}/metadata.json"
        blob = self.bucket.blob(blob_name)
        
        # Add timestamp
        metadata["stored_at"] = datetime.utcnow().isoformat()
        
        blob.upload_from_string(
            json.dumps(metadata, indent=2),
            content_type="application/json"
        )
        
        logger.info(f"Stored scan metadata: gs://{self.bucket_name}/{blob_name}")
        return blob_name
    
    async def store_findings(self, scan_id: str, findings: List[Dict[str, Any]]) -> str:
        """Store findings in GCS."""
        if not self.enabled:
            logger.info(f"GCS disabled - skipping findings storage for scan {scan_id}")
            return f"local/{scan_id}/findings.json"
        
        blob_name = f"scans/{scan_id}/findings.json"
        blob = self.bucket.blob(blob_name)
        
        findings_data = {
            "scan_id": scan_id,
            "findings": findings,
            "count": len(findings),
            "stored_at": datetime.utcnow().isoformat()
        }
        
        blob.upload_from_string(
            json.dumps(findings_data, indent=2),
            content_type="application/json"
        )
        
        logger.info(f"Stored {len(findings)} findings: gs://{self.bucket_name}/{blob_name}")
        return blob_name
    
    async def store_html_report(self, scan_id: str, html_content: str) -> str:
        """Store HTML report in GCS."""
        if not self.enabled:
            logger.info(f"GCS disabled - skipping HTML report storage for scan {scan_id}")
            return f"local/{scan_id}/report.html"
        
        blob_name = f"scans/{scan_id}/report.html"
        blob = self.bucket.blob(blob_name)
        
        blob.upload_from_string(
            html_content,
            content_type="text/html"
        )
        
        logger.info(f"Stored HTML report: gs://{self.bucket_name}/{blob_name}")
        return blob_name
    
    async def store_repository_files(self, scan_id: str, repo_path: str) -> str:
        """Store repository files in GCS for analysis."""
        if not self.enabled:
            logger.info(f"GCS disabled - skipping repository storage for scan {scan_id}")
            return f"local/{scan_id}/repository.zip"
        
        from pathlib import Path
        
        temp_zip_path = None
        try:
            # Create a zip archive of the repository
            import zipfile
            import shutil
            
            temp_zip_path = f"/tmp/{scan_id}_repo.zip"
            
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in Path(repo_path).rglob("**/*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(repo_path)
                        zipf.write(file_path, relative_path)
            
            # Upload to GCS
            blob_name = f"temp/{scan_id}/repository.zip"
            blob = self.bucket.blob(blob_name)
            
            blob.upload_from_filename(temp_zip_path)
            
            logger.info(f"Stored repository: gs://{self.bucket_name}/{blob_name}")
            return blob_name
            
        finally:
            # Cleanup temp file
            if temp_zip_path and os.path.exists(temp_zip_path):
                os.unlink(temp_zip_path)
    
    async def get_findings(self, scan_id: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve findings from GCS."""
        if not self.enabled:
            logger.info(f"GCS disabled - cannot retrieve findings for scan {scan_id}")
            return None
        
        blob_name = f"scans/{scan_id}/findings.json"
        blob = self.bucket.blob(blob_name)
        
        try:
            content = blob.download_as_text()
            data = json.loads(content)
            return data.get("findings", [])
        except NotFound:
            logger.warning(f"Findings not found for scan {scan_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve findings for scan {scan_id}: {e}")
            return None
    
    async def get_scan_metadata(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve scan metadata from GCS."""
        if not self.enabled:
            logger.info(f"GCS disabled - cannot retrieve metadata for scan {scan_id}")
            return None
        
        blob_name = f"scans/{scan_id}/metadata.json"
        blob = self.bucket.blob(blob_name)
        
        try:
            content = blob.download_as_text()
            return json.loads(content)
        except NotFound:
            logger.warning(f"Metadata not found for scan {scan_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve metadata for scan {scan_id}: {e}")
            return None
    
    async def get_html_report_url(self, scan_id: str, expiration_hours: int = 24) -> Optional[str]:
        """Get a signed URL for the HTML report."""
        if not self.enabled:
            logger.info(f"GCS disabled - cannot generate report URL for scan {scan_id}")
            return None
        
        blob_name = f"scans/{scan_id}/report.html"
        blob = self.bucket.blob(blob_name)
        
        try:
            # Check if blob exists
            if not blob.exists():
                return None
            
            # Generate signed URL
            expiration = datetime.utcnow() + timedelta(hours=expiration_hours)
            url = blob.generate_signed_url(expiration=expiration)
            
            return url
        except Exception as e:
            logger.error(f"Failed to generate report URL for scan {scan_id}: {e}")
            return None
    
    async def cleanup_temp_files(self, scan_id: str):
        """Clean up temporary files for a scan."""
        if not self.enabled:
            logger.info(f"GCS disabled - skipping temp file cleanup for scan {scan_id}")
            return
        
        temp_prefix = f"temp/{scan_id}/"
        
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=temp_prefix)
            for blob in blobs:
                blob.delete()
                logger.info(f"Deleted temp file: {blob.name}")
        except Exception as e:
            logger.error(f"Failed to cleanup temp files for scan {scan_id}: {e}")
    
    async def list_scans(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List recent scans from GCS."""
        if not self.enabled:
            logger.info("GCS disabled - cannot list scans from GCS")
            return []
        
        scans = []
        
        try:
            blobs = self.client.list_blobs(
                self.bucket_name, 
                prefix="scans/",
                delimiter="/"
            )
            
            scan_dirs = set()
            for blob in blobs:
                if blob.name.endswith("/metadata.json"):
                    scan_id = blob.name.split("/")[1]
                    scan_dirs.add(scan_id)
            
            # Get metadata for each scan
            for scan_id in list(scan_dirs)[:limit]:
                metadata = await self.get_scan_metadata(scan_id)
                if metadata:
                    scans.append({
                        "scan_id": scan_id,
                        **metadata
                    })
            
            # Sort by stored_at timestamp
            scans.sort(key=lambda x: x.get("stored_at", ""), reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list scans: {e}")
        
        return scans


# Global instance
gcs_storage = GCSStorageService()
