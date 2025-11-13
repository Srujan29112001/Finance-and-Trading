# 📈 Finance Analytics & Trading Co-Pilot

> **Real-Time Finance Analytics Platform with AI-Powered Trading Assistant**

A comprehensive, production-ready platform that combines streaming data processing, machine learning, and AI to provide real-time market insights and trading recommendations.

![Architecture](https://img.shields.io/badge/Architecture-Microservices-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎯 Project Overview

This platform addresses the **data overload problem** in modern trading by providing:

- **Real-time data ingestion** from multiple sources (market data, news, social media)
- **AI-powered analysis** using LangChain with RAG (Retrieval-Augmented Generation) and GraphRAG
- **ML-based trading signals** using Reinforcement Learning (DQN)
- **Interactive dashboard** for visualization and AI chat interface
- **Comprehensive monitoring** and observability

### Key Features

✅ **Streaming Analytics**: Apache Kafka + Spark for high-throughput real-time processing
✅ **AI Co-Pilot**: LangChain-powered conversational analytics with contextual awareness
✅ **Smart Model Orchestration**: Automatically selects best available models (online/offline) with graceful fallback
✅ **VLM Chart Analysis**: Vision Language Models for visual interpretation of stock charts
✅ **Offline Analytics**: 100% local LLM processing (LLaMA/Mistral) for complete privacy
✅ **RL Trading Agent**: Deep Q-Network for intelligent trading recommendations
✅ **Multi-Modal Data Fusion**: Combines prices, news sentiment, and social media
✅ **Graph RAG**: Knowledge graph queries for relationship-based insights
✅ **Production-Ready**: Docker Compose orchestration with comprehensive monitoring

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                             │
│         Market Data | News Feeds | Social Media                  │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APACHE KAFKA (Streaming Bus)                  │
│         Topics: market_prices, news_events, social_tweets        │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│              APACHE SPARK (Stream Processing)                    │
│    • Windowed Aggregations    • Anomaly Detection               │
│    • Feature Engineering       • Sentiment Analysis              │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                               │
│  PostgreSQL  │  MongoDB  │  Qdrant (Vector)  │  Neo4j (Graph)  │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AI/ML LAYER                               │
│  • LangChain Agent (RAG/GraphRAG)                               │
│  • RL Trading Agent (DQN)                                       │
│  • Sentiment Models                                             │
│  • MLflow (Experiment Tracking)                                 │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API LAYER                                 │
│              FastAPI (REST + GraphQL)                            │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                                │
│              Streamlit Dashboard + AI Chat                       │
└─────────────────────────────────────────────────────────────────┘

             ┌────────────────────┐
             │  MONITORING        │
             │  Prometheus        │
             │  Grafana          │
             └────────────────────┘
```

### Tech Stack

| Category | Technologies |
|----------|-------------|
| **Streaming** | Apache Kafka, Apache Spark Structured Streaming |
| **Databases** | PostgreSQL, MongoDB, Qdrant (Vector DB), Neo4j (Graph DB) |
| **AI/ML** | LangChain, OpenAI GPT-4, Stable-Baselines3 (RL) |
| **Vision Models** | GPT-4 Vision, LLaVA, BLIP-2 |
| **Offline LLMs** | LLaMA 2, Mistral (via llama.cpp) |
| **Backend** | FastAPI, GraphQL (Strawberry) |
| **Frontend** | Streamlit, Plotly |
| **Orchestration** | Apache Airflow, Docker Compose |
| **Monitoring** | Prometheus, Grafana |
| **MLOps** | MLflow, Weights & Biases |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (v2.0+)
- 16GB+ RAM recommended
- 20GB+ free disk space

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Finance-and-Trading.git
   cd Finance-and-Trading
   ```

2. **Create environment file** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (OpenAI, etc.)
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to initialize** (~2-3 minutes)
   ```bash
   docker-compose logs -f
   ```

5. **Access the services**
   - **Dashboard**: http://localhost:8501
   - **API Docs**: http://localhost:8000/docs
   - **Grafana**: http://localhost:3000 (admin/admin)
   - **Kafka UI**: http://localhost:9092
   - **Airflow**: http://localhost:8082
   - **MLflow**: http://localhost:5000

---

## 📊 Usage

### 1. Viewing Real-Time Market Data

The **Data Producers** automatically generate simulated market data for multiple stocks:

```bash
# Check data producers logs
docker-compose logs -f data-producers
```

View the **Streamlit Dashboard** at http://localhost:8501 to see:
- Real-time price charts
- Trading volume
- Market sentiment
- AI-generated alerts

### 2. Using the AI Co-Pilot

Navigate to the **AI Co-Pilot** tab in the dashboard and ask questions like:

- "Why did TSLA spike at 10:03 today?"
- "What's the sentiment on Apple stock?"
- "Should I buy Microsoft now?"
- "Compare earnings of AAPL and GOOGL"
- "Analyze the chart patterns for NVDA" (with visual chart analysis)

The AI uses **RAG (Retrieval-Augmented Generation)** to provide data-backed answers by:
1. Querying the vector database for relevant documents
2. Fetching real-time price and volume data
3. Analyzing sentiment from news and social media
4. Consulting the knowledge graph for relationships
5. Generating a coherent, sourced response

**🎯 Smart Model Orchestration** (NEW!):
The system automatically selects the best available AI models:
- 🟢 **Both API keys configured** → Uses OpenAI GPT-4 + Vision (best quality)
- 🟡 **Only LLM configured** → Uses GPT-4 text analysis (informs about VLM unavailable)
- 🟡 **Only VLM configured** → Uses Vision for charts (informs about LLM unavailable)
- 🔵 **No API keys** → Uses offline LLaMA/Mistral (100% private, free)

Check current model status:
```bash
curl http://localhost:8000/api/chat/model-status
```

See `SMART_ORCHESTRATION_GUIDE.md` for complete details.

### 3. Getting Trading Signals

The **RL Trading Agent** (Deep Q-Network) generates BUY/SELL/HOLD signals:

```bash
# Generate a signal via API
curl -X POST "http://localhost:8000/api/trading/signal/generate?symbol=AAPL"
```

Or use the **Trading Signals** tab in the dashboard.

### 4. API Usage

#### REST API Examples

```bash
# Get latest price
curl http://localhost:8000/api/market/latest/AAPL

# Get market summary
curl http://localhost:8000/api/market/summary/TSLA

# Get sentiment
curl http://localhost:8000/api/analysis/sentiment/GOOGL

# Ask AI a question
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "Why did TSLA spike?", "symbol": "TSLA"}'
```

#### GraphQL Example

```graphql
query {
  priceHistory(symbol: "AAPL", limit: 10) {
    timestamp
    close
    volume
  }
  latestNews(symbol: "AAPL", limit: 5) {
    headline
    sentiment
  }
}
```

---

## 🧠 AI/ML Components

### 1. LangChain Agent (RAG + GraphRAG)

**Location**: `backend/app/agents/langchain_agent.py`

The agent has access to multiple tools:
- **VectorSearch**: Semantic search over financial documents
- **GetStockPrice**: Real-time price data
- **GetSentiment**: Aggregated sentiment scores
- **GetTradingSignal**: RL agent recommendations
- **GraphQuery**: Knowledge graph relationships
- **GetNewsArticles**: Recent news articles

**RAG Pipeline**:
1. User query → Generate embedding
2. Search Qdrant vector DB for similar documents
3. Retrieve relevant context (prices, news, sentiment)
4. LLM generates response with retrieved context

**GraphRAG**:
- Queries Neo4j knowledge graph for entity relationships
- Example: "How might Tesla's CEO change affect related companies?"
- Multi-hop reasoning over company-event-impact relationships

### 2. RL Trading Agent (DQN)

**Location**: `backend/app/agents/rl_agent.py`

Uses **Deep Q-Network** to learn trading policies:
- **State**: Price, volume, technical indicators, position
- **Actions**: BUY, SELL, HOLD
- **Reward**: Profit/loss and risk-adjusted returns

Training:
```python
from app.agents.rl_agent import get_rl_agent

agent = get_rl_agent()
await agent.train(symbol="AAPL", episodes=1000)
```

### 3. Sentiment Analysis

Processes news and social media to generate sentiment scores:
- **News**: Professional articles (Reuters, Bloomberg)
- **Social**: Twitter, Reddit posts
- **Aggregation**: Weighted average with recency bias
- **Output**: Score (-1.0 to +1.0) and label (positive/negative/neutral)

---

## 🔄 Data Flow

### Real-Time Pipeline

1. **Data Producers** → Simulate market data, news, tweets
2. **Kafka** → Stream events to topics
3. **Spark Streaming** → Process in micro-batches:
   - Calculate windowed aggregations (5-min averages)
   - Detect anomalies (volume spikes, price jumps)
   - Compute sentiment scores
4. **Storage** → Write to PostgreSQL, MongoDB, Qdrant
5. **APIs** → Serve data to frontend and AI agents
6. **Dashboard** → Real-time visualization

### Batch Pipeline (Airflow)

Daily jobs (2 AM):
1. Refresh materialized views
2. Calculate technical indicators (SMA, RSI, MACD)
3. Retrain RL model with latest data
4. Generate daily reports
5. Update embeddings in vector DB

---

## 📈 Monitoring & Observability

### Prometheus Metrics

- API request latency (p50, p95, p99)
- Kafka consumer lag
- Spark processing time
- Database query performance
- Model inference time

### Grafana Dashboards

Access at http://localhost:3000 (admin/admin)

Pre-configured dashboards:
- System Health Overview
- API Performance
- Kafka Metrics
- Database Metrics
- Model Performance

### Logging

All services log to stdout. View logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi
docker-compose logs -f spark-master
```

---

## 🧪 Development

### Project Structure

```
Finance-and-Trading/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── agents/         # AI agents (LangChain, RL)
│   │   ├── models/         # Database models
│   │   └── main.py         # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # Streamlit dashboard
│   ├── app.py
│   └── requirements.txt
├── data-producers/          # Kafka producers
│   ├── main.py
│   └── requirements.txt
├── spark/                   # Spark jobs
│   └── jobs/
│       └── streaming_processor.py
├── airflow/                 # Airflow DAGs
│   └── dags/
│       └── daily_analytics_pipeline.py
├── sql/                     # Database schemas
│   └── init.sql
├── monitoring/              # Prometheus & Grafana config
│   ├── prometheus.yml
│   └── grafana/
├── docker-compose.yml       # Orchestration
└── README.md
```

### Adding a New Feature

1. **Add API endpoint**: `backend/app/api/`
2. **Update database models**: `backend/app/models/`
3. **Add to dashboard**: `frontend/app.py`
4. **Update tests**: `backend/tests/`

### Running Tests

```bash
# Backend tests
docker-compose exec fastapi pytest

# Integration tests
pytest tests/integration/
```

---

## 🔒 Security & Compliance

- **Read-only broker integration** for paper trading
- **Audit logs** for all AI decisions and trades
- **RBAC** for user access control
- **Rate limiting** on API endpoints
- **Secrets management** via environment variables
- **Data encryption** in transit (HTTPS/TLS)

---

## 🎓 Key Concepts

### RAG (Retrieval-Augmented Generation)

Instead of relying solely on the LLM's training data, RAG:
1. Retrieves relevant documents from a knowledge base
2. Injects them as context into the LLM prompt
3. Grounds responses in factual, up-to-date information
4. Reduces hallucinations

### GraphRAG

Extends RAG with knowledge graph queries:
- Captures relationships between entities
- Enables multi-hop reasoning
- Example: "Company A → acquired by → Company B → CEO → Person X"

### Reinforcement Learning for Trading

The RL agent learns through trial and error:
- **Training**: Simulates thousands of trading episodes on historical data
- **Policy**: Neural network that maps states to actions
- **Deployment**: Generates signals based on current market state
- **Continuous Learning**: Periodically retrained with new data

### Computational Psychiatry

Monitors trader behavior for psychological risk factors:
- **Impulsive trading**: Rapid consecutive trades
- **Loss chasing**: Increased risk after losses
- **FOMO**: Following herd sentiment
- **Recommendations**: "Take a break" alerts

---

## 🚧 Roadmap

- [ ] Add options flow data integration
- [ ] Implement portfolio optimization (MPT)
- [ ] Add backtesting framework
- [ ] Multi-asset support (crypto, forex)
- [ ] Advanced ML models (Transformers for time-series)
- [ ] Mobile app (React Native)
- [ ] Cloud deployment (AWS/GCP/Azure)
- [ ] Advanced risk analytics (CVaR, Greeks)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style

- Python: PEP 8, Black formatter
- Type hints required
- Docstrings for all public functions
- Unit tests for new features

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Apache Software Foundation** for Kafka, Spark, Airflow
- **LangChain** for the agent framework
- **OpenAI** for GPT models
- **Stable-Baselines3** for RL algorithms
- **Streamlit** for rapid UI development

---

## 📧 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/Finance-and-Trading/issues)
- **Email**: your.email@example.com
- **Documentation**: Full docs at [docs/](docs/)

---

## ⚠️ Disclaimer

**This platform is for educational and research purposes only.**

- Not financial advice
- No guarantees on trading performance
- Use at your own risk
- Consult a licensed financial advisor for investment decisions
- Past performance does not indicate future results

---

## 🎉 Getting Started Video

[Coming Soon] Watch a 5-minute walkthrough of the platform

---

## 📚 Additional Resources

### Setup Guides
- [Getting Started Guide](GETTING_STARTED.md) - Complete setup and testing instructions
- [VLM & Offline Analytics Setup](VLM_AND_OFFLINE_GUIDE.md) - Visual chart analysis and local LLMs
- [Smart Orchestration Guide](SMART_ORCHESTRATION_GUIDE.md) - Intelligent model selection and fallback

### Technical Documentation
- [Architecture Deep Dive](docs/ARCHITECTURE.md)
- [API Reference](http://localhost:8000/docs)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [ML Models Documentation](docs/ML_MODELS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

---

**Built with ❤️ for the trading and AI community**

⭐ **Star this repo** if you find it useful!
