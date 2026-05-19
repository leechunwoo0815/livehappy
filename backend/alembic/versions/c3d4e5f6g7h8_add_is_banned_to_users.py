"""add is_banned to users

Revision ID: c3d4e5f6g7h8
Revises: a1b2c3d4e5f6
Create Date: 2026-05-19 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6g7h8"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_banned", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False),
    )
    op.create_index(op.f("ix_users_is_banned"), "users", ["is_banned"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_is_banned"), table_name="users")
    op.drop_column("users", "is_banned")
