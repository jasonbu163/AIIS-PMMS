from __future__ import annotations

import os

import httpx

from app.user.models.user import User
from core.security import hash_password
from database.session import AsyncSessionLocal


async def _login(client: httpx.AsyncClient, username: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["data"]["accessToken"]


async def _create_viewer_user() -> None:
    async with AsyncSessionLocal() as db:
        db.add(
            User(
                username="viewer",
                password_hash=hash_password("viewer-pass"),
                display_name="Viewer",
                role="viewer",
                status="active",
            )
        )
        await db.commit()


async def test_database_status_requires_access_token(client: httpx.AsyncClient) -> None:
    response = await client.get(
        "/api/v1/admin/database/status",
        headers={"X-Maintenance-Token": os.environ["MAINTENANCE_TOKEN"]},
    )

    assert response.status_code == 401


async def test_database_status_requires_admin_role(client: httpx.AsyncClient) -> None:
    await _create_viewer_user()
    token = await _login(client, "viewer", "viewer-pass")

    response = await client.get(
        "/api/v1/admin/database/status",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Maintenance-Token": os.environ["MAINTENANCE_TOKEN"],
        },
    )

    assert response.status_code == 403


async def test_database_status_requires_maintenance_token(client: httpx.AsyncClient) -> None:
    token = await _login(
        client,
        os.environ["BOOTSTRAP_ROOT_USERNAME"],
        os.environ["BOOTSTRAP_ROOT_PASSWORD"],
    )

    response = await client.get(
        "/api/v1/admin/database/status",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["errorCode"] == "invalid_maintenance_token"


async def test_database_initialize_is_idempotent(client: httpx.AsyncClient) -> None:
    token = await _login(
        client,
        os.environ["BOOTSTRAP_ROOT_USERNAME"],
        os.environ["BOOTSTRAP_ROOT_PASSWORD"],
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Maintenance-Token": os.environ["MAINTENANCE_TOKEN"],
    }

    status_response = await client.get("/api/v1/admin/database/status", headers=headers)
    assert status_response.status_code == 200
    status = status_response.json()["data"]
    assert status["schemaManaged"] is False
    assert status["targetRevision"] == "0006_inventory_spec_import"

    first_response = await client.post(
        "/api/v1/admin/database/initialize",
        headers=headers,
    )
    assert first_response.status_code == 200
    first_payload = first_response.json()["data"]
    assert first_payload["schemaManaged"] is False
    assert "user:root" in first_payload["skipped"]
    assert first_payload["warnings"] == [
        "schema migration skipped for sqlite runtime",
    ]

    second_response = await client.post(
        "/api/v1/admin/database/initialize",
        headers=headers,
    )
    assert second_response.status_code == 200
    second_payload = second_response.json()["data"]
    assert second_payload["skipped"] == first_payload["skipped"]
