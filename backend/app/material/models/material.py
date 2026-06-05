from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Material(Base):
    __tablename__ = "materials"
    __table_args__ = (
        UniqueConstraint("material_grade", "thickness", name="uq_materials_grade_thickness"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    material_grade: Mapped[str] = mapped_column(String(64), nullable=False)
    thickness: Mapped[float] = mapped_column(Float, nullable=False)
    spec_description: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    default_unit: Mapped[str] = mapped_column(String(32), nullable=False, default="sheet")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
