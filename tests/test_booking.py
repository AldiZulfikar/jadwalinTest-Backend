import pytest
import uuid
from datetime import date, timedelta
from httpx import AsyncClient

SEED_TEST_ENV_ID = "11111111-1111-1111-1111-111111111111"
SEED_TEST_ENV_2_ID = "22222222-2222-2222-2222-222222222222"


@pytest.mark.asyncio
async def test_create_booking_success(async_client: AsyncClient, qa_headers: dict):
    future_date = date.today() + timedelta(days=5)
    future_date_str = future_date.isoformat()
    date_formatted = future_date.strftime("%Y%m%d")

    payload = {
        "project_name": "Core Banking",
        "application_name": "Payment Gateway",
        "pic_name": "Jane Smith",
        "pic_email": "jane.smith@example.com",
        "booking_date": future_date_str,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "environment_id": SEED_TEST_ENV_ID,
        "test_type": "LoadTest",
        "description": "Quarterly load testing"
    }

    response = await async_client.post("/api/v1/bookings", json=payload, headers=qa_headers)
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["message"] == "Booking created successfully."
    assert "id" in json_data["data"]
    assert json_data["data"]["project_name"] == "Core Banking"
    assert json_data["data"]["status"] == "Pending"
    assert json_data["data"]["test_type"] == "LoadTest"
    assert json_data["data"]["environment_id"] == SEED_TEST_ENV_ID
    
    # Assert Sprint 1.2 Enhancements
    assert "booking_number" in json_data["data"]
    assert json_data["data"]["booking_number"] == f"BK-{date_formatted}-0001"
    assert json_data["data"]["duration_minutes"] == 180


@pytest.mark.asyncio
async def test_booking_number_daily_sequence_increment_and_reset(async_client: AsyncClient, qa_headers: dict):
    date1 = date.today() + timedelta(days=5)
    date1_str = date1.isoformat()
    date1_formatted = date1.strftime("%Y%m%d")

    date2 = date.today() + timedelta(days=6)
    date2_str = date2.isoformat()
    date2_formatted = date2.strftime("%Y%m%d")

    payload1 = {
        "project_name": "Core Banking",
        "application_name": "Payment Gateway",
        "pic_name": "Jane Smith",
        "pic_email": "jane.smith@example.com",
        "booking_date": date1_str,
        "start_time": "08:00:00",
        "end_time": "09:00:00",
        "environment_id": SEED_TEST_ENV_ID,
        "test_type": "LoadTest"
    }
    payload2 = {
        "project_name": "Core Banking",
        "application_name": "Payment Gateway",
        "pic_name": "Jane Smith",
        "pic_email": "jane.smith@example.com",
        "booking_date": date1_str,
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "environment_id": SEED_TEST_ENV_ID,
        "test_type": "LoadTest"
    }
    payload_next_day = {
        "project_name": "Core Banking",
        "application_name": "Payment Gateway",
        "pic_name": "Jane Smith",
        "pic_email": "jane.smith@example.com",
        "booking_date": date2_str,
        "start_time": "08:00:00",
        "end_time": "09:00:00",
        "environment_id": SEED_TEST_ENV_ID,
        "test_type": "LoadTest"
    }

    # 1. Create first booking on date1
    res1 = await async_client.post("/api/v1/bookings", json=payload1, headers=qa_headers)
    assert res1.status_code == 201
    assert res1.json()["data"]["booking_number"] == f"BK-{date1_formatted}-0001"

    # 2. Create second booking on date1 -> sequence increments to 0002
    res2 = await async_client.post("/api/v1/bookings", json=payload2, headers=qa_headers)
    assert res2.status_code == 201
    assert res2.json()["data"]["booking_number"] == f"BK-{date1_formatted}-0002"

    # 3. Create booking on date2 -> sequence resets to 0001
    res3 = await async_client.post("/api/v1/bookings", json=payload_next_day, headers=qa_headers)
    assert res3.status_code == 201
    assert res3.json()["data"]["booking_number"] == f"BK-{date2_formatted}-0001"


@pytest.mark.asyncio
async def test_duration_minutes_calculation(async_client: AsyncClient, qa_headers: dict):
    future_date = (date.today() + timedelta(days=5)).isoformat()
    payload = {
        "project_name": "Core Banking",
        "application_name": "Payment Gateway",
        "pic_name": "Jane Smith",
        "pic_email": "jane.smith@example.com",
        "booking_date": future_date,
        "start_time": "09:30:00",
        "end_time": "11:15:00",  # 1 hour 45 min = 105 min
        "environment_id": SEED_TEST_ENV_ID,
        "test_type": "LoadTest"
    }

    response = await async_client.post("/api/v1/bookings", json=payload, headers=qa_headers)
    assert response.status_code == 201
    assert response.json()["data"]["duration_minutes"] == 105


@pytest.mark.asyncio
async def test_create_booking_invalid_environment_id(async_client: AsyncClient, qa_headers: dict):
    future_date = (date.today() + timedelta(days=5)).isoformat()
    invalid_env_id = str(uuid.uuid4())
    payload = {
        "project_name": "Core Banking",
        "application_name": "Payment Gateway",
        "pic_name": "Jane Smith",
        "pic_email": "jane.smith@example.com",
        "booking_date": future_date,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "environment_id": invalid_env_id,
        "test_type": "LoadTest"
    }

    response = await async_client.post("/api/v1/bookings", json=payload, headers=qa_headers)
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["success"] is False
    assert "Environment" in json_data["message"]


@pytest.mark.asyncio
async def test_create_booking_overlap_conflict(async_client: AsyncClient, qa_headers: dict):
    future_date = (date.today() + timedelta(days=5)).isoformat()
    payload1 = {
        "project_name": "Core Banking",
        "application_name": "Payment Gateway",
        "pic_name": "Jane Smith",
        "pic_email": "jane.smith@example.com",
        "booking_date": future_date,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "environment_id": SEED_TEST_ENV_ID,
        "test_type": "LoadTest"
    }
    res1 = await async_client.post("/api/v1/bookings", json=payload1, headers=qa_headers)
    assert res1.status_code == 201

    payload_overlapping = {
        "project_name": "Loan System",
        "application_name": "Credit Decisioning",
        "pic_name": "Bob Martin",
        "pic_email": "bob.martin@example.com",
        "booking_date": future_date,
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "environment_id": SEED_TEST_ENV_ID,
        "test_type": "StressTest"
    }

    res2 = await async_client.post("/api/v1/bookings", json=payload_overlapping, headers=qa_headers)
    assert res2.status_code == 409
    json_data = res2.json()
    assert json_data["success"] is False
    assert json_data["message"] == "Booking schedule overlaps with existing reservation."


@pytest.mark.asyncio
async def test_soft_delete_booking(async_client: AsyncClient, qa_headers: dict):
    future_date = (date.today() + timedelta(days=5)).isoformat()
    payload = {
        "project_name": "Core Banking",
        "application_name": "Payment Gateway",
        "pic_name": "Jane Smith",
        "pic_email": "jane.smith@example.com",
        "booking_date": future_date,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "environment_id": SEED_TEST_ENV_ID,
        "test_type": "LoadTest"
    }

    create_res = await async_client.post("/api/v1/bookings", json=payload, headers=qa_headers)
    booking_id = create_res.json()["data"]["id"]

    # 1. Soft-delete booking
    del_res = await async_client.delete(f"/api/v1/bookings/{booking_id}?deleted_by=admin@example.com", headers=qa_headers)
    assert del_res.status_code == 200

    # 2. GET by ID should return 404
    get_res = await async_client.get(f"/api/v1/bookings/{booking_id}", headers=qa_headers)
    assert get_res.status_code == 404

    # 3. Overlapping booking on same slot SHOULD NOW SUCCEED because original was soft-deleted
    res_retry = await async_client.post("/api/v1/bookings", json=payload, headers=qa_headers)
    assert res_retry.status_code == 201


@pytest.mark.asyncio
async def test_approve_booking_success(async_client: AsyncClient, qa_headers: dict):
    future_date = (date.today() + timedelta(days=5)).isoformat()
    payload = {
        "project_name": "Lifecycle Test",
        "application_name": "App 1",
        "pic_name": "Lead Tester",
        "pic_email": "tester@example.com",
        "booking_date": future_date,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "environment_id": SEED_TEST_ENV_ID,
        "test_type": "LoadTest"
    }

    create_res = await async_client.post("/api/v1/bookings", json=payload, headers=qa_headers)
    booking_id = create_res.json()["data"]["id"]

    # Approve booking
    approve_res = await async_client.post(f"/api/v1/bookings/{booking_id}/approve", json={"approved_by": "qa.manager@example.com"}, headers=qa_headers)
    assert approve_res.status_code == 200
    data = approve_res.json()["data"]
    assert data["status"] == "Approved"
    assert data["approved_by"] == "qa.manager@example.com"
    assert data["approved_at"] is not None


@pytest.mark.asyncio
async def test_reject_booking_requires_reason(async_client: AsyncClient, qa_headers: dict):
    future_date = (date.today() + timedelta(days=5)).isoformat()
    payload = {
        "project_name": "Lifecycle Test",
        "application_name": "App 2",
        "pic_name": "Lead Tester",
        "pic_email": "tester@example.com",
        "booking_date": future_date,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "environment_id": SEED_TEST_ENV_ID,
        "test_type": "LoadTest"
    }

    create_res = await async_client.post("/api/v1/bookings", json=payload, headers=qa_headers)
    booking_id = create_res.json()["data"]["id"]

    # Reject without reason should fail validation
    reject_fail = await async_client.post(f"/api/v1/bookings/{booking_id}/reject", json={"rejection_reason": ""}, headers=qa_headers)
    assert reject_fail.status_code in [400, 422]

    # Reject with valid reason should succeed
    reject_res = await async_client.post(f"/api/v1/bookings/{booking_id}/reject", json={"rejection_reason": "Maintenance window conflict", "rejected_by": "qa.manager@example.com"}, headers=qa_headers)
    assert reject_res.status_code == 200
    data = reject_res.json()["data"]
    assert data["status"] == "Rejected"
    assert data["rejection_reason"] == "Maintenance window conflict"
    assert data["rejected_by"] == "qa.manager@example.com"


@pytest.mark.asyncio
async def test_start_and_complete_testing_lifecycle(async_client: AsyncClient, qa_headers: dict):
    future_date = (date.today() + timedelta(days=5)).isoformat()
    payload = {
        "project_name": "Full Lifecycle",
        "application_name": "App 3",
        "pic_name": "Lead Tester",
        "pic_email": "tester@example.com",
        "booking_date": future_date,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "environment_id": SEED_TEST_ENV_ID,
        "test_type": "LoadTest"
    }

    create_res = await async_client.post("/api/v1/bookings", json=payload, headers=qa_headers)
    booking_id = create_res.json()["data"]["id"]

    # 1. Approve
    await async_client.post(f"/api/v1/bookings/{booking_id}/approve", json={"approved_by": "qa.manager"}, headers=qa_headers)

    # 2. Start Testing (Approved -> InProgress)
    start_res = await async_client.post(f"/api/v1/bookings/{booking_id}/start", json={"started_by": "tester"}, headers=qa_headers)
    assert start_res.status_code == 200
    assert start_res.json()["data"]["status"] == "InProgress"
    assert start_res.json()["data"]["started_at"] is not None

    # 3. Complete Testing (InProgress -> Completed)
    comp_res = await async_client.post(f"/api/v1/bookings/{booking_id}/complete", json={"completed_by": "tester"}, headers=qa_headers)
    assert comp_res.status_code == 200
    assert comp_res.json()["data"]["status"] == "Completed"
    assert comp_res.json()["data"]["completed_at"] is not None


@pytest.mark.asyncio
async def test_invalid_state_transition_fails(async_client: AsyncClient, qa_headers: dict):
    future_date = (date.today() + timedelta(days=5)).isoformat()
    payload = {
        "project_name": "Invalid State Transition Test",
        "application_name": "App 4",
        "pic_name": "Tester",
        "pic_email": "tester@example.com",
        "booking_date": future_date,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "environment_id": SEED_TEST_ENV_ID,
        "test_type": "LoadTest"
    }

    create_res = await async_client.post("/api/v1/bookings", json=payload, headers=qa_headers)
    booking_id = create_res.json()["data"]["id"]

    # Attempting to start testing directly from Pending (without approval) should fail
    start_fail = await async_client.post(f"/api/v1/bookings/{booking_id}/start", json={"started_by": "tester"}, headers=qa_headers)
    assert start_fail.status_code in [400, 422]
    assert start_fail.json()["success"] is False
