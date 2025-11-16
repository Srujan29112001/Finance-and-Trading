"""
Finance Analytics & Trading Co-Pilot - Main FastAPI Application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys
from datetime import datetime

# Prometheus monitoring
from prometheus_fastapi_instrumentator import Instrumentator

# Import routers
from app.api import market_data, analysis, chat, trading, alerts, portfolio, vlm, offline_analytics, ocr, auth_api

# Import GraphQL (Strawberry-based)
from strawberry.fastapi import GraphQLRouter
from app.graphql_schema import schema

# Import database
from app.database import init_db, close_db

# Import config
from app.config import settings

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="DEBUG"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Finance Analytics & Trading Co-Pilot API...")
    await init_db()
    logger.info("Database connections initialized")

    yield

    # Shutdown
    logger.info("Shutting down Finance Analytics & Trading Co-Pilot API...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="Finance Analytics & Trading Co-Pilot API",
    description="""
    Real-Time Finance Analytics Platform with AI-Powered Trading Assistant

    ## Features

    * **Real-time Market Data**: Stream live market data via Kafka
    * **AI Assistant**: LangChain-powered conversational analytics with RAG
    * **Trading Signals**: RL-based trading recommendations
    * **Risk Analytics**: Portfolio risk metrics and behavioral analysis
    * **GraphQL & REST**: Flexible querying with both interfaces
    * **Real-time Alerts**: WebSocket-based market anomaly notifications
    * **OCR Processing**: Extract text and financial data from PDFs
    * **Authentication**: JWT-based security for protected endpoints

    ## Tech Stack

    - Apache Kafka for streaming
    - Apache Spark for processing
    - PostgreSQL, MongoDB, Neo4j, Qdrant for storage
    - LangChain with RAG/GraphRAG for AI
    - Reinforcement Learning for trading signals
    - LoRA/QLoRA for domain-specific fine-tuning
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus instrumentation
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/health"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app).expose(app)

# Include routers
app.include_router(auth_api.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(market_data.router, prefix="/api/market", tags=["Market Data"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(chat.router, prefix="/api/chat", tags=["AI Chat"])
app.include_router(trading.router, prefix="/api/trading", tags=["Trading"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(vlm.router, prefix="/api/vlm", tags=["VLM (Vision)"])
app.include_router(offline_analytics.router, prefix="/api/offline", tags=["Offline Analytics"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR"])

# Include GraphQL router (Strawberry)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql", tags=["GraphQL"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Finance Analytics & Trading Co-Pilot API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "graphql": "/graphql",
            "graphiql": "/graphql (interactive)",
            "health": "/health",
            "metrics": "/metrics",
            "auth": "/api/auth (JWT authentication)",
            "market_data": "/api/market",
            "analysis": "/api/analysis",
            "chat": "/api/chat",
            "trading": "/api/trading",
            "alerts": "/api/alerts",
            "portfolio": "/api/portfolio",
            "vlm": "/api/vlm",
            "offline": "/api/offline",
            "ocr": "/api/ocr"
        },
        "authentication": {
            "type": "JWT Bearer Token",
            "login": "/api/auth/token",
            "test_users": {
                "admin": "admin123 (full access)",
                "trader": "trader123 (trading access)",
                "analyst": "analyst123 (analysis access)"
            }
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "finance-analytics-api"
    }


@app.get("/api/info")
async def api_info():
    """API information and capabilities."""
    return {
        "capabilities": {
            "real_time_data": True,
            "ai_assistant": True,
            "rl_trading": True,
            "risk_analytics": True,
            "sentiment_analysis": True,
            "graph_rag": True,
            "websocket_alerts": True,
            "ocr_processing": True,
            "authentication": True,
            "backtesting": True
        },
        "data_sources": ["Kafka", "PostgreSQL", "MongoDB", "Neo4j", "Qdrant"],
        "ml_models": ["LLM (LoRA/QLoRA)", "RL Agent (DQN)", "Sentiment Analysis", "VLM (Vision)"],
        "api_types": ["REST", "GraphQL", "WebSocket"]
    }


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")


manager = ConnectionManager()


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time market alerts."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive any client messages
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket, symbols: str = ""):
    """WebSocket endpoint for real-time price updates."""
    await websocket.accept()
    try:
        symbol_list = symbols.split(",") if symbols else ["AAPL", "TSLA", "GOOGL"]
        logger.info(f"Client subscribed to price updates for: {symbol_list}")

        while True:
            data = await websocket.receive_text()
            # Echo back or handle client commands
            await websocket.send_json({"status": "subscribed", "symbols": symbol_list})
    except WebSocketDisconnect:
        logger.info("Price WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Price WebSocket error: {e}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
