import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_health(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "healthy"
    assert json_data["data"]["database"] == "UP"
    assert json_data["data"]["email"] == "UP"
    assert json_data["data"]["version"] == "2.0.0"


@pytest.mark.asyncio
async def test_liveness_probe(async_client: AsyncClient):
    response = await async_client.get("/health/live")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "ALIVE"


@pytest.mark.asyncio
async def test_readiness_probe(async_client: AsyncClient):
    response = await async_client.get("/health/ready")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "READY"
