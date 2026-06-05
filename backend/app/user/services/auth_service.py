from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.user.cruds import user_crud
from app.user.models.auth_token_revocation import AuthTokenRevocation
from app.user.models.user import User
from app.user.schemas.auth import TokenOut, UserOut
from common.error_codes import ErrorCode
from common.exceptions import BusinessException
from core.jwt import create_token_pair, decode_token
from core.security import hash_password, verify_password
from settings import get_settings


async def bootstrap_root_user(db: AsyncSession) -> None:
    settings = get_settings()
    user = await user_crud.get_user_by_username(db, settings.bootstrap_root_username)
    password_hash = hash_password(settings.bootstrap_root_password)

    if user is None:
        await user_crud.create_user(
            db,
            User(
                username=settings.bootstrap_root_username,
                password_hash=password_hash,
                display_name="Root",
                role="admin",
                status="active",
            ),
        )
    else:
        user.password_hash = password_hash
        user.role = "admin"
        user.status = "active"
    await db.commit()


async def login(db: AsyncSession, username: str, password: str) -> TokenOut:
    user = await user_crud.get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        raise BusinessException(ErrorCode.INVALID_CREDENTIALS)
    if user.status != "active":
        raise BusinessException(ErrorCode.USER_DISABLED)

    token_pair = create_token_pair(subject=user.username, role=user.role)
    return TokenOut(**token_pair)


async def refresh(db: AsyncSession, refresh_token: str) -> TokenOut:
    payload = decode_token(refresh_token, expected_type="refresh")
    await ensure_token_not_revoked(db, payload["jti"])
    user = await user_crud.get_user_by_username(db, payload["sub"])
    if user is None:
        raise BusinessException(ErrorCode.USER_NOT_FOUND)
    if user.status != "active":
        raise BusinessException(ErrorCode.USER_DISABLED)
    token_pair = create_token_pair(subject=user.username, role=user.role)
    return TokenOut(**token_pair)


async def get_active_user(db: AsyncSession, username: str) -> UserOut:
    user = await user_crud.get_user_by_username(db, username)
    if user is None:
        raise BusinessException(ErrorCode.USER_NOT_FOUND)
    if user.status != "active":
        raise BusinessException(ErrorCode.USER_DISABLED)
    return UserOut.model_validate(user)


async def ensure_token_not_revoked(db: AsyncSession, jti: str) -> None:
    if await user_crud.is_token_revoked(db, jti):
        raise BusinessException(ErrorCode.TOKEN_REVOKED, http_status_code=401, code=401)


async def logout(db: AsyncSession, access_payload: dict, refresh_token: str) -> None:
    refresh_payload = decode_token(refresh_token, expected_type="refresh")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for payload in (access_payload, refresh_payload):
        if not await user_crud.is_token_revoked(db, payload["jti"]):
            await user_crud.revoke_token(
                db,
                AuthTokenRevocation(
                    jti=payload["jti"],
                    token_type=payload["type"],
                    expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(
                        tzinfo=None
                    ),
                    revoked_at=now,
                    reason="logout",
                ),
            )
    await db.commit()
