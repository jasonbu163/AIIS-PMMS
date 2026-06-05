from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.user.models.auth_token_revocation import AuthTokenRevocation
from app.user.models.user import User


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.id))
    return list(result.scalars().all())


async def create_user(db: AsyncSession, user: User) -> User:
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def is_token_revoked(db: AsyncSession, jti: str) -> bool:
    result = await db.execute(
        select(AuthTokenRevocation).where(AuthTokenRevocation.jti == jti)
    )
    return result.scalar_one_or_none() is not None


async def revoke_token(db: AsyncSession, revocation: AuthTokenRevocation) -> None:
    db.add(revocation)
    await db.flush()
