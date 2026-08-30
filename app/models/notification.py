import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.timezone import get_utc_now


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        index=True,
        nullable=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    recipient: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Sent"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now
    )
