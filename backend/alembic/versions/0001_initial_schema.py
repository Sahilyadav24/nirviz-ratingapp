"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS customers (
            id UUID PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            phone VARCHAR(15) NOT NULL,
            address TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        )
    """))
    conn.execute(sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_customers_phone ON customers (phone)
    """))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS otp_logs (
            id UUID PRIMARY KEY,
            phone VARCHAR(15) NOT NULL,
            otp_hash VARCHAR(64) NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            used BOOLEAN DEFAULT FALSE NOT NULL,
            attempts INTEGER DEFAULT 0 NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        )
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_otp_logs_phone ON otp_logs (phone)
    """))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS prizes (
            id UUID PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            probability FLOAT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS prize_assignments (
            id UUID PRIMARY KEY,
            customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
            prize_id UUID NOT NULL REFERENCES prizes(id) ON DELETE RESTRICT,
            assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            notified BOOLEAN DEFAULT FALSE NOT NULL
        )
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_prize_assignments_customer_id ON prize_assignments (customer_id)
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_prize_assignments_prize_id ON prize_assignments (prize_id)
    """))


def downgrade() -> None:
    op.drop_table("prize_assignments")
    op.drop_table("prizes")
    op.drop_table("otp_logs")
    op.drop_table("customers")
