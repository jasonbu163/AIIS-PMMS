from __future__ import annotations

import asyncio

from app.user.cruds import user_crud
from app.user.models.user import User
from core.security import hash_password
from database.session import AsyncSessionLocal
from settings import get_settings


async def reset_root_password() -> dict[str, str]:
    settings = get_settings()
    async with AsyncSessionLocal() as db:
        user = await user_crud.get_user_by_username(db, settings.bootstrap_root_username)
        password_hash = hash_password(settings.bootstrap_root_password)
        if user is None:
            action = "created"
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
            action = "updated"
            user.password_hash = password_hash
            user.role = "admin"
            user.status = "active"
        await db.commit()
        return {
            "action": action,
            "username": settings.bootstrap_root_username,
            "role": "admin",
            "status": "active",
        }


def main() -> None:
    result = asyncio.run(reset_root_password())
    print(
        "root_password_reset "
        f"action={result['action']} "
        f"username={result['username']} "
        f"role={result['role']} "
        f"status={result['status']}"
    )


if __name__ == "__main__":
    main()
