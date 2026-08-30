from typing import Optional, List, Tuple
from datetime import date, time
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, asc, desc

from app.models.booking import Booking
from app.models.enums import BookingStatus, TestType
from app.repository.base_repository import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Booking, db_session)

    async def generate_next_booking_number(self, booking_date: date) -> str:
        """
        Transaction-safe sequence generator for human-friendly booking numbers.
        Format: BK-YYYYMMDD-XXXX (e.g., BK-20260728-0001)

        Concurrency Strategy:
        - Filters records matching prefix for the target date.
        - Uses SELECT FOR UPDATE lock where supported by dialect to prevent race conditions during concurrent creation.
        - Extracts maximum sequence suffix, increments by 1, and formats as 4-digit zero-padded string.
        """
        date_str = booking_date.strftime("%Y%m%d")
        prefix = f"BK-{date_str}-"
        pattern = f"{prefix}%"

        stmt = select(Booking.booking_number).where(
            Booking.booking_number.like(pattern)
        ).order_by(desc(Booking.booking_number))

        # Apply FOR UPDATE row lock on PostgreSQL / dialect supporting locking
        if self.db.bind and self.db.bind.dialect.name == "postgresql":
            stmt = stmt.with_for_update()

        result = await self.db.execute(stmt)
        existing_numbers = result.scalars().all()

        max_seq = 0
        for num in existing_numbers:
            try:
                # Extract the 4-digit sequence part after last hyphen
                parts = num.split("-")
                if len(parts) >= 3:
                    seq_int = int(parts[-1])
                    if seq_int > max_seq:
                        max_seq = seq_int
            except (ValueError, IndexError):
                continue

        next_seq = max_seq + 1
        return f"{prefix}{next_seq:04d}"

    async def find_by_booking_number(self, booking_number: str, include_deleted: bool = False) -> Optional[Booking]:
        """Find active booking by its human-friendly booking_number."""
        stmt = self._base_query(include_deleted=include_deleted).where(
            Booking.booking_number == booking_number
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def check_overlap(
        self,
        environment_id: UUID,
        booking_date: date,
        start_time: time,
        end_time: time,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if any active booking overlaps with the requested schedule.
        Rule: Same Environment ID AND Same Date AND Time Overlap AND Not Soft-Deleted AND Status != Cancelled.
        """
        conditions = [
            Booking.environment_id == environment_id,
            Booking.booking_date == booking_date,
            Booking.deleted_at.is_(None),
            Booking.status != BookingStatus.CANCELLED,
            and_(
                Booking.start_time < end_time,
                Booking.end_time > start_time
            )
        ]

        if exclude_id:
            conditions.append(Booking.id != exclude_id)

        stmt = select(Booking).where(*conditions)
        result = await self.db.execute(stmt)
        return result.first() is not None

    async def filter_and_paginate(
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
        include_deleted: bool = False
    ) -> Tuple[List[Booking], int]:
        """
        Applies combinable filters, sorting, and database-level pagination.
        Returns a tuple of (items, total_count).
        """
        stmt = self._base_query(include_deleted=include_deleted)
        conditions = []

        if booking_date:
            conditions.append(Booking.booking_date == booking_date)
        if environment_id:
            conditions.append(Booking.environment_id == environment_id)
        if status:
            conditions.append(Booking.status == status)
        if project_name:
            conditions.append(Booking.project_name.ilike(f"%{project_name}%"))
        if pic_name:
            conditions.append(Booking.pic_name.ilike(f"%{pic_name}%"))
        if test_type:
            conditions.append(Booking.test_type == test_type)

        if user_id or user_email:
            ownership_conds = []
            if user_id:
                ownership_conds.append(Booking.user_id == user_id)
            if user_email:
                ownership_conds.append(func.lower(Booking.pic_email) == user_email.lower().strip())
            conditions.append(or_(*ownership_conds))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Calculate total matching count before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Sorting logic
        sort_column = getattr(Booking, sort, Booking.created_at)
        sort_dir = desc(sort_column) if order.lower() == "desc" else asc(sort_column)
        stmt = stmt.order_by(sort_dir)

        # Pagination logic
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size)

        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, total
