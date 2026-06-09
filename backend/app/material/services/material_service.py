from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.material.cruds import material_crud
from app.material.models.material import Material
from app.material.schemas.material import MaterialCreateIn, MaterialOut, MaterialUpdateIn
from common.error_codes import ErrorCode
from common.exceptions import BusinessException
from common.pagination import PageData, PageMeta, normalize_page


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


async def page_materials(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    enabled: bool | None = None,
    material_grade: str | None = None,
    thickness: float | None = None,
) -> PageData[MaterialOut]:
    page, page_size = normalize_page(page, page_size)
    total = await material_crud.count_materials(
        db,
        enabled=enabled,
        material_grade=material_grade,
        thickness=thickness,
    )
    materials = await material_crud.page_materials(
        db,
        page=page,
        page_size=page_size,
        enabled=enabled,
        material_grade=material_grade,
        thickness=thickness,
    )
    return PageData(
        items=[MaterialOut.model_validate(material) for material in materials],
        meta=PageMeta(page=page, page_size=page_size, total=total),
    )


async def get_material(db: AsyncSession, material_id: int) -> MaterialOut:
    material = await material_crud.get_material(db, material_id)
    if material is None:
        raise BusinessException(ErrorCode.MATERIAL_NOT_FOUND)
    return MaterialOut.model_validate(material)


async def update_material(
    db: AsyncSession,
    material_id: int,
    data: MaterialUpdateIn,
) -> MaterialOut:
    material = await material_crud.get_material(db, material_id)
    if material is None:
        raise BusinessException(ErrorCode.MATERIAL_NOT_FOUND)

    update_data = data.model_dump(exclude_unset=True)
    next_grade = update_data.get("material_grade", material.material_grade)
    next_thickness = update_data.get("thickness", material.thickness)
    grade_changed = next_grade != material.material_grade
    thickness_changed = next_thickness != material.thickness
    spec_changed = grade_changed or thickness_changed
    if spec_changed:
        ref_count = await material_crud.count_inventory_refs(db, material.id)
        if ref_count > 0:
            raise BusinessException(ErrorCode.MATERIAL_IN_USE)
        existing = await material_crud.get_material_by_grade_thickness(
            db,
            next_grade,
            next_thickness,
        )
        if existing is not None and existing.id != material.id:
            raise BusinessException(ErrorCode.MATERIAL_ALREADY_EXISTS)

    for field, value in update_data.items():
        setattr(material, field, value)

    await db.commit()
    await db.refresh(material)
    return MaterialOut.model_validate(material)
