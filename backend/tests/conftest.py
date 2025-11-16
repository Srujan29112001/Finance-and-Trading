"""
Pytest configuration and fixtures for Finance Analytics tests

Provides test fixtures for database, API client, and common test data.
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["TESTING"] = "true"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"

from app.main import app
from app.database import Base, get_db, get_postgres_session


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh in-memory database for each test.
    Uses SQLite for fast, isolated testing.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session():
    """Database session for testing with real Postgres (integration tests)"""
    async with get_postgres_session() as session:
        yield session


@pytest.fixture
def client() -> Generator:
    """Synchronous test client for simple API tests"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Asynchronous HTTP client for testing API endpoints.
    Uses test_db for database isolation.
    """
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


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
