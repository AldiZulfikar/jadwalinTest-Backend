"""architecture hardening migration: environments table, soft delete, audit fields, enums

Revision ID: 002_architecture_hardening
Revises: 001_create_booking
Create Date: 2026-07-28 20:35:00.000000

"""
import uuid
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "002_architecture_hardening"
down_revision: Union[str, None] = "001_create_booking"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Initial seed data for environments
SEED_ENVIRONMENTS = [
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "code": "PERF01",
        "name": "Performance Environment 01",
        "description": "Primary high-throughput performance testing environment",
        "active": True
    },
    {
        "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "code": "PERF02",
        "name": "Performance Environment 02",
        "description": "Secondary performance testing environment for long-run soak tests",
        "active": True
    },
    {
        "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "code": "PERF03",
        "name": "Performance Environment 03",
        "description": "Isolated sandbox environment for component stress testing",
        "active": True
    },
    {
        "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "code": "UAT01",
        "name": "User Acceptance Testing 01",
        "description": "Shared UAT performance validation environment",
        "active": True
    }
]


def upgrade() -> None:
    # 1. Create environments table
    environments_table = op.create_table(
        "environments",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index(op.f("ix_environments_id"), "environments", ["id"], unique=False)
    op.create_index(op.f("ix_environments_code"), "environments", ["code"], unique=True)
    op.create_index(op.f("ix_environments_active"), "environments", ["active"], unique=False)

    # Seed environments table
    op.bulk_insert(environments_table, SEED_ENVIRONMENTS)

    # 2. Update bookings table columns
    op.add_column("bookings", sa.Column("environment_id", sa.Uuid(as_uuid=True), nullable=True))
    op.add_column("bookings", sa.Column("created_by", sa.String(length=255), nullable=True))
    op.add_column("bookings", sa.Column("updated_by", sa.String(length=255), nullable=True))
    op.add_column("bookings", sa.Column("deleted_by", sa.String(length=255), nullable=True))
    op.add_column("bookings", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    # Set default environment_id for any existing records to PERF01
    op.execute(
        f"UPDATE bookings SET environment_id = '{SEED_ENVIRONMENTS[0]['id']}' WHERE environment_id IS NULL"
    )
    if op.get_bind().dialect.name != "sqlite":
        op.alter_column("bookings", "environment_id", nullable=False)

    # Drop old string column 'environment' and its index
    with op.batch_alter_table("bookings") as batch_op:
        batch_op.drop_index("ix_bookings_environment")
        batch_op.drop_column("environment")

    # Add foreign key and indexes
    if op.get_bind().dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_bookings_environment_id_environments",
            "bookings", "environments",
            ["environment_id"], ["id"],
            ondelete="RESTRICT"
        )
    op.create_index(op.f("ix_bookings_environment_id"), "bookings", ["environment_id"], unique=False)
    op.create_index(op.f("ix_bookings_status"), "bookings", ["status"], unique=False)
    op.create_index(op.f("ix_bookings_deleted_at"), "bookings", ["deleted_at"], unique=False)
    op.create_index(
        "ix_bookings_env_date_deleted",
        "bookings",
        ["environment_id", "booking_date", "deleted_at"],
        unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_bookings_env_date_deleted", table_name="bookings")
    op.drop_index(op.f("ix_bookings_deleted_at"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_status"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_environment_id"), table_name="bookings")
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint("fk_bookings_environment_id_environments", "bookings", type_="foreignkey")
    
    op.add_column("bookings", sa.Column("environment", sa.String(length=50), nullable=True))
    op.execute("UPDATE bookings SET environment = 'PERF01'")
    op.alter_column("bookings", "environment", nullable=False)
    op.create_index(op.f("ix_bookings_environment"), "bookings", ["environment"], unique=False)

    op.drop_column("bookings", "deleted_at")
    op.drop_column("bookings", "deleted_by")
    op.drop_column("bookings", "updated_by")
    op.drop_column("bookings", "created_by")
    op.drop_column("bookings", "environment_id")

    op.drop_index(op.f("ix_environments_active"), table_name="environments")
    op.drop_index(op.f("ix_environments_code"), table_name="environments")
    op.drop_index(op.f("ix_environments_id"), table_name="environments")
    op.drop_table("environments")
