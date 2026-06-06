from __future__ import annotations

from typing import Optional

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.material.models.inventory_item import MaterialInventoryItem
from app.material.models.material import Material


async def get_inventory_item(
    db: AsyncSession,
    inventory_item_id: int,
) -> Optional[MaterialInventoryItem]:
    return await db.get(MaterialInventoryItem, inventory_item_id)


async def get_inventory_item_by_code(
    db: AsyncSession,
    inventory_code: str,
) -> Optional[MaterialInventoryItem]:
    result = await db.execute(
        select(MaterialInventoryItem).where(
            MaterialInventoryItem.inventory_code == inventory_code,
        )
    )
    return result.scalar_one_or_none()


async def list_inventory_items_by_codes(
    db: AsyncSession,
    inventory_codes: list[str],
) -> list[tuple[MaterialInventoryItem, str]]:
    result = await db.execute(
        select(MaterialInventoryItem, Material.material_grade)
        .join(Material, Material.id == MaterialInventoryItem.material_id)
        .where(MaterialInventoryItem.inventory_code.in_(inventory_codes))
    )
    return [(row[0], row[1]) for row in result.all()]


async def get_inventory_item_by_spec(
    db: AsyncSession,
    *,
    material_id: int,
    width: float,
    length: float,
    thickness: float,
) -> Optional[MaterialInventoryItem]:
    result = await db.execute(
        select(MaterialInventoryItem)
        .where(
            MaterialInventoryItem.material_id == material_id,
            MaterialInventoryItem.width == width,
            MaterialInventoryItem.length == length,
            MaterialInventoryItem.thickness == thickness,
        )
        .order_by(MaterialInventoryItem.id.asc())
    )
    return result.scalars().first()


def _apply_filters(
    query: Select[tuple[MaterialInventoryItem]],
    *,
    inventory_code: Optional[str],
    material_id: Optional[int],
    inventory_type: Optional[str],
    status: Optional[str],
    reusable: Optional[bool],
    min_width: Optional[float],
    min_length: Optional[float],
    material_grade: Optional[str],
    thickness: Optional[float],
) -> Select[tuple[MaterialInventoryItem]]:
    if inventory_code is not None:
        query = query.where(MaterialInventoryItem.inventory_code == inventory_code)
    if material_id is not None:
        query = query.where(MaterialInventoryItem.material_id == material_id)
    if inventory_type is not None:
        query = query.where(MaterialInventoryItem.inventory_type == inventory_type)
    if status is not None:
        query = query.where(MaterialInventoryItem.status == status)
    if reusable is not None:
        query = query.where(MaterialInventoryItem.reusable == reusable)
    if min_width is not None:
        query = query.where(MaterialInventoryItem.width >= min_width)
    if min_length is not None:
        query = query.where(MaterialInventoryItem.length >= min_length)
    if material_grade is not None:
        query = query.where(Material.material_grade == material_grade)
    if thickness is not None:
        query = query.where(MaterialInventoryItem.thickness == thickness)
    return query


async def list_inventory_items(
    db: AsyncSession,
    *,
    inventory_code: Optional[str] = None,
    material_id: Optional[int] = None,
    inventory_type: Optional[str] = None,
    status: Optional[str] = None,
    reusable: Optional[bool] = None,
    min_width: Optional[float] = None,
    min_length: Optional[float] = None,
    material_grade: Optional[str] = None,
    thickness: Optional[float] = None,
) -> list[tuple[MaterialInventoryItem, str]]:
    query = (
        select(MaterialInventoryItem, Material.material_grade)
        .join(Material, Material.id == MaterialInventoryItem.material_id)
        .order_by(MaterialInventoryItem.id.desc())
    )
    query = _apply_filters(
        query,
        inventory_code=inventory_code,
        material_id=material_id,
        inventory_type=inventory_type,
        status=status,
        reusable=reusable,
        min_width=min_width,
        min_length=min_length,
        material_grade=material_grade,
        thickness=thickness,
    )
    result = await db.execute(query)
    return [(row[0], row[1]) for row in result.all()]


async def count_inventory_items(
    db: AsyncSession,
    *,
    inventory_code: Optional[str] = None,
    material_id: Optional[int] = None,
    inventory_type: Optional[str] = None,
    status: Optional[str] = None,
    reusable: Optional[bool] = None,
    min_width: Optional[float] = None,
    min_length: Optional[float] = None,
    material_grade: Optional[str] = None,
    thickness: Optional[float] = None,
) -> int:
    query = select(func.count()).select_from(MaterialInventoryItem).join(
        Material,
        Material.id == MaterialInventoryItem.material_id,
    )
    query = _apply_filters(
        query,
        inventory_code=inventory_code,
        material_id=material_id,
        inventory_type=inventory_type,
        status=status,
        reusable=reusable,
        min_width=min_width,
        min_length=min_length,
        material_grade=material_grade,
        thickness=thickness,
    )
    result = await db.execute(query)
    return int(result.scalar_one())


async def page_inventory_items(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    inventory_code: Optional[str] = None,
    material_id: Optional[int] = None,
    inventory_type: Optional[str] = None,
    status: Optional[str] = None,
    reusable: Optional[bool] = None,
    min_width: Optional[float] = None,
    min_length: Optional[float] = None,
    material_grade: Optional[str] = None,
    thickness: Optional[float] = None,
) -> list[tuple[MaterialInventoryItem, str]]:
    query = (
        select(MaterialInventoryItem, Material.material_grade)
        .join(Material, Material.id == MaterialInventoryItem.material_id)
        .order_by(MaterialInventoryItem.id.desc())
    )
    query = _apply_filters(
        query,
        inventory_code=inventory_code,
        material_id=material_id,
        inventory_type=inventory_type,
        status=status,
        reusable=reusable,
        min_width=min_width,
        min_length=min_length,
        material_grade=material_grade,
        thickness=thickness,
    )
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return [(row[0], row[1]) for row in result.all()]


async def create_inventory_item(
    db: AsyncSession,
    inventory_item: MaterialInventoryItem,
) -> MaterialInventoryItem:
    db.add(inventory_item)
    await db.flush()
    await db.refresh(inventory_item)
    return inventory_item
