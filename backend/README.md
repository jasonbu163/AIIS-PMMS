# AIIS-PMMS Backend

[中文说明](README.zh-CN.md)

This directory contains the backend API implementation for the backend-first AIIS-PMMS plan.

## Development Commands

Host-local backend:

```bash
uv run pytest
uv run alembic heads
uv run uvicorn main:app --reload
```

Host-local project commands should use `uv run` so tests, migrations, and the dev server all use the project runtime instead of the agent/system Python.

Docker development stack:

```bash
docker compose -f docker-compose.dev.yml up --build
```

The Docker stack uses Compose project name `aiis-pmms` and `.env.docker`, starts:

- `api`: FastAPI backend at `http://127.0.0.1:18080`.
- `mssql-dev`: SQL Server development container published at `127.0.0.1:1433`.

The dev stack intentionally keeps only two long-running containers: `api` and `mssql-dev`. The `api` service runs `uv sync --frozen --no-dev` into a container-local `.venv` named volume, then uses `uv run --no-sync` to ensure the development database exists, run Alembic migrations, and start `uvicorn --reload`.

The `api` service bind-mounts this directory to `/app` and runs `uvicorn --reload`, so backend source edits hot-reload inside the container. The container still listens on port `8000`; only the host-published dev port is `18080`.

Do not bind-mount the host `.venv` into the container. The container keeps its own Linux `.venv` in the `api-venv` Docker volume and shares only the source tree plus uv cache. After changing Python dependencies with `uv add` / `uv remove`, restart the API container so `uv sync` updates the container venv:

```bash
docker compose -f docker-compose.dev.yml restart api
```

Rebuild is still required after Dockerfile, base image, ODBC driver, apt package, or Python version changes.

`mssql-dev` is pinned to `linux/amd64` because the official SQL Server Linux image is AMD64-oriented. On Apple Silicon it may run through Docker Desktop emulation.

Standalone MSSQL simulation for packaged backend testing:

```bash
docker compose -f docker-compose.mssql.yml up -d
```

Use this when the backend is running from the packaged executable and the real site SQL Server is not available for testing. In the packaged backend `.env`, point the database settings at the host-published container port:

```env
DB_HOST=127.0.0.1
DB_PORT=1433
DB_USER=sa
DB_PASSWORD=AIIS_PMMS_Dev_789!
```

This standalone container is a simulation database only. It uses SQL Server 2022 for local availability; production/site compatibility still targets Microsoft SQL Server 2016 and must be verified against the real target database when it becomes available.

`docker-compose.mssql.yml` reads `.env.mssql.example` by default. Copy it to `.env.mssql` only when you need local overrides that should stay ignored by Git.

The current deployment assumption is a China site runtime. API and SQL Server processes should run with `TZ=Asia/Shanghai` so database `GETDATE()` / SQLAlchemy `func.now()` and backend `datetime.now()` produce the same site-local date and time. Docker dev sets this through `.env.docker` and `docker-compose.dev.yml`; host-local and packaged deployments should keep the OS / SQL Server host timezone aligned with `Asia/Shanghai`.

The backend exposes:

- `GET /health`
- `GET /openapi.json`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/users`
- `GET /api/v1/users/page`
- `POST /api/v1/users`
- `GET /api/v1/users/{username}`
- `PATCH /api/v1/users/{username}`
- `PATCH /api/v1/users/{username}/password`
- `DELETE /api/v1/users/{username}`
- `GET /api/v1/admin/database/status`
- `POST /api/v1/admin/database/initialize`
- `POST /api/v1/admin/database/upgrade`
- `POST /api/v1/cutting-preparations`
- `GET /api/v1/cutting-preparations`
- `GET /api/v1/cutting-preparations/{order_id}`
- `POST /api/v1/cutting-preparations/{order_id}/items`
- `POST /api/v1/cutting-preparations/{order_id}/export-template`
- `GET /api/v1/cutting-preparations/template-exports/{export_id}/download`
- `POST /api/v1/materials`
- `GET /api/v1/materials`
- `POST /api/v1/inventory-items`
- `GET /api/v1/inventory-items`
- `GET /api/v1/inventory-items/page`
- `GET /api/v1/inventory-items/by-code`
- `POST /api/v1/inventory-items/import-xlsx`
- `POST /api/v1/inventory-items/export-xlsx`
- `PATCH /api/v1/inventory-items/{inventory_item_id}`
- `POST /api/v1/inventory-items/{inventory_item_id}/void`

## Root Bootstrap

The real `.env` or `.env.docker` is not committed to GitHub and may contain:

```env
BOOTSTRAP_ROOT_USERNAME=root
BOOTSTRAP_ROOT_PASSWORD=#789@root
```

`.env.example`, `.env.docker.example`, and `.env.backend.docker.example` keep placeholders only. The plaintext value is used only as initialization/reset input; the users table stores the normal password hash.

If the root password is forgotten, reset it to the current `.env` bootstrap password:

```bash
uv run python scripts/reset_root_password.py
```

The script only creates or updates the configured root user, forces `role=admin` and `status=active`, and does not print the plaintext password.

## Database Maintenance

Protected maintenance endpoints exist for sites that cannot conveniently run source-level Alembic commands. They still use Alembic for schema upgrades and only perform idempotent, incremental initialization.

Required protection:

- Bearer token for an `admin` user.
- `X-Maintenance-Token` matching `MAINTENANCE_TOKEN`.
- `ENABLE_MAINTENANCE_API=true`.

The maintenance endpoints do not provide table clearing, reset, `drop`, or `truncate` behavior.

## Template Export

`resources/Template.xlsx` remains the read-only sample contract. Exported files are written under `backend/storage/exports/templates/` and are ignored by Git.

The generated workbook keeps the sample column order:

```text
板材名称, 图纸路径, 宽, 长, 材质, 厚度, 数量
```

## Env Files

| File | Purpose | Git |
| --- | --- | --- |
| `.env.example` | Host-local or packaged backend template | committed |
| `.env` | Host-local real runtime config | ignored |
| `.env.docker.example` | Docker dev template | committed |
| `.env.docker` | Docker dev real runtime config | ignored |
| `.env.mssql.example` | Standalone MSSQL simulation template for packaged backend tests | committed |
| `.env.mssql` | Standalone MSSQL simulation real config | ignored |
| `.env.backend.docker.example` | Backend-only container template for host/site MSSQL | committed |
| `.env.backend.docker` | Backend-only container real runtime config | ignored |

The current Docker development database password is:

```env
MSSQL_SA_PASSWORD=AIIS_PMMS_Dev_789!
DB_PASSWORD=AIIS_PMMS_Dev_789!
```

This password is development-only. The site database password must be configured in the site `.env` or `.env.backend.docker` and is never committed.
