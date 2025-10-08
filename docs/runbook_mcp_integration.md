# MCP Integration Runbook

This document provides comprehensive guidance for setting up, configuring, and troubleshooting the MCP (Model Context Protocol) integration in VaultSentinel.

## Overview

The MCP integration provides a secure proxy layer between the VaultSentinel frontend and the MCP server, ensuring that:

- Secrets are never exposed to the browser
- All MCP communication is handled server-side
- Proper authentication and error handling
- CORS protection for frontend integration

## Architecture

```
Frontend (React) → Backend Proxy (FastAPI) → MCP Server (Cloud Run)
```

### Components

1. **Backend Proxy** (`/api/mcp/*`): FastAPI routes that proxy requests to MCP server
2. **MCP Client** (`api/clients/mcp_client.py`): Secure client with retries, circuit breaker, and telemetry
3. **Frontend Service** (`packages/ui/src/services/mcp.ts`): TypeScript service for API calls
4. **MCP Panel** (`packages/ui/src/pages/McpPanel.tsx`): React component for testing and interaction

## Configuration

### Environment Variables

Copy `env.example` to `.env` and configure the following variables:

```bash
# MCP Server Configuration
MCP_BASE_URL=https://vaultsentinel-mcp-923046029861.us-west1.run.app
MCP_API_KEY=mcp-prod-REPLACE_ME
MCP_AUTH_TYPE=api_key
MCP_TIMEOUT_SECONDS=30
DEMO_MODE=false

# MCP Proxy Configuration
MCP_TIMEOUT_MS=20000
MCP_RETRIES=2
MCP_AUTH_HEADER=Authorization

# Web Configuration
FRONTEND_ORIGIN=http://localhost:3000
BACKEND_ORIGIN=http://localhost:8000
NODE_ENV=development
```

### Required Configuration

- **MCP_BASE_URL**: The URL of your MCP server
- **MCP_API_KEY**: Authentication key for the MCP server
- **MCP_AUTH_TYPE**: Authentication method (`api_key`, `oauth2`, `mtls`, `none`)

### Optional Configuration

- **DEMO_MODE**: Set to `true` for development with mock responses
- **MCP_TIMEOUT_SECONDS**: Request timeout (default: 30 seconds)
- **MCP_RETRIES**: Number of retry attempts (default: 2)
- **FRONTEND_ORIGIN**: CORS origin for frontend (default: http://localhost:3000)

## Setup Instructions

### 1. Backend Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp env.example .env
   # Edit .env with your MCP server details
   ```

3. **Start Backend**:
   ```bash
   python main.py --api-only
   ```

### 2. Frontend Setup

1. **Install Dependencies**:
   ```bash
   cd packages/ui
   npm install
   ```

2. **Start Development Server**:
   ```bash
   npm run dev
   ```

3. **Access MCP Panel**:
   Navigate to `http://localhost:3000/mcp`

### 3. Production Deployment

1. **Build Frontend**:
   ```bash
   cd packages/ui
   npm run build
   ```

2. **Start Full Application**:
   ```bash
   python main.py --api-only
   ```

## API Endpoints

### Health Check

```http
GET /api/mcp/health
```

**Response**:
```json
{
  "status": "ok",
  "details": {
    "status": "ok",
    "version": "1.0.0"
  },
  "request_id": "uuid-here"
}
```

### Chat Request

```http
POST /api/mcp/chat
Content-Type: application/json

{
  "messages": [
    {
      "role": "user",
      "content": "Analyze this potential secret: AKIA1234567890"
    }
  ],
  "provider": "gemini"
}
```

**Response**:
```json
{
  "status": "ok",
  "result": [
    {
      "text": "This appears to be an AWS access key...",
      "confidence": 0.95,
      "reasoning": "High confidence secret detection"
    }
  ],
  "request_id": "uuid-here",
  "mcp_meta": {
    "model": "gemini-1.5-flash",
    "usage": {
      "prompt_tokens": 50,
      "completion_tokens": 25,
      "total_tokens": 75
    }
  }
}
```

## Testing

### Unit Tests

```bash
# Run MCP proxy tests
pytest tests/test_mcp_proxy.py -v

# Run MCP integration tests
pytest tests/test_mcp_integration.py -v
```

### Manual Testing

1. **Health Check**:
   ```bash
   curl http://localhost:8000/api/mcp/health
   ```

2. **Chat Test**:
   ```bash
   curl -X POST http://localhost:8000/api/mcp/chat \
     -H "Content-Type: application/json" \
     -d '{
       "messages": [{"role": "user", "content": "test"}],
       "provider": "gemini"
     }'
   ```

### Frontend Testing

1. Navigate to `http://localhost:3000/mcp`
2. Check health status (should show green if MCP server is accessible)
3. Send a test message and verify response

## Troubleshooting

### Common Issues

#### 1. CORS Errors

**Symptoms**: Browser console shows CORS errors
**Solution**: 
- Verify `FRONTEND_ORIGIN` in environment
- Check CORS middleware configuration in `api/app.py`

#### 2. Authentication Failures

**Symptoms**: 401/403 errors from MCP server
**Solution**:
- Verify `MCP_API_KEY` is correct
- Check `MCP_AUTH_TYPE` matches server configuration
- Ensure API key has proper permissions

#### 3. Timeout Errors

**Symptoms**: Requests timeout after 30 seconds
**Solution**:
- Increase `MCP_TIMEOUT_SECONDS` if needed
- Check network connectivity to MCP server
- Verify MCP server is responding

#### 4. Circuit Breaker Open

**Symptoms**: All requests fail with circuit breaker error
**Solution**:
- Check MCP server health
- Wait for circuit breaker timeout (60 seconds)
- Reset by restarting the application

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check Failures

1. **Check MCP Server Status**:
   ```bash
   curl https://vaultsentinel-mcp-923046029861.us-west1.run.app/health
   ```

2. **Verify Authentication**:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://vaultsentinel-mcp-923046029861.us-west1.run.app/health
   ```

3. **Test with Demo Mode**:
   Set `DEMO_MODE=true` in environment to use mock responses

### Network Issues

1. **Check Connectivity**:
   ```bash
   ping vaultsentinel-mcp-923046029861.us-west1.run.app
   ```

2. **Test HTTPS**:
   ```bash
   curl -I https://vaultsentinel-mcp-923046029861.us-west1.run.app/health
   ```

3. **Check DNS Resolution**:
   ```bash
   nslookup vaultsentinel-mcp-923046029861.us-west1.run.app
   ```

## Security Considerations

### Secret Protection

- API keys are never logged or exposed to frontend
- All secrets are redacted in logs
- Authentication headers are stripped from error messages

### CORS Configuration

- Only configured origins are allowed
- Credentials are disabled for security
- Preflight requests are handled properly

### Request Validation

- All requests are validated against schemas
- Path traversal attacks are prevented
- SSRF protection is implemented

## Monitoring

### Logs

Structured JSON logs are generated for all MCP requests:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "route": "/api/mcp/chat",
  "method": "POST",
  "status": 200,
  "latency_ms": 1250,
  "request_id": "uuid-here"
}
```

### Metrics

Key metrics to monitor:

- Request latency (should be < 2 seconds)
- Error rate (should be < 5%)
- Circuit breaker status
- Authentication failures

### Alerts

Set up alerts for:

- High error rates (> 10%)
- Long response times (> 5 seconds)
- Circuit breaker open
- Authentication failures

## Production Notes

### Performance

- Circuit breaker prevents cascade failures
- Exponential backoff reduces server load
- Request timeouts prevent hanging connections

### Scalability

- Stateless design allows horizontal scaling
- Connection pooling for efficiency
- Rate limiting prevents abuse

### Maintenance

- Regular health checks
- Monitor error rates
- Update API keys as needed
- Review logs for issues

## Support

For issues or questions:

1. Check this runbook first
2. Review application logs
3. Test with demo mode
4. Contact the development team

## Changelog

- **v1.0.0**: Initial MCP integration
  - Basic proxy functionality
  - Health check endpoint
  - Chat endpoint
  - Frontend panel
  - Comprehensive testing
  - Documentation
