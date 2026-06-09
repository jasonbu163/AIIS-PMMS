"""use unicode username

Revision ID: 0008_use_unicode_username
Revises: 0007_use_unicode_text_columns
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_use_unicode_username"
down_revision = "0007_use_unicode_text_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.alter_column(
        "users",
        "username",
        existing_type=sa.String(length=64),
        type_=sa.Unicode(length=64),
        existing_nullable=False,
    )
    op.create_unique_constraint("uq_users_username", "users", ["username"])
    op.create_index("ix_users_username", "users", ["username"])


def downgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.alter_column(
        "users",
        "username",
        existing_type=sa.Unicode(length=64),
        type_=sa.String(length=64),
        existing_nullable=False,
    )
    op.create_unique_constraint("uq_users_username", "users", ["username"])
    op.create_index("ix_users_username", "users", ["username"])
