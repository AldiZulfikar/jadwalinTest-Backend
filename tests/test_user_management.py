import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_qa_list_users_with_filters(async_client: AsyncClient, qa_headers: dict):
    # List all users
    response = await async_client.get("/api/v1/users", headers=qa_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["data"]["items"]) >= 2

    # Filter by role QA
    role_resp = await async_client.get("/api/v1/users?role=QA", headers=qa_headers)
    assert role_resp.status_code == 200
    items = role_resp.json()["data"]["items"]
    assert all(u["role"] == "QA" for u in items)

    # Filter by is_active True
    active_resp = await async_client.get("/api/v1/users?is_active=true", headers=qa_headers)
    assert active_resp.status_code == 200
    assert all(u["is_active"] is True for u in active_resp.json()["data"]["items"])

    # Search query
    search_resp = await async_client.get("/api/v1/users?search=qa", headers=qa_headers)
    assert search_resp.status_code == 200
    assert len(search_resp.json()["data"]["items"]) >= 1


@pytest.mark.asyncio
async def test_requester_forbidden_on_all_user_endpoints(async_client: AsyncClient, requester_headers: dict):
    # GET list
    resp1 = await async_client.get("/api/v1/users", headers=requester_headers)
    assert resp1.status_code == 403

    # POST create
    resp2 = await async_client.post(
        "/api/v1/users",
        headers=requester_headers,
        json={
            "username": "hacker",
            "password": "Password123!",
            "full_name": "Hacker User",
            "email": "hacker@example.com",
            "role": "QA"
        }
    )
    assert resp2.status_code == 403

    # PUT edit
    fake_id = str(uuid.uuid4())
    resp3 = await async_client.put(
        f"/api/v1/users/{fake_id}",
        headers=requester_headers,
        json={"full_name": "Hacked Name"}
    )
    assert resp3.status_code == 403

    # PATCH status
    resp4 = await async_client.patch(
        f"/api/v1/users/{fake_id}/status",
        headers=requester_headers,
        json={"is_active": False}
    )
    assert resp4.status_code == 403

    # POST reset password
    resp5 = await async_client.post(
        f"/api/v1/users/{fake_id}/reset-password",
        headers=requester_headers,
        json={"new_password": "NewSecretPassword123!"}
    )
    assert resp5.status_code == 403


@pytest.mark.asyncio
async def test_qa_create_user_success(async_client: AsyncClient, qa_headers: dict):
    unique_username = f"new_dev_{uuid.uuid4().hex[:6]}"
    unique_email = f"{unique_username}@company.com"

    create_resp = await async_client.post(
        "/api/v1/users",
        headers=qa_headers,
        json={
            "username": unique_username,
            "password": "SecurePassword123!",
            "full_name": "New Developer Account",
            "email": unique_email,
            "role": "Requester",
            "is_active": True
        }
    )
    assert create_resp.status_code == 201
    data = create_resp.json()["data"]
    assert data["username"] == unique_username
    assert data["email"] == unique_email
    assert data["role"] == "Requester"
    assert data["is_active"] is True
    assert "password_hash" not in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_create_user_validations(async_client: AsyncClient, qa_headers: dict):
    # Duplicate username
    resp1 = await async_client.post(
        "/api/v1/users",
        headers=qa_headers,
        json={
            "username": "qa",  # Existing seed username
            "password": "Password123!",
            "full_name": "Duplicate QA",
            "email": "diff_email@example.com",
            "role": "QA"
        }
    )
    assert resp1.status_code == 400
    assert "already taken" in resp1.json()["message"]

    # Duplicate email
    resp2 = await async_client.post(
        "/api/v1/users",
        headers=qa_headers,
        json={
            "username": f"user_{uuid.uuid4().hex[:6]}",
            "password": "Password123!",
            "full_name": "Duplicate Email QA",
            "email": "qa.manager@example.com",  # Existing seed email
            "role": "QA"
        }
    )
    assert resp2.status_code == 400
    assert "already registered" in resp2.json()["message"]

    # Short password (< 8 chars)
    resp3 = await async_client.post(
        "/api/v1/users",
        headers=qa_headers,
        json={
            "username": f"user_{uuid.uuid4().hex[:6]}",
            "password": "short",
            "full_name": "Short Password User",
            "email": f"short_{uuid.uuid4().hex[:6]}@example.com",
            "role": "Requester"
        }
    )
    assert resp3.status_code == 422


@pytest.mark.asyncio
async def test_qa_cannot_deactivate_self(async_client: AsyncClient, qa_headers: dict):
    # Get me to obtain QA user_id
    me_resp = await async_client.get("/api/v1/auth/me", headers=qa_headers)
    assert me_resp.status_code == 200
    qa_id = me_resp.json()["data"]["id"]

    # Attempt to deactivate self via PATCH /status
    status_resp = await async_client.patch(
        f"/api/v1/users/{qa_id}/status",
        headers=qa_headers,
        json={"is_active": False}
    )
    assert status_resp.status_code == 400
    assert "cannot deactivate your own account" in status_resp.json()["message"].lower()

    # Attempt to deactivate self via PUT
    put_resp = await async_client.put(
        f"/api/v1/users/{qa_id}",
        headers=qa_headers,
        json={"is_active": False}
    )
    assert put_resp.status_code == 400
    assert "cannot deactivate your own account" in put_resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_last_active_qa_cannot_be_deactivated(async_client: AsyncClient, qa_headers: dict):
    # Create a second QA user
    qa2_username = f"qa2_{uuid.uuid4().hex[:6]}"
    create_qa2 = await async_client.post(
        "/api/v1/users",
        headers=qa_headers,
        json={
            "username": qa2_username,
            "password": "Password123!",
            "full_name": "Second QA Lead",
            "email": f"{qa2_username}@company.com",
            "role": "QA"
        }
    )
    assert create_qa2.status_code == 201
    qa2_id = create_qa2.json()["data"]["id"]

    # Now deactivating QA2 is allowed because primary QA is active
    deactivate_qa2 = await async_client.patch(
        f"/api/v1/users/{qa2_id}/status",
        headers=qa_headers,
        json={"is_active": False}
    )
    assert deactivate_qa2.status_code == 200
    assert deactivate_qa2.json()["data"]["is_active"] is False


@pytest.mark.asyncio
async def test_user_deactivation_and_login_prevention(async_client: AsyncClient, qa_headers: dict):
    # Create test user to deactivate
    username = f"temp_dev_{uuid.uuid4().hex[:6]}"
    password = "TempPassword123!"
    create_resp = await async_client.post(
        "/api/v1/users",
        headers=qa_headers,
        json={
            "username": username,
            "password": password,
            "full_name": "Temporary Dev",
            "email": f"{username}@company.com",
            "role": "Requester"
        }
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["data"]["id"]

    # Verify user can login before deactivation
    login_before = await async_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password}
    )
    assert login_before.status_code == 200

    # Deactivate user
    deactivate_resp = await async_client.patch(
        f"/api/v1/users/{user_id}/status",
        headers=qa_headers,
        json={"is_active": False}
    )
    assert deactivate_resp.status_code == 200

    # Verify login after deactivation returns 401 Account is inactive
    login_after = await async_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password}
    )
    assert login_after.status_code == 401
    assert "inactive" in login_after.json()["message"].lower()

    # Reactivate user
    reactivate_resp = await async_client.patch(
        f"/api/v1/users/{user_id}/status",
        headers=qa_headers,
        json={"is_active": True}
    )
    assert reactivate_resp.status_code == 200

    # Verify login succeeds after reactivation
    login_reactivated = await async_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password}
    )
    assert login_reactivated.status_code == 200


@pytest.mark.asyncio
async def test_qa_reset_password_and_login(async_client: AsyncClient, qa_headers: dict):
    # Create test user
    username = f"reset_test_{uuid.uuid4().hex[:6]}"
    old_pass = "OldPassword123!"
    new_pass = "NewSecretPassword123!"

    create_resp = await async_client.post(
        "/api/v1/users",
        headers=qa_headers,
        json={
            "username": username,
            "password": old_pass,
            "full_name": "Reset Target User",
            "email": f"{username}@company.com",
            "role": "Requester"
        }
    )
    user_id = create_resp.json()["data"]["id"]

    # Reset password as QA
    reset_resp = await async_client.post(
        f"/api/v1/users/{user_id}/reset-password",
        headers=qa_headers,
        json={"new_password": new_pass}
    )
    assert reset_resp.status_code == 200

    # Login with old password should fail
    old_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": old_pass}
    )
    assert old_login.status_code == 401

    # Login with new password should succeed
    new_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": new_pass}
    )
    assert new_login.status_code == 200
    assert new_login.json()["success"] is True
