from __future__ import annotations

from common.schema_base import ApiSchema


class MaterialCreateIn(ApiSchema):
    material_grade: str
    thickness: float
    spec_description: str = ""
    default_unit: str = "sheet"
    enabled: bool = True


class MaterialOut(ApiSchema):
    id: int
    material_grade: str
    thickness: float
    spec_description: str
    default_unit: str
    enabled: bool
