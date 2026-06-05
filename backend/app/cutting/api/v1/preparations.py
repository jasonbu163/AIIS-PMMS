from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.cutting.schemas.preparation import (
    PreparationItemCreateIn,
    PreparationOrderCreateIn,
    PreparationOrderOut,
    TemplateExportOut,
)
from app.cutting.services import preparation_service
from common.response import StandardResponse
from core.deps import CurrentUser, get_current_user
from database.session import get_async_db

router = APIRouter()


@router.post("", response_model=StandardResponse[PreparationOrderOut])
async def create_preparation_order_api(
    data: PreparationOrderCreateIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[PreparationOrderOut]:
    order = await preparation_service.create_order(
        db,
        data,
        actor=current_user.user.username,
    )
    return StandardResponse(data=order)


@router.get("", response_model=StandardResponse[list[PreparationOrderOut]])
async def list_preparation_orders_api(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[list[PreparationOrderOut]]:
    orders = await preparation_service.list_orders(db)
    return StandardResponse(data=orders)


@router.get("/{order_id}", response_model=StandardResponse[PreparationOrderOut])
async def get_preparation_order_api(
    order_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[PreparationOrderOut]:
    order = await preparation_service.get_order(db, order_id)
    return StandardResponse(data=order)


@router.post("/{order_id}/items", response_model=StandardResponse[PreparationOrderOut])
async def add_preparation_item_api(
    order_id: int,
    data: PreparationItemCreateIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[PreparationOrderOut]:
    order = await preparation_service.add_item(db, order_id, data)
    return StandardResponse(data=order)


@router.post("/{order_id}/export-template", response_model=StandardResponse[TemplateExportOut])
async def export_template_api(
    order_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[TemplateExportOut]:
    export = await preparation_service.export_template(
        db,
        order_id,
        actor=current_user.user.username,
    )
    return StandardResponse(data=export)


@router.get("/template-exports/{export_id}/download", response_class=FileResponse)
async def download_template_export_api(
    export_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> FileResponse:
    file_path, file_name = await preparation_service.get_export_file(db, export_id)
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
