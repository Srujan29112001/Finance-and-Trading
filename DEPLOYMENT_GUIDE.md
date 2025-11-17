# 🚀 Complete Deployment & Build Guide

## Finance Analytics & Trading Co-Pilot - Production Deployment

This guide will walk you through building, running, testing, and deploying the entire Finance Analytics platform from scratch.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start)
3. [Development Setup](#development-setup)
4. [Building the Project](#building-the-project)
5. [Running the Platform](#running-the-platform)
6. [Verifying Services](#verifying-services)
7. [Configuration](#configuration)
8. [Production Deployment](#production-deployment)
9. [Monitoring & Maintenance](#monitoring--maintenance)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

```bash
# 1. Docker & Docker Compose
docker --version          # Should be 20.10+
docker-compose --version  # Should be 2.0+

# 2. Git
git --version            # Should be 2.0+

# 3. System Requirements
# - 16GB+ RAM (8GB minimum)
# - 20GB+ free disk space
# - 4+ CPU cores recommended
```

### Installation Links

- **Docker Desktop**: https://docs.docker.com/get-docker/
- **Docker Compose**: https://docs.docker.com/compose/install/
- **Git**: https://git-scm.com/downloads

---

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/Srujan29112001/Finance-and-Trading.git
cd Finance-and-Trading

# Run the quickstart script
chmod +x quickstart.sh
./quickstart.sh

# Start all services
docker-compose up -d

# Wait 2-3 minutes for initialization
# Access the dashboard at http://localhost:8501
```

### Option 2: Using Makefile

```bash
# Clone and setup
git clone https://github.com/Srujan29112001/Finance-and-Trading.git
cd Finance-and-Trading

# Initialize project
make setup

# Start services
make up

# Check status
make status
```

---

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Srujan29112001/Finance-and-Trading.git
cd Finance-and-Trading
```

### 2. Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your settings
nano .env  # or use your preferred editor
```

### 3. Configure Environment Variables

Edit `.env` file with your API keys and settings:

```bash
# ============================================
# API Keys (Optional but Recommended)
# ============================================

# OpenAI API Key (for GPT-4 chat features)
OPENAI_API_KEY=sk-your-openai-key-here

# Hugging Face Token (for offline LLMs)
HF_TOKEN=hf_your-token-here

# ============================================
# Database Settings
# ============================================

POSTGRES_USER=financeuser
POSTGRES_PASSWORD=financepass
POSTGRES_DB=financedb

MONGODB_USER=financeuser
MONGODB_PASSWORD=financepass

NEO4J_PASSWORD=financepass

# ============================================
# Security Settings
# ============================================

# Generate a secure key: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-very-secure-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production

# ============================================
# Application Settings
# ============================================

DEBUG=false
ENVIRONMENT=production
```

**Important Notes:**
- **Without API keys**: The system will use offline LLMs (LLaMA/Mistral)
- **With OpenAI key**: You get GPT-4 powered AI assistant
- **In production**: Always use strong, unique secret keys

### 4. Initialize Project Structure

```bash
# Ensure all directories exist
mkdir -p backend/logs
mkdir -p airflow/logs
mkdir -p airflow/plugins
mkdir -p spark/data/checkpoints
mkdir -p models
mkdir -p data

# Verify structure
ls -la backend/logs
ls -la airflow/logs
```

---

## Building the Project

### Build All Docker Images

```bash
# Build all services (first time takes 10-15 minutes)
docker-compose build --no-cache

# Or use Makefile
make build
```

### Build Individual Services

```bash
# Backend only
docker-compose build fastapi

# Frontend only
docker-compose build streamlit

# Data producers
docker-compose build data-producers

# Airflow
docker-compose build airflow-webserver airflow-scheduler
```

### Verify Build Success

```bash
# List all built images
docker images | grep finance

# Expected output:
# finance-and-trading-fastapi
# finance-and-trading-streamlit
# finance-and-trading-data-producers
# finance-and-trading-airflow-webserver
# finance-and-trading-airflow-scheduler
```

---

## Running the Platform

### Start All Services

```bash
# Start in detached mode (background)
docker-compose up -d

# Or start with logs visible
docker-compose up

# Using Makefile
make up
```

### Start Specific Services

```bash
# Start only databases
docker-compose up -d postgres mongodb qdrant neo4j redis

# Start backend and frontend
docker-compose up -d fastapi streamlit

# Start data pipeline
docker-compose up -d kafka zookeeper data-producers spark-master spark-worker
```

### Check Service Status

```bash
# View all running containers
docker-compose ps

# Or use Makefile
make status

# Expected output:
# NAME                    STATUS              PORTS
# fastapi                 Up 2 minutes        0.0.0.0:8000->8000/tcp
# streamlit               Up 2 minutes        0.0.0.0:8501->8501/tcp
# postgres                Up 2 minutes        0.0.0.0:5432->5432/tcp
# kafka                   Up 2 minutes        0.0.0.0:9092->9092/tcp
# ...
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi
docker-compose logs -f streamlit
docker-compose logs -f kafka

# Using Makefile
make logs              # All logs
make logs-api          # FastAPI logs
make logs-dashboard    # Streamlit logs
make logs-kafka        # Kafka logs
make logs-spark        # Spark logs
```

---

## Verifying Services

### 1. Check Service Health

```bash
# Health check script
make check-health

# Manual checks
curl http://localhost:8000/health
curl http://localhost:8501
curl http://localhost:3000/api/health  # Grafana
curl http://localhost:5000/health      # MLflow
```

### 2. Access Service Endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| **Dashboard** | http://localhost:8501 | None |
| **API Docs** | http://localhost:8000/docs | See below |
| **GraphQL** | http://localhost:8000/graphql | See below |
| **Grafana** | http://localhost:3000 | admin/admin |
| **MLflow** | http://localhost:5000 | None |
| **Airflow** | http://localhost:8082 | admin/admin |
| **Spark UI** | http://localhost:8080 | None |
| **Neo4j Browser** | http://localhost:7474 | neo4j/financepass |

### 3. Test API Authentication

```bash
# Get JWT token
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Use token in requests
TOKEN="your-token-here"
curl http://localhost:8000/api/market/latest/AAPL \
  -H "Authorization: Bearer $TOKEN"
```

**Default Test Users:**
- Admin: `admin` / `admin123`
- Trader: `trader` / `trader123`
- Analyst: `analyst` / `analyst123`

### 4. Test Data Flow

```bash
# Check if data producers are working
docker-compose logs data-producers | grep "Published"

# Check Kafka topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:29092

# Expected topics:
# market_prices
# news_events
# social_tweets
# market_alerts
# trading_signals

# View messages in a topic
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:29092 \
  --topic market_prices \
  --from-beginning \
  --max-messages 5
```

### 5. Test AI Assistant

```bash
# Test chat endpoint
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message": "What is the current price of AAPL?",
    "symbol": "AAPL"
  }'

# Check model status
curl http://localhost:8000/api/chat/model-status
```

### 6. Test Database Connections

```bash
# PostgreSQL
docker-compose exec postgres psql -U financeuser -d financedb -c "SELECT version();"

# MongoDB
docker-compose exec mongodb mongosh -u financeuser -p financepass --eval "db.version()"

# Redis
docker-compose exec redis redis-cli ping

# Neo4j
docker-compose exec neo4j cypher-shell -u neo4j -p financepass "RETURN 'connected' as status;"
```

---

## Configuration

### Database Initialization

The PostgreSQL database is automatically initialized with the schema from `sql/init.sql`. To manually reinitialize:

```bash
# Drop and recreate database
docker-compose exec postgres psql -U financeuser -d postgres -c "DROP DATABASE IF EXISTS financedb;"
docker-compose exec postgres psql -U financeuser -d postgres -c "CREATE DATABASE financedb;"

# Apply schema
docker-compose exec postgres psql -U financeuser -d financedb -f /docker-entrypoint-initdb.d/init.sql
```

### Running Database Migrations

```bash
# Run Alembic migrations
make db-migrate

# Or manually
docker-compose exec fastapi alembic upgrade head
```

### Importing Grafana Dashboards

```bash
# Import dashboards
make grafana-import

# Or manually access Grafana UI and import JSON files from:
# monitoring/grafana/dashboards/
```

### Training RL Model

```bash
# Access FastAPI container
docker-compose exec fastapi bash

# Run training script
python -c "
from app.agents.rl_agent import get_rl_agent
import asyncio

async def train():
    agent = get_rl_agent()
    await agent.train(symbol='AAPL', episodes=1000)

asyncio.run(train())
"
```

### Setting Up Airflow DAGs

Airflow is configured to run daily analytics pipelines. To trigger manually:

```bash
# Access Airflow UI at http://localhost:8082
# Login: admin/admin

# Or trigger via CLI
docker-compose exec airflow-webserver airflow dags trigger daily_analytics_pipeline
```

---

## Production Deployment

### 1. Pre-Production Checklist

```bash
# ✓ Update environment variables
# ✓ Change default passwords
# ✓ Set DEBUG=false
# ✓ Configure SSL/TLS certificates
# ✓ Set up backup strategy
# ✓ Configure monitoring alerts
# ✓ Review security settings
# ✓ Set up log rotation
```

### 2. Environment-Specific Configuration

**Production `.env` file:**

```bash
# Security
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=<strong-random-key>
JWT_SECRET_KEY=<strong-random-key>

# CORS - Restrict to your domain
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Database - Use strong passwords
POSTGRES_PASSWORD=<strong-password>
MONGODB_PASSWORD=<strong-password>
NEO4J_PASSWORD=<strong-password>

# External services
OPENAI_API_KEY=<your-production-key>
```

### 3. SSL/TLS Setup

Add a reverse proxy (Nginx) for SSL:

**nginx.conf example:**

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;

    # Dashboard
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Cloud Deployment Options

#### AWS Deployment

```bash
# Using Docker Compose on EC2
# 1. Launch EC2 instance (t3.xlarge or larger)
# 2. Install Docker and Docker Compose
# 3. Clone repository
# 4. Configure security groups (ports: 8000, 8501, 3000)
# 5. Run docker-compose up -d

# Using ECS
# See cloud/aws/ecs-task-definition.json

# Using EKS (Kubernetes)
# See cloud/kubernetes/ directory
```

#### GCP Deployment

```bash
# Using Compute Engine
# Similar to AWS EC2 approach

# Using Cloud Run
gcloud run deploy finance-analytics \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure Deployment

```bash
# Using Azure Container Instances
az container create \
  --resource-group finance-rg \
  --name finance-analytics \
  --image youracr.azurecr.io/finance-analytics:latest \
  --dns-name-label finance-analytics \
  --ports 8000 8501
```

### 5. Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f cloud/kubernetes/

# Check deployment
kubectl get pods
kubectl get services

# Access logs
kubectl logs -f deployment/fastapi
```

### 6. Database Backup Strategy

```bash
# PostgreSQL backup
make backup-db

# Or manually
docker-compose exec postgres pg_dump -U financeuser financedb > backup_$(date +%Y%m%d).sql

# MongoDB backup
docker-compose exec mongodb mongodump \
  --username financeuser \
  --password financepass \
  --out /backup/$(date +%Y%m%d)

# Automate with cron
0 2 * * * cd /path/to/Finance-and-Trading && make backup-db
```

### 7. Scaling Services

**Horizontal Scaling (docker-compose):**

```bash
# Scale Spark workers
docker-compose up -d --scale spark-worker=4

# Scale data producers
docker-compose up -d --scale data-producers=3
```

**Kubernetes Scaling:**

```bash
# Scale API replicas
kubectl scale deployment fastapi --replicas=5

# Auto-scaling
kubectl autoscale deployment fastapi --min=2 --max=10 --cpu-percent=70
```

---

## Monitoring & Maintenance

### 1. Prometheus Metrics

Access Prometheus at http://localhost:9090

**Useful Queries:**

```promql
# API request rate
rate(http_requests_total[5m])

# API latency p95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Kafka consumer lag
kafka_consumer_lag_seconds

# Database connections
postgres_connections_active
```

### 2. Grafana Dashboards

Access Grafana at http://localhost:3000 (admin/admin)

**Available Dashboards:**
- System Health Overview
- API Performance
- Kafka Metrics
- Database Metrics
- ML Model Performance

### 3. Log Management

```bash
# View logs
make logs

# Search logs for errors
docker-compose logs | grep ERROR

# Export logs
docker-compose logs > app_logs_$(date +%Y%m%d).log
```

### 4. Health Monitoring Script

Create `monitor.sh`:

```bash
#!/bin/bash

SERVICES=("fastapi:8000" "streamlit:8501" "grafana:3000")

for service in "${SERVICES[@]}"; do
    name="${service%%:*}"
    port="${service##*:}"

    if curl -f http://localhost:$port/health >/dev/null 2>&1; then
        echo "✓ $name is healthy"
    else
        echo "✗ $name is DOWN"
        # Send alert (email, Slack, PagerDuty, etc.)
    fi
done
```

### 5. Maintenance Tasks

**Weekly:**
```bash
# Clean up Docker resources
make docker-prune

# Backup databases
make backup-db

# Check logs for errors
docker-compose logs --since 7d | grep -i error
```

**Monthly:**
```bash
# Update Docker images
docker-compose pull
docker-compose up -d

# Retrain ML models
# Access Airflow and trigger model_retraining_dag
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

```bash
# Check Docker is running
docker info

# Check available disk space
df -h

# Check available memory
free -h

# View detailed error logs
docker-compose logs <service-name>
```

#### 2. Port Already in Use

```bash
# Find process using port
sudo lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

#### 3. Database Connection Errors

```bash
# Restart databases
docker-compose restart postgres mongodb neo4j

# Check database logs
docker-compose logs postgres
docker-compose logs mongodb

# Verify network
docker network ls
docker network inspect finance-and-trading_finance-net
```

#### 4. Kafka Issues

```bash
# Restart Kafka and Zookeeper
docker-compose restart zookeeper kafka

# Check Kafka logs
docker-compose logs kafka

# Recreate topics
docker-compose exec kafka kafka-topics --delete --topic market_prices --bootstrap-server localhost:29092
docker-compose exec kafka kafka-topics --create --topic market_prices --bootstrap-server localhost:29092 --partitions 3 --replication-factor 1
```

#### 5. Out of Memory

```bash
# Check container memory usage
docker stats

# Increase Docker memory limit (Docker Desktop -> Settings -> Resources)

# Or limit individual services in docker-compose.yml:
services:
  spark-worker:
    deploy:
      resources:
        limits:
          memory: 2G
```

#### 6. Slow Performance

```bash
# Check container resource usage
docker stats

# Optimize PostgreSQL
docker-compose exec postgres psql -U financeuser -d financedb -c "VACUUM ANALYZE;"

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Restart services
docker-compose restart
```

#### 7. ML Model Errors

```bash
# Check if model exists
ls -la models/

# Retrain model
docker-compose exec fastapi python scripts/train_lora_model.py

# Check model status endpoint
curl http://localhost:8000/api/chat/model-status
```

### Getting Help

```bash
# Check comprehensive logs
docker-compose logs --tail=100

# Check system info
docker info
docker-compose version

# Test individual components
docker-compose up fastapi  # Start one service to debug
```

### Reset Everything

```bash
# DANGER: This will delete all data
make clean

# Or manually
docker-compose down -v
rm -rf backend/logs/*
rm -rf airflow/logs/*
docker system prune -a --volumes
```

---

## Testing

### Run Backend Tests

```bash
# Run all tests
make test

# Or manually
docker-compose exec fastapi pytest -v

# Run specific test file
docker-compose exec fastapi pytest backend/tests/test_api.py -v

# Run with coverage
docker-compose exec fastapi pytest --cov=app --cov-report=html
```

### Integration Tests

```bash
# API endpoint tests
pytest tests/integration/test_api_endpoints.py

# OCR tests
pytest backend/tests/unit/test_ocr.py
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test API
ab -n 1000 -c 10 http://localhost:8000/health

# Or use Locust
pip install locust
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

---

## Performance Optimization

### 1. Database Indexing

```sql
-- Add indexes for common queries
CREATE INDEX idx_prices_timestamp ON market_prices(timestamp);
CREATE INDEX idx_prices_symbol ON market_prices(symbol);
CREATE INDEX idx_news_timestamp ON news_events(timestamp);
```

### 2. Redis Caching

```python
# Cache frequently accessed data
# Already implemented in backend/app/api/market_data.py
```

### 3. Spark Optimization

```bash
# Adjust Spark worker resources
# Edit docker-compose.yml:
SPARK_WORKER_MEMORY=4G
SPARK_WORKER_CORES=4
```

### 4. API Rate Limiting

Already configured in `backend/app/config.py`:
```python
RATE_LIMIT_PER_MINUTE=60
```

---

## Security Best Practices

1. **Change Default Passwords**: Update all passwords in `.env`
2. **Enable HTTPS**: Use SSL certificates in production
3. **Restrict CORS**: Limit `CORS_ORIGINS` to your domain
4. **API Authentication**: All protected endpoints require JWT tokens
5. **Database Security**: Use strong passwords, enable SSL for connections
6. **Network Security**: Use Docker networks for service isolation
7. **Regular Updates**: Keep Docker images and dependencies updated
8. **Audit Logs**: Review logs regularly for suspicious activity
9. **Secrets Management**: Use Docker secrets or vault for sensitive data
10. **Firewall Rules**: Restrict access to only necessary ports

---

## Next Steps

1. **Customize the AI**: Fine-tune models with your domain-specific data
2. **Add Data Sources**: Integrate real market data APIs (Alpha Vantage, IEX Cloud)
3. **Extend Analytics**: Add custom indicators and strategies
4. **Mobile App**: Build mobile interface using the REST/GraphQL APIs
5. **Advanced ML**: Implement transformer models for time-series prediction
6. **Multi-Asset**: Extend support to crypto, forex, commodities
7. **Backtesting**: Use the backtesting framework for strategy validation
8. **Alerts**: Configure custom alert rules and notifications

---

## Useful Commands Reference

```bash
# Start
make up                    # Start all services
make logs                  # View all logs
make status               # Check service status

# Development
make shell-api            # Open shell in FastAPI container
make shell-spark          # Open shell in Spark container
make format               # Format code with Black
make lint                 # Lint code with Flake8

# Database
make db-migrate           # Run migrations
make backup-db            # Backup PostgreSQL
make restore-db FILE=x    # Restore database

# Testing
make test                 # Run tests
make check-health         # Health check all services

# Maintenance
make clean                # Remove all data
make docker-prune         # Clean Docker resources
make restart              # Restart services
```

---

## Support & Documentation

- **Project Docs**: See `docs/` directory
- **API Reference**: http://localhost:8000/docs
- **Getting Started**: `GETTING_STARTED.md`
- **CI/CD Guide**: `CI_CD_GUIDE.md`
- **Offline Analytics**: `VLM_AND_OFFLINE_GUIDE.md`
- **Smart Orchestration**: `SMART_ORCHESTRATION_GUIDE.md`

---

## License

MIT License - See LICENSE file for details

---

**Happy Trading! 📈**

For issues or questions, please create an issue on GitHub.
