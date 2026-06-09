from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.material.models.inventory_item import MaterialInventoryItem
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


def _apply_filters(
    query,
    *,
    enabled: Optional[bool],
    material_grade: Optional[str],
    thickness: Optional[float],
):
    if enabled is not None:
        query = query.where(Material.enabled == enabled)
    if material_grade:
        query = query.where(Material.material_grade.like(f"%{material_grade}%"))
    if thickness is not None:
        query = query.where(Material.thickness == thickness)
    return query


async def count_materials(
    db: AsyncSession,
    *,
    enabled: Optional[bool] = None,
    material_grade: Optional[str] = None,
    thickness: Optional[float] = None,
) -> int:
    query = _apply_filters(
        select(func.count()).select_from(Material),
        enabled=enabled,
        material_grade=material_grade,
        thickness=thickness,
    )
    result = await db.execute(query)
    return int(result.scalar_one())


async def page_materials(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    enabled: Optional[bool] = None,
    material_grade: Optional[str] = None,
    thickness: Optional[float] = None,
) -> list[Material]:
    query = _apply_filters(
        select(Material).order_by(Material.material_grade, Material.thickness),
        enabled=enabled,
        material_grade=material_grade,
        thickness=thickness,
    )
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_inventory_refs(db: AsyncSession, material_id: int) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(MaterialInventoryItem)
        .where(MaterialInventoryItem.material_id == material_id)
    )
    return int(result.scalar_one())


async def create_material(db: AsyncSession, material: Material) -> Material:
    db.add(material)
    await db.flush()
    await db.refresh(material)
    return material
