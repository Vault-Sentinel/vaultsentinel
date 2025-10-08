# VaultSentinel

An agentic AI system for continuous secrets shielding that demonstrates an Observe → Think → Act loop across repositories with actionable alerts. Now featuring a comprehensive repository scanner with hybrid detection (regex + AI) and a modern React dashboard.

## 🏗️ Architecture

VaultSentinel is built as a modular monorepo with clear separation of concerns:

### Frontend Technology Stack
- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Full type safety and enhanced developer experience
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Vite**: Fast build tool and development server
- **React Router**: Client-side routing for single-page application
- **Axios**: HTTP client for API communication
- **Lucide React**: Beautiful, customizable icons
- **date-fns**: Modern date utility library

```
vaultsentinel/
├─ packages/
│  ├─ core/            # Agent loop, config, domain models
│  ├─ detectors/       # Pluggable secret detection engines
│  ├─ connectors/      # Data source integrations
│  ├─ remediation/     # Action handlers for findings
│  ├─ api/             # FastAPI service (REST + health/metrics)
│  ├─ ui/              # React dashboard with scanner interface
│  ├─ cli/             # Local runner (optional)
│  └─ sdk/             # External client SDK (future)
├─ scanner/            # Repository scanning engine
├─ detection/          # Hybrid detection (regex + MCP AI)
├─ api/                # FastAPI routes and models
├─ docs/               # Comprehensive documentation
├─ infra/
│  ├─ docker/          # Dockerfiles
│  ├─ helm/            # Helm chart (future)
│  └─ terraform/       # Infrastructure as code
├─ ops/
│  ├─ configs/         # Example configurations
│  └─ runbooks/        # Operational procedures
└─ tests/              # Unit + E2E tests
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

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Vault-Sentinel/vaultsentinel.git
cd vaultsentinel

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp ops/configs/config.example.yaml ops/configs/config.yaml

# Edit configuration
nano ops/configs/config.yaml
```

Required configuration:
- `GITHUB_REPO`: Repository to monitor (e.g., "org/repo")
- `GITHUB_TOKEN`: GitHub personal access token
- `SLACK_WEBHOOK_URL`: Slack incoming webhook URL

### 3. Run the Service

```bash
# Start the agent
python main.py

# Or run API server only
python main.py --api-only

# Run a single scan
python main.py --run-once

# Test connections
python main.py --test-connections
```

### 4. Build and Access the Dashboard

#### Option A: Development Mode (Recommended for development)
```bash
# Start the backend
python main.py --api-only

# In another terminal, start the frontend development server
cd packages/ui && npm install && npm run dev
```

#### Option B: Production Build
```bash
# Build the TypeScript React frontend
cd packages/ui && npm run build

# Start the full application (serves both API and frontend)
python main.py --api-only
```

The dashboard will be available at:
- **Development**: http://localhost:3000 (with hot reload)
- **Production**: http://localhost:8000 (served by FastAPI)

### 5. Using the Repository Scanner

#### **Quick Start - Scan a Repository:**
1. Open http://localhost:3000
2. Enter a GitHub repository URL (e.g., `https://github.com/owner/repo`)
3. Click "Start Scan"
4. Monitor progress in real-time
5. View detailed HTML report when complete

#### **API Usage:**
```bash
# Create a scan
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/owner/repo",
    "branch": "main",
    "mode": "full"
  }'

# Check scan status
curl http://localhost:8000/api/scans/{scan_id}/status

# Get HTML report
curl http://localhost:8000/scans/{scan_id}/report
```

#### **MCP Integration:**
```bash
# Test MCP health
curl http://localhost:8000/api/mcp/health

# Classify text
curl -X POST http://localhost:8000/api/mcp/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "AKIA1234567890ABCDEF"}'
```

## 🔍 Repository Scanner

### **New: Comprehensive Repository Scanner**

VaultSentinel now includes a powerful repository scanner that can analyze any public GitHub repository for secrets and security risks:

#### **Features:**
- **🔍 Hybrid Detection**: Combines regex patterns with AI-powered classification
- **📊 Risk Scoring**: Automated risk assessment with severity levels
- **📋 Detailed Reports**: Human-readable HTML reports with remediation guidance
- **🎯 Smart Filtering**: Context-aware detection with false positive reduction
- **⚡ Fast Processing**: Optimized for large repositories with configurable limits

#### **Detection Capabilities:**

- **Regex Detector**: Pattern-based detection for common secrets
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

- **AI Classification**: MCP-powered LLM analysis
  - Context-aware verification
  - Severity assessment
  - Remediation guidance
  - Confidence scoring

- **Entropy Detector**: Statistical analysis for high-entropy strings
  - Configurable entropy threshold
  - False positive filtering
  - Context-aware scoring

### Context Filtering

- **Allowlist Paths**: Reduces confidence for test files (`/tests/`, `/examples/`)
- **Denylist Patterns**: Filters out dummy/example content
- **File Type Analysis**: Higher confidence for config files
- **Content Analysis**: Detects test fixtures and placeholders

## 🚨 Alerting & Remediation

### Slack Notifications
- Rich formatted messages with masked secret previews
- Actionable buttons for acknowledgment
- Batch notifications for multiple findings
- Configurable retry logic with exponential backoff

### AWS Remediation (Stubbed)
- Access key rotation/revocation
- Secret key handling
- Safe defaults (disabled unless credentials provided)

## 📊 API & Dashboard

### REST API Endpoints

#### **Core API:**
- `GET /healthz` - Health check with agent status
- `GET /findings` - List findings with filters
- `PATCH /findings/{id}` - Update finding status
- `GET /metrics` - Comprehensive metrics and statistics
- `GET /docs` - Interactive API documentation

#### **Repository Scanner API:**
- `POST /api/scans` - Create a new repository scan
- `GET /api/scans/{id}/status` - Get scan progress and status
- `GET /scans/{id}/report` - Get HTML scan report
- `GET /api/findings` - List security findings with filters
- `GET /api/findings/{id}` - Get detailed finding information
- `POST /api/remediate` - Generate remediation patches
- `GET /api/dashboard/stats` - Get dashboard statistics

#### **MCP Integration API:**
- `GET /api/mcp/health` - MCP server health check
- `POST /api/mcp/chat` - Forward chat requests to MCP
- `POST /api/mcp/classify` - Classify text using MCP AI

### TypeScript React Dashboard
- **Modern UI**: Built with React 18, TypeScript, and Tailwind CSS
- **Repository Scanner**: Interactive GitHub repository scanning interface
- **Real-time Updates**: Live findings display with auto-refresh
- **Advanced Filtering**: Status, type, repository, and search filters
- **Interactive Management**: Update finding status and add notes
- **Responsive Design**: Mobile-first design with desktop optimization
- **Metrics Visualization**: Comprehensive statistics and charts
- **MCP Integration**: Quick text classification and AI-powered analysis
- **Settings Management**: Agent configuration and plugin status

#### **Dashboard Pages:**
- **Home** (`/`) - Repository scanning interface with progress tracking
- **Dashboards** (`/dashboards`) - Security metrics, KPIs, and statistics
- **Findings** (`/findings`) - Searchable and filterable findings table
- **MCP Panel** (`/mcp`) - Quick text classification using AI
- **Settings** (`/settings`) - Application configuration and health status

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=packages tests/

# Run specific test
pytest tests/test_regex_detector.py

# Run E2E tests
pytest tests/e2e_test.py
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -f infra/docker/Dockerfile -t vaultsentinel .
docker run -p 8000:8000 vaultsentinel
```

## 🔧 Configuration Reference

### **Repository Scanner Configuration**

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_BASE_URL` | MCP server URL | `http://localhost:9000` |
| `MCP_AUTH_TYPE` | Authentication type | `api_key` |
| `MCP_API_KEY` | MCP API key | Required |
| `MCP_TIMEOUT_MS` | Request timeout | `20000` |
| `MCP_RETRIES` | Number of retries | `2` |
| `FRONTEND_ORIGIN` | Frontend CORS origin | `http://localhost:3000` |
| `BACKEND_ORIGIN` | Backend CORS origin | `http://localhost:8000` |
| `DEMO_MODE` | Enable demo mode | `false` |

### **Legacy Agent Configuration**

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_REPO` | Repository to monitor | Required |
| `GITHUB_TOKEN` | GitHub API token | Required |
| `SLACK_WEBHOOK_URL` | Slack webhook URL | Required |
| `POLL_INTERVAL_SECONDS` | Scan frequency | 120 |
| `SCAN_DEPTH_COMMITS` | Commits to scan | 10 |
| `DETECTION_ENTROPY_THRESHOLD` | Entropy threshold | 4.5 |
| `ALLOWLIST_PATHS` | Test file paths | `["/tests/", "/examples/"]` |
| `DENYLIST_PATTERNS` | False positive patterns | `["dummy", "example"]` |
| `REMEDIATION_ENABLED` | Enable AWS remediation | false |
| `AWS_ACCESS_KEY_ID` | AWS access key | Optional |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Optional |

## 🔒 Security Considerations

- **Never logs full secrets**: Only masked previews and SHA256 fingerprints
- **Secure storage**: Uses SQLite with proper indexing
- **Environment isolation**: All credentials via environment variables
- **Safe defaults**: Remediation disabled unless explicitly enabled
- **Idempotent operations**: De-duplication by fingerprint + file path
- **Structured logging**: JSON logs for observability

## 🚀 Scaling Beyond POC

The architecture is designed to scale with additional components:

### Additional Connectors
- GitLab integration
- Jenkins build logs
- CI/CD pipeline scanning
- Cloud storage scanning

### Advanced Detectors
- ML-based classification
- LLM-powered analysis
- Custom pattern matching
- Behavioral analysis

### Enhanced Remediation
- Multi-cloud support (Azure, GCP)
- Automated key rotation
- Integration with secret managers
- Custom webhook actions

### Enterprise Features
- Multi-tenant support
- Role-based access control
- Audit logging
- Compliance reporting

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
pip install -e ".[dev]"

# Run linting
black packages/ tests/ main.py
isort packages/ tests/ main.py
flake8 packages/ tests/ main.py
mypy packages/ main.py

# Run tests
pytest tests/
```

## 🤖 LLM Integration via MCP (Model Context Protocol)

VaultSentinel now uses MCP (Model Context Protocol) as the single gateway for all LLM requests, providing secure, robust, and scalable LLM integration.

### **MCP Architecture Benefits:**
- **🔒 Security**: Centralized authentication and secret management
- **🔄 Reliability**: Built-in retries, circuit breaker, and rate limiting
- **📊 Telemetry**: Comprehensive logging and monitoring
- **🧪 Testing**: Demo mode with deterministic responses
- **🔧 Flexibility**: Support for multiple authentication methods

### **Quick Start - Demo Mode:**
```bash
# Enable demo mode for testing
export DEMO_MODE=true
python main.py --api-only

# Test MCP integration
curl -X POST http://localhost:8000/mcp/test \
  -H "Content-Type: application/json" \
  -d '{"text": "AKIAIOSFODNN7EXAMPLE", "context": {"file_path": "config/aws.py"}}'
```

### **Quick Start - Live MCP Server:**
```bash
# Start local MCP server
cd mcp-server
python server.py

# In another terminal, start VaultSentinel
cd ..
export MCP_BASE_URL=http://localhost:9000
export MCP_AUTH_TYPE=api_key
export MCP_API_KEY=demo-mcp-key-12345
export DEMO_MODE=false
python main.py --api-only

# Test live MCP integration
python test_live_mcp.py
```

### **Production Configuration:**
Edit your `.env` file with MCP settings:

```bash
# MCP (Model Context Protocol) Configuration
MCP_BASE_URL=https://mcp.your-company.com  # Your MCP server URL
MCP_AUTH_TYPE=api_key  # api_key, oauth2, mtls, none
MCP_API_KEY=your_mcp_api_key_here  # API key for MCP server
MCP_OAUTH_TOKEN_URL=https://auth.your-company.com/token  # OAuth2 token endpoint
MCP_CLIENT_ID=your_oauth_client_id  # OAuth2 client ID
MCP_CLIENT_SECRET=your_oauth_client_secret  # OAuth2 client secret
MCP_TIMEOUT_SECONDS=30  # Request timeout in seconds
DEMO_MODE=false  # Set to true for demo mode with mock responses

# Legacy LLM Configuration (will be replaced by MCP)
LLM_CLASSIFIER_ENABLED=true
LLM_PROVIDER=openai  # openai, gemini, both
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
OPENAI_MODEL=gpt-3.5-turbo  # gpt-3.5-turbo, gpt-4, gpt-4-turbo
GEMINI_MODEL=gemini-1.5-flash  # gemini-1.5-flash, gemini-1.5-pro
LLM_CONFIDENCE_THRESHOLD=0.7
```

### **MCP Authentication Methods:**

#### **1. API Key Authentication:**
```bash
MCP_AUTH_TYPE=api_key
MCP_API_KEY=your_mcp_api_key_here
```

#### **2. OAuth2 Client Credentials:**
```bash
MCP_AUTH_TYPE=oauth2
MCP_OAUTH_TOKEN_URL=https://auth.your-company.com/token
MCP_CLIENT_ID=your_oauth_client_id
MCP_CLIENT_SECRET=your_oauth_client_secret
```

#### **3. No Authentication (Development):**
```bash
MCP_AUTH_TYPE=none
```

### **Security Checklist:**

#### **✅ Production Security:**
- [ ] Store MCP API keys in secret management system (AWS Secrets Manager, HashiCorp Vault, etc.)
- [ ] Use HTTPS for all MCP communications
- [ ] Enable TLS certificate verification
- [ ] Implement IP allowlisting if supported by MCP server
- [ ] Set up RBAC (Role-Based Access Control) on MCP server
- [ ] Enable audit logging on MCP server
- [ ] Rotate API keys regularly (recommended: every 90 days)
- [ ] Use least privilege principle for MCP access

#### **✅ Secret Management:**
- [ ] Never commit API keys to version control
- [ ] Use environment variables or secret injection
- [ ] Implement key rotation procedures
- [ ] Monitor for secret leakage in logs
- [ ] Use different keys for different environments

#### **✅ Monitoring & Alerting:**
- [ ] Set up alerts for MCP authentication failures
- [ ] Monitor circuit breaker activations
- [ ] Track MCP request latency and error rates
- [ ] Set up alerts for secret detection in logs
- [ ] Monitor MCP server health and availability

### **Testing MCP Integration:**

#### **Unit Tests:**
```bash
# Run MCP client unit tests
pytest tests/test_mcp_client.py -v

# Run MCP integration tests
pytest tests/integration/test_mcp_integration.py -v
```

#### **Demo Mode Testing:**
```bash
# Test with demo mode
DEMO_MODE=true python -c "
import asyncio
from api.clients import get_mcp_client

async def test():
    client = get_mcp_client()
    result = await client.chat({'messages': [{'role': 'user', 'content': 'test'}]})
    print(f'Status: {result[\"status\"]}')
    print(f'Request ID: {result[\"request_id\"]}')

asyncio.run(test())
"
```

#### **API Testing:**
```bash
# Test MCP API endpoint
curl -X POST http://localhost:8000/mcp/test \
  -H "Content-Type: application/json" \
  -d '{
    "text": "AKIAIOSFODNN7EXAMPLE",
    "context": {
      "file_path": "config/aws.py",
      "secret_kind": "aws_access_key"
    }
  }'
```

### **Troubleshooting:**

#### **Common Issues:**

1. **Authentication Failures:**
   ```bash
   # Check MCP server connectivity
   curl -H "Authorization: Bearer $MCP_API_KEY" $MCP_BASE_URL/health
   ```

2. **Circuit Breaker Open:**
   ```bash
   # Check client stats
   curl http://localhost:8000/mcp/test -d '{"text": "test"}' | jq '.client_stats'
   ```

3. **Rate Limiting:**
   ```bash
   # Check for rate limit headers in logs
   grep "Rate limited" logs/vaultsentinel.log
   ```

#### **Log Analysis:**
```bash
# Check MCP request IDs in logs
grep "mcp_request_id" logs/vaultsentinel.log

# Check for secret leakage
python scripts/redact_logs.py logs/vaultsentinel.log --check

# Redact sensitive information
python scripts/redact_logs.py logs/vaultsentinel.log -o logs/redacted.log
```

### **Legacy LLM Configuration (Deprecated):**

> **⚠️ Note**: Direct LLM provider configuration is deprecated in favor of MCP integration. The following configuration will be removed in future versions.

```bash
# Interactive configuration helper (legacy)
python scripts/configure_llm.py

# Test legacy LLM classifiers
python test_llm_classifiers.py
```

### **Migration Guide:**

#### **From Direct LLM to MCP:**
1. **Update Environment Variables:**
   ```bash
   # Old configuration
   OPENAI_API_KEY=sk-your-key
   GEMINI_API_KEY=your-key
   
   # New MCP configuration
   MCP_BASE_URL=https://mcp.your-company.com
   MCP_AUTH_TYPE=api_key
   MCP_API_KEY=your_mcp_key
   ```

2. **Update Code:**
   ```python
   # Old direct LLM usage
   from openai import OpenAI
   client = OpenAI(api_key="sk-...")
   
   # New MCP usage
   from api.clients import get_mcp_client
   client = get_mcp_client()
   result = await client.chat(conversation)
   ```

3. **Test Migration:**
   ```bash
   # Run migration tests
   pytest tests/test_mcp_client.py tests/integration/test_mcp_integration.py
   ```

## 📚 Documentation

- **Repository Scanner**: [Scanner Runbook](docs/runbook_repository_scanner.md)
- **MCP Integration**: [MCP Integration Guide](docs/runbook_mcp_integration.md)
- **API Reference**: Available at `/docs` when running the server
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
- Leverages [Boto3](https://boto3.amazonaws.com/) for AWS integration
- Inspired by modern security practices and agentic AI patterns