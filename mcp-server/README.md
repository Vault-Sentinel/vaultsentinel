# VaultSentinel MCP Server

A local MCP (Model Context Protocol) server for testing VaultSentinel integration.

## 🚀 Quick Start

### Option 1: Direct Python (Recommended for Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python server.py

# Or with custom settings
python server.py --host 0.0.0.0 --port 9000 --debug
```

### Option 2: Docker (Recommended for Production)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run individual container
docker build -t vaultsentinel-mcp .
docker run -p 9000:9000 -e MCP_API_KEY=your-key-here vaultsentinel-mcp
```

### Option 3: Using the Start Script

```bash
# Make executable and run
chmod +x start_server.sh
./start_server.sh

# With custom environment
MCP_HOST=0.0.0.0 MCP_PORT=9000 MCP_API_KEY=your-key ./start_server.sh
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_API_KEY` | `demo-mcp-key-12345` | API key for authentication |
| `MCP_HOST` | `0.0.0.0` | Host to bind to |
| `MCP_PORT` | `9000` | Port to bind to |
| `MCP_DEBUG` | `false` | Enable debug mode |

### API Keys

The server accepts these API keys by default:
- `demo-mcp-key-12345` (default)
- `test-token-12345`
- Any key set in `MCP_API_KEY` environment variable

## 📚 API Endpoints

### Health Check
```bash
curl http://localhost:9000/health
```

### Chat Completion
```bash
curl -X POST http://localhost:9000/v1/chat \
  -H "Authorization: Bearer demo-mcp-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation": {
      "messages": [
        {"role": "system", "content": "You are a security expert."},
        {"role": "user", "content": "Analyze this secret: AKIAIOSFODNN7EXAMPLE"}
      ],
      "model": "gpt-3.5-turbo"
    }
  }'
```

### Text Completion
```bash
curl -X POST http://localhost:9000/v1/complete \
  -H "Authorization: Bearer demo-mcp-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Classify this secret: sk_test_1234567890abcdef",
    "params": {"temperature": 0.1}
  }'
```

### Server Statistics
```bash
curl -H "Authorization: Bearer demo-mcp-key-12345" \
  http://localhost:9000/v1/stats
```

## 🧪 Testing

### Test the MCP Server
```bash
# Run the test client
python test_client.py
```

### Test VaultSentinel Integration
```bash
# Set environment variables
export MCP_BASE_URL=http://localhost:9000
export MCP_AUTH_TYPE=api_key
export MCP_API_KEY=demo-mcp-key-12345
export DEMO_MODE=false

# Run VaultSentinel test
cd ..
python test_mcp_integration.py
```

### Test with VaultSentinel API
```bash
# Start VaultSentinel API
cd ..
python main.py --api-only

# Test MCP endpoint
curl -X POST http://localhost:8000/mcp/test \
  -H "Content-Type: application/json" \
  -d '{
    "text": "AKIAIOSFODNN7EXAMPLE",
    "context": {"file_path": "config/aws.py", "secret_kind": "aws_access_key"}
  }'
```

## 🔍 Monitoring

### View API Documentation
- **Swagger UI**: http://localhost:9000/docs
- **ReDoc**: http://localhost:9000/redoc

### Server Statistics
```bash
curl -H "Authorization: Bearer demo-mcp-key-12345" \
  http://localhost:9000/v1/stats
```

### Recent Requests
```bash
curl -H "Authorization: Bearer demo-mcp-key-12345" \
  http://localhost:9000/v1/requests
```

## 🐳 Docker Deployment

### Build and Run
```bash
# Build the image
docker build -t vaultsentinel-mcp .

# Run the container
docker run -d \
  --name vaultsentinel-mcp \
  -p 9000:9000 \
  -e MCP_API_KEY=your-production-key \
  vaultsentinel-mcp
```

### Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment
```bash
# Use production API key
export MCP_API_KEY=your-production-key-here

# Run with Docker Compose
docker-compose -f docker-compose.yml up -d
```

## 🔧 Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run in debug mode
python server.py --debug

# Run tests
python test_client.py
```

### Adding New Endpoints
1. Add the endpoint to `server.py`
2. Update the test client in `test_client.py`
3. Update this README

### Custom Authentication
Modify the `verify_auth` function in `server.py` to implement your authentication logic.

## 🚨 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find and kill process using port 9000
   lsof -ti:9000 | xargs kill -9
   ```

2. **Authentication errors**
   ```bash
   # Check API key
   curl -H "Authorization: Bearer demo-mcp-key-12345" \
     http://localhost:9000/health
   ```

3. **Connection refused**
   ```bash
   # Check if server is running
   curl http://localhost:9000/health
   ```

### Debug Mode
```bash
# Enable debug logging
python server.py --debug

# Or with environment variable
MCP_DEBUG=true python server.py
```

### Logs
```bash
# View server logs
tail -f logs/mcp-server.log

# Docker logs
docker logs vaultsentinel-mcp
```

## 📊 Performance

### Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 http://localhost:9000/health

# Test chat endpoint
ab -n 100 -c 5 -p chat_request.json -T application/json \
  -H "Authorization: Bearer demo-mcp-key-12345" \
  http://localhost:9000/v1/chat
```

### Monitoring
- **Health Check**: http://localhost:9000/health
- **Stats**: http://localhost:9000/v1/stats
- **API Docs**: http://localhost:9000/docs

## 🔒 Security

### Production Security Checklist
- [ ] Change default API key
- [ ] Use HTTPS in production
- [ ] Implement proper authentication
- [ ] Set up rate limiting
- [ ] Enable logging and monitoring
- [ ] Use environment variables for secrets

### API Key Management
```bash
# Generate secure API key
openssl rand -hex 32

# Set in environment
export MCP_API_KEY=$(openssl rand -hex 32)
```

## 📝 License

This MCP server is part of the VaultSentinel project and follows the same license terms.
