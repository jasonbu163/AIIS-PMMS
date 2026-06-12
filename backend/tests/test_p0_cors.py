from __future__ import annotations

import httpx


async def test_configured_origin_can_send_preflight_request(
    client: httpx.AsyncClient,
) -> None:
    response = await client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
