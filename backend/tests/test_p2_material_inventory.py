from __future__ import annotations

import os

import httpx


async def login_headers(client: httpx.AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": os.environ["BOOTSTRAP_ROOT_USERNAME"],
            "password": os.environ["BOOTSTRAP_ROOT_PASSWORD"],
        },
    )
    assert response.status_code == 200
    token = response.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


async def test_material_and_inventory_crud(client: httpx.AsyncClient) -> None:
    headers = await login_headers(client)

    material_response = await client.post(
        "/api/v1/materials",
        headers=headers,
        json={
            "materialGrade": "Q235",
            "thickness": 2.5,
            "specDescription": "Laser cutting sheet",
            "defaultUnit": "sheet",
        },
    )
    assert material_response.status_code == 200
    material = material_response.json()["data"]
    assert material["materialGrade"] == "Q235"
    assert material["thickness"] == 2.5
    assert material["enabled"] is True

    inventory_response = await client.post(
        "/api/v1/inventory-items",
        headers=headers,
        json={
            "materialId": material["id"],
            "inventoryType": "leftover",
            "width": 1200,
            "length": 800,
            "thickness": 2.5,
            "quantity": 1,
            "source": "production-report-001",
            "location": "A-01",
            "reusable": True,
        },
    )
    assert inventory_response.status_code == 200
    inventory = inventory_response.json()["data"]
    assert inventory["inventoryType"] == "leftover"
    assert inventory["status"] == "available"
    assert inventory["materialGrade"] == "Q235"
    assert inventory["location"] == "A-01"

    query_response = await client.get(
        "/api/v1/inventory-items",
        headers=headers,
        params={
            "materialId": material["id"],
            "inventoryType": "leftover",
            "status": "available",
            "minWidth": 1000,
            "minLength": 600,
            "reusable": "true",
        },
    )
    assert query_response.status_code == 200
    items = query_response.json()["data"]
    assert len(items) == 1
    assert items[0]["id"] == inventory["id"]

    update_response = await client.patch(
        f"/api/v1/inventory-items/{inventory['id']}",
        headers=headers,
        json={
            "quantity": 2,
            "location": "B-02",
            "status": "reserved",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()["data"]
    assert updated["quantity"] == 2
    assert updated["location"] == "B-02"
    assert updated["status"] == "reserved"

    void_response = await client.post(
        f"/api/v1/inventory-items/{inventory['id']}/void",
        headers=headers,
    )
    assert void_response.status_code == 200
    assert void_response.json()["data"]["status"] == "voided"


async def test_material_inventory_requires_auth(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/inventory-items")

    assert response.status_code == 401
