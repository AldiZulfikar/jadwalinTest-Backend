"""update environments master data to DEV, UAT/REGRESI, PRODUCTION

Revision ID: 005_update_environments
Revises: 004_booking_lifecycle
Create Date: 2026-08-02 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_update_environments"
down_revision: Union[str, None] = "004_booking_lifecycle"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE environments SET code = 'DEV', name = 'Development Environment', description = 'Isolated development environment for pre-testing' WHERE code = 'PERF01' OR id = '11111111-1111-1111-1111-111111111111'"
    )
    op.execute(
        "UPDATE environments SET code = 'UAT/REGRESI', name = 'UAT & Regresi Environment', description = 'User acceptance and regression testing environment' WHERE code = 'PERF02' OR id = '22222222-2222-2222-2222-222222222222'"
    )
    op.execute(
        "UPDATE environments SET code = 'PRODUCTION', name = 'Production Environment', description = 'Production performance validation environment' WHERE code = 'PERF03' OR id = '33333333-3333-3333-3333-333333333333'"
    )
    op.execute(
        "UPDATE environments SET active = 0 WHERE code = 'UAT01' OR id = '44444444-4444-4444-4444-444444444444'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE environments SET code = 'PERF01', name = 'Performance Environment 01' WHERE code = 'DEV'"
    )
    op.execute(
        "UPDATE environments SET code = 'PERF02', name = 'Performance Environment 02' WHERE code = 'UAT/REGRESI'"
    )
    op.execute(
        "UPDATE environments SET code = 'PERF03', name = 'Performance Environment 03' WHERE code = 'PRODUCTION'"
    )
    op.execute(
        "UPDATE environments SET active = 1 WHERE code = 'UAT01'"
    )
