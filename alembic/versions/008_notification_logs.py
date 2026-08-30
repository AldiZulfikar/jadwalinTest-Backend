"""create notification_logs table

Revision ID: 008_notification_logs
Revises: 007_seed_iam_users
Create Date: 2026-08-21 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "008_notification_logs"
down_revision: Union[str, None] = "007_seed_iam_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "notification_logs" not in tables:
        op.create_table(
            "notification_logs",
            sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("booking_id", sa.UUID(as_uuid=True), nullable=True),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("recipient", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="Sent"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index(op.f("ix_notification_logs_id"), "notification_logs", ["id"], unique=False)
        op.create_index(op.f("ix_notification_logs_booking_id"), "notification_logs", ["booking_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    if "notification_logs" in tables:
        op.drop_index(op.f("ix_notification_logs_booking_id"), table_name="notification_logs")
        op.drop_index(op.f("ix_notification_logs_id"), table_name="notification_logs")
        op.drop_table("notification_logs")
