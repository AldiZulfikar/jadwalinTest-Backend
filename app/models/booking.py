import uuid
from datetime import date, time, datetime
from typing import Optional
from sqlalchemy import String, Date, Time, Text, DateTime, ForeignKey, Enum as SQLEnum, Index, Uuid, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import BookingStatus, TestType
from app.models.environment import Environment
from app.utils.timezone import get_utc_now


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    # Human-friendly unique booking number (e.g. BK-20260728-0001)
    booking_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    project_name: Mapped[str] = mapped_column(String(100), nullable=False)
    application_name: Mapped[str] = mapped_column(String(100), nullable=False)
    pic_name: Mapped[str] = mapped_column(String(100), nullable=False)
    pic_email: Mapped[str] = mapped_column(String(255), nullable=False)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    # Stored duration in minutes
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Normalized Foreign Key to Environment
    environment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("environments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    environment_rel: Mapped["Environment"] = relationship("Environment", lazy="joined")

    # Optional Foreign Key to User
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    user: Mapped[Optional["User"]] = relationship("User", back_populates="bookings", lazy="joined")

    # Enums
    test_type: Mapped[TestType] = mapped_column(
        SQLEnum(TestType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=BookingStatus.PENDING,
        index=True
    )

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit Columns
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Lifecycle Audit Columns
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Soft Delete Column
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )

    # Timestamps (UTC)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
        server_default=func.now(),
        onupdate=get_utc_now
    )

    __table_args__ = (
        Index("ix_bookings_env_date_deleted", "environment_id", "booking_date", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<Booking num={self.booking_number} project={self.project_name} duration={self.duration_minutes}m status={self.status}>"
