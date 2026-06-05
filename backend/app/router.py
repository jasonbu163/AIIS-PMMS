from fastapi import APIRouter

from app.admin.api.v1.database import router as database_admin_router
from app.cutting.api.v1.preparations import router as cutting_preparations_router
from app.material.api.v1.inventory_items import router as inventory_items_router
from app.material.api.v1.materials import router as materials_router
from app.user.api.v1.auth import router as auth_router
from app.user.api.v1.users import router as users_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(
    database_admin_router,
    prefix="/admin/database",
    tags=["admin-database"],
)
router.include_router(
    cutting_preparations_router,
    prefix="/cutting-preparations",
    tags=["cutting-preparations"],
)
router.include_router(materials_router, prefix="/materials", tags=["materials"])
router.include_router(
    inventory_items_router,
    prefix="/inventory-items",
    tags=["inventory-items"],
)
