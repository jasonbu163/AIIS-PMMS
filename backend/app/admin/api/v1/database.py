from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas.database_maintenance import (
    DatabaseMaintenanceResultOut,
    DatabaseStatusOut,
)
from app.admin.services import database_maintenance_service
from common.response import StandardResponse
from core.deps import CurrentUser, require_maintenance_access
from database.session import get_async_db

router = APIRouter()


@router.get("/status", response_model=StandardResponse[DatabaseStatusOut])
async def get_database_status_api(
    current_user: CurrentUser = Depends(require_maintenance_access),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[DatabaseStatusOut]:
    status = await database_maintenance_service.get_database_status(db)
    return StandardResponse(data=status)


@router.post("/initialize", response_model=StandardResponse[DatabaseMaintenanceResultOut])
async def initialize_database_api(
    current_user: CurrentUser = Depends(require_maintenance_access),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[DatabaseMaintenanceResultOut]:
    result = await database_maintenance_service.initialize_database(
        db,
        actor=current_user.user.username,
    )
    return StandardResponse(data=result)


@router.post("/upgrade", response_model=StandardResponse[DatabaseMaintenanceResultOut])
async def upgrade_database_api(
    current_user: CurrentUser = Depends(require_maintenance_access),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[DatabaseMaintenanceResultOut]:
    result = await database_maintenance_service.initialize_database(
        db,
        actor=current_user.user.username,
    )
    return StandardResponse(data=result)
