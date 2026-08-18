# 🚀 Google Cloud Run Deployment Guide

## Overview

This guide shows how to deploy the VaultSentinel MCP Server to Google Cloud Run for production use.

## ✅ Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Cloud SDK** installed and configured
3. **Docker** installed locally
4. **API Keys** for OpenAI and/or Gemini

## 🚀 Quick Deployment

### **1. Set Environment Variables**

```bash
# Required
export PROJECT_ID="your-google-cloud-project-id"
export MCP_API_KEY="your-secure-mcp-api-key"

# Optional (for cost optimization)
export OPENAI_API_KEY="sk-your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
export DEFAULT_LLM_PROVIDER="gemini"  # or "openai"
```

### **2. Deploy with Script**

```bash
cd mcp-server
./deploy-cloudrun.sh
```

### **3. Manual Deployment**

```bash
# Set project
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and deploy
docker build -f Dockerfile.cloudrun -t gcr.io/$PROJECT_ID/vaultsentinel-mcp .
docker push gcr.io/$PROJECT_ID/vaultsentinel-mcp

gcloud run deploy vaultsentinel-mcp \
    --image gcr.io/$PROJECT_ID/vaultsentinel-mcp \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 9000 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --concurrency 100 \
    --timeout 300 \
    --set-env-vars "MCP_API_KEY=$MCP_API_KEY,USE_REAL_LLM=true,DEFAULT_LLM_PROVIDER=gemini,MAX_TOKENS=100,TEMPERATURE=0.1,ENABLE_CACHING=true"
```

## 🔧 Configuration Options

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_API_KEY` | Required | API key for MCP server authentication |
| `OPENAI_API_KEY` | Optional | OpenAI API key for LLM processing |
| `GEMINI_API_KEY` | Optional | Gemini API key for LLM processing |
| `DEFAULT_LLM_PROVIDER` | `gemini` | Default LLM provider (openai/gemini) |
| `USE_REAL_LLM` | `true` | Enable real LLM calls (vs simulation) |
| `MAX_TOKENS` | `100` | Maximum response tokens (cost optimization) |
| `TEMPERATURE` | `0.1` | LLM temperature (cost optimization) |
| `ENABLE_CACHING` | `true` | Enable response caching (cost optimization) |

### **Cloud Run Settings**

| Setting | Value | Description |
|---------|-------|-------------|
| **Memory** | 1Gi | Sufficient for LLM processing |
| **CPU** | 1 | Single CPU core |
| **Max Instances** | 10 | Scale up to 10 instances |
| **Min Instances** | 0 | Scale to zero when idle |
| **Concurrency** | 100 | Requests per instance |
| **Timeout** | 300s | 5-minute request timeout |
| **Port** | 9000 | MCP server port |

## 💰 Cost Optimization for Cloud Run

### **Ultra-Cheap Configuration**

```bash
# Use cheapest models
export DEFAULT_LLM_PROVIDER="gemini"
export GEMINI_MODEL="gemini-1.0-pro"  # Cheapest
export MAX_TOKENS="50"
export TEMPERATURE="0.1"
export ENABLE_CACHING="true"

# Deploy with cost optimization
gcloud run deploy vaultsentinel-mcp \
    --set-env-vars "DEFAULT_LLM_PROVIDER=gemini,GEMINI_MODEL=gemini-1.0-pro,MAX_TOKENS=50,TEMPERATURE=0.1,ENABLE_CACHING=true"
```

### **Production Configuration**

```bash
# Balanced cost/quality
export DEFAULT_LLM_PROVIDER="gemini"
export GEMINI_MODEL="gemini-1.5-flash"
export MAX_TOKENS="100"
export TEMPERATURE="0.1"
export ENABLE_CACHING="true"
```

## 🔒 Security Configuration

### **1. Secure API Keys**

```bash
# Use Google Secret Manager for production
gcloud secrets create mcp-api-key --data-file=- <<< "your-secure-mcp-key"
gcloud secrets create openai-api-key --data-file=- <<< "sk-your-openai-key"
gcloud secrets create gemini-api-key --data-file=- <<< "your-gemini-key"

# Deploy with secrets
gcloud run deploy vaultsentinel-mcp \
    --set-secrets "MCP_API_KEY=mcp-api-key:latest,OPENAI_API_KEY=openai-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest"
```

### **2. VPC and Network Security**

```bash
# Deploy to VPC (if needed)
gcloud run deploy vaultsentinel-mcp \
    --vpc-connector=your-vpc-connector \
    --vpc-egress=all-traffic
```

### **3. IAM and Authentication**

```bash
# Restrict access (remove --allow-unauthenticated for private access)
gcloud run deploy vaultsentinel-mcp \
    --no-allow-unauthenticated

# Grant access to specific users
gcloud run services add-iam-policy-binding vaultsentinel-mcp \
    --region us-central1 \
    --member="user:your-email@domain.com" \
    --role="roles/run.invoker"
```

## 📊 Monitoring and Logging

### **View Logs**

```bash
# Real-time logs
gcloud run logs tail vaultsentinel-mcp --region us-central1

# Historical logs
gcloud run logs read vaultsentinel-mcp --region us-central1 --limit 100
```

### **Monitor Performance**

```bash
# Check service status
gcloud run services describe vaultsentinel-mcp --region us-central1

# View metrics in Cloud Console
# https://console.cloud.google.com/run/detail/us-central1/vaultsentinel-mcp/metrics
```

## 🧪 Testing Deployment

### **1. Health Check**

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe vaultsentinel-mcp --region us-central1 --format="value(status.url)")

# Test health endpoint
curl "$SERVICE_URL/health"
```

### **2. API Test**

```bash
# Test MCP chat endpoint
curl -X POST "$SERVICE_URL/v1/chat" \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation": {
      "messages": [{"role": "user", "content": "Analyze this secret: AWS_ACCESS_KEY_ID_EXAMPLE"}],
      "provider": "gemini"
    }
  }'
```

### **3. Load Testing**

```bash
# Install hey (load testing tool)
go install github.com/rakyll/hey@latest

# Run load test
hey -n 100 -c 10 -H "Authorization: Bearer $MCP_API_KEY" "$SERVICE_URL/health"
```

## 🔄 CI/CD with Cloud Build

### **1. Create Cloud Build Trigger**

```bash
# Create trigger for automatic deployment
gcloud builds triggers create github \
    --repo-name=your-repo \
    --repo-owner=your-username \
    --branch-pattern="^main$" \
    --build-config=mcp-server/cloudbuild.yaml \
    --substitutions="_MCP_API_KEY=your-mcp-key"
```

### **2. Manual Build**

```bash
# Trigger build manually
gcloud builds submit --config mcp-server/cloudbuild.yaml \
    --substitutions="_MCP_API_KEY=your-mcp-key"
```

## 🚨 Troubleshooting

### **Common Issues**

1. **"Permission denied" errors**
   ```bash
   # Ensure proper IAM roles
   gcloud projects add-iam-policy-binding $PROJECT_ID \
       --member="user:your-email@domain.com" \
       --role="roles/run.admin"
   ```

2. **"Image not found" errors**
   ```bash
   # Ensure Container Registry is enabled
   gcloud services enable containerregistry.googleapis.com
   ```

3. **"Timeout" errors**
   ```bash
   # Increase timeout
   gcloud run services update vaultsentinel-mcp \
       --region us-central1 \
       --timeout 600
   ```

4. **"Memory limit exceeded"**
   ```bash
   # Increase memory
   gcloud run services update vaultsentinel-mcp \
       --region us-central1 \
       --memory 2Gi
   ```

### **Debug Commands**

```bash
# Check service status
gcloud run services describe vaultsentinel-mcp --region us-central1

# View recent logs
gcloud run logs read vaultsentinel-mcp --region us-central1 --limit 50

# Check IAM permissions
gcloud run services get-iam-policy vaultsentinel-mcp --region us-central1
```

## 📈 Scaling and Performance

### **Auto-scaling Configuration**

```bash
# Configure auto-scaling
gcloud run services update vaultsentinel-mcp \
    --region us-central1 \
    --max-instances 50 \
    --min-instances 1 \
    --concurrency 200
```

### **Performance Optimization**

1. **Enable caching** (already configured)
2. **Use cheapest models** (gemini-1.0-pro)
3. **Limit response length** (MAX_TOKENS=50)
4. **Optimize container size** (use slim base image)

## 💡 Best Practices

1. **Use Secret Manager** for API keys in production
2. **Enable monitoring** and alerting
3. **Set up CI/CD** for automatic deployments
4. **Configure proper IAM** roles and permissions
5. **Monitor costs** and usage patterns
6. **Use VPC** for network isolation if needed
7. **Enable audit logging** for compliance

## 🎯 Next Steps

1. **Deploy to Cloud Run** using the provided scripts
2. **Configure monitoring** and alerting
3. **Set up CI/CD** pipeline
4. **Test with VaultSentinel** integration
5. **Monitor costs** and optimize as needed

Your MCP server is now ready for production deployment on Google Cloud Run! 🚀
