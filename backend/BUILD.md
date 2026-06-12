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

The build script prints each step in Chinese: checking PyInstaller and required resources, cleaning old outputs, running PyInstaller, preparing site configuration and storage directories, and validating the package structure. It also adds common Windows packaging dynamic imports for SQLAlchemy MSSQL, Uvicorn, ODBC, and openpyxl.

## Output

The build output is:

```text
backend/dist/aiis-pmms-backend/
```

Expected important files:

- `aiis-pmms-backend.exe`
- `.env` or `.env.example`
- `logs/` created automatically on first startup
- `storage/exports/templates/`
- bundled `alembic.ini` and `alembic/`
- optional `resources/Template.xlsx` when the sample template exists

`resources/Template.xlsx` is a sample export template, not a hard packaging dependency. When it is missing, the backend export flow creates a basic workbook from the code-defined headers.

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
LOG_DIR=logs
```

Do not commit real site `.env` files.

`LOG_DIR` may be relative or absolute. Relative paths are resolved from `backend/` during source runs and from the executable directory during packaged runs. With the default value, source runs write local files to `backend/logs/`, and packaged runs write to `dist/aiis-pmms-backend/logs/`.

## Site Connectivity Checklist

Run these checks on the PMMS backend server before starting the packaged executable:

```powershell
Get-OdbcDriver | Where-Object { $_.Name -like "*SQL Server*" } | Select-Object Name
Test-NetConnection <db-host> -Port <db-port>
```

`DB_DRIVER` must exactly match one of the installed driver names on the PMMS backend server, not on the SQL Server machine. Prefer Microsoft ODBC Driver 17 or 18 for SQL Server on production deployments. Driver 11 may prove the configuration path, but it is old and can cause follow-up compatibility issues.

`Test-NetConnection` should report:

```text
TcpTestSucceeded : True
```

If ping succeeds but TCP fails, fix SQL Server TCP/IP, fixed port, or Windows Firewall on the database server before troubleshooting credentials. For a default site port, SQL Server Configuration Manager should have TCP/IP enabled, `IPAll -> TCP Dynamic Ports` empty, and `IPAll -> TCP Port` set to `1433`; restart the SQL Server service after changing it. If the site uses a named instance or dynamic port, set `DB_PORT` to the actual listening port.

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

Use the port configured by `SERVER_PORT`. For example, if `.env` has `SERVER_PORT=18080`, check `http://127.0.0.1:18080/health`.

Runtime logs are written under `LOG_DIR`, including `api.log` for normal `INFO+` output and `api-error.log` for `ERROR+` output.

## Autostart on Windows

Two practical autostart options are available for site deployments.

### Task Scheduler

Create `start-pmms.bat` in the executable directory:

```bat
@echo off
cd /d C:\pmms-backend
.\aiis-pmms-backend.exe
```

Create a Windows Task Scheduler task:

- General: name it `AIIS-PMMS Backend`, select `Run whether user is logged on or not`, and enable `Run with highest privileges`.
- Trigger: `At startup`.
- Action: start `C:\pmms-backend\start-pmms.bat`.
- Start in: `C:\pmms-backend`.
- Settings: enable restart on failure, for example every 1 minute for 3 attempts.

This option requires no extra tool and is usually the fastest first deployment path.

### Windows Service with NSSM

For a more service-like deployment, install NSSM on the PMMS backend server and run:

```powershell
nssm install AIIS-PMMS-Backend
```

In the NSSM dialog, set:

```text
Path: C:\pmms-backend\aiis-pmms-backend.exe
Startup directory: C:\pmms-backend
```

Then start it:

```powershell
nssm start AIIS-PMMS-Backend
```

Always set the startup directory to the executable directory so the backend reads the correct adjacent `.env`.

## Site Update

Do not package or overwrite historical site logs. `logs/` is runtime data and is created automatically when the service starts.

Before replacing a running site package:

1. Stop the backend service.
2. Back up the current package directory, or at least:
   - `.env`
   - `logs/`
   - `storage/`
3. Copy the new program files into place.
4. Restore or keep the site-owned `.env`, `logs/`, and `storage/`.
5. Start the backend service.
6. Check `/health`, then inspect `logs/api.log` and `logs/api-error.log`.

During normal updates, preserve these site-owned runtime paths:

```text
.env
logs/
storage/
```

Program files can be replaced from the new package:

```text
aiis-pmms-backend.exe
_internal/
alembic.ini
alembic/
.env.example
```

`storage/` may contain generated exports, uploaded files, archived source files, or other business evidence artifacts. Treat it as site data unless a separate migration or cleanup plan explicitly says otherwise.

## Database Upgrade

Preferred source-level command remains:

```powershell
uv run alembic upgrade head
```

For sites that can only use the packaged service, enable the protected maintenance API temporarily and call the admin maintenance endpoints with an admin bearer token plus `X-Maintenance-Token`. The maintenance flow is incremental and does not provide clear, drop, truncate, or reset behavior.

## Common Failures

- `No module named PyInstaller`: run the build command with `--with pyinstaller`.
- `打包产物缺少以下内容`: verify that `alembic.ini` and `alembic/` exist, then check whether PyInstaller was interrupted by permissions or security software. `resources/Template.xlsx` is optional and does not block packaging.
- `IM002` / `Data source name not found`: the PMMS backend server cannot find the driver named in `DB_DRIVER`. Run `Get-OdbcDriver ...` on the PMMS server and copy the driver name exactly, or install ODBC Driver 17/18 there.
- `08001` / `10061` / actively refused connection: the driver was found, but the database server port is unreachable. Run `Test-NetConnection <db-host> -Port <db-port>` from the PMMS server and fix SQL Server TCP/IP or the database server firewall until `TcpTestSucceeded` is `True`.
- Login failed or database not found: the network path is open, so verify `DB_USER`, `DB_PASSWORD`, `DB_NAME`, SQL Server mixed-mode authentication, and user permissions.
- Maintenance API returns disabled: set `ENABLE_MAINTENANCE_API=true` only during controlled initialization or upgrade, then disable it again.
