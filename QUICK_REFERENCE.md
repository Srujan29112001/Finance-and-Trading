# ⚡ Quick Reference Guide

## 30-Second Start

```bash
git clone https://github.com/Srujan29112001/Finance-and-Trading.git
cd Finance-and-Trading
./quickstart.sh
docker-compose up -d
```

Access: http://localhost:8501

---

## Essential Commands

### Start/Stop

```bash
docker-compose up -d           # Start all services
docker-compose down            # Stop all services
docker-compose restart         # Restart all services
make up                        # Start (alternative)
make down                      # Stop (alternative)
```

### Logs

```bash
docker-compose logs -f         # All logs
docker-compose logs -f fastapi # API logs
docker-compose logs -f streamlit # Dashboard logs
make logs                      # All logs (Makefile)
make logs-api                  # API logs (Makefile)
```

### Status

```bash
docker-compose ps              # Service status
make status                    # Service status (Makefile)
make check-health              # Health check all services
```

---

## Service URLs

| Service | URL | Login |
|---------|-----|-------|
| Dashboard | http://localhost:8501 | None |
| API Docs | http://localhost:8000/docs | JWT Token |
| GraphQL | http://localhost:8000/graphql | JWT Token |
| Grafana | http://localhost:3000 | admin/admin |
| MLflow | http://localhost:5000 | None |
| Airflow | http://localhost:8082 | admin/admin |
| Spark UI | http://localhost:8080 | None |
| Neo4j | http://localhost:7474 | neo4j/financepass |

---

## Quick API Tests

### Get JWT Token

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### Test Market Data

```bash
# Replace YOUR_TOKEN with actual token
curl http://localhost:8000/api/market/latest/AAPL \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test AI Chat

```bash
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "What is AAPL price?", "symbol": "AAPL"}'
```

---

## Default Credentials

### Test Users
- Admin: `admin` / `admin123`
- Trader: `trader` / `trader123`
- Analyst: `analyst` / `analyst123`

### Services
- Grafana: `admin` / `admin`
- Airflow: `admin` / `admin`
- Neo4j: `neo4j` / `financepass`
- PostgreSQL: `financeuser` / `financepass`
- MongoDB: `financeuser` / `financepass`

**⚠️ Change these in production!**

---

## Common Issues

### Port Already in Use

```bash
# Find what's using the port
sudo lsof -i :8000

# Kill it
kill -9 <PID>
```

### Services Won't Start

```bash
# Check Docker
docker info

# Check disk space
df -h

# View errors
docker-compose logs <service-name>
```

### Reset Everything

```bash
docker-compose down -v
docker system prune -a
make clean
```

---

## Database Commands

### PostgreSQL

```bash
# Access database
docker-compose exec postgres psql -U financeuser -d financedb

# Run query
docker-compose exec postgres psql -U financeuser -d financedb -c "SELECT * FROM market_prices LIMIT 5;"

# Backup
make backup-db
```

### MongoDB

```bash
# Access MongoDB shell
docker-compose exec mongodb mongosh -u financeuser -p financepass

# List databases
docker-compose exec mongodb mongosh -u financeuser -p financepass --eval "show dbs"
```

### Neo4j

```bash
# Access Cypher shell
docker-compose exec neo4j cypher-shell -u neo4j -p financepass

# Example query
docker-compose exec neo4j cypher-shell -u neo4j -p financepass "MATCH (n) RETURN n LIMIT 5;"
```

### Redis

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Clear cache
docker-compose exec redis redis-cli FLUSHALL
```

---

## Kafka Commands

### List Topics

```bash
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:29092
```

### View Messages

```bash
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:29092 \
  --topic market_prices \
  --from-beginning \
  --max-messages 10
```

### Create Topic

```bash
docker-compose exec kafka kafka-topics --create \
  --topic my_topic \
  --bootstrap-server localhost:29092 \
  --partitions 3 \
  --replication-factor 1
```

---

## Testing

### Run Tests

```bash
make test                                    # All tests
docker-compose exec fastapi pytest -v       # Backend tests
docker-compose exec fastapi pytest --cov    # With coverage
```

### Shell Access

```bash
make shell-api                # FastAPI container
make shell-spark              # Spark container
docker-compose exec fastapi bash  # Alternative
```

---

## Maintenance

### Daily

```bash
make check-health             # Verify all services
docker-compose logs | grep ERROR  # Check for errors
```

### Weekly

```bash
make backup-db                # Backup databases
make docker-prune             # Clean Docker resources
```

### Monthly

```bash
docker-compose pull           # Update images
docker-compose up -d          # Apply updates
```

---

## Performance Monitoring

### Resource Usage

```bash
docker stats                  # Container resource usage
docker-compose top            # Process list
```

### Prometheus Queries

Access http://localhost:9090

```promql
rate(http_requests_total[5m])                                    # Request rate
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))  # P95 latency
kafka_consumer_lag_seconds                                       # Kafka lag
postgres_connections_active                                      # DB connections
```

---

## Troubleshooting Checklist

- [ ] Docker is running: `docker info`
- [ ] Enough disk space: `df -h`
- [ ] Enough memory: `free -h`
- [ ] No port conflicts: `sudo lsof -i :8000`
- [ ] Services are up: `docker-compose ps`
- [ ] Logs show no errors: `docker-compose logs | grep ERROR`
- [ ] Databases are healthy: `make check-health`
- [ ] Environment file exists: `ls -la .env`

---

## Configuration Files

```
.env                          # Environment variables
docker-compose.yml            # Service orchestration
backend/requirements.txt      # Python dependencies (backend)
frontend/requirements.txt     # Python dependencies (frontend)
pyproject.toml                # Project metadata & tools
Makefile                      # Common commands
sql/init.sql                  # Database schema
monitoring/prometheus.yml     # Monitoring config
```

---

## Useful Makefile Commands

```bash
make help                     # Show all commands
make setup                    # Initial setup
make up                       # Start services
make down                     # Stop services
make restart                  # Restart services
make status                   # Check status
make logs                     # View logs
make test                     # Run tests
make clean                    # Reset everything
make backup-db                # Backup database
make check-health             # Health check
make docker-prune             # Clean Docker
make format                   # Format code
make lint                     # Lint code
```

---

## Environment Variables

Essential `.env` variables:

```bash
# Required in Production
SECRET_KEY=<generate-strong-key>
JWT_SECRET_KEY=<generate-strong-key>
DEBUG=false
ENVIRONMENT=production

# Optional (enables features)
OPENAI_API_KEY=sk-...         # For GPT-4 chat
HF_TOKEN=hf_...               # For offline LLMs

# Database (use strong passwords)
POSTGRES_PASSWORD=<strong-password>
MONGODB_PASSWORD=<strong-password>
NEO4J_PASSWORD=<strong-password>
```

Generate secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Getting Help

1. Check logs: `docker-compose logs <service>`
2. Check status: `docker-compose ps`
3. Review docs: `DEPLOYMENT_GUIDE.md`
4. Check API: http://localhost:8000/docs
5. GitHub Issues: [Create Issue](https://github.com/Srujan29112001/Finance-and-Trading/issues)

---

## Next Steps After Setup

1. ✅ Access dashboard at http://localhost:8501
2. ✅ Get JWT token from API
3. ✅ Test market data endpoints
4. ✅ Try AI chat feature
5. ✅ View Grafana dashboards
6. ✅ Check Kafka data flow
7. ✅ Explore GraphQL API
8. ✅ Review Airflow DAGs

---

**Full Documentation**: See `DEPLOYMENT_GUIDE.md`
