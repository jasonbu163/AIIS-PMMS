from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.schemas.user import UserCreateIn, UserOut, UserPasswordUpdateIn, UserUpdateIn
from app.user.services import user_service
from common.pagination import PageData
from common.response import StandardResponse
from core.deps import CurrentUser, get_current_user
from database.session import get_async_db

router = APIRouter()


@router.get("", response_model=StandardResponse[list[UserOut]])
async def list_users_api(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[list[UserOut]]:
    users = await user_service.list_users(db, actor=current_user.user)
    return StandardResponse(data=users)


@router.get("/page", response_model=StandardResponse[PageData[UserOut]])
async def page_users_api(
    page: int = Query(default=1),
    page_size: int = Query(default=20, alias="pageSize"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[PageData[UserOut]]:
    users = await user_service.page_users(
        db,
        actor=current_user.user,
        page=page,
        page_size=page_size,
    )
    return StandardResponse(data=users)


@router.post("", response_model=StandardResponse[UserOut])
async def create_user_api(
    data: UserCreateIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[UserOut]:
    user = await user_service.create_user(db, data, actor=current_user.user)
    return StandardResponse(data=user)


@router.patch("/{username}/password", response_model=StandardResponse[UserOut])
async def update_user_password_api(
    username: str,
    data: UserPasswordUpdateIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[UserOut]:
    user = await user_service.update_user_password(db, username, data, actor=current_user.user)
    return StandardResponse(data=user)


@router.get("/{username}", response_model=StandardResponse[UserOut])
async def get_user_api(
    username: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[UserOut]:
    user = await user_service.get_user(db, username, actor=current_user.user)
    return StandardResponse(data=user)


@router.patch("/{username}", response_model=StandardResponse[UserOut])
async def update_user_api(
    username: str,
    data: UserUpdateIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[UserOut]:
    user = await user_service.update_user(db, username, data, actor=current_user.user)
    return StandardResponse(data=user)


@router.delete("/{username}", response_model=StandardResponse[UserOut])
async def delete_user_api(
    username: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[UserOut]:
    user = await user_service.delete_user(db, username, actor=current_user.user)
    return StandardResponse(data=user)
