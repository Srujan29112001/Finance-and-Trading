# 🚀 Getting Started Guide - Finance Analytics & Trading Co-Pilot

## Step-by-Step Guide to Run and Test the Application

### 📋 Step 1: Prerequisites

#### Required Software:
- **Docker Desktop** (version 20.10 or higher)
  - Download: https://www.docker.com/products/docker-desktop
  - Verify: `docker --version` and `docker-compose --version`
- **Git** (for cloning the repository)
- **16GB RAM minimum** (recommended: 32GB)
- **20GB free disk space**

#### Check Prerequisites:
```bash
# Check Docker
docker --version
# Should show: Docker version 20.10.x or higher

# Check Docker Compose
docker-compose --version
# Should show: Docker Compose version 2.x or higher

# Check available memory
free -h  # Linux/Mac
# or
wmic OS get FreePhysicalMemory /Value  # Windows

# Check disk space
df -h  # Linux/Mac
# or
wmic logicaldisk get size,freespace,caption  # Windows
```

---

### 📥 Step 2: Clone and Setup (if not already done)

```bash
# Navigate to your projects directory
cd ~/projects  # or wherever you keep your code

# Clone the repository (if not already cloned)
git clone https://github.com/Srujan29112001/Finance-and-Trading.git
cd Finance-and-Trading

# Verify you're in the right directory
ls -la
# You should see: docker-compose.yml, README.md, backend/, frontend/, etc.
```

---

### ⚙️ Step 3: Configure Environment Variables (Optional but Recommended)

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file (optional - works without API keys too)
nano .env  # or use your favorite editor

# Add your OpenAI API key for enhanced AI responses (optional):
# OPENAI_API_KEY=sk-your-key-here

# Save and exit (Ctrl+X, then Y, then Enter in nano)
```

**Note**: The system works without API keys but uses a simpler AI model. For the best experience, add an OpenAI API key.

---

### 🚀 Step 4: Start the Application

#### Option A: Using the Quickstart Script (Easiest)

```bash
# Make the script executable (if not already)
chmod +x quickstart.sh

# Run the quickstart script
./quickstart.sh
```

The script will:
- ✅ Check prerequisites
- ✅ Create necessary directories
- ✅ Pull Docker images
- ✅ Start all services
- ✅ Wait for services to be ready
- ✅ Show you the URLs

#### Option B: Using Makefile

```bash
# Setup (first time only)
make setup

# Start all services
make up

# Check status
make status
```

#### Option C: Using Docker Compose Directly

```bash
# Create necessary directories
mkdir -p backend/logs spark/data/checkpoints airflow/logs models data

# Start all services
docker-compose up -d

# Watch the logs
docker-compose logs -f
```

---

### ⏱️ Step 5: Wait for Services to Initialize

**This takes 2-3 minutes**. Services need to:
- Download images (first time only)
- Initialize databases
- Create Kafka topics
- Start Spark workers
- Load models

#### Monitor Progress:

```bash
# Watch all logs
docker-compose logs -f

# Or watch specific services
docker-compose logs -f fastapi
docker-compose logs -f data-producers
docker-compose logs -f kafka

# Check which services are running
docker-compose ps
```

**What to look for:**
- ✅ `fastapi` - Should show "Application startup complete"
- ✅ `streamlit` - Should show "You can now view your Streamlit app"
- ✅ `data-producers` - Should show "Producing data for symbols: AAPL, TSLA..."
- ✅ `kafka` - Should show "started (kafka.server.KafkaServer)"
- ✅ `postgres` - Should show "database system is ready to accept connections"

---

### 🌐 Step 6: Access the Applications

Once services are ready, open these URLs in your browser:

#### Main Applications:

1. **📊 Streamlit Dashboard** (Main UI)
   ```
   http://localhost:8501
   ```
   - This is your main interface!
   - View real-time charts
   - Chat with AI
   - See trading signals

2. **🚀 FastAPI Documentation** (API Reference)
   ```
   http://localhost:8000/docs
   ```
   - Interactive API documentation
   - Test all endpoints
   - See request/response formats

3. **📈 Grafana** (Monitoring)
   ```
   http://localhost:3000
   ```
   - Username: `admin`
   - Password: `admin`
   - View system metrics
   - Create custom dashboards

4. **🔬 MLflow** (ML Experiments)
   ```
   http://localhost:5000
   ```
   - Track model training
   - View experiments
   - Compare model versions

5. **🔄 Airflow** (Job Scheduling)
   ```
   http://localhost:8082
   ```
   - View scheduled jobs
   - Trigger manual runs
   - Check job history

---

### 🧪 Step 7: Test Each Component

#### Test 1: Check API Health

```bash
# Check if API is responding
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","timestamp":"2025-11-13T...","service":"finance-analytics-api"}

# Check API info
curl http://localhost:8000/api/info

# You should see capabilities, data sources, and ML models listed
```

#### Test 2: View Live Market Data

```bash
# Get latest price for Apple
curl http://localhost:8000/api/market/latest/AAPL

# Get market summary
curl http://localhost:8000/api/market/summary/TSLA

# Get available symbols
curl http://localhost:8000/api/market/symbols
```

**Expected**: JSON responses with real-time price data

#### Test 3: Check Data Producers

```bash
# View data producer logs
docker-compose logs -f data-producers

# You should see:
# "Produced price tick: AAPL @ $175.23"
# "Produced news: Tesla Announces Record Q3 Earnings..."
# "Produced tweet: Just bought more $TSLA! 🚀"
```

**This confirms data is flowing into Kafka!**

#### Test 4: Check Kafka Topics

```bash
# List Kafka topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Expected topics:
# market_prices
# news_events
# social_tweets
```

#### Test 5: Check Databases

```bash
# Check PostgreSQL
docker-compose exec postgres psql -U financeuser -d financedb -c "SELECT COUNT(*) FROM stock_prices;"

# Expected: A number showing how many price records exist

# Check if data is recent
docker-compose exec postgres psql -U financeuser -d financedb -c "SELECT symbol, timestamp, close FROM stock_prices ORDER BY timestamp DESC LIMIT 5;"

# Expected: Recent price data for various stocks
```

#### Test 6: Test the Dashboard

1. Open http://localhost:8501
2. You should see:
   - ✅ Stock symbol dropdown
   - ✅ Current price and metrics
   - ✅ Real-time price chart
   - ✅ Volume chart
   - ✅ Sentiment scores

3. **Try different tabs**:
   - **Market Overview**: See live charts
   - **AI Co-Pilot**: Chat with the AI
   - **Trading Signals**: View ML recommendations
   - **Alerts**: See market anomalies
   - **About**: System information

#### Test 7: Test AI Co-Pilot

1. Go to **AI Co-Pilot** tab in the dashboard
2. Try these questions:

```
"What is the current price of Tesla?"
"What's the sentiment on Apple stock?"
"Should I buy Microsoft now?"
"Why did TSLA change today?"
```

3. **Or use the API**:

```bash
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the current price of AAPL?",
    "symbol": "AAPL"
  }'
```

**Expected**: AI-generated response with market data

#### Test 8: Test Trading Signals

```bash
# Generate a trading signal
curl -X POST "http://localhost:8000/api/trading/signal/generate?symbol=AAPL"

# Expected output:
# {
#   "symbol": "AAPL",
#   "signal_type": "BUY",  # or SELL, HOLD
#   "confidence": 0.75,
#   "price": 175.50,
#   "target_price": 184.28,
#   "stop_loss": 170.24,
#   "reasoning": "Signal generated by DQN...",
#   "timestamp": "2025-11-13T..."
# }
```

#### Test 9: Test Sentiment Analysis

```bash
# Get sentiment for a symbol
curl http://localhost:8000/api/analysis/sentiment/aggregate/TSLA

# Expected:
# {
#   "symbol": "TSLA",
#   "avg_sentiment": 0.234,
#   "sentiment_label": "positive",
#   "sample_size": 42,
#   "period_hours": 24
# }
```

#### Test 10: Check Spark Processing

```bash
# Check Spark master UI
# Open in browser: http://localhost:8080

# Or check logs
docker-compose logs spark-master

# You should see processing jobs running
```

---

### 📊 Step 8: Explore the Dashboard Features

#### A. Market Overview Tab

1. **Select a stock** from the dropdown (AAPL, TSLA, etc.)
2. **View metrics**:
   - Current Price
   - 24h High/Low
   - Volume
   - Price Change %
3. **Check sentiment**:
   - Sentiment label (Positive/Negative/Neutral)
   - Sentiment score (-1.0 to +1.0)
4. **Analyze charts**:
   - Candlestick chart shows OHLC (Open, High, Low, Close)
   - Volume bar chart
   - Zoom and pan to explore

#### B. AI Co-Pilot Tab

1. **Ask questions** in natural language
2. **Example conversations**:

   ```
   You: "Why did Tesla's stock move today?"
   AI: "Based on the available data: Tesla (TSLA) has shown
        movement today driven by sentiment and trading activity..."
   ```

3. **View tools used** - Click "Tools Used" expander to see:
   - VectorSearch
   - GetStockPrice
   - GetSentiment
   - etc.

4. **Clear chat** - Reset conversation anytime

#### C. Trading Signals Tab

1. **View latest signal** - BUY/SELL/HOLD recommendation
2. **Check confidence** - How confident is the model?
3. **See reasoning** - Why this recommendation?
4. **Review history** - Past signals and performance
5. **Generate new signal** - Click "Generate Signal Now"

#### D. Alerts Tab

1. **Monitor anomalies**:
   - Volume spikes
   - Price jumps
   - Unusual activity
2. **Color-coded severity**:
   - 🔴 Critical
   - 🟠 High
   - 🔵 Medium
   - ⚪ Low

---

### 🔍 Step 9: Advanced Testing

#### Test the GraphQL API

```bash
# Using curl
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ marketData { symbol currentPrice } }"
  }'
```

#### Test WebSocket (Real-time Updates)

```javascript
// In browser console (F12)
const ws = new WebSocket('ws://localhost:8000/ws/prices?symbols=AAPL,TSLA');

ws.onmessage = (event) => {
  console.log('Price update:', event.data);
};
```

#### Test Airflow DAGs

1. Go to http://localhost:8082
2. Find "daily_analytics_pipeline"
3. Click the play button to trigger manually
4. Watch the task execution

#### Test with Python Script

Create a test script:

```python
# test_api.py
import requests

API_URL = "http://localhost:8000"

# Test 1: Get latest price
response = requests.get(f"{API_URL}/api/market/latest/AAPL")
print("Latest Price:", response.json())

# Test 2: Ask AI
response = requests.post(
    f"{API_URL}/api/chat/ask",
    json={"message": "What is Apple's current price?", "symbol": "AAPL"}
)
print("AI Response:", response.json()['response'])

# Test 3: Get trading signal
response = requests.post(
    f"{API_URL}/api/trading/signal/generate?symbol=AAPL"
)
print("Trading Signal:", response.json())
```

Run it:
```bash
python test_api.py
```

---

### 📈 Step 10: Monitor System Performance

#### Using Grafana

1. Open http://localhost:3000
2. Login (admin/admin)
3. Explore → Dashboards
4. Import dashboard (optional):
   - Upload JSON from `monitoring/grafana/dashboards/`
5. **Key metrics to watch**:
   - API response times
   - Kafka consumer lag
   - Database connections
   - Memory usage

#### Using Prometheus

1. Open http://localhost:9090
2. **Try these queries**:
   ```
   # API request rate
   rate(http_requests_total[5m])

   # Average response time
   rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
   ```

#### Check Logs

```bash
# Real-time logs from all services
make logs

# Filter for errors
docker-compose logs | grep ERROR

# Logs for specific service
make logs-api        # FastAPI
make logs-dashboard  # Streamlit
make logs-kafka      # Kafka
make logs-spark      # Spark
make logs-producers  # Data producers
```

---

### 🔧 Step 11: Troubleshooting Common Issues

#### Issue 1: Services Won't Start

```bash
# Check if ports are already in use
sudo lsof -i :8000  # FastAPI
sudo lsof -i :8501  # Streamlit
sudo lsof -i :5432  # PostgreSQL

# If ports are busy, stop the conflicting service or change ports in docker-compose.yml
```

#### Issue 2: No Data in Dashboard

```bash
# Check if data producers are running
docker-compose ps data-producers

# Check producer logs
docker-compose logs data-producers

# Restart data producers
docker-compose restart data-producers
```

#### Issue 3: Database Connection Errors

```bash
# Check if PostgreSQL is ready
docker-compose exec postgres pg_isready -U financeuser

# Manually test connection
docker-compose exec postgres psql -U financeuser -d financedb

# If failed, restart postgres
docker-compose restart postgres
```

#### Issue 4: AI Not Responding

```bash
# Check FastAPI logs
docker-compose logs fastapi

# Verify database connections
curl http://localhost:8000/health

# Test a simple query
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

#### Issue 5: Out of Memory

```bash
# Check Docker resource usage
docker stats

# Free up resources
docker-compose down
docker system prune -a

# Increase Docker memory limit in Docker Desktop settings
# Recommended: 8GB minimum, 16GB preferred
```

#### Issue 6: Slow Performance

```bash
# Check resource usage
docker stats

# Reduce number of symbols in data producers
# Edit data-producers/main.py and reduce SYMBOLS list

# Restart with fewer services
docker-compose up -d postgres kafka fastapi streamlit data-producers
```

---

### 🛑 Step 12: Stopping the Application

```bash
# Stop all services (keeps data)
docker-compose down

# Or using Makefile
make down

# Stop and remove all data
docker-compose down -v

# Or using Makefile
make clean  # (will ask for confirmation)
```

---

### 🔄 Step 13: Restarting the Application

```bash
# Start again
docker-compose up -d

# Or
make up

# Check status
docker-compose ps
make status
```

---

### 📝 Step 14: Development Workflow

#### Making Changes to Backend

```bash
# Edit files in backend/app/
nano backend/app/api/market_data.py

# Restart FastAPI to see changes
docker-compose restart fastapi

# View logs
docker-compose logs -f fastapi
```

#### Making Changes to Frontend

```bash
# Edit files in frontend/
nano frontend/app.py

# Restart Streamlit
docker-compose restart streamlit

# Changes should appear immediately (Streamlit auto-reloads)
```

#### Adding New Data Producers

```bash
# Edit data-producers/main.py
# Restart producers
docker-compose restart data-producers
```

---

### ✅ Success Checklist

After setup, verify:

- [ ] All services running: `docker-compose ps` shows 15+ services "Up"
- [ ] Dashboard accessible: http://localhost:8501 loads
- [ ] API working: http://localhost:8000/docs shows documentation
- [ ] Data flowing: Logs show "Produced price tick..." messages
- [ ] Database populated: `SELECT COUNT(*) FROM stock_prices;` returns > 0
- [ ] AI responding: Chat in dashboard works
- [ ] Trading signals: Can generate signals for stocks
- [ ] Monitoring: Grafana shows metrics

---

### 🎓 Next Steps

1. **Explore the codebase**:
   - Read `backend/app/agents/langchain_agent.py` for AI logic
   - Check `spark/jobs/streaming_processor.py` for data processing
   - Review `frontend/app.py` for UI components

2. **Customize**:
   - Add new stock symbols
   - Create custom indicators
   - Build new dashboard tabs
   - Add more AI tools

3. **Extend**:
   - Connect real market data APIs (Alpha Vantage, Yahoo Finance)
   - Add more ML models
   - Implement backtesting
   - Deploy to cloud

---

### 📚 Additional Resources

- **Main README**: `README.md` - Complete project documentation
- **Project Summary**: `PROJECT_SUMMARY.md` - Overview and features
- **API Docs**: http://localhost:8000/docs - Interactive API reference
- **Makefile Help**: `make help` - See all available commands

---

### 🆘 Getting Help

If you encounter issues:

1. **Check logs**: `docker-compose logs -f`
2. **Check health**: `make check-health`
3. **Restart services**: `docker-compose restart`
4. **Full reset**: `make clean && make up`
5. **Search error messages** in logs for specific issues

---

### 🎉 You're All Set!

You now have a fully functional Finance Analytics & Trading Co-Pilot running locally!

**Happy Trading! 📈**
