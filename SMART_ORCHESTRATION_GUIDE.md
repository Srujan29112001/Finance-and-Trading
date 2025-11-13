# 🎯 Smart Model Orchestration - Complete Guide

## Overview

Your Finance Analytics & Trading Co-Pilot now features **intelligent model orchestration** that automatically selects the best available AI models based on your configuration and gracefully falls back to alternatives when needed.

---

## 🚀 How It Works

The system intelligently detects which AI models are available and automatically operates in the best possible mode:

### Operating Modes

#### 🟢 **FULL_ONLINE Mode** (Best Quality)
**When:** Both OpenAI API key and Vision API configured
- **Uses:** OpenAI GPT-4 (LLM) + GPT-4 Vision (VLM)
- **Capabilities:** Full text analysis + chart visual interpretation
- **Message:** *"Using OpenAI GPT-4 + Vision (Best Quality)"*

#### 🟡 **LLM_ONLY Mode**
**When:** Only OpenAI API key configured (no Vision)
- **Uses:** OpenAI GPT-4 for text analysis
- **Capabilities:** Full text analysis, no chart interpretation
- **Message:** *"Using OpenAI GPT-4 only. VLM not available. Enable GPT-4 Vision for chart analysis."*

#### 🟡 **VLM_ONLY Mode**
**When:** Only Vision API configured (no text LLM)
- **Uses:** GPT-4 Vision for chart analysis
- **Capabilities:** Chart interpretation only
- **Message:** *"Using GPT-4 Vision only. LLM not available. Set OPENAI_API_KEY for full text analysis."*

#### 🔵 **OFFLINE Mode** (Maximum Privacy)
**When:** No API keys configured
- **Uses:** Local LLaMA 2 or Mistral models
- **Capabilities:** Full analytics running 100% locally
- **Message:** *"Using Offline Mode (Local LLaMA/Mistral). Data stays private. Add API keys for faster response."*

---

## 📋 Configuration Examples

### Example 1: Full Online Mode (Recommended)

```bash
# .env file
OPENAI_API_KEY=sk-your-openai-key-here
```

**Result:**
- Uses both GPT-4 and GPT-4 Vision
- Best quality responses
- Fast response times
- Full capabilities

### Example 2: Offline Only (Maximum Privacy)

```bash
# .env file
# Leave OPENAI_API_KEY commented out or empty
# OPENAI_API_KEY=
```

**Result:**
- Uses local Mistral/LLaMA models
- 100% private (data never leaves your server)
- No API costs
- Slightly slower responses

### Example 3: Mixed Configuration

```bash
# .env file
OPENAI_API_KEY=sk-your-key-here
# VLM will fall back to local models
```

**Result:**
- Uses GPT-4 for text analysis
- Automatically notifies you VLM unavailable
- Suggests configuration for chart analysis

---

## 🔍 Checking Model Status

### API Endpoint: `/api/chat/model-status`

Check which models are currently available:

```bash
curl http://localhost:8000/api/chat/model-status
```

**Example Response (Full Online):**
```json
{
  "current_mode": "full_online",
  "status_message": "🟢 Using OpenAI GPT-4 + Vision (Best Quality)",
  "available_models": ["openai-gpt4", "gpt4-vision"],
  "model_details": {
    "llm": {
      "status": "available",
      "type": "OpenAI GPT-4"
    },
    "vlm": {
      "status": "available",
      "type": "GPT-4 Vision"
    },
    "offline": {
      "status": "available",
      "type": "LLaMA/Mistral (Local)"
    }
  },
  "features_available": {
    "text_analysis": true,
    "chart_analysis": true,
    "offline_mode": true
  }
}
```

**Example Response (Offline Mode):**
```json
{
  "current_mode": "offline",
  "status_message": "🔵 Using Offline Mode (Local LLaMA/Mistral). Data stays private. Add API keys for faster response.",
  "available_models": ["mistral-7b-local"],
  "model_details": {
    "llm": {
      "status": "not_configured",
      "type": "Not configured"
    },
    "vlm": {
      "status": "not_configured",
      "type": "Not configured"
    },
    "offline": {
      "status": "available",
      "type": "LLaMA/Mistral (Local)"
    }
  },
  "features_available": {
    "text_analysis": true,
    "chart_analysis": false,
    "offline_mode": true
  }
}
```

---

## 💬 Using the Chat API

### Standard Query (Auto-selects Best Models)

```bash
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Why did AAPL spike today?",
    "symbol": "AAPL"
  }'
```

**Response includes model status:**
```json
{
  "session_id": "abc123",
  "message": "Why did AAPL spike today?",
  "response": "Apple (AAPL) spiked 3.2% today primarily due to...",
  "mode": "full_online",
  "status_message": "🟢 Using OpenAI GPT-4 + Vision (Best Quality)",
  "models_used": ["openai-gpt4", "gpt4-vision"],
  "sources": [...],
  "timestamp": "2025-11-13T10:30:00Z"
}
```

### Query with Chart Analysis

```bash
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze TSLA chart patterns",
    "symbol": "TSLA",
    "include_chart_analysis": true
  }'
```

**If VLM available:**
```json
{
  "response": "Based on visual chart analysis, TSLA shows...",
  "mode": "full_online",
  "status_message": "🟢 Using OpenAI GPT-4 + Vision (Best Quality)",
  "chart_analysis": "The candlestick chart reveals a clear bullish flag pattern...",
  "models_used": ["openai-gpt4", "gpt4-vision"]
}
```

**If VLM not available:**
```json
{
  "response": "Based on technical indicators, TSLA shows...",
  "mode": "llm_only",
  "status_message": "🟡 Using OpenAI GPT-4 only. VLM not available.",
  "warning": "Chart visual analysis unavailable. Enable GPT-4 Vision for visual chart interpretation.",
  "models_used": ["openai-gpt4"]
}
```

---

## 🎨 Python Client Example

```python
import requests

API_URL = "http://localhost:8000"

# Check current model status
status = requests.get(f"{API_URL}/api/chat/model-status").json()
print(f"Current Mode: {status['current_mode']}")
print(f"Status: {status['status_message']}")
print(f"Available Models: {status['available_models']}")

# Ask a question (auto-selects best models)
response = requests.post(
    f"{API_URL}/api/chat/ask",
    json={
        "message": "What's happening with NVDA?",
        "symbol": "NVDA",
        "include_chart_analysis": True
    }
).json()

print(f"\nMode: {response['mode']}")
print(f"Status: {response['status_message']}")
print(f"Models Used: {response['models_used']}")
print(f"\nResponse:\n{response['response']}")

if response.get('chart_analysis'):
    print(f"\nChart Analysis:\n{response['chart_analysis']}")

if response.get('warning'):
    print(f"\n⚠️ Warning: {response['warning']}")
```

---

## 🔄 Mode Transitions

The system automatically adapts:

### Startup Detection
When the backend starts, it:
1. Checks for `OPENAI_API_KEY` environment variable
2. Tests if LLM is accessible
3. Tests if VLM is accessible
4. Checks if offline models are available
5. Selects best operating mode
6. Logs the mode to console

### Runtime Behavior
- If API calls fail → gracefully falls back to next best option
- If offline models requested → always available as fallback
- Status messages always inform user of current capabilities

---

## 📊 Dashboard Integration

When using the Streamlit dashboard, you'll see:

```
🤖 AI Co-Pilot Status
━━━━━━━━━━━━━━━━━━━━━━━
Mode: FULL_ONLINE
🟢 Using OpenAI GPT-4 + Vision (Best Quality)

Available Features:
✅ Text Analysis (GPT-4)
✅ Chart Analysis (Vision)
✅ Offline Fallback (LLaMA/Mistral)
```

Or in offline mode:

```
🤖 AI Co-Pilot Status
━━━━━━━━━━━━━━━━━━━━━━━
Mode: OFFLINE
🔵 Using Offline Mode (Local LLaMA/Mistral)

Available Features:
✅ Text Analysis (Local)
❌ Chart Analysis (Install VLM)
✅ Offline Mode Active

💡 Tip: Add OPENAI_API_KEY to .env for faster responses
```

---

## 🐛 Troubleshooting

### Issue: "Using Offline Mode" but I have API key

**Check:**
```bash
# Verify API key is set
docker-compose exec fastapi env | grep OPENAI_API_KEY

# Check model status
curl http://localhost:8000/api/chat/model-status
```

**Fix:**
1. Ensure `.env` file has `OPENAI_API_KEY=sk-...`
2. Restart backend: `docker-compose restart fastapi`
3. Check logs: `docker-compose logs fastapi | grep -i "model"`

### Issue: "VLM not available" message

**This is expected if:**
- You only set `OPENAI_API_KEY` (GPT-4 text, not Vision)
- VLM models not downloaded for local use

**To enable VLM:**
1. For cloud: API key gives access to both GPT-4 and Vision
2. For local: Follow `VLM_AND_OFFLINE_GUIDE.md` to set up local VLM

### Issue: Slow responses in offline mode

**This is normal:**
- Offline models run on your hardware
- Expected: 5-30 seconds per response
- With GPU: 3-10 seconds
- CPU only: 20-60 seconds

**Optimization:**
- Use GPU if available
- Use smaller models (7B not 13B)
- Consider hybrid: online for speed, offline for privacy

---

## 🎯 Best Practices

### For Development
```bash
# Use online mode for speed
OPENAI_API_KEY=sk-your-key-here
```

### For Production (High Volume)
```bash
# Use offline to avoid API costs
# Ensure GPU available for performance
# Comment out or remove API keys
```

### For Privacy-Critical Applications
```bash
# Use offline mode exclusively
# Ensure offline models downloaded
# Never set API keys
```

### For Best Quality
```bash
# Use full online mode
OPENAI_API_KEY=sk-your-key-here
# This enables both GPT-4 and Vision
```

---

## 📈 Performance Comparison

| Mode | Response Time | Quality | Privacy | Cost |
|------|--------------|---------|---------|------|
| **Full Online** | 1-3s | ⭐⭐⭐⭐⭐ | ❌ Cloud | $$ API |
| **LLM Only** | 1-3s | ⭐⭐⭐⭐⭐ | ❌ Cloud | $$ API |
| **VLM Only** | 1-3s | ⭐⭐⭐ | ❌ Cloud | $$ API |
| **Offline** | 5-30s | ⭐⭐⭐⭐ | ✅ 100% Local | ✅ Free |

---

## 🔐 Security Notes

**API Keys:**
- Stored in `.env` file (not committed to git)
- Never logged or exposed via API
- Validated at startup only

**Offline Mode:**
- No data ever sent to external servers
- Models run entirely locally
- Suitable for confidential financial data

**Hybrid Approach:**
- Consider: offline for sensitive queries, online for general queries
- Future: Per-query mode selection

---

## ✅ Testing the Feature

### Quick Test Script

```bash
#!/bin/bash

echo "=== Testing Smart Orchestration ==="

# Test 1: Check model status
echo -e "\n1. Checking model status..."
curl -s http://localhost:8000/api/chat/model-status | jq .

# Test 2: Simple query
echo -e "\n2. Testing simple query..."
curl -s -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is a bull market?"}' | jq '.mode, .status_message'

# Test 3: Query with symbol
echo -e "\n3. Testing query with symbol..."
curl -s -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze AAPL", "symbol": "AAPL"}' | jq '.mode, .models_used'

# Test 4: Query with chart analysis
echo -e "\n4. Testing chart analysis..."
curl -s -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "Show chart patterns", "symbol": "TSLA", "include_chart_analysis": true}' \
  | jq '.mode, .chart_analysis'

echo -e "\n=== Tests Complete ==="
```

Save as `test_orchestration.sh` and run:
```bash
chmod +x test_orchestration.sh
./test_orchestration.sh
```

---

## 🎉 Summary

**You now have a truly intelligent AI system that:**

✅ Automatically uses the best available models
✅ Gracefully falls back when models unavailable
✅ Always informs you which models are active
✅ Never fails - always has a working mode
✅ Adapts to your configuration
✅ Provides clear status messages
✅ Works online, offline, or hybrid

**No manual switching needed - the system handles everything automatically!**

---

For more details:
- VLM Setup: See `VLM_AND_OFFLINE_GUIDE.md`
- General Setup: See `GETTING_STARTED.md`
- API Reference: See `README.md`

**Happy Trading with Smart AI! 🚀📊**
