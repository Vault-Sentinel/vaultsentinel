"""FastAPI application for VaultSentinel."""

import time
import os
import subprocess
import tempfile
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from core.config import get_config
from core.storage import FindingRepository, ScanRunRepository
from core.models import Finding, FindingStatus, SecretKind
from core.agent import VaultSentinelAgent

# Global agent instance
_agent: Optional[VaultSentinelAgent] = None

def get_agent() -> VaultSentinelAgent:
    """Get the global agent instance."""
    global _agent
    if _agent is None:
        _agent = VaultSentinelAgent()
    return _agent

def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="VaultSentinel",
        description="Agentic system for continuous secrets shielding",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files for React build
    current_dir = Path(__file__).parent.parent.parent
    dist_path = current_dir / "packages" / "ui" / "dist"
    
    if dist_path.exists():
        # Mount assets directory to serve CSS and JS files
        assets_path = dist_path / "assets"
        if assets_path.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
            print(f"Frontend assets mounted from: {assets_path}")
        else:
            print(f"Warning: Assets directory not found at {assets_path}")
    else:
        print(f"Warning: Frontend dist directory not found at {dist_path}")

    # Startup time for uptime calculation
    startup_time = time.time()
    
    class FindingUpdate(BaseModel):
        """Model for updating finding status."""
        status: Optional[FindingStatus] = None
        notes: Optional[str] = None
    
    @app.get("/healthz")
    async def health_check():
        """Health check endpoint."""
        print("Health check requested")
        uptime = time.time() - startup_time
        agent = get_agent()
        status = agent.get_status()
        
        return {
            "status": "ok",
            "version": "1.0.0",
            "uptime": uptime,
            "agent_status": status
        }
    
    @app.get("/api/findings")
    async def get_findings(
        status: Optional[str] = Query(None, description="Filter by status"),
        kind: Optional[str] = Query(None, description="Filter by secret kind"),
        since: Optional[str] = Query(None, description="Filter by date (ISO format)"),
        repo: Optional[str] = Query(None, description="Filter by repository"),
        limit: int = Query(100, description="Limit results"),
        offset: int = Query(0, description="Offset for pagination")
    ):
        """Get findings with optional filters."""
        agent = get_agent()
        finding_repo = agent.finding_repo
        
        # Convert string parameters to enum values, handling empty strings
        status_enum = None
        if status and status.strip():
            try:
                status_enum = FindingStatus(status)
            except ValueError:
                pass
        
        kind_enum = None
        if kind and kind.strip():
            try:
                kind_enum = SecretKind(kind)
            except ValueError:
                pass
        
        findings = finding_repo.get_all(
            limit=limit,
            offset=offset,
            status=status_enum,
            kind=kind_enum,
            repo=repo if repo and repo.strip() else None
        )
        
        return {
            "findings": [finding.to_dict() for finding in findings],
            "total": len(findings),
            "limit": limit,
            "offset": offset
        }
    
    @app.patch("/findings/{finding_id}")
    async def update_finding(
        finding_id: str,
        update: FindingUpdate
    ):
        """Update finding status and notes."""
        agent = get_agent()
        finding_repo = agent.finding_repo
        
        finding = finding_repo.get_by_id(finding_id)
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        
        if update.status:
            finding.status = update.status
        
        if update.notes is not None:
            finding.notes = update.notes
        
        finding.last_seen_at = datetime.utcnow()
        finding_repo.update(finding)
        
        return {"message": "Finding updated successfully"}
    
    @app.get("/api/metrics")
    async def get_metrics():
        """Get basic metrics."""
        agent = get_agent()
        finding_repo = agent.finding_repo
        scan_run_repo = agent.scan_run_repo
        
        # Get finding metrics
        finding_metrics = finding_repo.get_metrics()
        
        # Get last scan time
        last_scan = scan_run_repo.get_latest()
        
        return {
            "findings": finding_metrics,
            "last_scan_at": last_scan.started_at.isoformat() if last_scan else None,
            "agent_status": agent.get_status()
        }
    
    @app.post("/api/scan")
    async def trigger_scan(repo: str = "Vault-Sentinel/test-VS", github_url: str = None):
        """Trigger a manual scan of the specified repository."""
        try:
            agent = get_agent()
            
            # Determine what to scan
            if github_url:
                # Extract repo name from GitHub URL
                if "github.com/" in github_url:
                    repo_path = github_url.split("github.com/")[1].rstrip("/")
                    repo = repo_path
                else:
                    raise HTTPException(status_code=400, detail="Invalid GitHub URL format")
            
            print(f"🔍 Starting manual scan of {repo}...")
            
            # Initialize detectors
            from packages.detectors.regex_detector import RegexDetector
            from packages.detectors.entropy_detector import EntropyDetector
            from packages.core.interfaces import DetectionContext
            
            regex_detector = RegexDetector()
            entropy_detector = EntropyDetector()
            
            findings_count = 0
            
            # Check if it's a local test repo or GitHub repo
            if repo == "Vault-Sentinel/test-VS" or "test-VS" in repo:
                # Scan local test files
                test_files = [
                    "test-secrets-repo/config.py",
                    "test-secrets-repo/README.md"
                ]
                
                for file_path in test_files:
                    if not os.path.exists(file_path):
                        continue
                        
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Create detection context
                    context = DetectionContext(
                        repo=repo,
                        commit_sha="manual-scan-123",
                        file_path=file_path,
                        content=content
                    )
                    
                    # Run detection
                    regex_findings = list(regex_detector.detect(context))
                    entropy_findings = list(entropy_detector.detect(context))
                    file_findings = regex_findings + entropy_findings
                    findings_count += len(file_findings)
                    
                    # Store findings
                    for finding in file_findings:
                        try:
                            agent.finding_repo.create(finding)
                        except Exception as e:
                            print(f"Warning: Could not store finding: {e}")
            else:
                # For GitHub repos, we would need to clone and scan
                # For now, return a message about GitHub scanning
                return {
                    "message": f"GitHub repository scanning not yet implemented",
                    "repo": repo,
                    "github_url": github_url,
                    "findings_count": 0,
                    "scan_id": f"github-scan-{int(time.time())}",
                    "status": "not_implemented",
                    "note": "Currently only supports local test repository scanning"
                }
            
            # Create a scan run record
            from packages.core.models import ScanRun
            scan_run = ScanRun(
                id=f"manual-scan-{int(time.time())}",
                repo=repo,
                started_at=datetime.utcnow(),
                ended_at=datetime.utcnow(),
                status="OK",
                new_findings_count=findings_count,
                commit_range="manual-scan-123"
            )
            
            try:
                agent.scan_run_repo.create(scan_run)
            except Exception as e:
                print(f"Warning: Could not store scan run: {e}")
            
            return {
                "message": f"Scan completed successfully",
                "repo": repo,
                "findings_count": findings_count,
                "scan_id": scan_run.id,
                "status": "completed"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
    
    @app.post("/api/scan-github")
    async def scan_github_repo(request: dict):
        """Scan a GitHub repository by URL."""
        try:
            github_url = request.get("github_url")
            if not github_url:
                raise HTTPException(status_code=400, detail="github_url is required")
            
            # Extract repo name from GitHub URL
            if "github.com/" not in github_url:
                raise HTTPException(status_code=400, detail="Invalid GitHub URL format")
            
            repo_path = github_url.split("github.com/")[1].rstrip("/")
            print(f"🔍 Starting GitHub scan of {repo_path}...")
            
            # For now, we'll simulate GitHub scanning by using the test files
            # In a real implementation, this would:
            # 1. Clone the GitHub repository
            # 2. Scan all files in the repo
            # 3. Use the GitHub connector to fetch commits
            
            agent = get_agent()
            
            # Initialize detectors
            from packages.detectors.regex_detector import RegexDetector
            from packages.detectors.entropy_detector import EntropyDetector
            from packages.core.interfaces import DetectionContext
            
            regex_detector = RegexDetector()
            entropy_detector = EntropyDetector()
            
            findings_count = 0
            
            # Actually clone and scan the GitHub repository
            findings = clone_and_scan_github_repo(github_url, regex_detector, entropy_detector)
            findings_count = len(findings)
            
            # Store findings
            stored_count = 0
            for finding in findings:
                try:
                    agent.finding_repo.create(finding)
                    stored_count += 1
                except Exception as e:
                    print(f"❌ Error storing finding: {e}")
                    print(f"Finding details: {finding}")
                    import traceback
                    traceback.print_exc()
            
            print(f"✅ Successfully stored {stored_count} out of {len(findings)} findings")
            
            # Create a scan run record
            from packages.core.models import ScanRun
            scan_run = ScanRun(
                id=f"github-scan-{int(time.time())}",
                repo=repo_path,
                started_at=datetime.utcnow(),
                ended_at=datetime.utcnow(),
                status="OK",
                new_findings_count=findings_count,
                commit_range="github-scan-123"
            )
            
            try:
                agent.scan_run_repo.create(scan_run)
            except Exception as e:
                print(f"Warning: Could not store scan run: {e}")
            
            return {
                "message": f"GitHub repository scan completed",
                "repo": repo_path,
                "github_url": github_url,
                "findings_count": findings_count,
                "scan_id": scan_run.id,
                "status": "completed",
                "note": f"Scanned actual files from {repo_path} repository"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"GitHub scan failed: {str(e)}")
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Serve React frontend."""
        try:
            html_path = dist_path / "index.html"
            with open(html_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>VaultSentinel Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>VaultSentinel Dashboard</h1>
                    <p>Continuous secrets shielding for your repositories</p>
                    <p><a href="/docs">API Documentation</a> | <a href="/metrics">Metrics</a></p>
                    <p><strong>Note:</strong> React frontend not built. Run <code>cd packages/ui && npm run build</code> to build the frontend.</p>
                </div>
            </body>
            </html>
            """
    
    @app.get("/{path:path}", response_class=HTMLResponse)
    async def serve_react_app(path: str):
        """Serve React app for all non-API routes (client-side routing)."""
        # Skip API routes - only handle actual API endpoints, not React routes
        api_routes = ['docs', 'redoc', 'openapi.json', 'healthz']
        if path in api_routes or path.startswith('api/'):
            raise HTTPException(status_code=404, detail="Not found")
        
        try:
            html_path = dist_path / "index.html"
            with open(html_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>VaultSentinel Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>VaultSentinel Dashboard</h1>
                    <p>Continuous secrets shielding for your repositories</p>
                    <p><a href="/docs">API Documentation</a> | <a href="/metrics">Metrics</a></p>
                    <p><strong>Note:</strong> React frontend not built. Run <code>cd packages/ui && npm run build</code> to build the frontend.</p>
                </div>
            </body>
            </html>
            """
    
    return app

def clone_and_scan_github_repo(github_url: str, regex_detector, entropy_detector):
    """Clone a GitHub repository and scan it for secrets."""
    from packages.core.interfaces import DetectionContext
    findings = []
    
    # Extract repo name from GitHub URL
    repo_path = github_url.split("github.com/")[1].rstrip("/")
    
    # Create a temporary directory for cloning
    with tempfile.TemporaryDirectory() as temp_dir:
        clone_path = os.path.join(temp_dir, "repo")
        
        try:
            # Clone the repository
            print(f"📥 Cloning {github_url} to {clone_path}...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", github_url, clone_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"❌ Failed to clone repository: {result.stderr}")
                return findings
            
            print(f"✅ Successfully cloned repository")
            
            # Find all files to scan (exclude common non-source files)
            exclude_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env', 'dist', 'build', '.next', '.nuxt'}
            exclude_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.pdf', '.zip', '.tar', '.gz'}
            
            for root, dirs, files in os.walk(clone_path):
                # Remove excluded directories from dirs list to prevent walking into them
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, clone_path)
                    
                    # Skip excluded file types
                    if any(file.lower().endswith(ext) for ext in exclude_extensions):
                        continue
                    
                    # Skip binary files
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except (UnicodeDecodeError, PermissionError):
                        continue
                    
                    # Create detection context
                    context = DetectionContext(
                        repo=repo_path,
                        commit_sha="github-scan-123",
                        file_path=relative_path,
                        content=content
                    )
                    
                    # Run detection
                    regex_findings = list(regex_detector.detect(context))
                    entropy_findings = list(entropy_detector.detect(context))
                    file_findings = regex_findings + entropy_findings
                    
                    if file_findings:
                        findings.extend(file_findings)
                        print(f"🔍 Found {len(file_findings)} secrets in {relative_path}")
            
            print(f"📊 Total findings: {len(findings)}")
            
        except subprocess.TimeoutExpired:
            print("❌ Repository cloning timed out")
        except Exception as e:
            print(f"❌ Error scanning repository: {e}")
    
    return findings
