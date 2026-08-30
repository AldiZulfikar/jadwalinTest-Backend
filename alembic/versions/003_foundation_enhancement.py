"""foundation enhancement migration: booking_number and duration_minutes

Revision ID: 003_foundation_enhancement
Revises: 002_architecture_hardening
Create Date: 2026-07-28 20:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_foundation_enhancement"
down_revision: Union[str, None] = "002_architecture_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns as nullable for data backfill
    op.add_column("bookings", sa.Column("booking_number", sa.String(length=50), nullable=True))
    op.add_column("bookings", sa.Column("duration_minutes", sa.Integer(), nullable=True))

    # Backfill existing records if any
    connection = op.get_bind()
    results = connection.execute(sa.text("SELECT id, booking_date, start_time, end_time FROM bookings ORDER BY booking_date, created_at"))
    
    date_counters = {}
    for row in results:
        booking_id = row[0]
        booking_date = str(row[1]).replace("-", "")
        
        # Calculate sequence per date
        date_counters[booking_date] = date_counters.get(booking_date, 0) + 1
        seq_num = date_counters[booking_date]
        booking_num = f"BK-{booking_date}-{seq_num:04d}"

        # Calculate duration in minutes
        # Note: SQLite / Postgres handling for time difference
        start_t = row[2]
        end_t = row[3]
        
        # Default duration fallback
        duration_min = 180
        try:
            if hasattr(start_t, "hour") and hasattr(end_t, "hour"):
                start_min = start_t.hour * 60 + start_t.minute
                end_min = end_t.hour * 60 + end_t.minute
                duration_min = end_min - start_min
        except Exception:
            pass

        connection.execute(
            sa.text("UPDATE bookings SET booking_number = :num, duration_minutes = :dur WHERE id = :bid"),
            {"num": booking_num, "dur": duration_min, "bid": booking_id}
        )

    # Set columns as NOT NULL and create index/unique constraint
    if op.get_bind().dialect.name != "sqlite":
        op.alter_column("bookings", "booking_number", nullable=False)
        op.alter_column("bookings", "duration_minutes", nullable=False)
    op.create_index(op.f("ix_bookings_booking_number"), "bookings", ["booking_number"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_bookings_booking_number"), table_name="bookings")
    op.drop_column("bookings", "duration_minutes")
    op.drop_column("bookings", "booking_number")
