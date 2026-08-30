import pytest
import uuid
from datetime import date, timedelta
from httpx import AsyncClient

SEED_TEST_ENV_ID = "11111111-1111-1111-1111-111111111111"


@pytest.mark.asyncio
async def test_qa_can_approve_booking(async_client: AsyncClient, qa_headers: dict):
    # 1. Create booking
    future_date_str = (date.today() + timedelta(days=5)).isoformat()
    create_resp = await async_client.post(
        "/api/v1/bookings",
        headers=qa_headers,
        json={
            "project_name": "RBAC Test Project",
            "application_name": "App QA",
            "pic_name": "QA Lead",
            "pic_email": "qa.manager@example.com",
            "booking_date": future_date_str,
            "start_time": "10:00:00",
            "end_time": "12:00:00",
            "environment_id": SEED_TEST_ENV_ID,
            "test_type": "LoadTest"
        }
    )
    assert create_resp.status_code == 201
    booking_id = create_resp.json()["data"]["id"]

    # 2. Approve booking as QA
    approve_resp = await async_client.post(
        f"/api/v1/bookings/{booking_id}/approve",
        headers=qa_headers,
        json={"approved_by": "QA Manager"}
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["data"]["status"] == "Approved"


@pytest.mark.asyncio
async def test_requester_forbidden_to_approve_booking(
    async_client: AsyncClient,
    qa_headers: dict,
    requester_headers: dict
):
    # 1. Create booking
    future_date_str = (date.today() + timedelta(days=6)).isoformat()
    create_resp = await async_client.post(
        "/api/v1/bookings",
        headers=qa_headers,
        json={
            "project_name": "RBAC Test Project 2",
            "application_name": "App Requester",
            "pic_name": "Dev Person",
            "pic_email": "requester@example.com",
            "booking_date": future_date_str,
            "start_time": "14:00:00",
            "end_time": "16:00:00",
            "environment_id": SEED_TEST_ENV_ID,
            "test_type": "StressTest"
        }
    )
    booking_id = create_resp.json()["data"]["id"]

    # 2. Attempt to approve booking as Requester -> Must return HTTP 403 Forbidden
    approve_resp = await async_client.post(
        f"/api/v1/bookings/{booking_id}/approve",
        headers=requester_headers,
        json={"approved_by": "Hacker Requester"}
    )
    assert approve_resp.status_code == 403
    assert "Forbidden" in approve_resp.json()["message"]


@pytest.mark.asyncio
async def test_requester_forbidden_user_management(async_client: AsyncClient, requester_headers: dict):
    response = await async_client.get("/api/v1/users", headers=requester_headers)
    assert response.status_code == 403
    assert "Forbidden" in response.json()["message"]


@pytest.mark.asyncio
async def test_qa_can_access_user_management(async_client: AsyncClient, qa_headers: dict):
    response = await async_client.get("/api/v1/users", headers=qa_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["data"]["items"]) >= 2
