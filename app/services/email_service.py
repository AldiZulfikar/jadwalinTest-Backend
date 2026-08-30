import asyncio
import smtplib
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.logging import logger
from app.templates.render import render_email_template
from app.db.session import AsyncSessionLocal
from app.models.notification import NotificationLog
from app.utils.timezone import get_utc_now


@dataclass
class EmailResult:
    """Structured result envelope for email delivery operations."""
    success: bool
    provider: str
    recipient: str
    event_type: str
    error_message: Optional[str] = None


class BaseEmailService(ABC):
    """Abstract Base Class for Email Service Providers."""

    @abstractmethod
    async def send_booking_notification(self, booking_data: Dict[str, Any], recipient_email: str) -> EmailResult:
        """Send notification email upon successful booking creation."""
        pass

    @abstractmethod
    async def send_lifecycle_email(
        self,
        booking_data: Dict[str, Any],
        event_type: str,
        recipient_email: str,
        reason: Optional[str] = None
    ) -> EmailResult:
        """Send notification email upon lifecycle state transition."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check status of email provider configuration/connectivity."""
        pass


class SMTPEmailService(BaseEmailService):
    """SMTP Implementation of Email Service with retry & failure isolation."""

    def __init__(self):
        self.enabled = settings.EMAIL_ENABLED
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.use_tls = settings.SMTP_USE_TLS

    async def health_check(self) -> bool:
        """Verify SMTP configuration initialization."""
        if not self.enabled:
            return True
        return bool(self.host and self.port)

    async def send_booking_notification(self, booking_data: Dict[str, Any], recipient_email: str) -> EmailResult:
        return await self.send_lifecycle_email(booking_data, "Created", recipient_email)

    async def send_lifecycle_email(
        self,
        booking_data: Dict[str, Any],
        event_type: str,
        recipient_email: str,
        reason: Optional[str] = None
    ) -> EmailResult:
        booking_num = booking_data.get("booking_number", "N/A")
        project_name = booking_data.get("project_name", "N/A")
        booking_id_raw = booking_data.get("id")

        booking_uuid = None
        if booking_id_raw:
            try:
                booking_uuid = uuid.UUID(str(booking_id_raw))
            except Exception:
                pass

        # 1. Email Disabled Check
        if not self.enabled:
            logger.info(
                f"[EmailService] EMAIL_ENABLED=False. Simulated {event_type} notification to {recipient_email} for Booking {booking_num}"
            )
            await self._persist_notification_log(
                booking_id=booking_uuid,
                event_type=event_type,
                recipient=recipient_email,
                status="Simulated",
                error_message=None
            )
            return EmailResult(
                success=True,
                provider="disabled",
                recipient=recipient_email,
                event_type=event_type
            )

        subject = f"[JadwalinTest] Status Update - {event_type} ({booking_num}): {project_name}"
        html_body = render_email_template(
            event_type=event_type,
            booking_data=booking_data,
            reason=reason
        )

        msg = MIMEMultipart("alternative")
        msg["From"] = self.from_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        # 2. Simulated Mode if localhost/example host
        if not self.host or self.host == "localhost" or "example.com" in self.from_email or "example.com" in self.username:
            logger.info(
                f"[EmailService] [Simulated Email] {event_type} notification sent to {recipient_email} for Booking '{booking_num}'"
            )
            await self._persist_notification_log(
                booking_id=booking_uuid,
                event_type=event_type,
                recipient=recipient_email,
                status="Simulated",
                error_message=None
            )
            return EmailResult(
                success=True,
                provider="smtp-simulated",
                recipient=recipient_email,
                event_type=event_type
            )

        # 3. SMTP Execution with Retry Loop (up to 2 retries)
        max_attempts = 3
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                with smtplib.SMTP(self.host, self.port, timeout=8) as server:
                    if self.use_tls:
                        server.starttls()
                    if self.username and self.password:
                        server.login(self.username, self.password)
                    server.send_message(msg)

                logger.info(f"[EmailService] Lifecycle Email ({event_type}) successfully sent to {recipient_email}")
                await self._persist_notification_log(
                    booking_id=booking_uuid,
                    event_type=event_type,
                    recipient=recipient_email,
                    status="Sent",
                    error_message=None
                )
                return EmailResult(
                    success=True,
                    provider="smtp",
                    recipient=recipient_email,
                    event_type=event_type
                )
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    f"[EmailService] Attempt {attempt}/{max_attempts} failed to send {event_type} email to {recipient_email}: {exc}"
                )
                if attempt < max_attempts:
                    await asyncio.sleep(0.5 * attempt)

        # 4. Final Failure Isolation Handled Gracefully
        logger.error(
            f"[EmailService] All attempts failed to send {event_type} notification email for Booking {booking_num}: {last_error}"
        )
        await self._persist_notification_log(
            booking_id=booking_uuid,
            event_type=event_type,
            recipient=recipient_email,
            status="Failed",
            error_message=last_error
        )
        return EmailResult(
            success=False,
            provider="smtp",
            recipient=recipient_email,
            event_type=event_type,
            error_message=last_error
        )

    async def _persist_notification_log(
        self,
        booking_id: Optional[uuid.UUID],
        event_type: str,
        recipient: str,
        status: str,
        error_message: Optional[str]
    ) -> None:
        """Safely record notification audit log without raising DB exceptions."""
        try:
            async with AsyncSessionLocal() as db:
                log_entry = NotificationLog(
                    booking_id=booking_id,
                    event_type=event_type,
                    recipient=recipient,
                    status=status,
                    error_message=error_message,
                    sent_at=get_utc_now() if status in ["Sent", "Simulated"] else None
                )
                db.add(log_entry)
                await db.commit()
        except Exception as exc:
            logger.warning(f"[EmailService] Failed to persist NotificationLog audit entry: {exc}")


class GraphEmailService(BaseEmailService):
    """Microsoft Graph API Email Service Placeholder."""

    def __init__(self):
        self.tenant_id = settings.GRAPH_TENANT_ID
        self.client_id = settings.GRAPH_CLIENT_ID
        self.client_secret = settings.GRAPH_CLIENT_SECRET

    async def health_check(self) -> bool:
        return bool(self.tenant_id or self.client_id)

    async def send_booking_notification(self, booking_data: Dict[str, Any], recipient_email: str) -> EmailResult:
        return await self.send_lifecycle_email(booking_data, "Created", recipient_email)

    async def send_lifecycle_email(
        self,
        booking_data: Dict[str, Any],
        event_type: str,
        recipient_email: str,
        reason: Optional[str] = None
    ) -> EmailResult:
        logger.info(
            f"[GraphEmailService Placeholder] Mocking Graph API lifecycle email ({event_type}) to {recipient_email} for booking {booking_data.get('booking_number')}"
        )
        return EmailResult(
            success=True,
            provider="graph",
            recipient=recipient_email,
            event_type=event_type
        )


def get_email_service() -> BaseEmailService:
    provider = settings.EMAIL_PROVIDER.lower()
    if provider == "graph":
        return GraphEmailService()
    return SMTPEmailService()
