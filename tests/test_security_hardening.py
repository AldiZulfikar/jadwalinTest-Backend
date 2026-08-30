import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_x_request_id_correlation_middleware(async_client: AsyncClient):
    """Verify X-Request-ID middleware echoes or generates correlation ID."""
    # 1. Custom request ID provided
    custom_id = "req-12345-test-uuid"
    response = await async_client.get("/api/v1/health/live", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id

    # 2. Generated request ID when header omitted
    response_auto = await async_client.get("/api/v1/health/live")
    assert response_auto.status_code == 200
    assert "X-Request-ID" in response_auto.headers
    assert len(response_auto.headers["X-Request-ID"]) > 10


@pytest.mark.asyncio
async def test_security_response_headers(async_client: AsyncClient):
    """Verify standard HTTP security headers are attached to all API responses."""
    response = await async_client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"


@pytest.mark.asyncio
async def test_liveness_and_readiness_health_probes(async_client: AsyncClient):
    """Verify OpenShift Liveness and Readiness probes return correct payloads."""
    # 1. Liveness probe
    live_resp = await async_client.get("/api/v1/health/live")
    assert live_resp.status_code == 200
    live_data = live_resp.json()
    assert live_data["success"] is True
    assert live_data["data"]["status"] == "ALIVE"

    # 2. Readiness probe
    ready_resp = await async_client.get("/api/v1/health/ready")
    assert ready_resp.status_code == 200
    ready_data = ready_resp.json()
    assert ready_data["success"] is True
    assert ready_data["data"]["status"] == "READY"
