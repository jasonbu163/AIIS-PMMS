from __future__ import annotations

import uvicorn

from settings import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
