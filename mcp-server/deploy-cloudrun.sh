#!/bin/bash
"""Deploy MCP Server to Google Cloud Run."""

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-project-id"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"vaultsentinel-mcp"}
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Deploying VaultSentinel MCP Server to Google Cloud Run"
echo "========================================================"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Image: $IMAGE_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found"
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with gcloud"
    echo "Please run: gcloud auth login"
    exit 1
fi

# Set project
echo "🔧 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push image
echo "🏗️  Building and pushing container image..."
docker build -f Dockerfile.cloudrun -t $IMAGE_NAME .
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 9000 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --concurrency 100 \
    --timeout 300 \
    --set-env-vars "MCP_API_KEY=${MCP_API_KEY:-demo-mcp-key-12345},USE_REAL_LLM=true,DEFAULT_LLM_PROVIDER=gemini,MAX_TOKENS=100,TEMPERATURE=0.1,ENABLE_CACHING=true" \
    --quiet

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")

echo ""
echo "✅ Deployment completed!"
echo "🌐 Service URL: $SERVICE_URL"
echo "🔍 Health check: $SERVICE_URL/health"
echo "📚 API docs: $SERVICE_URL/docs"
echo ""

# Test the deployment
echo "🧪 Testing deployment..."
if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    echo "Check logs with: gcloud run logs read $SERVICE_NAME --region $REGION"
fi

echo ""
echo "🔧 To update environment variables:"
echo "gcloud run services update $SERVICE_NAME --region $REGION --set-env-vars 'KEY=VALUE'"
echo ""
echo "📊 To view logs:"
echo "gcloud run logs read $SERVICE_NAME --region $REGION"
echo ""
echo "🔍 To test the API:"
echo "curl -H 'Authorization: Bearer ${MCP_API_KEY:-demo-mcp-key-12345}' $SERVICE_URL/health"
