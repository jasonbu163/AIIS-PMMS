"""add inventory template fields

Revision ID: 0005_inventory_template_fields
Revises: 0004_add_inventory_code
Create Date: 2026-06-06
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_inventory_template_fields"
down_revision = "0004_add_inventory_code"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "material_inventory_items",
        sa.Column("sheet_name", sa.String(length=100), nullable=False, server_default=""),
    )
    op.add_column(
        "material_inventory_items",
        sa.Column("drawing_path", sa.String(length=500), nullable=False, server_default=""),
    )
    op.alter_column(
        "material_inventory_items",
        "sheet_name",
        existing_type=sa.String(length=100),
        server_default=None,
    )
    op.alter_column(
        "material_inventory_items",
        "drawing_path",
        existing_type=sa.String(length=500),
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("material_inventory_items", "drawing_path")
    op.drop_column("material_inventory_items", "sheet_name")
