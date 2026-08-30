import os
from datetime import datetime
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.logging import logger
from app.utils.timezone import get_utc_now

TEMPLATES_DIR = os.path.dirname(os.path.abspath(__file__))
EMAIL_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, "email")

jinja_env = Environment(
    loader=FileSystemLoader(EMAIL_TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"])
)


def render_email_template(
    event_type: str,
    booking_data: Dict[str, Any],
    reason: Optional[str] = None,
    portal_url: str = "http://localhost:3000"
) -> str:
    """
    Renders an HTML email template for a given lifecycle event_type.
    Falls back to base_email.html with dynamic intro messages.
    """
    event_intros = {
        "Created": "A new performance test booking request has been submitted and is pending review.",
        "Approved": "Your performance test booking request has been APPROVED by the QA team.",
        "Rejected": "Your performance test booking request has been REJECTED by the QA team.",
        "Started": "Performance testing execution for your booking has now STARTED.",
        "Completed": "Performance testing execution for your booking has been COMPLETED.",
        "Cancelled": "The performance test booking has been CANCELLED.",
    }

    intro_message = event_intros.get(
        event_type,
        f"The status of your performance test booking has been updated to '{event_type}'."
    )

    context = {
        "subject": f"[JadwalinTest] Booking {event_type} - {booking_data.get('booking_number', 'N/A')}",
        "event_type": event_type,
        "pic_name": booking_data.get("pic_name", "User"),
        "intro_message": intro_message,
        "reason": reason or booking_data.get("rejection_reason"),
        "booking_number": booking_data.get("booking_number", "N/A"),
        "project_name": booking_data.get("project_name", "N/A"),
        "application_name": booking_data.get("application_name", "N/A"),
        "environment_name": booking_data.get("environment_name") or booking_data.get("environment_id", "N/A"),
        "booking_date": booking_data.get("booking_date", "N/A"),
        "start_time": booking_data.get("start_time", "N/A"),
        "end_time": booking_data.get("end_time", "N/A"),
        "duration_minutes": booking_data.get("duration_minutes", "N/A"),
        "test_type": booking_data.get("test_type", "N/A"),
        "status": booking_data.get("status", "N/A"),
        "portal_url": portal_url,
        "current_year": get_utc_now().year,
    }

    try:
        template = jinja_env.get_template("base_email.html")
        return template.render(**context)
    except Exception as exc:
        logger.error(f"[render_email_template] Failed to render Jinja2 email template: {exc}")
        # Safe plain-text fallback HTML
        return f"<h3>JadwalinTest Booking {event_type} ({booking_data.get('booking_number')})</h3><p>{intro_message}</p>"
