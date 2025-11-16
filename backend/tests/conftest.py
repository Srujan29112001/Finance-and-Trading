"""
Pytest configuration and fixtures

Provides test fixtures for database, API client, and common test data.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db


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
    Create a fresh database for each test.
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
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing API endpoints.
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
        "open": 150.00,
        "high": 152.50,
        "low": 149.00,
        "close": 151.00,
        "volume": 1000000
    }


@pytest.fixture
def sample_news_data():
    """Sample news article for testing"""
    return {
        "symbol": "AAPL",
        "headline": "Apple announces new product",
        "content": "Apple Inc. today announced a groundbreaking new product...",
        "source": "Reuters",
        "sentiment": 0.8
    }


@pytest.fixture
def sample_trading_signal():
    """Sample trading signal for testing"""
    return {
        "symbol": "AAPL",
        "action": "BUY",
        "confidence": 0.85,
        "target_price": 155.00,
        "stop_loss": 148.00,
        "reasoning": "Strong momentum and positive sentiment"
    }
