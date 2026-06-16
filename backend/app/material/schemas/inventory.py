from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import Field

from common.schema_base import ApiSchema

InventoryType = Literal["whole_sheet", "leftover"]
InventoryStatus = Literal["available", "reserved", "consumed", "scrapped", "voided"]


class InventoryItemCreateIn(ApiSchema):
    inventory_code: Optional[str] = None
    material_id: int
    inventory_type: InventoryType
    width: float
    length: float
    thickness: float
    quantity: int = 1
    remark: str = ""
    source: str = ""
    location: str = ""
    status: InventoryStatus = "available"
    reusable: bool = True


class InventoryItemUpdateIn(ApiSchema):
    width: Optional[float] = None
    length: Optional[float] = None
    thickness: Optional[float] = None
    quantity: Optional[int] = None
    remark: Optional[str] = None
    source: Optional[str] = None
    location: Optional[str] = None
    status: Optional[InventoryStatus] = None
    reusable: Optional[bool] = None


class InventoryItemStockInIn(ApiSchema):
    quantity: int = Field(ge=1)
    source: str = "site-stock-in"
    location: Optional[str] = None
    remark: Optional[str] = None
    reusable: Optional[bool] = None


class InventoryItemConsumeIn(ApiSchema):
    quantity: int = Field(ge=1)
    source: str = "site-consume"
    remark: Optional[str] = None


class InventoryItemOut(ApiSchema):
    id: int
    inventory_code: str
    material_id: int
    material_grade: str
    inventory_type: str
    width: float
    length: float
    thickness: float
    quantity: int
    remark: str
    source: str
    location: str
    status: str
    reusable: bool
    created_at: datetime
    updated_at: datetime


class InventoryImportError(ApiSchema):
    row_number: int
    message: str


class InventoryImportPreviewRow(ApiSchema):
    row_number: int
    action: Literal["create", "consume", "stock_in"]
    inventory_code: Optional[str] = None
    material_grade: str
    inventory_type: str
    width: float
    length: float
    thickness: float
    quantity: int
    used_quantity: int
    added_quantity: int
    remark: str
    source: str
    location: str
    status: str
    reusable: bool


class InventoryImportResult(ApiSchema):
    dry_run: bool
    total_rows: int
    valid_rows: int
    created: int
    updated: int
    skipped: int
    errors: list[InventoryImportError] = Field(default_factory=list)
    preview_rows: list[InventoryImportPreviewRow] = Field(default_factory=list)


class InventoryExportIn(ApiSchema):
    inventory_codes: list[str] = Field(default_factory=list)
