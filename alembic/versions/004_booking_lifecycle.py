"""booking lifecycle migration: audit columns for approval, rejection, start, and completion

Revision ID: 004_booking_lifecycle
Revises: 003_foundation_enhancement
Create Date: 2026-08-02 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004_booking_lifecycle"
down_revision: Union[str, None] = "003_foundation_enhancement"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bookings", sa.Column("approved_by", sa.String(length=255), nullable=True))
    op.add_column("bookings", sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bookings", sa.Column("rejected_by", sa.String(length=255), nullable=True))
    op.add_column("bookings", sa.Column("rejection_reason", sa.Text(), nullable=True))
    op.add_column("bookings", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bookings", sa.Column("started_by", sa.String(length=255), nullable=True))
    op.add_column("bookings", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bookings", sa.Column("completed_by", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("bookings", "completed_by")
    op.drop_column("bookings", "completed_at")
    op.drop_column("bookings", "started_by")
    op.drop_column("bookings", "started_at")
    op.drop_column("bookings", "rejection_reason")
    op.drop_column("bookings", "rejected_by")
    op.drop_column("bookings", "rejected_at")
    op.drop_column("bookings", "approved_by")
    op.drop_column("bookings", "approved_at")
