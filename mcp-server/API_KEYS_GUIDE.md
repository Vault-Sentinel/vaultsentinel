# 🔑 MCP Server API Keys Configuration Guide

## Overview

The MCP server can use your real OpenAI and Gemini API keys to provide actual LLM-powered secret classification instead of simulated responses.

## 🔧 Configuration Options

### **1. Environment Variables**

Set these environment variables to configure your API keys:

```bash
# MCP Server Authentication (for accessing the MCP server)
export MCP_API_KEY="your-mcp-server-key-here"

# LLM Provider API Keys
export OPENAI_API_KEY="sk-your-openai-api-key-here"
export GEMINI_API_KEY="your-gemini-api-key-here"

# LLM Configuration
export USE_REAL_LLM="true"  # Enable real LLM calls
export DEFAULT_LLM_PROVIDER="openai"  # or "gemini"
```

### **2. Using .env File**

Create a `.env` file in the `mcp-server` directory:

```bash
# MCP Server Configuration
MCP_API_KEY=your-mcp-server-api-key-here

# LLM Provider API Keys
OPENAI_API_KEY=sk-your-openai-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# LLM Configuration
DEFAULT_LLM_PROVIDER=openai
USE_REAL_LLM=true
```

## 🚀 Quick Start

### **Option 1: Using the Enhanced Server Script**

```bash
# Set your API keys
export OPENAI_API_KEY="sk-proj-your-openai-key-here"
export GEMINI_API_KEY="AIzaSy-your-gemini-key-here"
export MCP_API_KEY="demo-mcp-key-12345"

# Start the enhanced server
cd mcp-server
./start_with_real_llm.sh
```

### **Option 2: Manual Configuration**

```bash
# Set environment variables
export OPENAI_API_KEY="sk-proj-your-openai-key-here"
export GEMINI_API_KEY="AIzaSy-your-gemini-key-here"
export MCP_API_KEY="demo-mcp-key-12345"
export USE_REAL_LLM="true"
export DEFAULT_LLM_PROVIDER="openai"

# Install dependencies
pip install openai google-generativeai

# Start the enhanced server
python enhanced_server.py
```

## 🔄 Switching Between Providers

### **Use OpenAI Only:**
```bash
export OPENAI_API_KEY="sk-proj-your-key"
export GEMINI_API_KEY=""  # Leave empty
export DEFAULT_LLM_PROVIDER="openai"
```

### **Use Gemini Only:**
```bash
export OPENAI_API_KEY=""  # Leave empty
export GEMINI_API_KEY="AIzaSy-your-key"
export DEFAULT_LLM_PROVIDER="gemini"
```

### **Use Both (Provider Selection):**
```bash
export OPENAI_API_KEY="sk-proj-your-key"
export GEMINI_API_KEY="AIzaSy-your-key"
export DEFAULT_LLM_PROVIDER="openai"  # Default provider
```

## 🧪 Testing Your Configuration

### **1. Check Server Health:**
```bash
curl -H "Authorization: Bearer demo-mcp-key-12345" \
  http://localhost:9000/health
```

### **2. Test OpenAI Classification:**
```bash
curl -X POST http://localhost:9000/v1/chat \
  -H "Authorization: Bearer demo-mcp-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation": {
      "messages": [
        {"role": "user", "content": "Analyze this secret: AKIAIOSFODNN7EXAMPLE"}
      ],
      "model": "gpt-3.5-turbo",
      "provider": "openai"
    }
  }'
```

### **3. Test Gemini Classification:**
```bash
curl -X POST http://localhost:9000/v1/chat \
  -H "Authorization: Bearer demo-mcp-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation": {
      "messages": [
        {"role": "user", "content": "Analyze this secret: AKIAIOSFODNN7EXAMPLE"}
      ],
      "model": "gemini-1.5-flash",
      "provider": "gemini"
    }
  }'
```

## 🔒 Security Best Practices

### **1. API Key Security:**
- Never commit API keys to version control
- Use environment variables or secure secret managers
- Rotate API keys regularly
- Use least-privilege access

### **2. MCP Server Security:**
- Use a strong MCP_API_KEY
- Consider IP allowlisting for production
- Enable HTTPS in production
- Monitor API usage and costs

### **3. Cost Management:**
- Monitor OpenAI/Gemini API usage
- Set usage limits in your provider accounts
- Use appropriate models for your needs
- Consider caching responses for repeated requests

## 📊 Monitoring and Debugging

### **Check Server Status:**
```bash
curl http://localhost:9000/health
```

### **View Server Statistics:**
```bash
curl -H "Authorization: Bearer demo-mcp-key-12345" \
  http://localhost:9000/v1/stats
```

### **View Recent Requests:**
```bash
curl -H "Authorization: Bearer demo-mcp-key-12345" \
  http://localhost:9000/v1/requests
```

## 🐛 Troubleshooting

### **Common Issues:**

1. **"OpenAI client not available"**
   - Check OPENAI_API_KEY is set correctly
   - Verify the API key is valid
   - Install openai package: `pip install openai`

2. **"Gemini client not available"**
   - Check GEMINI_API_KEY is set correctly
   - Verify the API key is valid
   - Install google-generativeai package: `pip install google-generativeai`

3. **"Invalid API key"**
   - Check MCP_API_KEY matches between client and server
   - Verify the Authorization header format

4. **Rate limiting errors**
   - Check your OpenAI/Gemini API quotas
   - Consider implementing retry logic
   - Monitor usage in provider dashboards

### **Debug Mode:**
```bash
export MCP_DEBUG="true"
python enhanced_server.py
```

## 🔄 Integration with VaultSentinel

Once your MCP server is running with real API keys, configure VaultSentinel to use it:

```bash
# In VaultSentinel
export MCP_BASE_URL=http://localhost:9000
export MCP_AUTH_TYPE=api_key
export MCP_API_KEY=demo-mcp-key-12345
export DEMO_MODE=false

# Start VaultSentinel
python main.py --api-only
```

## 📈 Performance Optimization

### **Model Selection:**
- **OpenAI**: Use `gpt-3.5-turbo` for cost efficiency, `gpt-4` for accuracy
- **Gemini**: Use `gemini-1.5-flash` for speed, `gemini-1.5-pro` for accuracy

### **Caching:**
- Consider implementing response caching for repeated requests
- Use Redis or in-memory cache for frequently classified patterns

### **Batch Processing:**
- Process multiple secrets in batches to reduce API calls
- Implement request queuing for high-volume scenarios
