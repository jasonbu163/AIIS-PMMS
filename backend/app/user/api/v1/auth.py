from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.schemas.auth import LoginIn, LogoutIn, RefreshIn, TokenOut, UserOut
from app.user.services import auth_service
from common.response import StandardResponse
from database.session import get_async_db
from core.deps import CurrentUser, get_current_user

router = APIRouter()


@router.post("/login", response_model=StandardResponse[TokenOut])
async def login_api(
    data: LoginIn,
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[TokenOut]:
    tokens = await auth_service.login(db, data.username, data.password)
    return StandardResponse(data=tokens)


@router.post("/refresh", response_model=StandardResponse[TokenOut])
async def refresh_api(
    data: RefreshIn,
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[TokenOut]:
    tokens = await auth_service.refresh(db, data.refresh_token)
    return StandardResponse(data=tokens)


@router.post("/logout", response_model=StandardResponse[dict[str, bool]])
async def logout_api(
    data: LogoutIn,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StandardResponse[dict[str, bool]]:
    await auth_service.logout(db, current_user.payload, data.refresh_token)
    return StandardResponse(data={"revoked": True})


@router.get("/me", response_model=StandardResponse[UserOut])
async def me_api(
    current_user: CurrentUser = Depends(get_current_user),
) -> StandardResponse[UserOut]:
    return StandardResponse(data=current_user.user)
