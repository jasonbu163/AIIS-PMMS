from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.router import router as api_router
from app.user.services.auth_service import bootstrap_root_user
from common.exceptions import BusinessException
from common.response import StandardResponse
from database.base import Base
from database.session import AsyncSessionLocal, async_engine
from settings import get_settings

import app.user.models  # noqa: F401
import app.material.models  # noqa: F401
import app.cutting.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.app_env == "test":
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await bootstrap_root_user(db)
    yield


app = FastAPI(
    title="AIIS-PMMS Backend",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(BusinessException)
async def business_exception_handler(
    request: Request,
    exc: BusinessException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": None,
            "errorCode": exc.error_code.value,
        },
    )


@app.get("/health", response_model=StandardResponse[dict[str, str]])
async def health() -> StandardResponse[dict[str, str]]:
    return StandardResponse(data={"status": "ok"})


app.include_router(api_router, prefix=get_settings().api_prefix)
