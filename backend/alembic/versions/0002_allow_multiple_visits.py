"""allow multiple visits per customer

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Drop unique constraint if it exists, then recreate as non-unique
    conn.execute(sa.text("""
        DROP INDEX IF EXISTS ix_prize_assignments_customer_id
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_prize_assignments_customer_id ON prize_assignments (customer_id)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_prize_assignments_customer_id"))
    conn.execute(sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_prize_assignments_customer_id ON prize_assignments (customer_id)
    """))
