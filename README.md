# AIIS-PMMS Backend

[中文说明](README.zh-CN.md)

AIIS-PMMS is a laser-cutting remaining-material management backend. The current implementation direction is backend-first: build the core API, database model, authentication, and OpenAPI contract before committing to a Qt or Vue client.

The backend will expose `openapi.json` for Qt, Vue, or other API consumers. The business source of truth is Microsoft SQL Server; Excel and PDF files are input/output evidence, not the main database.

## Positioning

This project is intended to answer a specific production question:

> For each laser-cutting day and preparation task, which whole sheets and reusable leftovers are available, which sheets are exported to the machine `Template.xlsx`, what did the production report say, and which leftovers or scraps were confirmed afterward?

The system should support:

- Authentication and protected backend APIs.
- Sheet-material inventory records covering whole sheets and reusable leftovers, plus scrap records.
- Daily laser-cutting material preparation.
- Exporting a machine-importable `Template.xlsx`.
- Archiving and parsing laser production report PDFs.
- Confirming reusable leftovers and scraps after production.
- Daily/monthly statistics that can later support settlement or performance calculation.

## Scope

The first stage is not a full ERP, MES, WMS, or WCS. It should focus on the laser-cutting material loop:

```text
Daily cutting task
    ↓
Select whole sheets and reusable leftovers
    ↓
Generate machine-importable Template.xlsx
    ↓
Laser production
    ↓
Import production report PDF
    ↓
Parse running and cutting metrics
    ↓
Confirm leftovers and scraps
    ↓
Daily / monthly settlement data
    ↓
Performance calculation data
```

## Backend Direction

Current backend defaults:

- Framework: FastAPI.
- ORM and migration: SQLAlchemy 2.x + Alembic.
- Database: Microsoft SQL Server 2016 in production.
- Driver: `mssql+pyodbc`.
- API contract: FastAPI OpenAPI at `/openapi.json`.
- Response envelope: `code / message / data`, with stable `errorCode` for business failures.
- Auth: JWT Bearer, refresh token, bcrypt, and simple role-based access for MVP.
- Runtime configuration: host-local backend runs from `.env`; Docker development runs from `.env.docker`.
- Dev environment: `backend/docker-compose.dev.yml` runs both the backend API container and a local SQL Server-compatible development container. The delivered backend executable still connects to the actual site database through `.env`.
- Timezone: current site runtime uses `Asia/Shanghai` local factory time. Backend and SQL Server hosts should keep this timezone aligned; API timestamps are displayed as site-local time.

Because the target database is SQL Server 2016, implementation should keep migrations and queries compatible with SQL Server 2016 unless a newer feature is explicitly approved.

## Development Runtime Split

Runtime configuration is split by where the backend process runs:

| Runtime | Env file | Entry |
| --- | --- | --- |
| Host-local backend | `backend/.env` | `cd backend && uv run python run.py` |
| Docker dev stack | `backend/.env.docker` | `cd backend && docker compose -f docker-compose.dev.yml up --build` |
| Backend-only container later | `backend/.env.backend.docker` | Connects to host/site MSSQL through `host.docker.internal` or a real LAN IP/DNS |

Committed files are examples only: `backend/.env.example`, `backend/.env.docker.example`, and `backend/.env.backend.docker.example`. Real `.env*` files are ignored by Git.

The Docker dev database password is planned as:

```env
MSSQL_SA_PASSWORD=AIIS_PMMS_Dev_789!
DB_PASSWORD=AIIS_PMMS_Dev_789!
```

The Docker dev stack uses Compose project name `aiis-pmms` to avoid collisions with other backend projects. It keeps only two long-running containers: `api` and `mssql-dev`; the API container ensures the development database exists before running migrations. The API is published on host port `18080` and still listens on container port `8000`. It uses SQL Server 2022 as a convenient local database container. The MSSQL service is pinned to `linux/amd64` because the official SQL Server Linux image is AMD64-oriented; on Apple Silicon it may run through Docker Desktop emulation. Production/site compatibility must still be validated against real SQL Server 2016.

## Fallback Account

The backend must support a fallback account that can be initialized or reset through `.env`:

- Username: `root`
- Default plaintext password: `#789@root`

The real `.env` file is not committed to GitHub, so it can store the plaintext bootstrap password:

```env
BOOTSTRAP_ROOT_USERNAME=root
BOOTSTRAP_ROOT_PASSWORD=#789@root
```

The committed `.env.example` should keep only variable names and placeholder guidance, not the actual site `.env`. Implementation code must not hard-code `#789@root`; the plaintext value from `.env` is only the initialization/reset input, and the password stored in the users table should still use the backend authentication module's normal password hashing strategy.

## Core Data Direction

The sample `resources/Template.xlsx` defines the first export contract:

| Column | Header | Meaning |
| --- | --- | --- |
| A | 板材名称 | Sheet name or row item identifier |
| B | 图纸路径 | Drawing or cutting file path |
| C | 宽 | Width |
| D | 长 | Length |
| E | 材质 | Material grade |
| F | 厚度 | Thickness |
| G | 数量 | Quantity |

The first backend database should model:

- Users and token revocation records.
- Material definitions and material grades.
- Sheet-material inventory items covering whole sheets and leftovers. The first XLSX import/export contract and frontend workflow are sheet-oriented; pipe/profile inventory fields should be planned separately later.
- Daily cutting preparation orders and preparation items.
- Exported `Template.xlsx` file metadata.
- Uploaded production report PDF metadata and parsed metrics.
- Leftover confirmations, scrap confirmations, and daily settlements.

## Documents

- [Backend Core Plan](PLAN.md)
- [Chinese Backend Core Plan](PLAN.zh-CN.md)
- [Documentation Index](docs/README.md)
- [System Positioning](docs/00-overview.zh-CN.md)
- [Glossary and System Relationships](docs/01-glossary.zh-CN.md)
- [Business Scope](docs/02-business-scope.zh-CN.md)
- [Data and Metrics](docs/03-data-and-metrics.zh-CN.md)
- [MVP Roadmap](docs/04-mvp-roadmap.zh-CN.md)
- [English MVP Roadmap](docs/04-mvp-roadmap.md)

## Current Status

This repository is now in backend-core implementation. The backend skeleton, authentication, Docker dev stack, first sheet-material inventory APIs, protected database maintenance APIs, and daily preparation `Template.xlsx` export are in place.

Completed:

- Project positioning and scope documents.
- Chinese business documentation.
- Bilingual root README files.
- MVP roadmap for the next stage.
- Git repository initialization.
- Backend-first direction and tracking plan.
- P0 backend skeleton and API contract.
- P1 authentication and root fallback account.
- P2 sheet-material inventory API first version, covering whole sheets and leftovers.
- P3 protected database status / initialize / upgrade APIs.
- P4 daily preparation order, preparation items, source reservation, and `Template.xlsx` export.

Decided for the backend core:

- FastAPI backend.
- Microsoft SQL Server 2016 target database.
- `.env` for host-local/runtime package configuration and `.env.docker` for Docker development.
- OpenAPI JSON as the integration contract for Qt/Vue clients.
- `backend/docker-compose.dev.yml` only for development convenience.
- Protected database maintenance APIs are available for sites that cannot run source-level Alembic commands; they require admin Bearer auth, `X-Maintenance-Token`, and `ENABLE_MAINTENANCE_API=true`.
- `Template.xlsx` export uses the checked-in sample as the column contract and writes generated files to ignored backend storage.
- Docker dev uses source bind mount plus a container-local `.venv` named volume. Ordinary source edits hot-reload; ordinary Python dependency changes should use `uv add` / `uv remove` locally, then restart `api` so container-side `uv sync` updates its own Linux venv.

Still deferred:

- Concrete Qt or Vue frontend implementation.
- Full ERP / MES / WMS integration.
- Worker/Celery background processing unless PDF parsing or batch jobs require it.
- Final executable packaging tool selection.

## Recommended Next Step

Continue with `PLAN.md` P5:

1. Add production report PDF upload/archive records.
2. Store parse status and reserved parsed-result fields.
3. Add leftover confirmation and scrap confirmation endpoints.
4. Keep confirmed leftovers selectable by later preparation orders.
