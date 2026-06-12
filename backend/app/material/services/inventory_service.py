from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any
from uuid import uuid4

from openpyxl import Workbook, load_workbook
from sqlalchemy.ext.asyncio import AsyncSession

from app.material.cruds import inventory_crud, material_crud
from app.material.models.inventory_item import MaterialInventoryItem
from app.material.models.material import Material
from app.material.schemas.inventory import InventoryItemCreateIn, InventoryItemOut, InventoryItemUpdateIn
from app.material.schemas.inventory import (
    InventoryImportError,
    InventoryImportPreviewRow,
    InventoryImportResult,
)
from common.error_codes import ErrorCode
from common.exceptions import BusinessException
from common.log import logger
from common.pagination import PageData, PageMeta, normalize_page

ALLOWED_STATUS = {"available", "reserved", "consumed", "scrapped", "voided"}
INVENTORY_XLSX_ROW_LIMIT = 200
INVENTORY_EXPORT_HEADERS = [
    ("inventory_code", "板材名称"),
    ("empty_drawing_path", "图纸路径"),
    ("width", "宽"),
    ("length", "长"),
    ("material_grade", "材质"),
    ("thickness", "厚度"),
    ("quantity", "数量"),
]
HEADER_ALIASES = {
    "materialgrade": "material_grade",
    "material_grade": "material_grade",
    "材质": "material_grade",
    "width": "width",
    "宽": "width",
    "length": "length",
    "长": "length",
    "thickness": "thickness",
    "厚度": "thickness",
    "quantity": "quantity",
    "数量": "quantity",
    "usedquantity": "used_quantity",
    "used_quantity": "used_quantity",
    "usequantity": "used_quantity",
    "使用数量": "used_quantity",
}


def to_inventory_out(item: MaterialInventoryItem, material_grade: str) -> InventoryItemOut:
    return InventoryItemOut(
        id=item.id,
        inventory_code=item.inventory_code,
        material_id=item.material_id,
        material_grade=material_grade,
        inventory_type=item.inventory_type,
        width=item.width,
        length=item.length,
        thickness=item.thickness,
        quantity=item.quantity,
        remark=item.remark,
        source=item.source,
        location=item.location,
        status=item.status,
        reusable=item.reusable,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _format_dimension(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value).rstrip("0").rstrip(".")


def _sanitize_code_part(value: str) -> str:
    cleaned = value.strip().replace(" ", "")
    for char in (":", "/", "\\"):
        cleaned = cleaned.replace(char, "-")
    return cleaned or "UNKNOWN"


def build_inventory_code(
    *,
    material_grade: str,
    width: float,
    length: float,
    thickness: float,
    inventory_item_id: int,
) -> str:
    date_key = datetime.now().strftime("%Y%m%d")
    grade = _sanitize_code_part(material_grade)
    size = "x".join(
        [
            _format_dimension(width),
            _format_dimension(length),
            _format_dimension(thickness),
        ]
    )
    return f"RM:{grade}-{size}-{date_key}-{inventory_item_id}"


def _temporary_inventory_code() -> str:
    return f"RM:PENDING-{uuid4().hex[:16]}"


async def _ensure_material(
    db: AsyncSession,
    *,
    material_grade: str,
    thickness: float,
) -> Material:
    material = await material_crud.get_material_by_grade_thickness(
        db,
        material_grade,
        thickness,
    )
    if material is not None:
        return material
    return await material_crud.create_material(
        db,
        Material(
            material_grade=material_grade,
            thickness=thickness,
            spec_description="",
            default_unit="sheet",
            enabled=True,
        ),
    )


async def _assign_generated_inventory_code(
    item: MaterialInventoryItem,
    *,
    material_grade: str,
) -> None:
    item.inventory_code = build_inventory_code(
        material_grade=material_grade,
        width=item.width,
        length=item.length,
        thickness=item.thickness,
        inventory_item_id=item.id,
    )


async def create_inventory_item(
    db: AsyncSession,
    data: InventoryItemCreateIn,
) -> InventoryItemOut:
    material = await material_crud.get_material(db, data.material_id)
    if material is None:
        raise BusinessException(ErrorCode.MATERIAL_NOT_FOUND)

    inventory_code = data.inventory_code.strip() if data.inventory_code else ""
    if inventory_code:
        existing = await inventory_crud.get_inventory_item_by_code(db, inventory_code)
        if existing is not None:
            raise BusinessException(ErrorCode.INVENTORY_CODE_ALREADY_EXISTS)

    create_data = data.model_dump(exclude_none=True)
    create_data["inventory_code"] = inventory_code or _temporary_inventory_code()
    item = await inventory_crud.create_inventory_item(
        db,
        MaterialInventoryItem(**create_data),
    )
    if not inventory_code:
        await _assign_generated_inventory_code(item, material_grade=material.material_grade)
    await db.commit()
    await db.refresh(item)
    logger.info(
        "inventory_item_created id={} code={} material_id={} type={} quantity={} status={}",
        item.id,
        item.inventory_code,
        item.material_id,
        item.inventory_type,
        item.quantity,
        item.status,
    )
    return to_inventory_out(item, material.material_grade)


async def list_inventory_items(
    db: AsyncSession,
    *,
    material_id: int | None = None,
    inventory_type: str | None = None,
    status: str | None = None,
    reusable: bool | None = None,
    min_width: float | None = None,
    min_length: float | None = None,
    material_grade: str | None = None,
    thickness: float | None = None,
    inventory_code: str | None = None,
) -> list[InventoryItemOut]:
    rows = await inventory_crud.list_inventory_items(
        db,
        inventory_code=inventory_code,
        material_id=material_id,
        inventory_type=inventory_type,
        status=status,
        reusable=reusable,
        min_width=min_width,
        min_length=min_length,
        material_grade=material_grade,
        thickness=thickness,
    )
    return [to_inventory_out(item, grade) for item, grade in rows]


async def page_inventory_items(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    inventory_code: str | None = None,
    material_id: int | None = None,
    inventory_type: str | None = None,
    status: str | None = None,
    reusable: bool | None = None,
    min_width: float | None = None,
    min_length: float | None = None,
    material_grade: str | None = None,
    thickness: float | None = None,
) -> PageData[InventoryItemOut]:
    page, page_size = normalize_page(page, page_size)
    total = await inventory_crud.count_inventory_items(
        db,
        inventory_code=inventory_code,
        material_id=material_id,
        inventory_type=inventory_type,
        status=status,
        reusable=reusable,
        min_width=min_width,
        min_length=min_length,
        material_grade=material_grade,
        thickness=thickness,
    )
    rows = await inventory_crud.page_inventory_items(
        db,
        page=page,
        page_size=page_size,
        inventory_code=inventory_code,
        material_id=material_id,
        inventory_type=inventory_type,
        status=status,
        reusable=reusable,
        min_width=min_width,
        min_length=min_length,
        material_grade=material_grade,
        thickness=thickness,
    )
    return PageData(
        items=[to_inventory_out(item, grade) for item, grade in rows],
        meta=PageMeta(page=page, page_size=page_size, total=total),
    )


async def get_inventory_item_by_code(db: AsyncSession, inventory_code: str) -> InventoryItemOut:
    item = await inventory_crud.get_inventory_item_by_code(db, inventory_code)
    if item is None:
        raise BusinessException(ErrorCode.INVENTORY_ITEM_NOT_FOUND)
    material = await material_crud.get_material(db, item.material_id)
    if material is None:
        raise BusinessException(ErrorCode.MATERIAL_NOT_FOUND)
    return to_inventory_out(item, material.material_grade)


async def update_inventory_item(
    db: AsyncSession,
    inventory_item_id: int,
    data: InventoryItemUpdateIn,
) -> InventoryItemOut:
    item = await inventory_crud.get_inventory_item(db, inventory_item_id)
    if item is None:
        raise BusinessException(ErrorCode.INVENTORY_ITEM_NOT_FOUND)

    old_status = item.status
    old_quantity = item.quantity
    update_data = data.model_dump(exclude_unset=True)
    status = update_data.get("status")
    if status is not None and status not in ALLOWED_STATUS:
        raise BusinessException(ErrorCode.INVALID_INVENTORY_STATUS)
    for field, value in update_data.items():
        setattr(item, field, value)

    material = await material_crud.get_material(db, item.material_id)
    if material is None:
        raise BusinessException(ErrorCode.MATERIAL_NOT_FOUND)
    await db.commit()
    await db.refresh(item)
    logger.info(
        "inventory_item_updated id={} code={} old_status={} new_status={} "
        "old_quantity={} new_quantity={}",
        item.id,
        item.inventory_code,
        old_status,
        item.status,
        old_quantity,
        item.quantity,
    )
    return to_inventory_out(item, material.material_grade)


async def void_inventory_item(db: AsyncSession, inventory_item_id: int) -> InventoryItemOut:
    return await update_inventory_item(
        db,
        inventory_item_id,
        InventoryItemUpdateIn(status="voided"),
    )


def _normalize_header(value: Any) -> str:
    text = str(value or "").strip()
    return text.replace(" ", "").replace("-", "").lower()


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_float(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number") from exc


def _as_int(value: Any, field_name: str, default: int = 1) -> int:
    if value in (None, ""):
        return default
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if number <= 0:
        raise ValueError(f"{field_name} must be greater than 0")
    return number


def _as_non_negative_int(value: Any, field_name: str, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if number < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")
    return number


def _parse_inventory_xlsx(content: bytes) -> tuple[list[dict[str, Any]], list[InventoryImportError]]:
    try:
        workbook = load_workbook(BytesIO(content), data_only=True, read_only=True)
    except Exception as exc:
        raise BusinessException(ErrorCode.INVENTORY_XLSX_INVALID) from exc
    worksheet = workbook.active
    rows = list(worksheet.iter_rows(values_only=True))
    if not rows:
        return [], []

    header_map: dict[int, str] = {}
    for index, header in enumerate(rows[0]):
        normalized = _normalize_header(header)
        field_name = HEADER_ALIASES.get(normalized)
        if field_name is not None:
            header_map[index] = field_name

    parsed_rows: list[dict[str, Any]] = []
    errors: list[InventoryImportError] = []
    for row_number, row in enumerate(rows[1:], start=2):
        if all(value in (None, "") for value in row):
            continue
        raw = {field: row[index] for index, field in header_map.items() if index < len(row)}
        try:
            material_grade = _as_str(raw.get("material_grade"))
            if not material_grade:
                raise ValueError("material_grade is required")
            width = _as_float(raw.get("width"), "width")
            length = _as_float(raw.get("length"), "length")
            thickness = _as_float(raw.get("thickness"), "thickness")
            parsed_rows.append(
                {
                    "row_number": row_number,
                    "inventory_code": "",
                    "material_grade": material_grade,
                    "inventory_type": "leftover",
                    "width": width,
                    "length": length,
                    "thickness": thickness,
                    "quantity": _as_int(raw.get("quantity"), "quantity"),
                    "used_quantity": _as_non_negative_int(
                        raw.get("used_quantity"),
                        "used_quantity",
                    ),
                    "source": "",
                    "location": "",
                    "status": "available",
                    "reusable": True,
                    "remark": "",
                }
            )
        except ValueError as exc:
            errors.append(InventoryImportError(row_number=row_number, message=str(exc)))
    return parsed_rows, errors


def _to_preview_row(row: dict[str, Any], action: str) -> InventoryImportPreviewRow:
    return InventoryImportPreviewRow(
        row_number=row["row_number"],
        action=action,  # type: ignore[arg-type]
        inventory_code=row["inventory_code"] or None,
        material_grade=row["material_grade"],
        inventory_type=row["inventory_type"],
        width=row["width"],
        length=row["length"],
        thickness=row["thickness"],
        quantity=row["quantity"],
        used_quantity=row["used_quantity"],
        remark=row["remark"],
        source=row["source"],
        location=row["location"],
        status=row["status"],
        reusable=row["reusable"],
    )


def _build_import_result(
    *,
    current_quantity: int,
    used_quantity: int,
    matched: bool,
) -> tuple[int, str]:
    if used_quantity == 0:
        if matched:
            return current_quantity, f"本次操作使用数量为0，库存数 {current_quantity} - 0 = {current_quantity}。"
        return current_quantity, f"未匹配到库存，已新建。库存数 {current_quantity} - 使用数量 0 = {current_quantity}。"

    if used_quantity > current_quantity:
        shortage = used_quantity - current_quantity
        if matched:
            return 0, f"本次操作使用数量 {used_quantity} 大于库存数 {current_quantity}，已将库存数置为0，差额{shortage}请人工确认。"
        return 0, f"未匹配到库存，已新建。本次操作使用数量 {used_quantity} 大于导入数量 {current_quantity}，已将库存数置为0，差额{shortage}请人工确认。"

    next_quantity = current_quantity - used_quantity
    if matched:
        return next_quantity, f"本次操作使用数量 {used_quantity}，库存数 {current_quantity} - {used_quantity} = {next_quantity}。"
    return next_quantity, f"未匹配到库存，已新建。库存数 {current_quantity} - 使用数量 {used_quantity} = {next_quantity}。"


async def import_inventory_xlsx(
    db: AsyncSession,
    *,
    content: bytes,
    dry_run: bool,
) -> InventoryImportResult:
    rows, errors = _parse_inventory_xlsx(content)
    total_rows = len(rows) + len(errors)
    if total_rows > INVENTORY_XLSX_ROW_LIMIT:
        raise BusinessException(ErrorCode.INVENTORY_XLSX_LIMIT_EXCEEDED)

    preview_rows: list[InventoryImportPreviewRow] = []
    actions: list[str] = []
    simulated_by_spec: dict[tuple[str, float, float, float], dict[str, Any]] = {}
    for row in rows:
        spec_key = (row["material_grade"], row["thickness"], row["width"], row["length"])
        simulated = simulated_by_spec.get(spec_key)
        if simulated is None:
            material = await material_crud.get_material_by_grade_thickness(
                db,
                row["material_grade"],
                row["thickness"],
            )
            existing = None
            if material is not None:
                existing = await inventory_crud.get_inventory_item_by_spec(
                    db,
                    material_id=material.id,
                    width=row["width"],
                    length=row["length"],
                    thickness=row["thickness"],
                )
            matched = existing is not None
            current_quantity = existing.quantity if existing is not None else row["quantity"]
            row["inventory_code"] = existing.inventory_code if existing is not None else ""
        else:
            matched = True
            current_quantity = simulated["quantity"]
            row["inventory_code"] = simulated["inventory_code"]

        next_quantity, remark = _build_import_result(
            current_quantity=current_quantity,
            used_quantity=row["used_quantity"],
            matched=matched,
        )
        row["remark"] = remark
        simulated_by_spec[spec_key] = {
            "quantity": next_quantity,
            "inventory_code": row["inventory_code"],
        }
        action = "update" if matched else "create"
        actions.append(action)
        preview_rows.append(_to_preview_row(row, action))

    result = InventoryImportResult(
        dry_run=dry_run,
        total_rows=total_rows,
        valid_rows=len(rows),
        created=sum(1 for action in actions if action == "create"),
        updated=sum(1 for action in actions if action == "update"),
        skipped=len(errors),
        errors=errors,
        preview_rows=preview_rows,
    )
    if dry_run or errors:
        logger.info(
            "inventory_xlsx_import_preview dry_run={} total_rows={} valid_rows={} "
            "created={} updated={} skipped={}",
            dry_run,
            result.total_rows,
            result.valid_rows,
            result.created,
            result.updated,
            result.skipped,
        )
        return result

    created = 0
    updated = 0
    for row in rows:
        material = await _ensure_material(
            db,
            material_grade=row["material_grade"],
            thickness=row["thickness"],
        )
        existing = await inventory_crud.get_inventory_item_by_spec(
            db,
            material_id=material.id,
            width=row["width"],
            length=row["length"],
            thickness=row["thickness"],
        )
        if existing is None:
            next_quantity, remark = _build_import_result(
                current_quantity=row["quantity"],
                used_quantity=row["used_quantity"],
                matched=False,
            )
            item = await inventory_crud.create_inventory_item(
                db,
                MaterialInventoryItem(
                    inventory_code=row["inventory_code"] or _temporary_inventory_code(),
                    material_id=material.id,
                    inventory_type=row["inventory_type"],
                    width=row["width"],
                    length=row["length"],
                    thickness=row["thickness"],
                    quantity=next_quantity,
                    remark=remark,
                    source=row["source"],
                    location=row["location"],
                    status=row["status"],
                    reusable=row["reusable"],
                ),
            )
            if not row["inventory_code"]:
                await _assign_generated_inventory_code(item, material_grade=material.material_grade)
            created += 1
        else:
            next_quantity, remark = _build_import_result(
                current_quantity=existing.quantity,
                used_quantity=row["used_quantity"],
                matched=True,
            )
            existing.quantity = next_quantity
            existing.remark = remark
            updated += 1

    await db.commit()
    result.created = created
    result.updated = updated
    logger.info(
        "inventory_xlsx_import_applied total_rows={} valid_rows={} created={} updated={} skipped={}",
        result.total_rows,
        result.valid_rows,
        result.created,
        result.updated,
        result.skipped,
    )
    return result


async def export_inventory_xlsx(
    db: AsyncSession,
    *,
    inventory_codes: list[str],
) -> bytes:
    codes = []
    seen: set[str] = set()
    for code in inventory_codes:
        cleaned = code.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            codes.append(cleaned)
    if not codes:
        raise BusinessException(ErrorCode.INVENTORY_EXPORT_EMPTY)
    if len(codes) > INVENTORY_XLSX_ROW_LIMIT:
        raise BusinessException(ErrorCode.INVENTORY_XLSX_LIMIT_EXCEEDED)

    rows = await inventory_crud.list_inventory_items_by_codes(db, codes)
    row_by_code = {item.inventory_code: (item, grade) for item, grade in rows}
    if len(row_by_code) != len(codes):
        raise BusinessException(ErrorCode.INVENTORY_ITEM_NOT_FOUND)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Inventory"
    worksheet.append([header for _, header in INVENTORY_EXPORT_HEADERS])
    worksheet.column_dimensions["A"].width = 18
    worksheet.column_dimensions["B"].width = 42
    worksheet.column_dimensions["C"].width = 14
    worksheet.column_dimensions["D"].width = 14
    worksheet.column_dimensions["E"].width = 18

    for row_index, code in enumerate(codes, start=2):
        item, grade = row_by_code[code]
        worksheet.cell(row=row_index, column=1, value=item.inventory_code)
        worksheet.cell(row=row_index, column=2, value="")
        worksheet.cell(row=row_index, column=3, value=item.width)
        worksheet.cell(row=row_index, column=4, value=item.length)
        worksheet.cell(row=row_index, column=5, value=grade)
        worksheet.cell(row=row_index, column=6, value=item.thickness)
        worksheet.cell(row=row_index, column=7, value=item.quantity)

    output = BytesIO()
    workbook.save(output)
    logger.info("inventory_xlsx_exported row_count={}", len(codes))
    return output.getvalue()
