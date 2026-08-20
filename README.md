# VaultSentinel

> **⚠️ Educational Project**: This is an educational project designed to showcase the Model Context Protocol (MCP) server integration. It demonstrates how to build a secrets detection platform with AI-powered analysis using MCP. This project's live deployment was taken offline post-launch to optimize cloud spend; source code and architecture remain available for review.

A modern secrets detection platform with AI-powered analysis and a comprehensive React dashboard. VaultSentinel provides on-demand repository scanning with hybrid detection (regex + AI) and real-time security findings management.

## 🏗️ Architecture

VaultSentinel is built as a cloud-native application with three main services:

### **Live Production URLs**
- **Frontend**: https://vaultsentinel-frontend-fgain323oq-uw.a.run.app
- **Backend API**: https://vaultsentinel-backend-fgain323oq-uw.a.run.app
- **MCP Server**: https://vaultsentinel-mcp-fgain323oq-uw.a.run.app

### **Technology Stack**
- **Backend**: FastAPI with SQLite database and Google Cloud Storage
- **Frontend**: React 18 + TypeScript + Tailwind CSS + Vite
- **AI Integration**: MCP (Model Context Protocol) for LLM communication
- **Deployment**: Google Cloud Run with Docker containers
- **Storage**: SQLite (local) + Google Cloud Storage (reports)

### **Current Architecture**
```
vaultsentinel/
├─ api/                    # FastAPI backend service
│  ├─ app.py              # Main FastAPI application
│  ├─ scanner_routes.py   # Repository scanning endpoints
│  ├─ scanner_models.py   # Database models
│  ├─ gcs_storage.py      # Google Cloud Storage integration
│  └─ clients/            # MCP client integration
├─ packages/ui/           # React frontend application
│  ├─ src/pages/          # React components (Home, Dashboard, Findings, etc.)
│  ├─ src/services/       # API and MCP service clients
│  └─ dist/               # Built frontend assets
├─ detection/             # Secret detection engines
│  ├─ regex_detectors.py  # Pattern-based detection
│  ├─ entropy.py          # Entropy analysis
│  └─ mcp_classifier.py   # AI-powered classification
├─ scanner/               # Repository scanning engine
├─ mcp-server/            # MCP server for AI integration
├─ Dockerfile.backend     # Backend container
├─ Dockerfile.frontend    # Frontend container
└─ docs/                  # Documentation
```

## 🔌 Plugin Architecture

VaultSentinel uses a plugin-first design where detectors, connectors, and remediation modules can be easily swapped or extended:

### Detector Interface
```python
class Detector(Protocol):
    name: str
    def detect(self, context: DetectionContext) -> Iterable[Finding]: ...
    def is_enabled(self) -> bool: ...
```

### Connector Interface
```python
class Connector(Protocol):
    name: str
    def connect(self) -> bool: ...
    def fetch_changes(self, since: Optional[str] = None) -> Iterable[DetectionContext]: ...
    def is_enabled(self) -> bool: ...
```

### Remediation Handler Interface
```python
class RemediationHandler(Protocol):
    name: str
    def can_handle(self, finding: Finding) -> bool: ...
    def remediate(self, finding: Finding) -> Dict[str, Any]: ...
    def is_enabled(self) -> bool: ...
```

## 🚀 Quick Start

### **🌐 Live Application**
The application is already deployed and running:
- **Frontend**: https://vaultsentinel-frontend-fgain323oq-uw.a.run.app
- **API Documentation**: https://vaultsentinel-backend-fgain323oq-uw.a.run.app/docs

### **📱 Using the Application**

#### **1. Repository Scanning**
1. Open the [Frontend Dashboard](https://vaultsentinel-frontend-fgain323oq-uw.a.run.app)
2. Enter a GitHub repository URL (e.g., `https://github.com/owner/repo`)
3. Click "Start Scan" to begin analysis
4. Monitor real-time progress and view results

#### **2. API Usage**
```bash
# Create a scan
curl -X POST https://vaultsentinel-backend-fgain323oq-uw.a.run.app/api/scans \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/owner/repo",
    "branch": "main",
    "mode": "full"
  }'

# Check scan status
curl https://vaultsentinel-backend-fgain323oq-uw.a.run.app/api/scans/{scan_id}/status

# Get HTML report
curl https://vaultsentinel-backend-fgain323oq-uw.a.run.app/scans/{scan_id}/report
```

#### **3. MCP Integration**
> **Note**: This project showcases MCP (Model Context Protocol) server integration for educational purposes. The MCP server demonstrates how to integrate LLM capabilities into security scanning workflows.

```bash
# Test MCP health
curl https://vaultsentinel-backend-fgain323oq-uw.a.run.app/api/mcp/health

# Classify text using AI
curl -X POST https://vaultsentinel-backend-fgain323oq-uw.a.run.app/api/mcp/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "AKIA1234567890ABCDEF"}]}'
```

### **🔧 Local Development**

#### **Prerequisites**
- Python 3.12+
- Node.js 18+
- Docker (optional)

#### **Backend Setup**
```bash
# Clone the repository
git clone https://github.com/Vault-Sentinel/vaultsentinel.git
cd vaultsentinel

# Install Python dependencies
pip install -r requirements.txt

# Start the backend API
cd api && python -m uvicorn app:app --reload --port 8000
```

#### **Frontend Setup**
```bash
# Install frontend dependencies
cd packages/ui
npm install

# Start development server
npm run dev
```

#### **Docker Development**
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -f Dockerfile.backend -t vaultsentinel-backend .
docker build -f Dockerfile.frontend -t vaultsentinel-frontend .
```

## 🔍 Repository Scanner

### **Features**
- **🔍 Hybrid Detection**: Combines regex patterns with AI-powered classification
- **📊 Risk Scoring**: Automated risk assessment with severity levels
- **📋 Detailed Reports**: Human-readable HTML reports with remediation guidance
- **🎯 Smart Filtering**: Context-aware detection with false positive reduction
- **⚡ Fast Processing**: Optimized for large repositories with configurable limits

### **Detection Capabilities**

#### **Regex Detector**: Pattern-based detection for common secrets
- AWS Access Keys (`AKIA...`)
- AWS Secret Keys (generic patterns)
- Google API Keys (`AIza...`)
- GitHub Tokens (`ghp_...`)
- Slack Tokens (`xox...`)
- Private Keys (`-----BEGIN PRIVATE KEY-----`)
- JWT Secrets (generic patterns)
- Stripe Keys (`sk_live_...`)
- Twilio Tokens
- And more...

#### **AI Classification**: MCP-powered LLM analysis
- Context-aware verification
- Severity assessment
- Remediation guidance
- Confidence scoring

#### **Entropy Detector**: Statistical analysis for high-entropy strings
- Configurable entropy threshold
- False positive filtering
- Context-aware scoring

### **Context Filtering**
- **Allowlist Paths**: Reduces confidence for test files (`/tests/`, `/examples/`)
- **Denylist Patterns**: Filters out dummy/example content
- **File Type Analysis**: Higher confidence for config files
- **Content Analysis**: Detects test fixtures and placeholders

## 📊 API & Dashboard

### **REST API Endpoints**

#### **Core API:**
- `GET /healthz` - Health check endpoint
- `GET /` - Dashboard with recent findings
- `GET /docs` - Interactive API documentation
- `GET /openapi.json` - OpenAPI specification

#### **Repository Scanner API:**
- `POST /api/scans` - Create a new repository scan
- `GET /api/scans/{id}/status` - Get scan progress and status
- `GET /scans/{id}/report` - Get HTML scan report
- `GET /api/findings` - List security findings with filters
- `GET /api/findings/{id}` - Get detailed finding information
- `PATCH /api/findings/{id}` - Update finding status
- `GET /api/dashboard/stats` - Get dashboard statistics

#### **MCP Integration API:**
- `GET /api/mcp/health` - MCP server health check
- `POST /api/mcp/chat` - Forward chat requests to MCP
- `POST /api/mcp/classify` - Classify text using MCP AI

### **React Dashboard**
- **Modern UI**: Built with React 18, TypeScript, and Tailwind CSS
- **Repository Scanner**: Interactive GitHub repository scanning interface
- **Real-time Updates**: Live findings display with auto-refresh
- **Advanced Filtering**: Status, type, repository, and search filters
- **Interactive Management**: Update finding status and add notes
- **Responsive Design**: Mobile-first design with desktop optimization
- **MCP Integration**: Quick text classification and AI-powered analysis
- **Settings Management**: Application configuration and health status

#### **Dashboard Pages:**
- **Home** (`/`) - Repository scanning interface with progress tracking
- **Dashboards** (`/dashboards`) - Security metrics, KPIs, and statistics
- **Findings** (`/findings`) - Searchable and filterable findings table
- **MCP Panel** (`/mcp`) - Quick text classification using AI
- **Settings** (`/settings`) - Application configuration and health status

## 🐳 Docker Deployment

### **Production Deployment (Google Cloud Run)**
The application is deployed on Google Cloud Run with three services:

```bash
# Backend deployment
gcloud run deploy vaultsentinel-backend \
  --source . \
  --region us-west1 \
  --service-account vs-runner@vault-sentinel.iam.gserviceaccount.com \
  --execution-environment gen2 \
  --cpu 1 --memory 512Mi --timeout 60s \
  --set-env-vars GCS_ENABLED=true,GCS_BUCKET_NAME=vaultsentinel-scans,GCS_PROJECT_ID=vault-sentinel \
  --allow-unauthenticated

# Frontend deployment
gcloud run deploy vaultsentinel-frontend \
  --source . \
  --region us-west1 \
  --execution-environment gen2 \
  --cpu 1 --memory 512Mi --timeout 60s \
  --allow-unauthenticated
```

### **Local Docker Development**
```bash
# Build backend image
docker build -f Dockerfile.backend -t vaultsentinel-backend .

# Build frontend image
docker build -f Dockerfile.frontend -t vaultsentinel-frontend .

# Run locally
docker run -p 8000:8080 vaultsentinel-backend
docker run -p 3000:80 vaultsentinel-frontend
```

## 🔧 Configuration Reference

### **Production Environment Variables**

| Variable | Description | Production Value |
|----------|-------------|-----------------|
| `MCP_BASE_URL` | MCP server URL | `https://vaultsentinel-mcp-fgain323oq-uw.a.run.app` |
| `MCP_API_KEY` | MCP API key | `<your-mcp-api-key>` |
| `FRONTEND_ORIGIN` | Frontend CORS origin | `https://vaultsentinel-frontend-fgain323oq-uw.a.run.app` |
| `BACKEND_ORIGIN` | Backend CORS origin | `https://vaultsentinel-backend-fgain323oq-uw.a.run.app` |
| `CORS_ORIGINS` | Allowed CORS origins | `https://vaultsentinel-frontend-fgain323oq-uw.a.run.app` |
| `GCS_ENABLED` | Enable Google Cloud Storage | `true` |
| `GCS_BUCKET_NAME` | GCS bucket for reports | `vaultsentinel-scans` |
| `GCS_PROJECT_ID` | Google Cloud project ID | `vault-sentinel` |
| `DATABASE_URL` | Database connection | `sqlite:///./vaultsentinel.db` |

### **Local Development Configuration**

| Variable | Description | Local Value |
|----------|-------------|-------------|
| `MCP_BASE_URL` | MCP server URL | `https://vaultsentinel-mcp-fgain323oq-uw.a.run.app` |
| `MCP_API_KEY` | MCP API key | `<your-mcp-api-key>` |
| `FRONTEND_ORIGIN` | Frontend CORS origin | `http://localhost:3000` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `GCS_ENABLED` | Enable Google Cloud Storage | `false` |
| `DATABASE_URL` | Database connection | `sqlite:///./vaultsentinel.db` |

## 🔒 Security Considerations

> **⚠️ Security Warning**: Never commit API keys, secrets, or credentials to version control. Always use environment variables or secure secret management systems.

- **Never logs full secrets**: Only masked previews and SHA256 fingerprints
- **Secure storage**: Uses SQLite with proper indexing
- **Environment isolation**: All credentials via environment variables
- **Safe defaults**: Remediation disabled unless explicitly enabled
- **Idempotent operations**: De-duplication by fingerprint + file path
- **Structured logging**: JSON logs for observability
- **Secret management**: All sensitive values should be stored in environment variables or secret management systems

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Start backend development server
cd api && python -m uvicorn app:app --reload --port 8000

# Start frontend development server
cd packages/ui && npm install && npm run dev
```

## 📚 Documentation

- **Repository Scanner**: [Scanner Runbook](docs/runbook_repository_scanner.md)
- **MCP Integration**: [MCP Integration Guide](docs/runbook_mcp_integration.md)
- **API Reference**: Available at https://vaultsentinel-backend-fgain323oq-uw.a.run.app/docs
- **Frontend Guide**: React components and routing documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [GitHub Wiki](https://github.com/Vault-Sentinel/vaultsentinel/wiki)
- **Issues**: [GitHub Issues](https://github.com/Vault-Sentinel/vaultsentinel/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Vault-Sentinel/vaultsentinel/discussions)
- **Security**: [Security Policy](SECURITY.md)

## 🏆 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for the API layer
- Uses [SQLAlchemy](https://www.sqlalchemy.org/) for data persistence
- Leverages [Google Cloud Storage](https://cloud.google.com/storage) for report storage
- Inspired by modern security practices and AI-powered analysis
