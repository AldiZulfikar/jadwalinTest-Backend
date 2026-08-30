from typing import List, Optional, Tuple, Dict, Any
from datetime import date
from uuid import UUID

from app.models.booking import Booking
from app.models.enums import BookingStatus, TestType
from app.schemas.booking import BookingCreate
from app.repository.booking_repository import BookingRepository
from app.repository.environment_repository import EnvironmentRepository
from app.services.email_service import BaseEmailService
from app.core.exceptions import (
    BookingOverlapException,
    BookingNotFoundException,
    EnvironmentNotFoundException,
    InvalidBookingStateException,
)
from app.utils.timezone import calculate_duration_minutes, get_utc_now
from app.core.logging import logger


class BookingService:
    def __init__(
        self,
        booking_repo: BookingRepository,
        environment_repo: EnvironmentRepository,
        email_service: BaseEmailService
    ):
        self.booking_repo = booking_repo
        self.environment_repo = environment_repo
        self.email_service = email_service

    async def create_booking(self, payload: BookingCreate, user_id: Optional[UUID] = None) -> Booking:
        """
        Validates environment existence, schedule availability, computes duration, 
        generates human-friendly booking_number, and creates a new booking.
        Triggers email notification upon successful persistence.
        """
        # 1. Validate Environment existence
        env = await self.environment_repo.find_by_id(payload.environment_id)
        if not env or not env.active:
            logger.warning(f"Environment ID={payload.environment_id} not found or inactive.")
            raise EnvironmentNotFoundException(f"Environment ID {payload.environment_id} is invalid or inactive.")

        # 2. Check for schedule collision in service layer
        has_overlap = await self.booking_repo.check_overlap(
            environment_id=payload.environment_id,
            booking_date=payload.booking_date,
            start_time=payload.start_time,
            end_time=payload.end_time
        )

        if has_overlap:
            logger.warning(
                f"Booking conflict detected for environment_id='{payload.environment_id}' on date={payload.booking_date}"
            )
            raise BookingOverlapException("Booking schedule overlaps with existing reservation.")

        # 3. Calculate duration in minutes
        duration_min = calculate_duration_minutes(payload.start_time, payload.end_time)

        # 4. Generate transaction-safe human-friendly booking number
        booking_num = await self.booking_repo.generate_next_booking_number(payload.booking_date)

        # 5. Instantiate ORM model with UTC timestamps
        utc_now = get_utc_now()
        booking_obj = Booking(
            booking_number=booking_num,
            project_name=payload.project_name,
            application_name=payload.application_name,
            pic_name=payload.pic_name,
            pic_email=payload.pic_email,
            booking_date=payload.booking_date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            duration_minutes=duration_min,
            environment_id=payload.environment_id,
            user_id=user_id,
            test_type=payload.test_type,
            description=payload.description,
            created_by=payload.created_by,
            status=BookingStatus.PENDING,
            created_at=utc_now,
            updated_at=utc_now
        )

        created_booking = await self.booking_repo.create(booking_obj)
        logger.info(f"Booking Created successfully with Number={created_booking.booking_number} (ID={created_booking.id})")

        # 6. Trigger Email Notification
        await self._trigger_email(created_booking, "Created")

        return created_booking

    async def get_booking_by_id(self, booking_id: UUID, include_deleted: bool = False) -> Booking:
        """Retrieves a booking by UUID."""
        booking = await self.booking_repo.find_by_id(booking_id, include_deleted=include_deleted)
        if not booking:
            logger.warning(f"Booking with ID={booking_id} not found.")
            raise BookingNotFoundException("Booking not found.")
        return booking

    async def get_bookings_paginated(
        self,
        page: int = 1,
        size: int = 20,
        sort: str = "created_at",
        order: str = "desc",
        booking_date: Optional[date] = None,
        environment_id: Optional[UUID] = None,
        status: Optional[BookingStatus] = None,
        project_name: Optional[str] = None,
        pic_name: Optional[str] = None,
        test_type: Optional[TestType] = None,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
    ) -> Tuple[List[Booking], int]:
        """Retrieves paginated and filtered list of bookings (including cancelled)."""
        return await self.booking_repo.filter_and_paginate(
            page=page,
            size=size,
            sort=sort,
            order=order,
            booking_date=booking_date,
            environment_id=environment_id,
            status=status,
            project_name=project_name,
            pic_name=pic_name,
            test_type=test_type,
            user_id=user_id,
            user_email=user_email,
            include_deleted=True
        )

    # --------------------------------------------------------------------------
    # Sprint 3 Lifecycle State Machine Actions
    # --------------------------------------------------------------------------

    async def approve_booking(self, booking_id: UUID, approved_by: Optional[str] = None) -> Booking:
        """Transitions booking state: Pending -> Approved."""
        booking = await self.get_booking_by_id(booking_id, include_deleted=True)

        if booking.status != BookingStatus.PENDING:
            raise InvalidBookingStateException(
                f"Cannot approve booking in '{booking.status.value}' state. Only Pending bookings can be approved."
            )

        utc_now = get_utc_now()
        booking.status = BookingStatus.APPROVED
        booking.approved_at = utc_now
        booking.approved_by = approved_by
        booking.updated_at = utc_now

        updated_booking = await self.booking_repo.update(booking)
        logger.info(f"Booking Number={updated_booking.booking_number} APPROVED by {approved_by or 'System'}")

        await self._trigger_email(updated_booking, "Approved")
        return updated_booking

    async def reject_booking(self, booking_id: UUID, rejection_reason: str, rejected_by: Optional[str] = None) -> Booking:
        """Transitions booking state: Pending -> Rejected (requires rejection_reason)."""
        booking = await self.get_booking_by_id(booking_id, include_deleted=True)

        if booking.status != BookingStatus.PENDING:
            raise InvalidBookingStateException(
                f"Cannot reject booking in '{booking.status.value}' state. Only Pending bookings can be rejected."
            )

        if not rejection_reason or not rejection_reason.strip():
            raise InvalidBookingStateException("Rejection reason is required when rejecting a booking.")

        utc_now = get_utc_now()
        booking.status = BookingStatus.REJECTED
        booking.rejected_at = utc_now
        booking.rejected_by = rejected_by
        booking.rejection_reason = rejection_reason.strip()
        booking.updated_at = utc_now

        updated_booking = await self.booking_repo.update(booking)
        logger.info(f"Booking Number={updated_booking.booking_number} REJECTED by {rejected_by or 'System'}")

        await self._trigger_email(updated_booking, "Rejected", reason=rejection_reason)
        return updated_booking

    async def start_testing(self, booking_id: UUID, started_by: Optional[str] = None) -> Booking:
        """Transitions booking state: Approved -> InProgress."""
        booking = await self.get_booking_by_id(booking_id, include_deleted=True)

        if booking.status != BookingStatus.APPROVED:
            raise InvalidBookingStateException(
                f"Cannot start testing for booking in '{booking.status.value}' state. Only Approved bookings can transition to InProgress."
            )

        utc_now = get_utc_now()
        booking.status = BookingStatus.IN_PROGRESS
        booking.started_at = utc_now
        booking.started_by = started_by
        booking.updated_at = utc_now

        updated_booking = await self.booking_repo.update(booking)
        logger.info(f"Booking Number={updated_booking.booking_number} STARTED (InProgress) by {started_by or 'System'}")

        await self._trigger_email(updated_booking, "InProgress")
        return updated_booking

    async def complete_testing(self, booking_id: UUID, completed_by: Optional[str] = None) -> Booking:
        """Transitions booking state: InProgress -> Completed."""
        booking = await self.get_booking_by_id(booking_id, include_deleted=True)

        if booking.status != BookingStatus.IN_PROGRESS:
            raise InvalidBookingStateException(
                f"Cannot complete testing for booking in '{booking.status.value}' state. Only InProgress bookings can be completed."
            )

        utc_now = get_utc_now()
        booking.status = BookingStatus.COMPLETED
        booking.completed_at = utc_now
        booking.completed_by = completed_by
        booking.updated_at = utc_now

        updated_booking = await self.booking_repo.update(booking)
        logger.info(f"Booking Number={updated_booking.booking_number} COMPLETED by {completed_by or 'System'}")

        await self._trigger_email(updated_booking, "Completed")
        return updated_booking

    async def delete_booking(self, booking_id: UUID, deleted_by: Optional[str] = None) -> None:
        """Transitions booking state to Cancelled & performs soft-delete."""
        booking = await self.get_booking_by_id(booking_id, include_deleted=True)

        if booking.status in [BookingStatus.COMPLETED, BookingStatus.REJECTED, BookingStatus.CANCELLED]:
            raise InvalidBookingStateException(
                f"Cannot cancel booking in terminal state '{booking.status.value}'."
            )

        booking.status = BookingStatus.CANCELLED
        await self.booking_repo.soft_delete(booking, deleted_by=deleted_by)
        logger.info(f"Booking Number={booking.booking_number} CANCELLED & soft-deleted by {deleted_by or 'System'}")

        await self._trigger_email(booking, "Cancelled")

    async def _trigger_email(self, booking: Booking, event_type: str, reason: Optional[str] = None) -> None:
        """Helper to build booking dictionary, resolve recipients, and call EmailService safely."""
        try:
            env_name = str(booking.environment_id)
            if hasattr(booking, "environment") and booking.environment:
                env_name = getattr(booking.environment, "name", str(booking.environment_id))

            booking_dict = {
                "id": str(booking.id),
                "booking_number": booking.booking_number,
                "project_name": booking.project_name,
                "application_name": booking.application_name,
                "pic_name": booking.pic_name,
                "pic_email": booking.pic_email,
                "booking_date": str(booking.booking_date),
                "start_time": str(booking.start_time),
                "end_time": str(booking.end_time),
                "duration_minutes": booking.duration_minutes,
                "environment_id": str(booking.environment_id),
                "environment_name": env_name,
                "test_type": booking.test_type.value if hasattr(booking.test_type, 'value') else str(booking.test_type),
                "description": booking.description,
                "status": booking.status.value if hasattr(booking.status, 'value') else str(booking.status),
                "rejection_reason": reason or booking.rejection_reason,
            }

            # Map event type labels for template display
            display_event = "Started" if event_type in ["Started", "InProgress"] else event_type

            # Resolve recipients based on event type matrix
            if display_event == "Created":
                recipients = [settings.QA_NOTIFICATION_EMAIL or settings.QA_EMAIL]
            elif display_event == "Cancelled":
                recipients = [booking.pic_email]
                qa_mail = settings.QA_NOTIFICATION_EMAIL or settings.QA_EMAIL
                if qa_mail and qa_mail != booking.pic_email:
                    recipients.append(qa_mail)
            else:
                recipients = [booking.pic_email]

            for recipient in set(recipients):
                if recipient:
                    res = await self.email_service.send_lifecycle_email(
                        booking_data=booking_dict,
                        event_type=display_event,
                        recipient_email=recipient,
                        reason=reason
                    )
                    if not res.success:
                        logger.warning(
                            f"[BookingService] Email notification for '{display_event}' to '{recipient}' failed: {res.error_message}. Business transaction remains successful."
                        )
        except Exception as exc:
            logger.error(
                f"[BookingService] Exception caught in _trigger_email for event '{event_type}': {exc}. Business transaction remains successful."
            )

