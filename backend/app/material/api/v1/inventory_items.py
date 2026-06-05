from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.material.schemas.inventory import InventoryItemCreateIn, InventoryItemOut, InventoryItemUpdateIn
from app.material.services import inventory_service
from common.response import StandardResponse
from core.deps import CurrentUser, get_current_user
from database.session import get_async_db

router = APIRouter()


@router.post("", response_model=StandardResponse[InventoryItemOut])
async def create_inventory_item_api(
    data: InventoryItemCreateIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[InventoryItemOut]:
    item = await inventory_service.create_inventory_item(db, data)
    return StandardResponse(data=item)


@router.get("", response_model=StandardResponse[list[InventoryItemOut]])
async def list_inventory_items_api(
    material_id: int | None = Query(default=None, alias="materialId"),
    inventory_type: str | None = Query(default=None, alias="inventoryType"),
    status: str | None = Query(default=None),
    reusable: bool | None = Query(default=None),
    min_width: float | None = Query(default=None, alias="minWidth"),
    min_length: float | None = Query(default=None, alias="minLength"),
    material_grade: str | None = Query(default=None, alias="materialGrade"),
    thickness: float | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[list[InventoryItemOut]]:
    items = await inventory_service.list_inventory_items(
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
    return StandardResponse(data=items)


@router.patch("/{inventory_item_id}", response_model=StandardResponse[InventoryItemOut])
async def update_inventory_item_api(
    inventory_item_id: int,
    data: InventoryItemUpdateIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[InventoryItemOut]:
    item = await inventory_service.update_inventory_item(db, inventory_item_id, data)
    return StandardResponse(data=item)


@router.post("/{inventory_item_id}/void", response_model=StandardResponse[InventoryItemOut])
async def void_inventory_item_api(
    inventory_item_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[InventoryItemOut]:
    item = await inventory_service.void_inventory_item(db, inventory_item_id)
    return StandardResponse(data=item)
