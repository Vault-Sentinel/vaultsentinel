# VaultSentinel

An agentic AI system for continuous secrets shielding that demonstrates an Observe → Think → Act loop across repositories with actionable alerts.

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
│  ├─ ui/              # Minimal dashboard
│  ├─ cli/             # Local runner (optional)
│  └─ sdk/             # External client SDK (future)
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
./scripts/dev-frontend.sh
# Or manually:
# cd packages/ui && npm install && npm run dev
```

#### Option B: Production Build
```bash
# Build the TypeScript React frontend
./scripts/build-frontend.sh

# Start the full application (serves both API and frontend)
python main.py --api-only
```

The dashboard will be available at:
- **Development**: http://localhost:3000 (with hot reload)
- **Production**: http://localhost:8000 (served by FastAPI)

## 🔍 Detection Capabilities

### Built-in Detectors

- **Regex Detector**: Pattern-based detection for common secrets
  - AWS Access Keys (`AKIA...`)
  - GitHub Tokens (`ghp_...`)
  - Slack Webhooks (`https://hooks.slack.com/...`)
  - JWT Tokens (`eyJ...`)
  - RSA Private Keys (`-----BEGIN PRIVATE KEY-----`)
  - Database URLs (`postgres://...`, `mysql://...`, `mongodb://...`)
  - Bearer Tokens (`Bearer ...`)

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
- `GET /healthz` - Health check with agent status
- `GET /findings` - List findings with filters
- `PATCH /findings/{id}` - Update finding status
- `GET /metrics` - Comprehensive metrics and statistics
- `GET /docs` - Interactive API documentation

### TypeScript React Dashboard
- **Modern UI**: Built with React 18, TypeScript, and Tailwind CSS
- **Real-time Updates**: Live findings display with auto-refresh
- **Advanced Filtering**: Status, type, repository, and search filters
- **Interactive Management**: Update finding status and add notes
- **Responsive Design**: Mobile-first design with desktop optimization
- **Metrics Visualization**: Comprehensive statistics and charts
- **Settings Management**: Agent configuration and plugin status

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

## 🤖 LLM Model Selection

VaultSentinel supports multiple LLM providers and models. You can choose which models to use based on your needs:

### **Available Providers:**
- **OpenAI**: GPT-3.5-turbo, GPT-4, GPT-4-turbo
- **Google Gemini**: Gemini-1.5-flash, Gemini-1.5-pro
- **Both**: Use both providers for comparison

### **Quick Configuration:**
```bash
# Interactive configuration helper
python scripts/configure_llm.py
```

### **Manual Configuration:**
Edit your `.env` file:

```bash
# LLM Configuration
LLM_CLASSIFIER_ENABLED=true
LLM_PROVIDER=openai  # openai, gemini, both
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
OPENAI_MODEL=gpt-3.5-turbo  # gpt-3.5-turbo, gpt-4, gpt-4-turbo
GEMINI_MODEL=gemini-1.5-flash  # gemini-1.5-flash, gemini-1.5-pro
LLM_CONFIDENCE_THRESHOLD=0.7
```

### **Model Recommendations:**

| Use Case | Recommended Model | Speed | Cost | Accuracy |
|----------|------------------|-------|------|----------|
| **Development** | `gpt-3.5-turbo` | Fast | Low | Good |
| **Production** | `gpt-4` | Medium | High | Excellent |
| **High Volume** | `gemini-1.5-flash` | Very Fast | Low | Good |
| **Best Accuracy** | `gemini-1.5-pro` | Medium | Medium | Excellent |

### **Provider Selection:**
- **`openai`**: Use only OpenAI models
- **`gemini`**: Use only Google Gemini models  
- **`both`**: Use both providers (recommended for comparison)

### **Testing LLM Classifiers:**
```bash
# Test all configured LLM classifiers
python test_llm_classifiers.py
```

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