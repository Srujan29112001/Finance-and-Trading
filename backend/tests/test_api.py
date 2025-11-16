"""
API Endpoint Tests

Tests for all API endpoints including market data, trading, analysis, and chat.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime


class TestMarketDataAPI:
    """Test market data endpoints"""

    @pytest.mark.asyncio
    async def test_get_latest_price(self, client: AsyncClient):
        """Test getting latest price for a symbol"""
        response = await client.get("/api/market/latest/AAPL")
        assert response.status_code in [200, 404]  # 404 if no data in test DB

    @pytest.mark.asyncio
    async def test_get_market_summary(self, client: AsyncClient):
        """Test getting market summary"""
        response = await client.get("/api/market/summary/AAPL")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_price_history(self, client: AsyncClient):
        """Test getting price history"""
        response = await client.get("/api/market/history/AAPL?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAuthAPI:
    """Test authentication endpoints"""

    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(self, client: AsyncClient):
        """Test login with valid credentials"""
        response = await client.post(
            "/api/auth/token",
            data={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials"""
        response = await client.post(
            "/api/auth/token",
            data={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient):
        """Test getting current user info"""
        # First login
        login_response = await client.post(
            "/api/auth/token",
            data={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        # Then get user info
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"


class TestTradingAPI:
    """Test trading endpoints"""

    @pytest.mark.asyncio
    async def test_get_trading_signals(self, client: AsyncClient):
        """Test getting trading signals"""
        response = await client.get("/api/trading/signals/AAPL?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_quick_backtest(self, client: AsyncClient):
        """Test quick backtest endpoint"""
        response = await client.get("/api/trading/backtest/quick/AAPL?days=7")
        # May fail if no data, so check for either 200 or 400
        assert response.status_code in [200, 400]


class TestChatAPI:
    """Test AI chat endpoints"""

    @pytest.mark.asyncio
    async def test_model_status(self, client: AsyncClient):
        """Test getting model status"""
        response = await client.get("/api/chat/model-status")
        assert response.status_code == 200
        data = response.json()
        assert "llm_available" in data


class TestGraphQLAPI:
    """Test GraphQL endpoint"""

    @pytest.mark.asyncio
    async def test_graphql_introspection(self, client: AsyncClient):
        """Test GraphQL introspection query"""
        query = """
        query {
            __schema {
                types {
                    name
                }
            }
        }
        """
        response = await client.post(
            "/graphql",
            json={"query": query}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestHealthEndpoints:
    """Test health and info endpoints"""

    @pytest.mark.asyncio
    async def test_root(self, client: AsyncClient):
        """Test root endpoint"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"

    @pytest.mark.asyncio
    async def test_health(self, client: AsyncClient):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_api_info(self, client: AsyncClient):
        """Test API info endpoint"""
        response = await client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "capabilities" in data
        assert "ml_models" in data
