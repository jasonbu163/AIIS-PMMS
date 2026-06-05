from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from typing import Any, Optional

from common.error_codes import ErrorCode
from common.exceptions import BusinessException
from settings import get_settings


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign(message: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), message.encode("ascii"), hashlib.sha256)
    return _b64encode(digest.digest())


def create_token(
    subject: str,
    token_type: str,
    expires_in_seconds: int,
    role: Optional[str] = None,
) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + expires_in_seconds,
    }
    if role is not None:
        payload["role"] = role

    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = ".".join(
        [
            _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = _sign(signing_input, get_settings().jwt_secret_key)
    return f"{signing_input}.{signature}"


def create_token_pair(subject: str, role: str) -> dict[str, str]:
    settings = get_settings()
    return {
        "access_token": create_token(
            subject,
            "access",
            settings.jwt_access_token_minutes * 60,
            role=role,
        ),
        "refresh_token": create_token(
            subject,
            "refresh",
            settings.jwt_refresh_token_days * 24 * 60 * 60,
        ),
        "token_type": "bearer",
    }


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}"
        expected_signature = _sign(signing_input, get_settings().jwt_secret_key)
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("bad signature")
        payload = json.loads(_b64decode(payload_b64))
    except Exception as exc:
        raise BusinessException(
            ErrorCode.INVALID_TOKEN,
            code=401,
            http_status_code=401,
        ) from exc

    if payload.get("type") != expected_type or payload.get("exp", 0) < int(time.time()):
        raise BusinessException(ErrorCode.INVALID_TOKEN, code=401, http_status_code=401)
    return payload
