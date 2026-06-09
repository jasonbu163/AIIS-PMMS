from __future__ import annotations

from typing import Optional

from common.schema_base import ApiSchema


class MaterialCreateIn(ApiSchema):
    material_grade: str
    thickness: float
    spec_description: str = ""
    default_unit: str = "sheet"
    enabled: bool = True


class MaterialUpdateIn(ApiSchema):
    material_grade: Optional[str] = None
    thickness: Optional[float] = None
    spec_description: Optional[str] = None
    default_unit: Optional[str] = None
    enabled: Optional[bool] = None


class MaterialOut(ApiSchema):
    id: int
    material_grade: str
    thickness: float
    spec_description: str
    default_unit: str
    enabled: bool
