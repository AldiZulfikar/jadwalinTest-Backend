"""create booking table

Revision ID: 001_create_booking
Revises: 
Create Date: 2026-07-28 20:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "001_create_booking"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bookings",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_name", sa.String(length=100), nullable=False),
        sa.Column("application_name", sa.String(length=100), nullable=False),
        sa.Column("pic_name", sa.String(length=100), nullable=False),
        sa.Column("pic_email", sa.String(length=255), nullable=False),
        sa.Column("booking_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("environment", sa.String(length=50), nullable=False),
        sa.Column("test_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index(op.f("ix_bookings_id"), "bookings", ["id"], unique=False)
    op.create_index(op.f("ix_bookings_booking_date"), "bookings", ["booking_date"], unique=False)
    op.create_index(op.f("ix_bookings_environment"), "bookings", ["environment"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bookings_environment"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_booking_date"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_id"), table_name="bookings")
    op.drop_table("bookings")
