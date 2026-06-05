from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class CuttingPreparationOrder(Base):
    __tablename__ = "cutting_preparation_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    preparation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    exported_file_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class CuttingPreparationItem(Base):
    __tablename__ = "cutting_preparation_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("cutting_preparation_orders.id"),
        nullable=False,
        index=True,
    )
    source_inventory_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("material_inventory_items.id"),
        nullable=True,
        index=True,
    )
    sheet_name: Mapped[str] = mapped_column(String(100), nullable=False)
    drawing_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    width: Mapped[float] = mapped_column(Float, nullable=False)
    length: Mapped[float] = mapped_column(Float, nullable=False)
    material_grade: Mapped[str] = mapped_column(String(64), nullable=False)
    thickness: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class CuttingTemplateExport(Base):
    __tablename__ = "cutting_template_exports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("cutting_preparation_orders.id"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
