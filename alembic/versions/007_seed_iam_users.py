"""seed initial IAM users (qa & requester)

Revision ID: 007_seed_iam_users
Revises: 006_user_management
Create Date: 2026-08-02 21:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import bcrypt

# revision identifiers, used by Alembic.
revision: str = "007_seed_iam_users"
down_revision: Union[str, None] = "006_user_management"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Pre-hashed bcrypt password for "ChangeMe123!"
DEFAULT_HASH = bcrypt.hashpw(b"ChangeMe123!", bcrypt.gensalt()).decode("utf-8")

QA_USER_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
REQUESTER_USER_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    true_val = "1" if is_sqlite else "true"

    # 1. Insert QA User if not exists
    op.execute(
        f"""
        INSERT INTO users (id, username, password_hash, full_name, email, role, is_active, created_at, updated_at)
        SELECT
            '{QA_USER_ID}',
            'qa',
            '{DEFAULT_HASH}',
            'QA Lead Manager',
            'qa.manager@example.com',
            'QA',
            {true_val},
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'qa');
        """
    )

    # 2. Insert Requester User if not exists
    op.execute(
        f"""
        INSERT INTO users (id, username, password_hash, full_name, email, role, is_active, created_at, updated_at)
        SELECT
            '{REQUESTER_USER_ID}',
            'requester',
            '{DEFAULT_HASH}',
            'Application Developer',
            'requester@example.com',
            'Requester',
            {true_val},
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'requester');
        """
    )

    # 3. Associate existing initial seeded bookings to QA user
    op.execute(
        f"""
        UPDATE bookings SET user_id = '{QA_USER_ID}' WHERE user_id IS NULL;
        """
    )


def downgrade() -> None:
    op.execute("UPDATE bookings SET user_id = NULL;")
    op.execute("DELETE FROM users WHERE username IN ('qa', 'requester');")
