# VaultSentinel Scanner Runbook

This document provides comprehensive guidance for the VaultSentinel repository scanner, including setup, configuration, and troubleshooting.

## Overview

The VaultSentinel scanner is a comprehensive security scanning solution that combines:

- **Regex Detection**: Fast pattern matching for common secrets
- **AI Classification**: MCP-powered LLM analysis for context-aware detection
- **Risk Assessment**: Automated risk scoring and severity classification
- **Report Generation**: Human-readable HTML reports with remediation guidance

## Architecture

```
Frontend (React) → Backend API (FastAPI) → Scan Engine → GitHub → MCP Server
                                    ↓
                              Database (SQLite/PostgreSQL)
```

### Components

1. **Scan Engine** (`scanner/scan_engine.py`): Core scanning logic
2. **Regex Detectors** (`detection/regex_detectors.py`): Pattern-based detection
3. **MCP Classifier** (`detection/mcp_classifier.py`): AI-powered classification
4. **API Routes** (`api/scanner_routes.py`): REST API endpoints
5. **Report Renderer** (`api/report_renderer.py`): HTML report generation
6. **Frontend Pages**: React components for user interface

## Configuration

### Environment Variables

```bash
# MCP Configuration
MCP_BASE_URL=https://vaultsentinel-mcp-923046029861.us-west1.run.app
MCP_API_KEY=your-mcp-api-key
MCP_TIMEOUT_MS=20000
MCP_RETRIES=2

# Web Configuration
FRONTEND_ORIGIN=http://localhost:3000
BACKEND_ORIGIN=http://localhost:8000

# Optional: GitHub Rate Limiting
GITHUB_TOKEN=your-github-token
```

### Database Configuration

The scanner uses SQLite by default in development and PostgreSQL in production:

```bash
# Development
DATABASE_URL=sqlite:///./vaultsentinel.db

# Production
DATABASE_URL=postgresql://user:password@localhost/vaultsentinel
```

## API Endpoints

### Scan Management

#### Create Scan
```http
POST /api/scans
Content-Type: application/json

{
  "repo_url": "https://github.com/owner/repo",
  "branch": "main",
  "mode": "full",
  "include": ["**/*.py", "**/*.js", "**/*.env"],
  "exclude": ["**/node_modules/**", "**/dist/**"],
  "max_files": 2000,
  "max_bytes_per_file": 200000,
  "timeout_sec": 120
}
```

**Response:**
```json
{
  "scan_id": "uuid-here",
  "status": "queued",
  "message": "Scan job created successfully"
}
```

#### Get Scan Status
```http
GET /api/scans/{scan_id}/status
```

**Response:**
```json
{
  "status": "running",
  "progress": 45,
  "message": null
}
```

#### Get Scan Report
```http
GET /scans/{scan_id}/report
```

**Response:** HTML report page

### Findings Management

#### Get Findings
```http
GET /api/findings?repo=owner/repo&severity=HIGH&limit=100&offset=0
```

**Response:**
```json
[
  {
    "id": "uuid",
    "type": "aws_access_key",
    "severity": "HIGH",
    "confidence": 0.95,
    "repo": "owner/repo",
    "file_path": "config/aws.py",
    "start_line": 15,
    "end_line": 15,
    "description": "AWS Access Key found",
    "remediation_text": "Remove hardcoded key...",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

#### Get Finding Details
```http
GET /api/findings/{finding_id}
```

### Remediation

#### Generate Remediation
```http
POST /api/remediate
Content-Type: application/json

{
  "finding_ids": ["uuid1", "uuid2"],
  "repo_url": "https://github.com/owner/repo",
  "branch": "main"
}
```

**Response:**
```json
{
  "unified_diff": "--- a/file.py\n+++ b/file.py\n@@ -15,1 +15,1 @@\n-aws_key = 'AKIA...'\n+# SECRET REMOVED",
  "pr_title": "Security: Fix 2 secret(s) in owner/repo",
  "pr_body": "## Security Fix\n\nThis PR addresses the following security findings..."
}
```

### MCP Classification

#### Classify Text
```http
POST /api/mcp/classify
Content-Type: application/json

{
  "text": "AWS_ACCESS_KEY_ID_EXAMPLE_123"
}
```

**Response:**
```json
{
  "is_secret": true,
  "is_vulnerability": false,
  "type": "aws_access_key",
  "severity": "HIGH",
  "confidence": 0.95,
  "remediation": "Rotate the AWS access key immediately",
  "reasoning": "This appears to be a valid AWS access key format"
}
```

### Dashboard Statistics

#### Get Dashboard Stats
```http
GET /api/dashboard/stats
```

**Response:**
```json
{
  "total_scans": 25,
  "total_findings": 150,
  "severity_breakdown": {
    "CRITICAL": 5,
    "HIGH": 20,
    "MEDIUM": 50,
    "LOW": 75
  },
  "top_secret_types": {
    "aws_access_key": 30,
    "github_token": 25,
    "password": 20
  },
  "recent_scans": [...]
}
```

## Frontend Pages

### 1. Landing Page (`/`)
- Repository URL input with validation
- Branch selection
- Advanced options (include/exclude patterns)
- Real-time scan progress
- Completion redirect to report

### 2. Dashboards (`/dashboards`)
- KPI tiles (total scans, findings, critical issues)
- Severity breakdown charts
- Top secret types
- Recent scans list
- Quick action buttons

### 3. Findings (`/findings`)
- Searchable and filterable findings table
- Severity-based color coding
- Finding detail modal
- Context lines and remediation
- Generate patch functionality

### 4. Scan Report (`/scans/:scanId/report`)
- Risk score gauge
- Severity-based findings sections
- File context and remediation
- Export options (PDF, SARIF)
- Copy PR body/commands

### 5. MCP Classify (`/mcp`)
- Text input for quick classification
- Real-time AI analysis
- Confidence scores and reasoning
- Remediation suggestions

## Scan Process

### 1. Repository Cloning
- Validates GitHub URL format
- Clones with `--depth=1` for efficiency
- Supports branch selection
- Handles authentication if `GITHUB_TOKEN` provided

### 2. File Selection
- Applies include/exclude glob patterns
- Respects file size limits
- Skips binary files and common exclusions
- Limits total files for performance

### 3. Regex Detection
- Runs compiled regex patterns
- Detects common secret types:
  - AWS Access Keys: `AKIA[0-9A-Z]{16}`
  - AWS Secret Keys: Generic pattern matching
  - Google API Keys: `AIza[0-9A-Za-z\-_]{35}`
  - Slack Tokens: `xox[baprs]-[0-9a-zA-Z]{10,48}`
  - GitHub Tokens: `ghp_[0-9a-zA-Z]{36}`
  - Private Keys: `-----BEGIN (?:RSA|EC|DSA|OPENSSH) PRIVATE KEY-----`
  - And more...

### 4. MCP Classification
- Sends regex candidates to MCP server
- AI-powered verification and enhancement
- Context-aware severity assessment
- Remediation guidance generation

### 5. Risk Scoring
- Weighted severity calculation
- Confidence-based adjustments
- Normalized 0-100 scale
- Critical (80+), High (60+), Medium (40+), Low (<40)

### 6. Report Generation
- HTML template with Tailwind CSS
- Interactive charts and visualizations
- Exportable formats (PDF, SARIF)
- Copy-paste remediation

## Security Features

### Secret Protection
- Secrets never logged or exposed to frontend
- All analysis happens server-side
- Secure MCP communication with API keys
- Redacted error messages

### Input Validation
- GitHub URL format validation
- File size and count limits
- Path traversal prevention
- SSRF protection

### Rate Limiting
- 3 scans per minute per IP
- Burst allowance of 6 scans
- Request timeout handling
- Graceful degradation

## Performance Optimization

### Scan Limits
- Default: 2000 files per scan
- File size limit: 200KB per file
- Timeout: 120 seconds
- Concurrent processing

### Database Optimization
- Indexed queries on severity, type, repo
- Pagination for large result sets
- Efficient aggregation queries
- Connection pooling

### Caching
- MCP response caching
- Database query optimization
- Static asset caching
- CDN integration ready

## Troubleshooting

### Common Issues

#### 1. Scan Timeout
**Symptoms**: Scan fails with timeout error
**Solution**: 
- Increase `timeout_sec` in scan request
- Reduce `max_files` limit
- Check repository size and complexity

#### 2. MCP Classification Failures
**Symptoms**: Regex findings not getting AI verification
**Solution**:
- Check MCP server connectivity
- Verify API key configuration
- Review MCP server logs
- Enable demo mode for testing

#### 3. Database Connection Issues
**Symptoms**: Scan creation fails
**Solution**:
- Verify database URL configuration
- Check database permissions
- Ensure database is running
- Run database migrations

#### 4. GitHub Rate Limiting
**Symptoms**: Repository cloning fails
**Solution**:
- Add `GITHUB_TOKEN` to environment
- Reduce concurrent scans
- Implement exponential backoff

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

```bash
# Check API health
curl http://localhost:8000/healthz

# Check MCP connectivity
curl http://localhost:8000/api/mcp/health

# Check database
curl http://localhost:8000/api/dashboard/stats
```

## Monitoring

### Key Metrics
- Scan completion rate
- Average scan duration
- Finding detection rate
- MCP classification accuracy
- Error rates by component

### Alerts
- High error rates (>10%)
- Long scan durations (>5 minutes)
- MCP service failures
- Database connection issues

## Production Deployment

### Environment Setup
1. Configure production database
2. Set up MCP server credentials
3. Configure GitHub token for rate limiting
4. Set up monitoring and logging

### Scaling Considerations
- Database connection pooling
- Horizontal scaling with load balancer
- MCP server capacity planning
- File storage for large repositories

### Security Hardening
- HTTPS enforcement
- API key rotation
- Database encryption
- Network security groups
- Regular security updates

## Support

For issues or questions:

1. Check this runbook first
2. Review application logs
3. Test with demo mode
4. Contact the development team

## Changelog

- **v1.0.0**: Initial scanner implementation
  - Regex detection engine
  - MCP classification integration
  - HTML report generation
  - React frontend
  - Comprehensive API
  - Security features
  - Performance optimization
