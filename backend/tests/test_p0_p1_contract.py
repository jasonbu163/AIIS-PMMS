from __future__ import annotations

import os

import httpx


async def test_health_uses_standard_response(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "code": 200,
        "message": "success",
        "data": {"status": "ok"},
    }


async def test_openapi_exposes_bearer_auth(client: httpx.AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()

    assert "BearerAuth" in schema["components"]["securitySchemes"]
    assert schema["components"]["securitySchemes"]["BearerAuth"]["type"] == "http"
    assert schema["components"]["securitySchemes"]["BearerAuth"]["scheme"] == "bearer"


async def test_root_login_current_user_and_logout(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": os.environ["BOOTSTRAP_ROOT_USERNAME"],
            "password": os.environ["BOOTSTRAP_ROOT_PASSWORD"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert payload["data"]["tokenType"] == "bearer"
    access_token = payload["data"]["accessToken"]
    refresh_token = payload["data"]["refreshToken"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["data"] == {
        "username": "root",
        "displayName": "Root",
        "role": "admin",
        "status": "active",
    }

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": refresh_token},
    )
    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()["data"]
    assert refreshed["tokenType"] == "bearer"
    assert refreshed["accessToken"] != access_token

    logout_response = await client.post(
        "/api/v1/auth/logout",
        json={"refreshToken": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_response.status_code == 200
    assert logout_response.json()["data"] == {"revoked": True}

    revoked_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert revoked_response.status_code == 401


async def test_protected_endpoint_requires_access_token(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
