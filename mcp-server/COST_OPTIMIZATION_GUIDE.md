# 💰 MCP Server Cost Optimization Guide

## 🎯 Cheapest Model Configuration

### **OpenAI Models (Cost per 1K tokens)**
```
gpt-3.5-turbo:        $0.0015 input / $0.002 output  ← CHEAPEST
gpt-3.5-turbo-16k:    $0.003  input / $0.004 output
gpt-4:                $0.03   input / $0.06  output  ← MOST EXPENSIVE
gpt-4-turbo:          $0.01   input / $0.03  output
```

### **Gemini Models (Cost per 1K tokens)**
```
gemini-1.5-flash:     $0.00075 input / $0.003 output  ← CHEAPEST
gemini-1.0-pro:       $0.0005  input / $0.0015 output  ← LEGACY, CHEAPER
gemini-1.5-pro:       $0.00125 input / $0.005 output  ← MORE EXPENSIVE
```

## 🔧 Cost-Optimized Configuration

### **Ultra-Cheap Setup (Recommended)**
```bash
# Use the cheapest models
export OPENAI_MODEL="gpt-3.5-turbo"
export GEMINI_MODEL="gemini-1.5-flash"
export DEFAULT_LLM_PROVIDER="gemini"  # Gemini is cheaper than OpenAI

# Limit response length
export MAX_TOKENS="50"  # Very short responses
export TEMPERATURE="0.1"  # Consistent, shorter responses

# Enable caching
export ENABLE_CACHING="true"
```

### **Balanced Setup (Good Quality + Low Cost)**
```bash
# Use cheap but good models
export OPENAI_MODEL="gpt-3.5-turbo"
export GEMINI_MODEL="gemini-1.5-flash"
export DEFAULT_LLM_PROVIDER="gemini"

# Moderate response length
export MAX_TOKENS="100"
export TEMPERATURE="0.1"

# Enable caching
export ENABLE_CACHING="true"
```

### **Quality Setup (Higher Quality + Moderate Cost)**
```bash
# Use better models
export OPENAI_MODEL="gpt-3.5-turbo-16k"
export GEMINI_MODEL="gemini-1.5-pro"
export DEFAULT_LLM_PROVIDER="openai"

# Longer responses
export MAX_TOKENS="200"
export TEMPERATURE="0.2"

# Enable caching
export ENABLE_CACHING="true"
```

## 📊 Cost Comparison Examples

### **Secret Classification Request:**
```
Input: "Analyze this secret: AWS_ACCESS_KEY_ID_EXAMPLE"
Expected Output: ~50 tokens
```

### **Cost per 1000 requests:**

| Model | Input Cost | Output Cost | Total Cost |
|-------|------------|-------------|------------|
| **gpt-3.5-turbo** | $0.15 | $0.10 | **$0.25** |
| **gemini-1.5-flash** | $0.075 | $0.15 | **$0.225** |
| **gemini-1.0-pro** | $0.05 | $0.075 | **$0.125** |
| gpt-4 | $1.50 | $3.00 | $4.50 |
| gemini-1.5-pro | $0.125 | $0.25 | $0.375 |

**Winner: gemini-1.0-pro at $0.125 per 1000 requests!**

## 🚀 Quick Start - Ultra Cheap Setup

### **1. Set Environment Variables:**
```bash
# API Keys
export OPENAI_API_KEY="sk-your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
export MCP_API_KEY="demo-mcp-key-12345"

# Cost Optimization
export OPENAI_MODEL="gpt-3.5-turbo"
export GEMINI_MODEL="gemini-1.0-pro"  # Cheapest option
export DEFAULT_LLM_PROVIDER="gemini"
export MAX_TOKENS="50"
export TEMPERATURE="0.1"
export ENABLE_CACHING="true"
export USE_REAL_LLM="true"
```

### **2. Start the Server:**
```bash
cd mcp-server
python enhanced_server.py
```

### **3. Test Cost Optimization:**
```bash
# Test with caching (should be very fast and cheap)
curl -X POST http://localhost:9000/v1/chat \
  -H "Authorization: Bearer demo-mcp-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation": {
      "messages": [{"role": "user", "content": "Analyze this secret: AWS_ACCESS_KEY_ID_EXAMPLE"}],
      "provider": "gemini"
    }
  }'
```

## 💡 Advanced Cost Optimization Tips

### **1. Use Gemini 1.0 Pro (Legacy)**
```bash
export GEMINI_MODEL="gemini-1.0-pro"  # Cheapest option
```
- **Cost**: $0.0005 input / $0.0015 output
- **Quality**: Good for secret classification
- **Speed**: Fast

### **2. Enable Aggressive Caching**
```bash
export ENABLE_CACHING="true"
```
- Caches responses for 1 hour
- Avoids duplicate API calls
- Can reduce costs by 80%+ for repeated requests

### **3. Limit Response Length**
```bash
export MAX_TOKENS="50"  # Very short responses
```
- Forces concise responses
- Reduces output token costs
- Still effective for secret classification

### **4. Use Lower Temperature**
```bash
export TEMPERATURE="0.1"
```
- More consistent responses
- Shorter, more focused outputs
- Better for classification tasks

### **5. Provider Selection Strategy**
```bash
# Use Gemini for most requests (cheaper)
export DEFAULT_LLM_PROVIDER="gemini"

# Fallback to OpenAI only when needed
# (can be configured per request)
```

## 📈 Monitoring Costs

### **Check Server Statistics:**
```bash
curl -H "Authorization: Bearer demo-mcp-key-12345" \
  http://localhost:9000/v1/stats
```

### **Monitor Cache Hit Rate:**
Look for log messages like:
```
Using cached response for key: a1b2c3d4...
Cached response for key: e5f6g7h8...
```

### **Track API Usage:**
- Monitor OpenAI dashboard for usage
- Check Gemini console for API calls
- Set up billing alerts

## 🔄 Dynamic Model Selection

### **Per-Request Model Selection:**
```bash
# Use cheapest model for simple tasks
curl -X POST http://localhost:9000/v1/chat \
  -H "Authorization: Bearer demo-mcp-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation": {
      "messages": [{"role": "user", "content": "Simple secret check"}],
      "provider": "gemini",
      "model": "gemini-1.0-pro"
    }
  }'

# Use better model for complex tasks
curl -X POST http://localhost:9000/v1/chat \
  -H "Authorization: Bearer demo-mcp-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation": {
      "messages": [{"role": "user", "content": "Complex analysis needed"}],
      "provider": "openai",
      "model": "gpt-3.5-turbo"
    }
  }'
```

## 🎯 Recommended Configurations

### **For Development/Testing:**
```bash
export GEMINI_MODEL="gemini-1.0-pro"
export MAX_TOKENS="30"
export ENABLE_CACHING="true"
```
**Cost**: ~$0.05 per 1000 requests

### **For Production (Low Volume):**
```bash
export GEMINI_MODEL="gemini-1.5-flash"
export MAX_TOKENS="100"
export ENABLE_CACHING="true"
```
**Cost**: ~$0.225 per 1000 requests

### **For Production (High Volume):**
```bash
export GEMINI_MODEL="gemini-1.0-pro"
export MAX_TOKENS="50"
export ENABLE_CACHING="true"
```
**Cost**: ~$0.125 per 1000 requests

## 🚨 Cost Alerts Setup

### **OpenAI Usage Limits:**
1. Go to OpenAI dashboard
2. Set usage limits (e.g., $10/month)
3. Enable email alerts

### **Gemini Usage Limits:**
1. Go to Google Cloud Console
2. Set API quotas
3. Configure billing alerts

### **MCP Server Monitoring:**
```bash
# Check cache hit rate
curl -H "Authorization: Bearer demo-mcp-key-12345" \
  http://localhost:9000/v1/stats | jq '.cache_hit_rate'
```

This configuration will give you the **cheapest possible setup** while maintaining good quality for secret classification tasks!
