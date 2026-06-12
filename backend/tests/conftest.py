from __future__ import annotations

import os

import httpx
import pytest

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DB_DIALECT", "sqlite")
os.environ.setdefault("SQLITE_DATABASE", ":memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("BOOTSTRAP_ROOT_USERNAME", "root")
os.environ.setdefault("BOOTSTRAP_ROOT_PASSWORD", "#789@root")
os.environ.setdefault("ENABLE_MAINTENANCE_API", "true")
os.environ.setdefault("MAINTENANCE_TOKEN", "test-maintenance-token")
os.environ.setdefault("CORS_ORIGINS", "http://127.0.0.1:5173")

from main import app  # noqa: E402


@pytest.fixture()
async def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DB_DIALECT", "sqlite")
    monkeypatch.setenv("SQLITE_DATABASE", ":memory:")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("BOOTSTRAP_ROOT_USERNAME", "root")
    monkeypatch.setenv("BOOTSTRAP_ROOT_PASSWORD", "#789@root")
    monkeypatch.setenv("ENABLE_MAINTENANCE_API", "true")
    monkeypatch.setenv("MAINTENANCE_TOKEN", "test-maintenance-token")
    monkeypatch.setenv("CORS_ORIGINS", "http://127.0.0.1:5173")
    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as test_client:
            yield test_client
