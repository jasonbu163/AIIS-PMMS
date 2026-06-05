"""create material inventory tables

Revision ID: 0002_material_inventory
Revises: 0001_create_auth_tables
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_material_inventory"
down_revision = "0001_create_auth_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("material_grade", sa.String(length=64), nullable=False),
        sa.Column("thickness", sa.Float(), nullable=False),
        sa.Column("spec_description", sa.String(length=255), nullable=False),
        sa.Column("default_unit", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "material_grade",
            "thickness",
            name="uq_materials_grade_thickness",
        ),
    )
    op.create_table(
        "material_inventory_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=False),
        sa.Column("inventory_type", sa.String(length=32), nullable=False),
        sa.Column("width", sa.Float(), nullable=False),
        sa.Column("length", sa.Float(), nullable=False),
        sa.Column("thickness", sa.Float(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reusable", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_material_inventory_items_inventory_type",
        "material_inventory_items",
        ["inventory_type"],
    )
    op.create_index(
        "ix_material_inventory_items_material_id",
        "material_inventory_items",
        ["material_id"],
    )
    op.create_index(
        "ix_material_inventory_items_status",
        "material_inventory_items",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_material_inventory_items_status", table_name="material_inventory_items")
    op.drop_index("ix_material_inventory_items_material_id", table_name="material_inventory_items")
    op.drop_index("ix_material_inventory_items_inventory_type", table_name="material_inventory_items")
    op.drop_table("material_inventory_items")
    op.drop_table("materials")
