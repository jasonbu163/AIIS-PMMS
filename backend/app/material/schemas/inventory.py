from __future__ import annotations

from typing import Literal, Optional

from common.schema_base import ApiSchema

InventoryType = Literal["whole_sheet", "leftover"]
InventoryStatus = Literal["available", "reserved", "consumed", "scrapped", "voided"]


class InventoryItemCreateIn(ApiSchema):
    material_id: int
    inventory_type: InventoryType
    width: float
    length: float
    thickness: float
    quantity: int = 1
    source: str = ""
    location: str = ""
    status: InventoryStatus = "available"
    reusable: bool = True


class InventoryItemUpdateIn(ApiSchema):
    width: Optional[float] = None
    length: Optional[float] = None
    thickness: Optional[float] = None
    quantity: Optional[int] = None
    source: Optional[str] = None
    location: Optional[str] = None
    status: Optional[InventoryStatus] = None
    reusable: Optional[bool] = None


class InventoryItemOut(ApiSchema):
    id: int
    material_id: int
    material_grade: str
    inventory_type: str
    width: float
    length: float
    thickness: float
    quantity: int
    source: str
    location: str
    status: str
    reusable: bool
