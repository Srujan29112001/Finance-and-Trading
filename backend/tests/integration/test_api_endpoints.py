"""
Integration tests for API endpoints
"""

import pytest
from httpx import AsyncClient


class TestMarketDataAPI:
    """Test market data endpoints"""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint"""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_api_info(self, async_client: AsyncClient):
        """Test API info endpoint"""
        response = await async_client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "capabilities" in data
        assert data["capabilities"]["real_time_data"] is True
        assert data["capabilities"]["ai_assistant"] is True

    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client: AsyncClient):
        """Test root endpoint"""
        response = await async_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Finance Analytics & Trading Co-Pilot API"
        assert "endpoints" in data


class TestGraphQLAPI:
    """Test GraphQL endpoints"""

    @pytest.mark.asyncio
    async def test_graphql_endpoint_exists(self, async_client: AsyncClient):
        """Test that GraphQL endpoint is accessible"""
        # GraphQL introspection query
        query = """
        {
            __schema {
                queryType {
                    name
                }
            }
        }
        """

        response = await async_client.post(
            "/graphql",
            json={"query": query}
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestOCRAPI:
    """Test OCR endpoints"""

    @pytest.mark.asyncio
    async def test_ocr_health_check(self, async_client: AsyncClient):
        """Test OCR health check"""
        response = await async_client.get("/api/ocr/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
