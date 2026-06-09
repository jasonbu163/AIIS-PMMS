from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.material.schemas.material import MaterialCreateIn, MaterialOut, MaterialUpdateIn
from app.material.services import material_service
from common.pagination import PageData
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


@router.get("/page", response_model=StandardResponse[PageData[MaterialOut]])
async def page_materials_api(
    page: int = Query(default=1),
    page_size: int = Query(default=20, alias="pageSize"),
    enabled: bool | None = Query(default=None),
    material_grade: str | None = Query(default=None, alias="materialGrade"),
    thickness: float | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[PageData[MaterialOut]]:
    materials = await material_service.page_materials(
        db,
        page=page,
        page_size=page_size,
        enabled=enabled,
        material_grade=material_grade,
        thickness=thickness,
    )
    return StandardResponse(data=materials)


@router.get("/{material_id}", response_model=StandardResponse[MaterialOut])
async def get_material_api(
    material_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[MaterialOut]:
    material = await material_service.get_material(db, material_id)
    return StandardResponse(data=material)


@router.patch("/{material_id}", response_model=StandardResponse[MaterialOut])
async def update_material_api(
    material_id: int,
    data: MaterialUpdateIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[MaterialOut]:
    material = await material_service.update_material(db, material_id, data)
    return StandardResponse(data=material)
