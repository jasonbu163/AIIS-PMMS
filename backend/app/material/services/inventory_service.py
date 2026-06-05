from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.material.cruds import inventory_crud, material_crud
from app.material.models.inventory_item import MaterialInventoryItem
from app.material.schemas.inventory import InventoryItemCreateIn, InventoryItemOut, InventoryItemUpdateIn
from common.error_codes import ErrorCode
from common.exceptions import BusinessException

ALLOWED_STATUS = {"available", "reserved", "consumed", "scrapped", "voided"}


def to_inventory_out(item: MaterialInventoryItem, material_grade: str) -> InventoryItemOut:
    return InventoryItemOut(
        id=item.id,
        material_id=item.material_id,
        material_grade=material_grade,
        inventory_type=item.inventory_type,
        width=item.width,
        length=item.length,
        thickness=item.thickness,
        quantity=item.quantity,
        source=item.source,
        location=item.location,
        status=item.status,
        reusable=item.reusable,
    )


async def create_inventory_item(
    db: AsyncSession,
    data: InventoryItemCreateIn,
) -> InventoryItemOut:
    material = await material_crud.get_material(db, data.material_id)
    if material is None:
        raise BusinessException(ErrorCode.MATERIAL_NOT_FOUND)

    item = await inventory_crud.create_inventory_item(
        db,
        MaterialInventoryItem(**data.model_dump()),
    )
    await db.commit()
    return to_inventory_out(item, material.material_grade)


async def list_inventory_items(
    db: AsyncSession,
    *,
    material_id: int | None = None,
    inventory_type: str | None = None,
    status: str | None = None,
    reusable: bool | None = None,
    min_width: float | None = None,
    min_length: float | None = None,
    material_grade: str | None = None,
    thickness: float | None = None,
) -> list[InventoryItemOut]:
    rows = await inventory_crud.list_inventory_items(
        db,
        material_id=material_id,
        inventory_type=inventory_type,
        status=status,
        reusable=reusable,
        min_width=min_width,
        min_length=min_length,
        material_grade=material_grade,
        thickness=thickness,
    )
    return [to_inventory_out(item, grade) for item, grade in rows]


async def update_inventory_item(
    db: AsyncSession,
    inventory_item_id: int,
    data: InventoryItemUpdateIn,
) -> InventoryItemOut:
    item = await inventory_crud.get_inventory_item(db, inventory_item_id)
    if item is None:
        raise BusinessException(ErrorCode.INVENTORY_ITEM_NOT_FOUND)

    update_data = data.model_dump(exclude_unset=True)
    status = update_data.get("status")
    if status is not None and status not in ALLOWED_STATUS:
        raise BusinessException(ErrorCode.INVALID_INVENTORY_STATUS)
    for field, value in update_data.items():
        setattr(item, field, value)

    material = await material_crud.get_material(db, item.material_id)
    if material is None:
        raise BusinessException(ErrorCode.MATERIAL_NOT_FOUND)
    await db.commit()
    await db.refresh(item)
    return to_inventory_out(item, material.material_grade)


async def void_inventory_item(db: AsyncSession, inventory_item_id: int) -> InventoryItemOut:
    return await update_inventory_item(
        db,
        inventory_item_id,
        InventoryItemUpdateIn(status="voided"),
    )
