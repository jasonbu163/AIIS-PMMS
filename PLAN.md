# AIIS-PMMS Backend Core Plan

[中文计划](PLAN.zh-CN.md)

This document is the active implementation tracker for the current stage. The current decision is backend-first: the backend should expose a stable OpenAPI contract for Qt, Vue, or other clients, and the client technology should not decide the business database or API boundary.

## 0. Current Decisions

- Delivery shape: deliver the backend API first; do not build Vue or Qt first.
- API contract: FastAPI exposes `/openapi.json`; an export command may be added when clients need a static contract file.
- Database: production and site deployments use Microsoft SQL Server 2016.
- Development environment: `backend/docker-compose.dev.yml` runs both the backend API container and the MSSQL development container; it is only for debugging and is not a final delivery dependency.
- Runtime configuration: host-local and packaged backend runs read `.env`; Docker development reads `.env.docker`; backend-only Docker later should use `.env.backend.docker`.
- Delivery package: deliver a backend executable or executable directory with `.env.example`, migrations, bootstrap-admin instructions, and operations notes.
- Fallback account: default username is `root`, default plaintext password is `#789@root`; the real `.env` is not committed to GitHub and may set `BOOTSTRAP_ROOT_PASSWORD` in plaintext, while `.env.example` keeps placeholders only.
- Docker dev database password: `AIIS_PMMS_Dev_789!` for both `MSSQL_SA_PASSWORD` and backend `DB_PASSWORD` in `.env.docker`; this is development-only and not a site credential.
- Protected database maintenance APIs exist for sites that cannot run source-level Alembic commands; they require admin Bearer auth, `X-Maintenance-Token`, and `ENABLE_MAINTENANCE_API=true`.

## 1. Scope Boundary

The first backend version focuses only on the laser-cutting remaining-material loop. It must not expand into a full ERP, MES, or WMS.

Prioritize:

- Authentication and basic user management.
- Material specs, sheet-material inventory covering whole sheets and reusable leftovers, and scrap records.
- Cutting-template data structures based on `resources/Template.xlsx`.
- Daily preparation orders and `Template.xlsx` export.
- Laser production report PDF upload records and reserved parsed-result tables.
- Leftover / scrap confirmation, status transitions, and query statistics.
- OpenAPI contract, unified response envelope, and stable error codes.

Out of scope for the first version:

- Full procurement, sales, finance, or cost accounting.
- Full MES scheduling, routing, inspection, or production reporting.
- WCS / PLC / laser equipment control.
- Complex performance-rule engine.
- Multi-factory or complex multi-organization authorization.

## 2. Sample Evidence

Current local `resources/Template.xlsx` structure:

| Column | Header | Initial Meaning |
| --- | --- | --- |
| A | 板材名称 | Sheet name or row item identifier |
| B | 图纸路径 | Drawing or cutting file path |
| C | 宽 | Sheet width |
| D | 长 | Sheet length |
| E | 材质 | Material grade |
| F | 厚度 | Material thickness |
| G | 数量 | Sheet quantity |

Do not treat Excel as the database. Excel is an input/output evidence artifact; MSSQL is the business state source of truth.

## 3. Backend Technical Plan

- Framework: FastAPI.
- ORM / Migration: SQLAlchemy 2.x + Alembic.
- DB driver: `mssql+pyodbc`, with SQL Server 2016 compatibility as a priority.
- API response: unified `code / message / data` envelope; business failures use stable `errorCode` values.
- API fields: backend internals and database use `snake_case`; external JSON defaults to `camelCase`.
- Auth: JWT Bearer + refresh token + bcrypt; MVP RBAC uses a `role` field on the users table.
- Root bootstrap: `BOOTSTRAP_ROOT_USERNAME=root`, `BOOTSTRAP_ROOT_PASSWORD=#789@root`; plaintext is only an initialization/reset input, and the users table still stores the normal password hash.
- Status values: database and APIs store stable English keys, such as `draft`, `generated`, `uploaded`, `parsed`, `confirmed`, `settled`, and `voided`.
- File archive: uploaded PDFs, exported Templates, and raw parsed files keep file metadata; database tables store parsed results and business status.
- MSSQL 2016 constraint: keep migrations and queries compatible with SQL Server 2016; avoid SQL Server 2017+/2022-only syntax, functions, and index capabilities unless the project explicitly approves them.
- Docker dev constraint: the local dev stack may use a SQL Server 2022 container for availability, with the MSSQL service pinned to `linux/amd64`; MSSQL 2016 compatibility remains the implementation and site-verification target.

## 4. Core Table Draft

First-stage tables should start with the following list and evolve from actual samples and user confirmation:

- `users`: account, password hash, display name, role, status.
- `auth_token_revocations`: revoked token `jti`, expiry, revoke reason.
- `materials`: material grade, thickness, spec description, default unit, enabled status.
- `material_inventory_items`: sheet-material inventory items covering whole sheets and leftovers, width, length, thickness, material, quantity, source, location, status, reusability. Current sheet-oriented dimensions come from `Template.xlsx`; pipe/profile fields should be planned separately later.
- `cutting_preparation_orders`: daily preparation order header, date, status, creator, generated time, exported file.
- `cutting_preparation_items`: preparation details matching Template.xlsx columns: sheet name, drawing path, width, length, material, thickness, quantity, and inventory source.
- `laser_report_files`: production report PDF archive and parse status.
- `laser_report_metrics`: parsed cutting duration, cutting length, piercing count, and equipment runtime metrics.
- `residual_confirmations`: post-production leftover confirmation, linked preparation item, actual size, quantity, location, confirmer, status.
- `scrap_confirmations`: scrap confirmation, linked preparation item, quantity, reason, confirmer, status.
- `daily_settlements`: daily settlement lock record, settlement date, status, locked by, locked at.

## 5. Phase Tracker

### P0 - Contract Freeze and Backend Skeleton

Goal: create a runnable backend skeleton with stable API rules.

Tasks:

- [x] Create the backend project structure.
- [x] Configure `.env.example` with site MSSQL 2016 connection settings.
- [x] Configure `.env.docker.example`, `.env.backend.docker.example`, and ignored `.env.docker` for Docker development.
- [x] Configure Alembic.
- [x] Provide unified response, error codes, and schema camelCase output.
- [x] Provide `/health` and OpenAPI docs.
- [x] Document `backend/docker-compose.dev.yml` with backend + MSSQL dev containers and state clearly that it is not a final delivery dependency.

Verification:

- [x] `uv run pytest`
- [x] `uv run alembic heads`
- [x] `docker compose -f docker-compose.dev.yml config --quiet`
- [x] Fetch or export `/openapi.json`

### P1 - Authentication and Users

Goal: provide minimum usable backend authentication.

Tasks:

- [x] Implement users table, password hashing, and admin bootstrap.
- [x] Implement `root` fallback account initialization/reset; the real `.env` accepts plaintext `BOOTSTRAP_ROOT_PASSWORD`, while `.env.example` must not contain the real site password.
- [x] Implement login, refresh token, logout, and current-user endpoints.
- [x] Implement role dependencies: `admin`, `operator`, `viewer`.
- [x] Protected endpoints must validate access tokens.

Verification:

- [x] Successful login returns access token and refresh token.
- [x] `BOOTSTRAP_ROOT_PASSWORD=#789@root` can initialize or reset `root`, and the users table stores the normal password hash.
- [x] Revoked or expired tokens cannot access protected endpoints.
- [x] OpenAPI marks BearerAuth.

### P2 - Materials and Sheet-Material Inventory

Goal: create the core tables and APIs for sheet-material inventory. The first version covers whole sheets and leftovers; pipe/profile inventory is deferred.

Tasks:

- [x] Implement material / thickness / spec base data.
- [x] Implement sheet-material inventory CRUD for whole sheets and leftovers.
- [x] Implement status transitions: `available`, `reserved`, `consumed`, `scrapped`, `voided`.
- [x] Support inventory queries by material, thickness, size, status, location, and inventory type.

Verification:

- [x] Inventory items can be created, queried, updated, and voided.
- [x] Status keys are stable; Chinese text is only for display-layer translation.
- [ ] SQL Server 2016 migration can run.

### P3 - Protected Database Maintenance

Goal: provide a safe site-facing database status, initialization, and upgrade entry without replacing Alembic as the schema version source.

Tasks:

- [x] Implement protected database status endpoint.
- [x] Implement protected database initialize endpoint.
- [x] Implement protected database upgrade endpoint.
- [x] Require admin Bearer auth, `X-Maintenance-Token`, and `.env` enablement.
- [x] Keep initialization idempotent and incremental; no clear, drop, truncate, or reset behavior.

Verification:

- [x] Unauthenticated requests are rejected.
- [x] Non-admin users are rejected.
- [x] Missing or invalid maintenance token is rejected.
- [x] Initialization can be called repeatedly without clearing existing data.
- [x] `uv run pytest`
- [x] Docker dev stack exposes `/api/v1/admin/database/status` through port `18080`.

### P4 - Daily Preparation and Template.xlsx

Goal: generate a machine-importable `Template.xlsx` from backend data.

Tasks:

- [x] Implement preparation order header and detail tables.
- [x] Detail fields cover the sample columns: sheet name, drawing path, width, length, material, thickness, quantity.
- [x] Support selecting sources from available whole sheets / leftovers.
- [x] Implement `Template.xlsx` export without overwriting the original `resources/Template.xlsx` sample.

Verification:

- [x] Exported Excel headers and column order match the sample.
- [x] Exported files have archive records.
- [x] OpenAPI covers preparation order creation, detail maintenance, and export endpoints.
- [x] `uv run pytest`

### P5 - Report Import and Leftover / Scrap Confirmation

Goal: connect production PDF reports, leftover confirmation, and scrap confirmation to the database.

Tasks:

- [ ] Implement PDF upload archive.
- [ ] Store parse status and parsed-result tables.
- [ ] Implement leftover confirmation endpoint that creates reusable inventory.
- [ ] Implement scrap confirmation endpoint with scrap reason and quantity.

Verification:

- [ ] Uploaded files are retained and parse status is queryable.
- [ ] Confirmed leftovers can be selected again by preparation orders.
- [ ] Scrap statistics can be aggregated by date, material, and thickness.

### P6 - Packaging and Site Configuration

Goal: produce a deliverable backend executable package.

Tasks:

- [ ] Decide packaging tool and entry command.
- [ ] Output `.env.example` and site configuration instructions.
- [ ] Output migration / admin bootstrap / start / stop / log-path instructions.
- [ ] Output OpenAPI JSON for Qt / Vue consumers.

Verification:

- [ ] In a no-source runtime directory, the package can connect to the configured database through `.env`.
- [ ] `/health` works after the executable package starts.
- [ ] `/openapi.json` is available to client teams.

## 6. Immediate Next Step

Continue with P5:

1. Add production report PDF upload/archive records.
2. Store parse status and reserved parsed-result fields.
3. Add leftover confirmation and scrap confirmation endpoints.
4. Keep confirmed leftovers selectable by later preparation orders.
