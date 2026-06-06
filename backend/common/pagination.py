from __future__ import annotations

from typing import Generic, TypeVar

from common.schema_base import ApiSchema

T = TypeVar("T")


class PageMeta(ApiSchema):
    page: int
    page_size: int
    total: int


class PageData(ApiSchema, Generic[T]):
    items: list[T]
    meta: PageMeta


def normalize_page(page: int, page_size: int) -> tuple[int, int]:
    return max(page, 1), min(max(page_size, 1), 200)
