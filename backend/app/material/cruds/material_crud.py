from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.material.models.material import Material


async def get_material(db: AsyncSession, material_id: int) -> Optional[Material]:
    return await db.get(Material, material_id)


async def get_material_by_grade_thickness(
    db: AsyncSession,
    material_grade: str,
    thickness: float,
) -> Optional[Material]:
    result = await db.execute(
        select(Material).where(
            Material.material_grade == material_grade,
            Material.thickness == thickness,
        )
    )
    return result.scalar_one_or_none()


async def list_materials(db: AsyncSession, *, enabled: Optional[bool] = None) -> list[Material]:
    query = select(Material).order_by(Material.material_grade, Material.thickness)
    if enabled is not None:
        query = query.where(Material.enabled == enabled)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_material(db: AsyncSession, material: Material) -> Material:
    db.add(material)
    await db.flush()
    await db.refresh(material)
    return material
