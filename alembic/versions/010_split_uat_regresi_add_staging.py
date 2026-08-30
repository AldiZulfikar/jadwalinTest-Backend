"""split UAT and REGRESI environments, add STAGING environment

Revision ID: 010_split_uat_regresi_add_staging
Revises: 009_must_change_password
Create Date: 2026-08-30 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "010_split_uat_regresi_add_staging"
down_revision: Union[str, None] = "009_must_change_password"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    true_val = "1" if is_sqlite else "true"

    # 1. Update existing UAT/REGRESI record to UAT
    op.execute(
        "UPDATE environments SET code = 'UAT', name = 'UAT Environment', description = 'User acceptance testing environment' WHERE code = 'UAT/REGRESI' OR id = '22222222-2222-2222-2222-222222222222'"
    )

    # 2. Insert REGRESI environment if it doesn't exist
    op.execute(
        f"INSERT INTO environments (id, code, name, description, active) "
        f"SELECT '55555555-5555-5555-5555-555555555555', 'REGRESI', 'Regresi Environment', 'Regression testing environment', {true_val} "
        f"WHERE NOT EXISTS (SELECT 1 FROM environments WHERE code = 'REGRESI')"
    )

    # 3. Insert STAGING environment if it doesn't exist
    op.execute(
        f"INSERT INTO environments (id, code, name, description, active) "
        f"SELECT '66666666-6666-6666-6666-666666666666', 'STAGING', 'Staging Environment', 'Staging pre-production testing environment', {true_val} "
        f"WHERE NOT EXISTS (SELECT 1 FROM environments WHERE code = 'STAGING')"
    )


def downgrade() -> None:
    op.execute("DELETE FROM environments WHERE code IN ('REGRESI', 'STAGING')")
    op.execute(
        "UPDATE environments SET code = 'UAT/REGRESI', name = 'UAT & Regresi Environment', description = 'User acceptance and regression testing environment' WHERE code = 'UAT'"
    )
