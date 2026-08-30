import pytest
import uuid
from datetime import date, timedelta
from httpx import AsyncClient
from unittest.mock import patch

from app.services.email_service import SMTPEmailService, EmailResult
from app.templates.render import render_email_template


@pytest.mark.asyncio
async def test_email_template_rendering():
    """Verify Jinja2 email template renders without errors."""
    booking_data = {
        "booking_number": "BK-20260821-TEST",
        "project_name": "Test Project Alpha",
        "application_name": "Core Payment Gateway",
        "pic_name": "John Doe",
        "pic_email": "john@example.com",
        "booking_date": "2026-08-25",
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "duration_minutes": 180,
        "environment_name": "Staging 01",
        "test_type": "Load Testing",
        "status": "Approved"
    }

    html_output = render_email_template(
        event_type="Approved",
        booking_data=booking_data,
        reason=None
    )

    assert "JadwalinTest" in html_output
    assert "BK-20260821-TEST" in html_output
    assert "Test Project Alpha" in html_output
    assert "APPROVED" in html_output


@pytest.mark.asyncio
async def test_email_disabled_mode():
    """Verify email service in disabled mode (EMAIL_ENABLED=False)."""
    service = SMTPEmailService()
    service.enabled = False

    booking_data = {
        "booking_number": "BK-20260821-TEST",
        "project_name": "Test Project Beta",
        "pic_name": "Jane Smith"
    }

    result = await service.send_lifecycle_email(
        booking_data=booking_data,
        event_type="Created",
        recipient_email="qa-team@company.com"
    )

    assert isinstance(result, EmailResult)
    assert result.success is True
    assert result.provider == "disabled"
    assert result.recipient == "qa-team@company.com"


@pytest.mark.asyncio
async def test_email_failure_isolation_does_not_throw():
    """Verify that SMTP failure returns EmailResult(success=False) without raising exceptions."""
    service = SMTPEmailService()
    service.enabled = True
    service.host = "invalid.smtp.nonexistent.domain.local"
    service.from_email = "no-reply@company.com"
    service.username = "test_user"
    service.password = "test_pass"

    booking_data = {
        "id": str(uuid.uuid4()),
        "booking_number": "BK-FAIL-001",
        "project_name": "Failure Resilience Test",
        "pic_name": "Test User"
    }

    # Should attempt up to 3 times, fail, log error, and return EmailResult(success=False)
    result = await service.send_lifecycle_email(
        booking_data=booking_data,
        event_type="Approved",
        recipient_email="requester@company.com"
    )

    assert isinstance(result, EmailResult)
    assert result.success is False
    assert result.recipient == "requester@company.com"
    assert result.error_message is not None


@pytest.mark.asyncio
async def test_booking_creation_succeeds_even_if_email_fails(async_client: AsyncClient, requester_headers: dict):
    """Verify CRITICAL RELIABILITY RULE: Booking creation succeeds (HTTP 201) even when SMTP fails."""
    tomorrow = date.today() + timedelta(days=1)

    booking_payload = {
        "project_name": "Email Failure Isolation Test",
        "application_name": "Mobile Banking",
        "pic_name": "Resilience Tester",
        "pic_email": "resilience@company.com",
        "booking_date": str(tomorrow),
        "start_time": "14:00:00",
        "end_time": "16:00:00",
        "environment_id": "11111111-1111-1111-1111-111111111111",
        "test_type": "StressTest",
        "description": "Ensuring business transaction commits even if notification delivery fails."
    }

    with patch("app.services.email_service.SMTPEmailService.send_lifecycle_email") as mock_email:
        # Mock email failure
        mock_email.return_value = EmailResult(
            success=False,
            provider="smtp",
            recipient="qa-team@company.com",
            event_type="Created",
            error_message="SMTP connection refused"
        )

        response = await async_client.post("/api/v1/bookings", json=booking_payload, headers=requester_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["project_name"] == "Email Failure Isolation Test"
        assert "BK-" in data["data"]["booking_number"]
