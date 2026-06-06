from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas.database_maintenance import (
    DatabaseMaintenanceResultOut,
    DatabaseStatusOut,
)
from app.user.cruds import user_crud
from app.user.models.user import User
from core.security import hash_password, verify_password
from settings import get_packaged_resource_root, get_settings


BACKEND_ROOT = get_packaged_resource_root()
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"


def _alembic_config() -> Config:
    return Config(str(ALEMBIC_INI))


def _get_target_revision() -> str:
    script = ScriptDirectory.from_config(_alembic_config())
    heads = script.get_heads()
    return heads[0] if len(heads) == 1 else ",".join(heads)


def _schema_managed() -> bool:
    settings = get_settings()
    return settings.db_dialect != "sqlite"


async def _get_current_revision(db: AsyncSession) -> str | None:
    if not _schema_managed():
        return None
    try:
        result = await db.execute(text("SELECT version_num FROM alembic_version"))
    except SQLAlchemyError:
        return None
    versions = [row[0] for row in result.all()]
    if not versions:
        return None
    return ",".join(sorted(versions))


async def get_database_status(db: AsyncSession) -> DatabaseStatusOut:
    settings = get_settings()
    target_revision = _get_target_revision()
    current_revision = await _get_current_revision(db)
    schema_managed = _schema_managed()
    return DatabaseStatusOut(
        schema_managed=schema_managed,
        current_revision=current_revision,
        target_revision=target_revision,
        upgrade_required=schema_managed and current_revision != target_revision,
        app_env=settings.app_env,
        database_dialect=settings.db_dialect,
    )


async def _ensure_root_user(db: AsyncSession) -> tuple[Literal["created", "updated", "skipped"], str]:
    settings = get_settings()
    user = await user_crud.get_user_by_username(db, settings.bootstrap_root_username)
    password_matches = (
        user is not None and verify_password(settings.bootstrap_root_password, user.password_hash)
    )

    if user is None:
        await user_crud.create_user(
            db,
            User(
                username=settings.bootstrap_root_username,
                password_hash=hash_password(settings.bootstrap_root_password),
                display_name="Root",
                role="admin",
                status="active",
            ),
        )
        await db.commit()
        return "created", f"user:{settings.bootstrap_root_username}"

    if not password_matches or user.role != "admin" or user.status != "active":
        user.password_hash = hash_password(settings.bootstrap_root_password)
        user.role = "admin"
        user.status = "active"
        await db.commit()
        return "updated", f"user:{settings.bootstrap_root_username}"

    return "skipped", f"user:{settings.bootstrap_root_username}"


def _run_alembic_upgrade() -> None:
    command.upgrade(_alembic_config(), "head")


async def initialize_database(
    db: AsyncSession,
    *,
    actor: str,
) -> DatabaseMaintenanceResultOut:
    warnings: list[str] = []
    created: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []

    if _schema_managed():
        await asyncio.to_thread(_run_alembic_upgrade)
    else:
        warnings.append("schema migration skipped for sqlite runtime")

    action, item = await _ensure_root_user(db)
    if action == "created":
        created.append(item)
    elif action == "updated":
        updated.append(item)
    else:
        skipped.append(item)

    status = await get_database_status(db)
    result = DatabaseMaintenanceResultOut(
        **status.model_dump(),
        created=created,
        updated=updated,
        skipped=skipped,
        warnings=warnings,
    )
    logger.info(
        "database maintenance completed actor={} current_revision={} target_revision={} "
        "created={} updated={} skipped={} warnings={}",
        actor,
        result.current_revision,
        result.target_revision,
        result.created,
        result.updated,
        result.skipped,
        result.warnings,
    )
    return result
