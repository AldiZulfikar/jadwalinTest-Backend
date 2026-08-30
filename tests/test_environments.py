import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_environments(async_client: AsyncClient):
    response = await async_client.get("/environments")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 2
    codes = [env["code"] for env in json_data["data"]]
    assert "PERF01" in codes
    assert "PERF02" in codes
