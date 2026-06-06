# AIIS-PMMS Backend Build

[中文说明](BUILD.zh-CN.md)

This guide packages the backend API as a Windows-friendly executable for sites that cannot run Docker.

## Environment

Use Windows with Python 3.11+, `uv`, and the Microsoft ODBC Driver for SQL Server installed on the target machine. SQL Server remains the source of truth; the package only contains the API service, Alembic migrations, and required runtime resources.

Install or sync project dependencies from `backend/`:

```powershell
uv sync
```

## Build

Run from `backend/`:

```powershell
uv run --with pyinstaller python build.py
```

The script builds `main.py`, not the development reload command. To copy the local real `backend/.env` into the package for a controlled site delivery:

```powershell
uv run --with pyinstaller python build.py --include-env
```

Without `--include-env`, the package contains `.env.example` only. Rename or copy it to `.env` before running at the site.

## Output

The build output is:

```text
backend/dist/aiis-pmms-backend/
```

Expected important files:

- `aiis-pmms-backend.exe`
- `.env` or `.env.example`
- `storage/exports/templates/`
- bundled `alembic.ini`, `alembic/`, and `resources/Template.xlsx`

## Site Configuration

Edit `.env` in the executable directory. At minimum, set:

```env
APP_ENV=production
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DB_DIALECT=mssql
DB_HOST=127.0.0.1
DB_PORT=1433
DB_NAME=AIIS_PMMS
DB_USER=sa
DB_PASSWORD=change-me
DB_DRIVER=ODBC Driver 18 for SQL Server
JWT_SECRET_KEY=change-me-in-site-env
BOOTSTRAP_ROOT_USERNAME=root
BOOTSTRAP_ROOT_PASSWORD=change-me-in-real-env
ENABLE_MAINTENANCE_API=false
MAINTENANCE_TOKEN=change-me-maintenance-token
```

Do not commit real site `.env` files.

## Packaged Backend with Standalone MSSQL

When the real site SQL Server cannot be used for testing, start the project-owned standalone MSSQL simulation from `backend/`:

```powershell
docker compose -f docker-compose.mssql.yml up -d
```

Then configure the packaged backend `.env` to connect through the host-published port:

```env
DB_HOST=127.0.0.1
DB_PORT=1433
DB_USER=sa
DB_PASSWORD=AIIS_PMMS_Dev_789!
```

This is suitable for packaged-service smoke tests, maintenance API initialization tests, and API flow checks. It is not a production compatibility proof: the container uses SQL Server 2022, while the site target remains Microsoft SQL Server 2016. Switch the same packaged backend `.env` to the real site host, port, user, and password when the site database is ready.

`docker-compose.mssql.yml` reads `.env.mssql.example` by default. Copy it to `.env.mssql` only when you need local overrides that should stay ignored by Git.

For a backend-only Docker service instead of the Windows executable, use:

```powershell
docker compose -f docker-compose.backend.yml up --build
```

That compose file starts only the backend container, reads `.env.backend.docker.example`, and overlays `.env.backend.docker` when present. It does not include a database service.

## Run

From `backend/dist/aiis-pmms-backend/`:

```powershell
.\aiis-pmms-backend.exe
```

Minimum smoke checks:

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/openapi.json
```

## Database Upgrade

Preferred source-level command remains:

```powershell
uv run alembic upgrade head
```

For sites that can only use the packaged service, enable the protected maintenance API temporarily and call the admin maintenance endpoints with an admin bearer token plus `X-Maintenance-Token`. The maintenance flow is incremental and does not provide clear, drop, truncate, or reset behavior.

## Common Failures

- `No module named PyInstaller`: run the build command with `--with pyinstaller`.
- SQL Server connection fails: install the ODBC driver named in `DB_DRIVER`, then verify host, port, user, password, and SQL Server TCP settings.
- Maintenance API returns disabled: set `ENABLE_MAINTENANCE_API=true` only during controlled initialization or upgrade, then disable it again.
