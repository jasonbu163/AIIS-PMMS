from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.schemas.auth import UserOut
from app.user.services import auth_service
from common.error_codes import ErrorCode
from common.exceptions import BusinessException
from core.jwt import decode_token
from database.session import get_async_db
from settings import get_settings

bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    auto_error=False,
)


@dataclass(frozen=True)
class CurrentUser:
    user: UserOut
    payload: dict


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_async_db),
) -> CurrentUser:
    if credentials is None:
        raise BusinessException(ErrorCode.INVALID_TOKEN, code=401, http_status_code=401)

    payload = decode_token(credentials.credentials, expected_type="access")
    await auth_service.ensure_token_not_revoked(db, payload["jti"])
    user = await auth_service.get_active_user(db, payload["sub"])
    return CurrentUser(user=user, payload=payload)


def require_roles(*allowed_roles: str) -> Callable[[CurrentUser], CurrentUser]:
    async def role_dependency(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.user.role not in allowed_roles:
            raise BusinessException(
                ErrorCode.INVALID_TOKEN,
                code=403,
                http_status_code=403,
                message="forbidden",
            )
        return current_user

    return role_dependency


async def require_maintenance_access(
    maintenance_token: str | None = Header(default=None, alias="X-Maintenance-Token"),
    current_user: CurrentUser = Depends(require_roles("admin")),
) -> CurrentUser:
    settings = get_settings()
    if not settings.enable_maintenance_api:
        raise BusinessException(
            ErrorCode.MAINTENANCE_API_DISABLED,
            code=403,
            http_status_code=403,
            message="maintenance_api_disabled",
        )
    if not settings.maintenance_token or maintenance_token != settings.maintenance_token:
        raise BusinessException(
            ErrorCode.INVALID_MAINTENANCE_TOKEN,
            code=403,
            http_status_code=403,
            message="invalid_maintenance_token",
        )
    return current_user


async def require_root_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    settings = get_settings()
    if current_user.user.username != settings.bootstrap_root_username:
        raise BusinessException(
            ErrorCode.ROOT_REQUIRED,
            code=403,
            http_status_code=403,
            message="root_required",
        )
    return current_user
