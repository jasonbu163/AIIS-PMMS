from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.material.schemas.material import MaterialCreateIn, MaterialOut
from app.material.services import material_service
from common.response import StandardResponse
from core.deps import CurrentUser, get_current_user
from database.session import get_async_db

router = APIRouter()


@router.post("", response_model=StandardResponse[MaterialOut])
async def create_material_api(
    data: MaterialCreateIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[MaterialOut]:
    material = await material_service.create_material(db, data)
    return StandardResponse(data=material)


@router.get("", response_model=StandardResponse[list[MaterialOut]])
async def list_materials_api(
    enabled: bool | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[list[MaterialOut]]:
    materials = await material_service.list_materials(db, enabled=enabled)
    return StandardResponse(data=materials)
