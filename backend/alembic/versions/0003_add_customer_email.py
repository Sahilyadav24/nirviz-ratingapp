"""add email to customers

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        ALTER TABLE customers ADD COLUMN IF NOT EXISTS email VARCHAR(255)
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_customers_email ON customers (email)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_customers_email"))
    conn.execute(sa.text("ALTER TABLE customers DROP COLUMN IF EXISTS email"))
