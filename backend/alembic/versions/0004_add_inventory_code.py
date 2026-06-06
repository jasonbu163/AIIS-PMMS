"""add inventory code

Revision ID: 0004_add_inventory_code
Revises: 0003_preparation_export
Create Date: 2026-06-05
"""

from __future__ import annotations

from datetime import datetime

from alembic import op
import sqlalchemy as sa

revision = "0004_add_inventory_code"
down_revision = "0003_preparation_export"
branch_labels = None
depends_on = None


def _format_dimension(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value).rstrip("0").rstrip(".")


def _sanitize_code_part(value: str) -> str:
    cleaned = value.strip().replace(" ", "")
    for char in (":", "/", "\\"):
        cleaned = cleaned.replace(char, "-")
    return cleaned or "UNKNOWN"


def _build_inventory_code(
    *,
    material_grade: str,
    width: float,
    length: float,
    thickness: float,
    inventory_item_id: int,
) -> str:
    date_key = datetime.now().strftime("%Y%m%d")
    grade = _sanitize_code_part(material_grade)
    size = "x".join(
        [
            _format_dimension(width),
            _format_dimension(length),
            _format_dimension(thickness),
        ]
    )
    return f"RM:{grade}-{size}-{date_key}-{inventory_item_id}"


def upgrade() -> None:
    op.add_column(
        "material_inventory_items",
        sa.Column("inventory_code", sa.String(length=128), nullable=True),
    )

    bind = op.get_bind()
    rows = list(
        bind.execute(
            sa.text(
                """
                SELECT i.id, i.width, i.length, i.thickness, m.material_grade
                FROM material_inventory_items AS i
                JOIN materials AS m ON m.id = i.material_id
                """
            )
        )
    )
    for row in rows:
        bind.execute(
            sa.text(
                """
                UPDATE material_inventory_items
                SET inventory_code = :inventory_code
                WHERE id = :id
                """
            ),
            {
                "id": row.id,
                "inventory_code": _build_inventory_code(
                    material_grade=row.material_grade,
                    width=row.width,
                    length=row.length,
                    thickness=row.thickness,
                    inventory_item_id=row.id,
                ),
            },
        )

    op.alter_column(
        "material_inventory_items",
        "inventory_code",
        existing_type=sa.String(length=128),
        nullable=False,
    )
    op.create_index(
        "ix_material_inventory_items_inventory_code",
        "material_inventory_items",
        ["inventory_code"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_material_inventory_items_inventory_code", table_name="material_inventory_items")
    op.drop_column("material_inventory_items", "inventory_code")
