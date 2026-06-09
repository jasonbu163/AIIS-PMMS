"""use unicode text columns

Revision ID: 0007_use_unicode_text_columns
Revises: 0006_inventory_spec_import
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_use_unicode_text_columns"
down_revision = "0006_inventory_spec_import"
branch_labels = None
depends_on = None


def _alter_to_unicode(table_name: str, column_name: str, length: int) -> None:
    op.alter_column(
        table_name,
        column_name,
        existing_type=sa.String(length=length),
        type_=sa.Unicode(length=length),
        existing_nullable=False,
    )


def _alter_to_string(table_name: str, column_name: str, length: int) -> None:
    op.alter_column(
        table_name,
        column_name,
        existing_type=sa.Unicode(length=length),
        type_=sa.String(length=length),
        existing_nullable=False,
    )


def upgrade() -> None:
    op.drop_constraint("uq_materials_grade_thickness", "materials", type_="unique")
    op.drop_index("ix_material_inventory_items_inventory_code", table_name="material_inventory_items")

    _alter_to_unicode("materials", "material_grade", 64)
    _alter_to_unicode("materials", "spec_description", 255)
    _alter_to_unicode("materials", "default_unit", 32)

    _alter_to_unicode("material_inventory_items", "inventory_code", 128)
    _alter_to_unicode("material_inventory_items", "remark", 500)
    _alter_to_unicode("material_inventory_items", "source", 255)
    _alter_to_unicode("material_inventory_items", "location", 100)

    _alter_to_unicode("cutting_preparation_orders", "created_by", 64)
    _alter_to_unicode("cutting_preparation_items", "sheet_name", 100)
    _alter_to_unicode("cutting_preparation_items", "drawing_path", 500)
    _alter_to_unicode("cutting_preparation_items", "material_grade", 64)
    _alter_to_unicode("cutting_template_exports", "file_name", 255)
    _alter_to_unicode("cutting_template_exports", "file_path", 1000)
    _alter_to_unicode("cutting_template_exports", "created_by", 64)

    _alter_to_unicode("users", "display_name", 100)
    _alter_to_unicode("auth_token_revocations", "reason", 100)

    op.create_unique_constraint(
        "uq_materials_grade_thickness",
        "materials",
        ["material_grade", "thickness"],
    )
    op.create_index(
        "ix_material_inventory_items_inventory_code",
        "material_inventory_items",
        ["inventory_code"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_material_inventory_items_inventory_code", table_name="material_inventory_items")
    op.drop_constraint("uq_materials_grade_thickness", "materials", type_="unique")

    _alter_to_string("auth_token_revocations", "reason", 100)
    _alter_to_string("users", "display_name", 100)

    _alter_to_string("cutting_template_exports", "created_by", 64)
    _alter_to_string("cutting_template_exports", "file_path", 1000)
    _alter_to_string("cutting_template_exports", "file_name", 255)
    _alter_to_string("cutting_preparation_items", "material_grade", 64)
    _alter_to_string("cutting_preparation_items", "drawing_path", 500)
    _alter_to_string("cutting_preparation_items", "sheet_name", 100)
    _alter_to_string("cutting_preparation_orders", "created_by", 64)

    _alter_to_string("material_inventory_items", "location", 100)
    _alter_to_string("material_inventory_items", "source", 255)
    _alter_to_string("material_inventory_items", "remark", 500)
    _alter_to_string("material_inventory_items", "inventory_code", 128)

    _alter_to_string("materials", "default_unit", 32)
    _alter_to_string("materials", "spec_description", 255)
    _alter_to_string("materials", "material_grade", 64)

    op.create_unique_constraint(
        "uq_materials_grade_thickness",
        "materials",
        ["material_grade", "thickness"],
    )
    op.create_index(
        "ix_material_inventory_items_inventory_code",
        "material_inventory_items",
        ["inventory_code"],
        unique=True,
    )
