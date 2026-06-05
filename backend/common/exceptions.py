from __future__ import annotations

from typing import Optional

from common.error_codes import ErrorCode


class BusinessException(Exception):
    def __init__(
        self,
        error_code: ErrorCode,
        *,
        code: int = 400,
        message: Optional[str] = None,
        http_status_code: int = 200,
    ) -> None:
        self.error_code = error_code
        self.code = code
        self.message = message or error_code.value
        self.http_status_code = http_status_code
