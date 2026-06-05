from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.material.cruds import material_crud
from app.material.models.material import Material
from app.material.schemas.material import MaterialCreateIn, MaterialOut
from common.error_codes import ErrorCode
from common.exceptions import BusinessException


async def create_material(db: AsyncSession, data: MaterialCreateIn) -> MaterialOut:
    existing = await material_crud.get_material_by_grade_thickness(
        db,
        data.material_grade,
        data.thickness,
    )
    if existing is not None:
        raise BusinessException(ErrorCode.MATERIAL_ALREADY_EXISTS)

    material = await material_crud.create_material(
        db,
        Material(**data.model_dump()),
    )
    await db.commit()
    return MaterialOut.model_validate(material)


async def list_materials(db: AsyncSession, *, enabled: bool | None = None) -> list[MaterialOut]:
    materials = await material_crud.list_materials(db, enabled=enabled)
    return [MaterialOut.model_validate(material) for material in materials]
