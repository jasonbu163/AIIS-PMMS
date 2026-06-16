from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.material.schemas.inventory import (
    InventoryExportIn,
    InventoryImportResult,
    InventoryItemConsumeIn,
    InventoryItemCreateIn,
    InventoryItemOut,
    InventoryItemStockInIn,
    InventoryItemUpdateIn,
)
from app.material.services import inventory_service
from common.pagination import PageData
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
    inventory_code: str | None = Query(default=None, alias="inventoryCode"),
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
    return StandardResponse(data=items)


@router.get("/page", response_model=StandardResponse[PageData[InventoryItemOut]])
async def page_inventory_items_api(
    page: int = Query(default=1),
    page_size: int = Query(default=20, alias="pageSize"),
    inventory_code: str | None = Query(default=None, alias="inventoryCode"),
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
) -> StandardResponse[PageData[InventoryItemOut]]:
    items = await inventory_service.page_inventory_items(
        db,
        page=page,
        page_size=page_size,
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
    return StandardResponse(data=items)


@router.get("/by-code", response_model=StandardResponse[InventoryItemOut])
async def get_inventory_item_by_code_api(
    inventory_code: str = Query(alias="inventoryCode"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[InventoryItemOut]:
    item = await inventory_service.get_inventory_item_by_code(db, inventory_code)
    return StandardResponse(data=item)


@router.post("/import-xlsx", response_model=StandardResponse[InventoryImportResult])
async def import_inventory_xlsx_api(
    dry_run: bool = Query(default=True, alias="dryRun"),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[InventoryImportResult]:
    content = await file.read()
    result = await inventory_service.import_inventory_xlsx(
        db,
        content=content,
        dry_run=dry_run,
    )
    return StandardResponse(data=result)


@router.post("/export-xlsx")
async def export_inventory_xlsx_api(
    data: InventoryExportIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> Response:
    content = await inventory_service.export_inventory_xlsx(
        db,
        inventory_codes=data.inventory_codes,
    )
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="inventory-items.xlsx"',
        },
    )


@router.patch("/{inventory_item_id}", response_model=StandardResponse[InventoryItemOut])
async def update_inventory_item_api(
    inventory_item_id: int,
    data: InventoryItemUpdateIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[InventoryItemOut]:
    item = await inventory_service.update_inventory_item(db, inventory_item_id, data)
    return StandardResponse(data=item)


@router.post("/{inventory_item_id}/stock-in", response_model=StandardResponse[InventoryItemOut])
async def stock_in_inventory_item_api(
    inventory_item_id: int,
    data: InventoryItemStockInIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[InventoryItemOut]:
    item = await inventory_service.stock_in_inventory_item(db, inventory_item_id, data)
    return StandardResponse(data=item)


@router.post("/{inventory_item_id}/consume", response_model=StandardResponse[InventoryItemOut])
async def consume_inventory_item_api(
    inventory_item_id: int,
    data: InventoryItemConsumeIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[InventoryItemOut]:
    item = await inventory_service.consume_inventory_item(db, inventory_item_id, data)
    return StandardResponse(data=item)


@router.post("/{inventory_item_id}/void", response_model=StandardResponse[InventoryItemOut])
async def void_inventory_item_api(
    inventory_item_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[InventoryItemOut]:
    item = await inventory_service.void_inventory_item(db, inventory_item_id)
    return StandardResponse(data=item)
