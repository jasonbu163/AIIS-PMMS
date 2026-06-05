"""create cutting preparation tables

Revision ID: 0003_preparation_export
Revises: 0002_material_inventory
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_preparation_export"
down_revision = "0002_material_inventory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cutting_preparation_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("preparation_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("exported_file_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cutting_preparation_orders_preparation_date",
        "cutting_preparation_orders",
        ["preparation_date"],
    )
    op.create_index(
        "ix_cutting_preparation_orders_status",
        "cutting_preparation_orders",
        ["status"],
    )
    op.create_table(
        "cutting_preparation_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("source_inventory_item_id", sa.Integer(), nullable=True),
        sa.Column("sheet_name", sa.String(length=100), nullable=False),
        sa.Column("drawing_path", sa.String(length=500), nullable=False),
        sa.Column("width", sa.Float(), nullable=False),
        sa.Column("length", sa.Float(), nullable=False),
        sa.Column("material_grade", sa.String(length=64), nullable=False),
        sa.Column("thickness", sa.Float(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["cutting_preparation_orders.id"]),
        sa.ForeignKeyConstraint(["source_inventory_item_id"], ["material_inventory_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cutting_preparation_items_order_id",
        "cutting_preparation_items",
        ["order_id"],
    )
    op.create_index(
        "ix_cutting_preparation_items_source_inventory_item_id",
        "cutting_preparation_items",
        ["source_inventory_item_id"],
    )
    op.create_table(
        "cutting_template_exports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["cutting_preparation_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cutting_template_exports_order_id",
        "cutting_template_exports",
        ["order_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_cutting_template_exports_order_id", table_name="cutting_template_exports")
    op.drop_table("cutting_template_exports")
    op.drop_index(
        "ix_cutting_preparation_items_source_inventory_item_id",
        table_name="cutting_preparation_items",
    )
    op.drop_index("ix_cutting_preparation_items_order_id", table_name="cutting_preparation_items")
    op.drop_table("cutting_preparation_items")
    op.drop_index(
        "ix_cutting_preparation_orders_status",
        table_name="cutting_preparation_orders",
    )
    op.drop_index(
        "ix_cutting_preparation_orders_preparation_date",
        table_name="cutting_preparation_orders",
    )
    op.drop_table("cutting_preparation_orders")
