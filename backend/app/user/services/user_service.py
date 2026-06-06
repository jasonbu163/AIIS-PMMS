from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.user.cruds import user_crud
from app.user.models.user import User
from app.user.schemas.auth import UserOut as ActorUser
from app.user.schemas.user import UserCreateIn, UserOut, UserPasswordUpdateIn, UserUpdateIn
from common.error_codes import ErrorCode
from common.exceptions import BusinessException
from common.pagination import PageData, PageMeta, normalize_page
from core.security import hash_password, verify_password
from settings import get_settings

ORDINARY_ROLES = {"operator", "viewer"}
MANAGED_ROLES = {"admin", *ORDINARY_ROLES}


def _to_user_out(user: User) -> UserOut:
    return UserOut.model_validate(user)


def _is_root_actor(actor: ActorUser) -> bool:
    return actor.username == get_settings().bootstrap_root_username


def _is_self(actor: ActorUser, username: str) -> bool:
    return actor.username == username


def _can_create_role(actor: ActorUser, role: str) -> bool:
    if _is_root_actor(actor):
        return role in MANAGED_ROLES
    if actor.role == "admin":
        return role in ORDINARY_ROLES
    return False


def _can_manage_user(actor: ActorUser, target: User) -> bool:
    if _is_root_actor(actor):
        return target.username != get_settings().bootstrap_root_username
    if actor.role == "admin":
        return target.role in ORDINARY_ROLES
    return False


async def _get_target_user(db: AsyncSession, username: str) -> User:
    user = await user_crud.get_user_by_username(db, username)
    if user is None:
        raise BusinessException(ErrorCode.USER_NOT_FOUND)
    return user


def _ensure_can_manage(actor: ActorUser, target: User) -> None:
    if not _can_manage_user(actor, target):
        raise BusinessException(
            ErrorCode.USER_PERMISSION_DENIED,
            code=403,
            http_status_code=403,
        )


async def create_user(db: AsyncSession, data: UserCreateIn, *, actor: ActorUser) -> UserOut:
    if not _can_create_role(actor, data.role):
        raise BusinessException(
            ErrorCode.USER_PERMISSION_DENIED,
            code=403,
            http_status_code=403,
        )
    existing = await user_crud.get_user_by_username(db, data.username)
    if existing is not None:
        raise BusinessException(ErrorCode.USER_ALREADY_EXISTS)

    user = await user_crud.create_user(
        db,
        User(
            username=data.username,
            password_hash=hash_password(data.password),
            display_name=data.display_name,
            role=data.role,
            status=data.status,
        ),
    )
    await db.commit()
    return _to_user_out(user)


async def list_users(db: AsyncSession, *, actor: ActorUser) -> list[UserOut]:
    users = await user_crud.list_users(db)
    if _is_root_actor(actor):
        return [_to_user_out(user) for user in users]
    if actor.role == "admin":
        return [_to_user_out(user) for user in users if user.role in ORDINARY_ROLES]
    raise BusinessException(
        ErrorCode.USER_PERMISSION_DENIED,
        code=403,
        http_status_code=403,
    )


async def page_users(
    db: AsyncSession,
    *,
    actor: ActorUser,
    page: int = 1,
    page_size: int = 20,
) -> PageData[UserOut]:
    page, page_size = normalize_page(page, page_size)
    if _is_root_actor(actor):
        roles = None
    elif actor.role == "admin":
        roles = ORDINARY_ROLES
    else:
        raise BusinessException(
            ErrorCode.USER_PERMISSION_DENIED,
            code=403,
            http_status_code=403,
        )

    total = await user_crud.count_users(db, roles=roles)
    users = await user_crud.page_users(db, page=page, page_size=page_size, roles=roles)
    return PageData(
        items=[_to_user_out(user) for user in users],
        meta=PageMeta(page=page, page_size=page_size, total=total),
    )


async def get_user(db: AsyncSession, username: str, *, actor: ActorUser) -> UserOut:
    target = await _get_target_user(db, username)
    if _is_self(actor, username) or _can_manage_user(actor, target):
        return _to_user_out(target)
    raise BusinessException(
        ErrorCode.USER_PERMISSION_DENIED,
        code=403,
        http_status_code=403,
    )


async def update_user(
    db: AsyncSession,
    username: str,
    data: UserUpdateIn,
    *,
    actor: ActorUser,
) -> UserOut:
    target = await _get_target_user(db, username)
    update_data = data.model_dump(exclude_unset=True)

    if _is_self(actor, username):
        if "role" in update_data or "status" in update_data:
            raise BusinessException(
                ErrorCode.USER_PERMISSION_DENIED,
                code=403,
                http_status_code=403,
            )
    else:
        _ensure_can_manage(actor, target)
        requested_role = update_data.get("role")
        if actor.role == "admin" and requested_role is not None and requested_role not in ORDINARY_ROLES:
            raise BusinessException(
                ErrorCode.USER_PERMISSION_DENIED,
                code=403,
                http_status_code=403,
            )

    for field, value in update_data.items():
        setattr(target, field, value)
    await db.commit()
    await db.refresh(target)
    return _to_user_out(target)


async def update_user_password(
    db: AsyncSession,
    username: str,
    data: UserPasswordUpdateIn,
    *,
    actor: ActorUser,
) -> UserOut:
    target = await _get_target_user(db, username)
    if _is_self(actor, username):
        if not data.old_password:
            raise BusinessException(ErrorCode.OLD_PASSWORD_REQUIRED)
        if not verify_password(data.old_password, target.password_hash):
            raise BusinessException(ErrorCode.INVALID_OLD_PASSWORD)
    else:
        _ensure_can_manage(actor, target)

    target.password_hash = hash_password(data.new_password)
    await db.commit()
    await db.refresh(target)
    return _to_user_out(target)


async def delete_user(db: AsyncSession, username: str, *, actor: ActorUser) -> UserOut:
    target = await _get_target_user(db, username)
    if _is_self(actor, username):
        raise BusinessException(
            ErrorCode.CANNOT_DELETE_SELF,
            code=403,
            http_status_code=403,
        )
    _ensure_can_manage(actor, target)
    target.status = "disabled"
    await db.commit()
    await db.refresh(target)
    return _to_user_out(target)
