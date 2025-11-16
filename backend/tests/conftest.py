"""
Pytest configuration and fixtures for Finance Analytics tests
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
import os

# Set test environment
os.environ["TESTING"] = "true"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"

from app.main import app
from app.database import get_postgres_session


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator:
    """Synchronous test client"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Asynchronous test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session():
    """Database session for testing"""
    async with get_postgres_session() as session:
        yield session


@pytest.fixture
def sample_stock_data():
    """Sample stock price data for testing"""
    return {
        "symbol": "AAPL",
        "open": 150.0,
        "high": 155.0,
        "low": 149.0,
        "close": 154.0,
        "volume": 1000000
    }


@pytest.fixture
def sample_news_article():
    """Sample news article for testing"""
    return {
        "headline": "Apple Announces Record Earnings",
        "content": "Apple Inc. reported record quarterly earnings...",
        "source": "TestNews",
        "symbol": "AAPL",
        "sentiment_score": 0.8,
        "sentiment_label": "positive"
    }


@pytest.fixture
def sample_trading_signal():
    """Sample trading signal for testing"""
    return {
        "symbol": "TSLA",
        "action": "BUY",
        "confidence": 0.85,
        "target_price": 250.0,
        "stop_loss": 230.0,
        "rationale": "Strong momentum and positive sentiment"
    }
