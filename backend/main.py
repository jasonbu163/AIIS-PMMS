from __future__ import annotations

from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.router import router as api_router
from app.user.services.auth_service import bootstrap_root_user
from common.exceptions import BusinessException
from common.log import logger, setup_logger
from common.response import StandardResponse
from database.base import Base
from database.session import AsyncSessionLocal, async_engine
from settings import get_settings

import app.user.models  # noqa: F401
import app.material.models  # noqa: F401
import app.cutting.models  # noqa: F401


setup_logger(process_name="api")


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

settings = get_settings()
if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def api_request_log_middleware(request: Request, call_next) -> Response:
    started_at = perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed_ms = (perf_counter() - started_at) * 1000
        logger.opt(exception=exc).error(
            "api_request_failed method={} path={} elapsed_ms={:.2f}",
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise

    elapsed_ms = (perf_counter() - started_at) * 1000
    logger.info(
        "api_request method={} path={} status={} elapsed_ms={:.2f}",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


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


app.include_router(api_router, prefix=settings.api_prefix)


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.server_host,
        port=settings.server_port,
        reload=False,
    )
