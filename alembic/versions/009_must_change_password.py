"""add must_change_password column to users table

Revision ID: 009_must_change_password
Revises: 008_notification_logs
Create Date: 2026-08-30 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "009_must_change_password"
down_revision: Union[str, None] = "008_notification_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("users")]

    if "must_change_password" not in columns:
        op.add_column(
            "users",
            sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.text("true"))
        )
        is_sqlite = bind.dialect.name == "sqlite"
        false_val = "0" if is_sqlite else "false"
        # Update seed users (qa, requester) to not force password change initially
        op.execute(f"UPDATE users SET must_change_password = {false_val} WHERE username IN ('qa', 'requester')")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("users")]

    if "must_change_password" in columns:
        op.drop_column("users", "must_change_password")
