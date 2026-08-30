import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success_qa(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "qa", "password": "ChangeMe123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["user"]["username"] == "qa"
    assert data["data"]["user"]["role"] == "QA"


@pytest.mark.asyncio
async def test_login_success_requester(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "requester", "password": "ChangeMe123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["user"]["username"] == "requester"
    assert data["data"]["user"]["role"] == "Requester"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "qa", "password": "WrongPassword!"}
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["message"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "ChangeMe123!"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_unauthenticated(async_client: AsyncClient):
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(async_client: AsyncClient, qa_headers: dict):
    response = await async_client.get("/api/v1/auth/me", headers=qa_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["username"] == "qa"
    assert data["data"]["role"] == "QA"


@pytest.mark.asyncio
async def test_refresh_token_success(async_client: AsyncClient):
    # 1. Login to get refresh token
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "qa", "password": "ChangeMe123!"}
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    # 2. Call refresh endpoint
    refresh_resp = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()["data"]


@pytest.mark.asyncio
async def test_change_password_success(async_client: AsyncClient, qa_headers: dict):
    response = await async_client.post(
        "/api/v1/auth/change-password",
        headers=qa_headers,
        json={"current_password": "ChangeMe123!", "new_password": "NewSecretPassword123!"}
    )
    assert response.status_code == 200

    # Verify login with new password
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "qa", "password": "NewSecretPassword123!"}
    )
    assert login_resp.status_code == 200
