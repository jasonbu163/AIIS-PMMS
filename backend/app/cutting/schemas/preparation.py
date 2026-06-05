from __future__ import annotations

from datetime import date, datetime

from common.schema_base import ApiSchema


class PreparationOrderCreateIn(ApiSchema):
    preparation_date: date


class PreparationItemCreateIn(ApiSchema):
    sheet_name: str
    drawing_path: str = ""
    width: float
    length: float
    material_grade: str
    thickness: float
    quantity: int = 1
    source_inventory_item_id: int | None = None
    sort_order: int = 0


class PreparationItemOut(ApiSchema):
    id: int
    order_id: int
    source_inventory_item_id: int | None
    sheet_name: str
    drawing_path: str
    width: float
    length: float
    material_grade: str
    thickness: float
    quantity: int
    sort_order: int


class TemplateExportOut(ApiSchema):
    id: int
    order_id: int
    file_name: str
    file_path: str
    row_count: int
    created_by: str
    created_at: datetime
    download_url: str


class PreparationOrderOut(ApiSchema):
    id: int
    preparation_date: date
    status: str
    created_by: str
    exported_file_id: int | None
    items: list[PreparationItemOut]
