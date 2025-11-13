#!/bin/bash

# Finance Analytics & Trading Co-Pilot - Quick Start Script

set -e

echo "=========================================="
echo "Finance Analytics & Trading Co-Pilot"
echo "Quick Start Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and add your API keys (optional but recommended)${NC}"
    echo ""
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
    echo ""
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p backend/logs
mkdir -p spark/data/checkpoints
mkdir -p airflow/logs
mkdir -p airflow/plugins
mkdir -p models
mkdir -p data/historical
mkdir -p data/news
mkdir -p data/social
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Pull Docker images
echo "Pulling Docker images (this may take a few minutes)..."
docker-compose pull
echo -e "${GREEN}✓ Images pulled${NC}"
echo ""

# Start services
echo "Starting all services..."
docker-compose up -d
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Wait for services to be ready
echo "Waiting for services to initialize (this may take 2-3 minutes)..."
echo "You can check the progress with: docker-compose logs -f"
sleep 10

# Check service health
echo ""
echo "Checking service health..."
sleep 5

# Function to check if service is responding
check_service() {
    local service=$1
    local url=$2
    local timeout=30
    local count=0

    while [ $count -lt $timeout ]; do
        if curl -s -o /dev/null -w "%{http_code}" $url | grep -q "200\|301\|302"; then
            echo -e "${GREEN}✓ $service is ready${NC}"
            return 0
        fi
        count=$((count + 1))
        sleep 1
    done

    echo -e "${YELLOW}⚠️  $service may still be initializing${NC}"
    return 1
}

# Check key services
check_service "FastAPI" "http://localhost:8000/health"
check_service "Streamlit Dashboard" "http://localhost:8501"
check_service "Grafana" "http://localhost:3000/api/health"

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "🌐 Access the services at:"
echo ""
echo "   📊 Dashboard:        http://localhost:8501"
echo "   🚀 API Docs:         http://localhost:8000/docs"
echo "   📈 Grafana:          http://localhost:3000 (admin/admin)"
echo "   🔬 MLflow:           http://localhost:5000"
echo "   🔄 Airflow:          http://localhost:8082"
echo ""
echo "📚 Documentation: README.md"
echo "🐛 Logs: docker-compose logs -f"
echo "🛑 Stop: docker-compose down"
echo ""
echo "=========================================="
echo -e "${GREEN}Happy Trading! 📈${NC}"
echo "=========================================="
