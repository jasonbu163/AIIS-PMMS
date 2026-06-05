from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cutting.models.preparation import (
    CuttingPreparationItem,
    CuttingPreparationOrder,
    CuttingTemplateExport,
)


async def get_order(
    db: AsyncSession,
    order_id: int,
) -> CuttingPreparationOrder | None:
    return await db.get(CuttingPreparationOrder, order_id)


async def create_order(
    db: AsyncSession,
    order: CuttingPreparationOrder,
) -> CuttingPreparationOrder:
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


async def list_orders(db: AsyncSession) -> list[CuttingPreparationOrder]:
    result = await db.execute(
        select(CuttingPreparationOrder).order_by(CuttingPreparationOrder.id.desc())
    )
    return list(result.scalars().all())


async def create_item(
    db: AsyncSession,
    item: CuttingPreparationItem,
) -> CuttingPreparationItem:
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def list_items(
    db: AsyncSession,
    order_id: int,
) -> list[CuttingPreparationItem]:
    result = await db.execute(
        select(CuttingPreparationItem)
        .where(CuttingPreparationItem.order_id == order_id)
        .order_by(CuttingPreparationItem.sort_order, CuttingPreparationItem.id)
    )
    return list(result.scalars().all())


async def create_export(
    db: AsyncSession,
    export: CuttingTemplateExport,
) -> CuttingTemplateExport:
    db.add(export)
    await db.flush()
    await db.refresh(export)
    return export


async def get_export(
    db: AsyncSession,
    export_id: int,
) -> CuttingTemplateExport | None:
    return await db.get(CuttingTemplateExport, export_id)
