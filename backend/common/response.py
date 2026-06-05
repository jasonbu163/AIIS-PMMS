from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, field_serializer

from common.schema_base import to_camel

T = TypeVar("T")


def serialize_api_data(value: Any) -> Any:
    if isinstance(value, BaseModel):
        value = value.model_dump(by_alias=True)
    if isinstance(value, Mapping):
        return {
            to_camel(key) if isinstance(key, str) else key: serialize_api_data(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [serialize_api_data(item) for item in value]
    return value


class StandardResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None

    @field_serializer("data")
    def serialize_data(self, data: Optional[T]) -> Any:
        return serialize_api_data(data)
