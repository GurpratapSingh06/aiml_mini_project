"""
VEDANTA Integration Tests — FastAPI v1 Endpoints
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_ping_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health/ping")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app"] == "vedanta"


@pytest.mark.asyncio
async def test_search_suggestions_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/search/suggestions?q=computer")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


@pytest.mark.asyncio
async def test_search_query_execution():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/search",
            json={
                "query": "Who is the HOD of Computer Engineering?",
                "top_k": 5,
                "include_evidence": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "answer" in data
        assert "verification_status" in data
        assert "citations" in data


@pytest.mark.asyncio
async def test_crawl_validation_blocks_external_url():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/crawl/start",
            json={
                "start_url": "https://malicious-external-site.com",
                "max_depth": 2,
                "max_pages": 50,
            },
        )
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"].lower()
