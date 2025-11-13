# 🎨 VLM & Offline Analytics - Complete Setup Guide

This guide shows you how to add **Vision Language Models (VLM)** for chart interpretation and **Offline LLM Engine** for analytics without cloud dependencies.

---

## 🎯 What You Get

### 1. **Vision Language Model (VLM)**
- **Interprets stock charts visually** like a human analyst
- Identifies patterns, trends, support/resistance
- Works with candlestick charts, technical indicators
- Multiple model options: LLaVA (local), BLIP-2, GPT-4 Vision

### 2. **Offline LLM Engine**
- **100% local analytics** - no cloud APIs needed
- Complete privacy - data never leaves your server
- No ongoing API costs
- Works without internet
- Supports LLaMA 2, Mistral, and other open-source models

---

## 📥 Installation

### Step 1: Install Additional Requirements

```bash
cd Finance-and-Trading/backend

# Install VLM and offline LLM dependencies
pip install -r requirements-vlm.txt
```

This installs:
- `transformers` - For loading VLM and LLM models
- `torch` - PyTorch for model inference
- `llama-cpp-python` - Fast C++ inference for GGUF models
- `bitsandbytes` - 4-bit/8-bit quantization
- `pillow`, `matplotlib` - Image and chart generation
- Other dependencies

### Step 2: Download Models

#### Option A: Offline LLM (Recommended - Start Here)

Download a GGUF model file:

```bash
# Create models directory
mkdir -p models/offline_llm

# Download Mistral 7B (recommended - 4GB)
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  -O models/offline_llm/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# Or download LLaMA 2 7B (also good)
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf \
  -O models/offline_llm/llama-2-7b-chat.Q4_K_M.gguf
```

**Or manually download**:
1. Go to https://huggingface.co/TheBloke
2. Search for "Mistral-7B-Instruct-v0.2-GGUF"
3. Download the `Q4_K_M` variant (~4GB)
4. Place in `models/offline_llm/`

#### Option B: VLM Models (Auto-downloads on first use)

VLM models download automatically when you first use them:

- **LLaVA 1.5 7B**: Downloads ~4GB on first API call
- **BLIP-2**: Downloads ~2GB on first use
- **GPT-4 Vision**: Requires OpenAI API key (no download)

---

## ⚙️ Configuration

### Option 1: Environment Variables (Recommended)

Edit `.env` file:

```bash
# For GPT-4 Vision (optional)
OPENAI_API_KEY=sk-your-key-here

# Model paths (optional - uses defaults if not set)
OFFLINE_LLM_MODEL=mistral-7b
VLM_MODEL=llava
```

### Option 2: Default Configuration

The system uses sensible defaults:
- **Offline LLM**: Mistral 7B (best quality/speed balance)
- **VLM**: LLaVA 1.5 7B (best open-source option)
- **Models directory**: `/models/offline_llm/`

---

## 🚀 Usage

### Restart Backend

After installing dependencies and downloading models:

```bash
# Stop backend
docker-compose restart fastapi

# Or if not using Docker
cd backend
uvicorn app.main:app --reload
```

---

## 🎨 Using VLM (Vision Language Model)

### API Endpoint 1: Analyze Chart from Data

Generate a chart from market data and analyze it:

```bash
curl -X POST http://localhost:8000/api/vlm/analyze-chart \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "chart_type": "candlestick",
    "model": "llava",
    "prompt": "What patterns do you see in this chart? Is it bullish or bearish?"
  }'
```

**Response:**
```json
{
  "symbol": "AAPL",
  "chart_type": "candlestick",
  "model": "LLaVA-1.5",
  "interpretation": "This chart shows a clear bullish trend with higher highs and higher lows. I can see a potential cup and handle pattern forming in the recent price action. The volume confirms the uptrend with increasing volume on up days. Support appears around $170, resistance at $180. Based on technical patterns, this suggests continued upward momentum with a target of $185-190.",
  "timestamp": "2025-11-13T10:30:00Z",
  "data_points": 100
}
```

### API Endpoint 2: Upload Your Own Chart

Upload any chart image:

```bash
curl -X POST http://localhost:8000/api/vlm/analyze-uploaded-chart \
  -F "file=@my_chart.png" \
  -F "model=llava" \
  -F "prompt=Analyze this chart and provide trading signals"
```

### Python Example

```python
import requests

# Analyze from data
response = requests.post(
    "http://localhost:8000/api/vlm/analyze-chart",
    json={
        "symbol": "TSLA",
        "chart_type": "technical",  # includes indicators
        "model": "llava",
        "prompt": "Identify key support and resistance levels"
    }
)

analysis = response.json()
print(f"Model: {analysis['model']}")
print(f"Analysis: {analysis['interpretation']}")

# Upload chart image
with open("chart.png", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/vlm/analyze-uploaded-chart",
        files={"file": f},
        data={
            "model": "llava",
            "prompt": "What patterns do you see?"
        }
    )

print(response.json()['interpretation'])
```

### Available VLM Models

| Model | Quality | Speed | Privacy | Cost |
|-------|---------|-------|---------|------|
| **llava** | ⭐⭐⭐⭐ | Medium | ✅ Local | Free |
| **blip2** | ⭐⭐⭐ | Fast | ✅ Local | Free |
| **gpt4-vision** | ⭐⭐⭐⭐⭐ | Fast | ❌ Cloud | $$ |

**Recommended**: Start with `llava` for best balance.

---

## 💻 Using Offline LLM Engine

### API Endpoint 1: Market Analysis

Get comprehensive market analysis without cloud APIs:

```bash
curl -X POST http://localhost:8000/api/offline/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "question": "Should I buy or sell based on current data?",
    "include_sentiment": true,
    "include_news": true
  }'
```

**Response:**
```json
{
  "symbol": "AAPL",
  "analysis": "Based on the current market data:\n\n**Price Action**: AAPL is trading at $175.50, showing a +2.3% gain in the last 24 hours. The stock has broken above the $175 resistance level with strong volume, which is a bullish signal.\n\n**Sentiment**: The sentiment is positive (score: 0.65), driven by recent news about strong iPhone sales and services growth. Social media buzz is also constructive.\n\n**Technical Indicators**: The price is above both the 20-day and 50-day moving averages, confirming the uptrend. RSI at 68 suggests momentum but approaching overbought territory.\n\n**Recommendation**: BUY with caution. The setup is bullish, but watch for a pullback to $172-173 for a better entry. Set stop loss at $170. Target: $182-185.\n\n**Risk Assessment**: Medium risk. Overbought conditions could lead to short-term consolidation.",
  "model": "mistral-7b",
  "processing_time_ms": 8500,
  "timestamp": "2025-11-13T10:35:00Z",
  "mode": "offline"
}
```

### API Endpoint 2: Offline Chat

Chat about markets without cloud:

```bash
curl -X POST http://localhost:8000/api/offline/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain what a bull market is and how to identify one"
  }'
```

### Python Example

```python
import requests

# Market analysis
response = requests.post(
    "http://localhost:8000/api/offline/analyze",
    json={
        "symbol": "TSLA",
        "question": "What are the risks and opportunities?",
        "include_sentiment": True,
        "include_news": True
    }
)

analysis = response.json()
print(f"Analysis ({analysis['model']}):")
print(analysis['analysis'])
print(f"Processing time: {analysis['processing_time_ms']}ms")

# Chat
response = requests.post(
    "http://localhost:8000/api/offline/chat",
    json={
        "message": "What technical indicators should I watch for swing trading?"
    }
)

print(response.json()['response'])
```

### Check Offline Engine Status

```bash
curl http://localhost:8000/api/offline/status
```

**Response:**
```json
{
  "status": "ready",
  "model_name": "mistral-7b",
  "backend": "llama-cpp",
  "model_path": "/models/offline_llm/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
  "loaded": true,
  "capabilities": {
    "market_analysis": true,
    "q_and_a": true,
    "no_internet_required": true,
    "privacy": "complete"
  },
  "performance": {
    "typical_response_time": "5-30 seconds",
    "memory_usage": "4-8GB RAM",
    "gpu_recommended": true
  }
}
```

---

## 🔄 Integration with Existing System

### Add to LangChain Agent

Edit `backend/app/agents/langchain_agent.py`:

```python
from app.agents.vlm_agent import get_vlm_agent
from app.agents.offline_llm import get_offline_analyzer

class FinanceCopilotAgent:
    def __init__(self):
        # ... existing code ...

        # Add VLM capability
        self.vlm_agent = get_vlm_agent()

        # Add offline analyzer
        self.offline_analyzer = get_offline_analyzer()

    async def process_query_with_vlm(self, symbol, query):
        """Enhanced query processing with chart analysis."""
        # Get price data
        price_data = await self._get_stock_price(symbol)

        # Generate and analyze chart
        vlm_analysis = await self.vlm_agent.analyze_from_data(
            price_data=price_data,
            symbol=symbol
        )

        # Use offline LLM for final synthesis
        final_analysis = await self.offline_analyzer.answer_question(
            question=query,
            context=f"Price: {price_data}\nChart Analysis: {vlm_analysis['interpretation']}"
        )

        return final_analysis
```

### Add to Dashboard

Update `frontend/app.py`:

```python
import streamlit as st

# Add VLM tab
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Market Overview",
    "AI Co-Pilot",
    "Trading Signals",
    "Alerts",
    "📊 VLM Charts",  # New!
    "💻 Offline Mode"  # New!
])

with tab5:
    st.header("🎨 VLM Chart Analysis")

    # Chart analysis
    if st.button("Analyze Chart with AI Vision"):
        with st.spinner("VLM analyzing chart..."):
            response = requests.post(
                f"{API_URL}/api/vlm/analyze-chart",
                json={
                    "symbol": selected_symbol,
                    "chart_type": "candlestick",
                    "model": "llava"
                }
            )

            if response.status_code == 200:
                result = response.json()
                st.success(f"Model: {result['model']}")
                st.write(result['interpretation'])

with tab6:
    st.header("💻 Offline Analytics")

    use_offline = st.checkbox("Use Offline Mode (No Cloud APIs)")

    if use_offline:
        st.info("🔒 Running locally - your data stays private")

        question = st.text_input("Ask offline AI:")
        if st.button("Ask"):
            with st.spinner("Offline LLM processing..."):
                response = requests.post(
                    f"{API_URL}/api/offline/analyze",
                    json={
                        "symbol": selected_symbol,
                        "question": question
                    }
                )

                result = response.json()
                st.write(result['analysis'])
                st.caption(f"Model: {result['model']} | Time: {result['processing_time_ms']}ms")
```

---

## ⚡ Performance & Optimization

### Hardware Requirements

| Component | Minimum | Recommended | Optimal |
|-----------|---------|-------------|---------|
| **CPU** | 4 cores | 8 cores | 16+ cores |
| **RAM** | 8GB | 16GB | 32GB |
| **GPU** | None (CPU only) | NVIDIA 6GB VRAM | NVIDIA 12GB+ VRAM |
| **Storage** | 10GB | 20GB | 50GB |

### Performance Tips

**For CPU-only systems**:
```python
# Use smaller models
model_name = "llama2-7b"  # Not 13B or 70B

# Reduce threads if needed
self.model = Llama(
    model_path=model_path,
    n_threads=4,  # Lower if needed
    n_gpu_layers=0  # CPU only
)
```

**With GPU**:
```python
# Use more GPU layers for speed
self.model = Llama(
    model_path=model_path,
    n_gpu_layers=35,  # All layers on GPU
    n_threads=8
)
```

**Typical Response Times**:
- **CPU only**: 20-60 seconds
- **GPU (6GB)**: 5-15 seconds
- **GPU (12GB+)**: 3-8 seconds

---

## 🆚 Online vs Offline Comparison

| Feature | Online (Cloud API) | Offline (Local) |
|---------|-------------------|-----------------|
| **Quality** | ⭐⭐⭐⭐⭐ (GPT-4) | ⭐⭐⭐⭐ (Mistral/LLaMA) |
| **Speed** | ⚡⚡⚡ (1-3s) | ⚡⚡ (5-30s) |
| **Privacy** | ❌ Data sent to cloud | ✅ 100% local |
| **Cost** | $$ API fees | ✅ Free |
| **Internet** | ❌ Required | ✅ Works offline |
| **Setup** | ✅ Easy (just API key) | ⚙️ Model download needed |
| **GPU** | ❌ Not needed | ⚡ Recommended |

**When to use each**:
- **Online**: Best quality, don't have GPU, small volume
- **Offline**: Privacy critical, high volume, have GPU, want no costs

---

## 🐛 Troubleshooting

### Issue 1: Model Not Loading

```bash
# Check model exists
ls -lh models/offline_llm/

# Check logs
docker-compose logs fastapi | grep -i "model"

# Verify model path in code
curl http://localhost:8000/api/offline/status
```

**Fix**: Ensure model file is downloaded and path is correct.

### Issue 2: Out of Memory

```bash
# Use smaller model (7B not 13B)
# Or reduce context window
n_ctx=2048  # Instead of 4096
```

### Issue 3: Slow Performance

```bash
# Check GPU usage
nvidia-smi  # Should show model loaded

# Reduce threads if using CPU
n_threads=4

# Use quantized models (Q4_K_M)
```

### Issue 4: VLM Not Working

```bash
# Install missing dependencies
pip install transformers accelerate bitsandbytes

# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"
```

---

## 📚 Additional Resources

### Model Downloads
- **LLaMA Models**: https://huggingface.co/TheBloke
- **Mistral Models**: https://huggingface.co/mistralai
- **VLM Models**: Auto-download on first use

### Documentation
- **llama.cpp**: https://github.com/ggerganov/llama.cpp
- **Transformers**: https://huggingface.co/docs/transformers
- **LLaVA**: https://llava-vl.github.io/

### Community
- **Discord**: Join for help with setup
- **GitHub Issues**: Report bugs or ask questions

---

## ✅ Quick Test

Run this to verify everything works:

```bash
# Test offline engine
curl http://localhost:8000/api/offline/status

# Test offline chat
curl -X POST http://localhost:8000/api/offline/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, are you working offline?"}'

# Test VLM
curl -X POST http://localhost:8000/api/vlm/analyze-chart \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "chart_type": "candlestick", "model": "llava"}'
```

If all three respond successfully, you're ready! 🎉

---

## 🎯 Next Steps

1. **Test both systems** with real queries
2. **Compare quality** between online and offline modes
3. **Integrate into dashboard** for seamless UX
4. **Fine-tune models** on your specific data (advanced)
5. **Deploy to production** with appropriate hardware

---

**You now have a complete offline-capable finance analytics system!** 🚀

No cloud dependencies, complete privacy, zero ongoing costs.

**Happy Analyzing! 📊🤖**
