"""create user_management table and add user_id to bookings

Revision ID: 006_user_management
Revises: 005_update_environments
Create Date: 2026-08-02 21:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "006_user_management"
down_revision: Union[str, None] = "005_update_environments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. Create users table if not exists
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("username", sa.String(length=100), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False, server_default="Requester"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
        op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. Add user_id column to bookings using batch_alter_table if not exists
    columns = [c["name"] for c in inspector.get_columns("bookings")]
    if "user_id" not in columns:
        with op.batch_alter_table("bookings") as batch_op:
            batch_op.add_column(sa.Column("user_id", sa.UUID(as_uuid=True), nullable=True))
            batch_op.create_index(op.f("ix_bookings_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("bookings")]
    if "user_id" in columns:
        with op.batch_alter_table("bookings") as batch_op:
            batch_op.drop_index(op.f("ix_bookings_user_id"))
            batch_op.drop_column("user_id")

    tables = inspector.get_table_names()
    if "users" in tables:
        op.drop_index(op.f("ix_users_email"), table_name="users")
        op.drop_index(op.f("ix_users_username"), table_name="users")
        op.drop_index(op.f("ix_users_id"), table_name="users")
        op.drop_table("users")
