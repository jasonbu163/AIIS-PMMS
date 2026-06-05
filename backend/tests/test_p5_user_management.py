from __future__ import annotations

import os

import httpx

from app.user.cruds import user_crud
from app.user.models.user import User
from core.security import hash_password
from database.session import AsyncSessionLocal
from scripts.reset_root_password import reset_root_password


async def _login(client: httpx.AsyncClient, username: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["data"]["accessToken"]


async def _root_headers(client: httpx.AsyncClient, password: str | None = None) -> dict[str, str]:
    token = await _login(
        client,
        os.environ["BOOTSTRAP_ROOT_USERNAME"],
        password or os.environ["BOOTSTRAP_ROOT_PASSWORD"],
    )
    return {"Authorization": f"Bearer {token}"}


async def _create_user(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    *,
    username: str,
    password: str,
    display_name: str,
    role: str = "viewer",
) -> dict:
    response = await client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "username": username,
            "password": password,
            "displayName": display_name,
            "role": role,
            "status": "active",
        },
    )
    assert response.status_code == 200
    assert response.json()["code"] == 200
    return response.json()["data"]


async def test_root_can_crud_admin_and_viewer_users(client: httpx.AsyncClient) -> None:
    headers = await _root_headers(client)
    admin = await _create_user(
        client,
        headers,
        username="site-admin",
        password="admin-pass",
        display_name="Site Admin",
        role="admin",
    )
    viewer = await _create_user(
        client,
        headers,
        username="viewer01",
        password="viewer-pass",
        display_name="Viewer 01",
        role="viewer",
    )
    assert admin["role"] == "admin"
    assert viewer["role"] == "viewer"

    list_response = await client.get("/api/v1/users", headers=headers)
    assert list_response.status_code == 200
    usernames = [user["username"] for user in list_response.json()["data"]]
    assert os.environ["BOOTSTRAP_ROOT_USERNAME"] in usernames
    assert "site-admin" in usernames
    assert "viewer01" in usernames

    update_response = await client.patch(
        "/api/v1/users/site-admin",
        headers=headers,
        json={"displayName": "Updated Admin", "status": "disabled"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["displayName"] == "Updated Admin"
    assert update_response.json()["data"]["status"] == "disabled"

    password_response = await client.patch(
        "/api/v1/users/viewer01/password",
        headers=headers,
        json={"newPassword": "viewer-new-pass"},
    )
    assert password_response.status_code == 200
    await _login(client, "viewer01", "viewer-new-pass")

    delete_response = await client.delete("/api/v1/users/site-admin", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["status"] == "disabled"


async def test_root_cannot_delete_self_and_self_password_requires_old_password(
    client: httpx.AsyncClient,
) -> None:
    headers = await _root_headers(client)

    missing_old_response = await client.patch(
        f"/api/v1/users/{os.environ['BOOTSTRAP_ROOT_USERNAME']}/password",
        headers=headers,
        json={"newPassword": "new-root-pass"},
    )
    assert missing_old_response.status_code == 200
    assert missing_old_response.json()["errorCode"] == "old_password_required"

    invalid_old_response = await client.patch(
        f"/api/v1/users/{os.environ['BOOTSTRAP_ROOT_USERNAME']}/password",
        headers=headers,
        json={"oldPassword": "wrong-pass", "newPassword": "new-root-pass"},
    )
    assert invalid_old_response.status_code == 200
    assert invalid_old_response.json()["errorCode"] == "invalid_old_password"

    valid_response = await client.patch(
        f"/api/v1/users/{os.environ['BOOTSTRAP_ROOT_USERNAME']}/password",
        headers=headers,
        json={
            "oldPassword": os.environ["BOOTSTRAP_ROOT_PASSWORD"],
            "newPassword": "new-root-pass",
        },
    )
    assert valid_response.status_code == 200
    await _root_headers(client, password="new-root-pass")

    delete_response = await client.delete(
        f"/api/v1/users/{os.environ['BOOTSTRAP_ROOT_USERNAME']}",
        headers={"Authorization": f"Bearer {await _login(client, 'root', 'new-root-pass')}"},
    )
    assert delete_response.status_code == 403
    assert delete_response.json()["errorCode"] == "cannot_delete_self"


async def test_admin_can_crud_only_ordinary_users(client: httpx.AsyncClient) -> None:
    root_headers = await _root_headers(client)
    await _create_user(
        client,
        root_headers,
        username="site-admin",
        password="admin-pass",
        display_name="Site Admin",
        role="admin",
    )
    admin_headers = {"Authorization": f"Bearer {await _login(client, 'site-admin', 'admin-pass')}"}

    viewer = await _create_user(
        client,
        admin_headers,
        username="viewer01",
        password="viewer-pass",
        display_name="Viewer 01",
        role="viewer",
    )
    assert viewer["role"] == "viewer"

    create_admin_response = await client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": "site-admin-2",
            "password": "admin-pass",
            "displayName": "Site Admin 2",
            "role": "admin",
        },
    )
    assert create_admin_response.status_code == 403
    assert create_admin_response.json()["errorCode"] == "user_permission_denied"

    list_response = await client.get("/api/v1/users", headers=admin_headers)
    assert list_response.status_code == 200
    assert [user["username"] for user in list_response.json()["data"]] == ["viewer01"]

    update_response = await client.patch(
        "/api/v1/users/viewer01",
        headers=admin_headers,
        json={"displayName": "Viewer Updated"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["displayName"] == "Viewer Updated"

    reset_password_response = await client.patch(
        "/api/v1/users/viewer01/password",
        headers=admin_headers,
        json={"newPassword": "viewer-new-pass"},
    )
    assert reset_password_response.status_code == 200
    await _login(client, "viewer01", "viewer-new-pass")

    delete_response = await client.delete("/api/v1/users/viewer01", headers=admin_headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["status"] == "disabled"

    root_update_response = await client.patch(
        f"/api/v1/users/{os.environ['BOOTSTRAP_ROOT_USERNAME']}",
        headers=admin_headers,
        json={"displayName": "Bad Idea"},
    )
    assert root_update_response.status_code == 403


async def test_viewer_can_only_change_own_password_with_old_password(
    client: httpx.AsyncClient,
) -> None:
    root_headers = await _root_headers(client)
    await _create_user(
        client,
        root_headers,
        username="viewer01",
        password="viewer-pass",
        display_name="Viewer 01",
        role="viewer",
    )
    viewer_headers = {"Authorization": f"Bearer {await _login(client, 'viewer01', 'viewer-pass')}"}

    list_response = await client.get("/api/v1/users", headers=viewer_headers)
    assert list_response.status_code == 403

    missing_old_response = await client.patch(
        "/api/v1/users/viewer01/password",
        headers=viewer_headers,
        json={"newPassword": "viewer-new-pass"},
    )
    assert missing_old_response.status_code == 200
    assert missing_old_response.json()["errorCode"] == "old_password_required"

    valid_response = await client.patch(
        "/api/v1/users/viewer01/password",
        headers=viewer_headers,
        json={"oldPassword": "viewer-pass", "newPassword": "viewer-new-pass"},
    )
    assert valid_response.status_code == 200
    await _login(client, "viewer01", "viewer-new-pass")

    root_password_response = await client.patch(
        f"/api/v1/users/{os.environ['BOOTSTRAP_ROOT_USERNAME']}/password",
        headers=viewer_headers,
        json={"newPassword": "bad-root-pass"},
    )
    assert root_password_response.status_code == 403


async def test_duplicate_username_is_rejected(client: httpx.AsyncClient) -> None:
    headers = await _root_headers(client)
    payload = {
        "username": "viewer01",
        "password": "viewer-pass",
        "displayName": "Viewer 01",
    }
    first_response = await client.post("/api/v1/users", headers=headers, json=payload)
    assert first_response.status_code == 200

    second_response = await client.post("/api/v1/users", headers=headers, json=payload)
    assert second_response.status_code == 200
    assert second_response.json()["code"] == 400
    assert second_response.json()["errorCode"] == "user_already_exists"


async def test_reset_root_password_script_restores_env_password(
    client: httpx.AsyncClient,
) -> None:
    async with AsyncSessionLocal() as db:
        root = await user_crud.get_user_by_username(db, os.environ["BOOTSTRAP_ROOT_USERNAME"])
        assert root is not None
        root.password_hash = hash_password("forgotten-pass")
        root.status = "disabled"
        await db.commit()

    failed_login = await client.post(
        "/api/v1/auth/login",
        json={
            "username": os.environ["BOOTSTRAP_ROOT_USERNAME"],
            "password": os.environ["BOOTSTRAP_ROOT_PASSWORD"],
        },
    )
    assert failed_login.status_code == 200
    assert failed_login.json()["errorCode"] == "invalid_credentials"

    result = await reset_root_password()
    assert result == {
        "action": "updated",
        "username": os.environ["BOOTSTRAP_ROOT_USERNAME"],
        "role": "admin",
        "status": "active",
    }

    await _root_headers(client)
