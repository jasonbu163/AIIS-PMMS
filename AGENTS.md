# AGENTS.md

[中文](AGENTS.zh-CN.md)

This file records the project-level collaboration rules for AIIS-PMMS. General coding principles still follow the user-level AGENTS / skills; this file only records the business boundary, technical stack, directory governance, and verification requirements that must remain stable in this project.

## 1. Project Positioning

This project is not a generic ERP, MES, WMS, or full PMMS. The first stage should be narrowed to:

> Laser-cutting remaining-material management system: daily preparation Excel generation, laser production report PDF recognition, laser production statistics, leftover / scrap confirmation, and daily / monthly settlement support.

Core business chain:

```text
Daily production task
  ↓
Select whole sheets and reusable previous leftovers
  ↓
Generate machine-importable Template.xlsx
  ↓
Laser production
  ↓
Import production report PDF
  ↓
Recognize equipment runtime and processing information
  ↓
Summarize laser production statistics
  ↓
Estimate material consumption
  ↓
Manually confirm leftovers / scrap
  ↓
Daily / monthly / performance settlement data
```

## 2. First-Stage Scope

Prioritize:

- Dashboard: material utilization, daily productivity, cutting duration, cutting length, piercing count, scrap rate, leftover trend.
- Material / leftover management: whole sheets, leftovers, material, thickness, width, length, quantity, source, status, reusability, location.
- Daily preparation: generate machine-importable `Template.xlsx` from today's tasks and leftover inventory.
- Production report import: upload laser-equipment PDF reports and recognize equipment runtime metrics.
- Laser production statistics: replace the manually maintained annual Excel statistics table and support export.
- Leftover / scrap confirmation: system estimation plus manual site review.
- Daily / monthly settlement: lock statistics for performance or settlement data.

Defer:

- Full procurement, sales, finance, or cost accounting.
- Full MES scheduling, routing, inspection, or production reporting.
- Full WMS wave, path, or putaway strategy.
- WCS / PLC / laser equipment control.
- Complex performance-rule engine.
- Multi-factory or complex multi-organization authorization.

## 3. Default Technical Stack

Unless the user explicitly changes it:

```text
frontend: Vue 3 + Vite + TypeScript + Element Plus
backend: FastAPI + SQLAlchemy 2.x + Alembic
database: Microsoft SQL Server 2016
db driver: mssql+pyodbc
architecture: B/S application for LAN or internal deployment
```

Key boundaries:

- MSSQL is the business source of truth.
- Current stage is backend-first: deliver backend API, authentication, database models, and OpenAPI contract first; Qt / Vue clients can later integrate through `/openapi.json`.
- Excel and PDF are input/output evidence artifacts, not the main database.
- Original uploaded files must be archived; the database stores parsed results, business status, and file metadata.
- Small-file parsing can run synchronously in the API; batch PDFs, long-running statistics, or retryable work should use task tables / background tasks.
- The backend owns Excel generation, PDF parsing, statistics, and export; the frontend only uploads, displays, edits, and triggers actions.
- Docker development uses `backend/docker-compose.dev.yml` with Compose project name `aiis-pmms` and only two long-running services, `api` / `mssql-dev`; host-local runs use `.env`, Docker dev uses `.env.docker`, and final backend executable/package must connect to site MSSQL 2016 through `.env`.
- Real env files are ignored by Git. Commit only `backend/.env.example`, `backend/.env.docker.example`, and `backend/.env.backend.docker.example`.
- The Docker dev database password is `AIIS_PMMS_Dev_789!` for both `MSSQL_SA_PASSWORD` and backend `DB_PASSWORD`; it is a development-only credential.
- Host-local backend commands must use the project runtime through `uv run`, for example `uv run pytest`, `uv run alembic heads`, and `uv run uvicorn main:app --reload`.
- Docker dev `api` must run with source bind mount plus `uvicorn --reload` so code changes in `backend/` hot-reload inside the container. Do not mount the host `.venv` into the container; use a container-local `.venv` named volume and run `uv sync` inside the container so dependency changes can be applied by restarting `api` instead of rebuilding for ordinary Python package changes.
- Avoid SQL Server 2017+ only features.
- Protected database maintenance APIs are allowed for sites that cannot run source-level Alembic commands, but they must stay admin-only, maintenance-token protected, `.env` gated, idempotent, and incremental; do not add clear/drop/truncate/reset behavior to the normal maintenance flow.
- Fallback account is `root`, with default plaintext password `#789@root`; the real `.env` is not committed to GitHub and may configure `BOOTSTRAP_ROOT_PASSWORD`, while `.env.example` keeps variable names and placeholders only. Do not hard-code the plaintext in code; users table still stores the normal password hash.

## 4. Sample File Rules

Files under `resources/` are requirement samples and parsing-contract sources:

- `resources/Template.xlsx`: laser-cutting machine import template sample.
- `resources/生产报告单.pdf`: laser equipment production report sample.
- `resources/2026年激光统计表.xls`: existing manual statistics sample.

Rules:

- Do not casually modify, overwrite, or reformat these sample files.
- Parsing, conversion, and experimental outputs should go to a later agreed temp or fixture directory, never overwrite original samples.
- Requirement and field judgments should first use sample files and user descriptions as evidence.
- If sample format conflicts with user description, state the conflict and confirm which source wins.

## 5. Skills Routing

This project currently loads the user's industrial-system skills through `.codex/skills`. `.codex/` is local agent configuration and is ignored by `.gitignore`; do not commit `.codex/` or `.trae/`.

Use:

- New project boundary, industrial system shape, cross-end planning: `industrial-system`.
- Vue pages, dashboard, lists, Element Plus, ECharts, theme: `frontend-ui`.
- FastAPI, SQLAlchemy, MSSQL, API, Service, Domain, response structure: `backend-arch`.
- Backend maintenance scripts, PDF/Excel batch scripts, site import/export tools: `backend-script-tooling`; use `backend-arch` too when API/DB is involved.
- User-visible text, menus, buttons, status labels, bilingual content: `i18n-workflow`.
- Documentation index, code headers, directory descriptions: `code-document-indexer`.
- If Worker / Celery is introduced for batch parsing or scheduled summaries, use `backend-arch` + `backend-celery`.

Notes:

- The skills suite fits this project well, but it does not replace project-level business boundaries.
- `AGENTS.md` tells agents what this project is; skills tell agents how to implement.
- If skills conflict with this file, the project business boundary here wins; general engineering details follow the corresponding skill.

## 6. Backend Rules

Follow `backend-arch` layering:

- API layer stays thin: input, auth dependencies, Service call, response.
- Service owns business orchestration, transactions, and status transitions.
- CRUD / repository only handles data access and does not commit transactions.
- Domain contains reusable business rules, such as leftover matching, material utilization, consumption estimation, and settlement checks.
- integrations contains PDF parsing, Excel generation, file storage, and external ERP/MES/WMS integration.
- DB is the source of truth; do not treat Excel, PDF, Redis, or frontend state as the business ledger.

Default API response envelope:

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

Business failures should use stable error codes or status keys, not Chinese text for client logic.

## 7. Frontend Rules

Follow `frontend-ui` by default:

- Vue 3 + TypeScript.
- Prefer Element Plus.
- Industrial B/S pages should be restrained, dense, and scannable; do not make marketing-style hero pages.
- The dashboard must show real project objects: materials, leftovers, scrap, laser reports, cutting tasks, settlement status.
- User-visible text should later enter locale files; do not scatter hard-coded Chinese in components.
- Frontend does not own global snake_case / camelCase conversion.
- High-risk actions such as upload, import, export, confirmation, and settlement must have clear state feedback.

## 8. Data and Status Principles

Core entities should trace at least:

- Date
- Production task / work order
- Drawing or processing file
- Material / leftover
- Material grade
- Thickness
- Width and length
- Quantity
- Source
- Equipment report
- Operator
- Confirmation status
- Daily / monthly settlement status

Status values use stable English keys; Chinese is display only. Typical statuses:

- `draft`
- `generated`
- `uploaded`
- `parsed`
- `confirmed`
- `settled`
- `voided`

After daily settlement, original records should generally not be edited directly; adjustments should keep adjustment records or reopen the confirmation flow.

## 9. Documentation Sync

This project is still in initialization and specification stages; documentation is the current source of truth. Sync documentation when these change:

- System positioning.
- Technical stack.
- Core workflow.
- Excel / PDF field definitions.
- Data model.
- API response contract.
- First screen and main page scope.

Top-level governance documents must be bilingual:

- README: `README.md` and `README.zh-CN.md`.
- PLAN: `PLAN.md` and `PLAN.zh-CN.md`.
- AGENTS: `AGENTS.md` and `AGENTS.zh-CN.md`.
- ROADMAP: `docs/04-mvp-roadmap.md` and `docs/04-mvp-roadmap.zh-CN.md`.

When changing one language version, update its pair in the same task unless the user explicitly marks the file as a temporary single-language draft.

Update first:

- `README.md`
- `README.zh-CN.md`
- `PLAN.md`
- `PLAN.zh-CN.md`
- `docs/README.md`
- matching `docs/*.md` / `docs/*.zh-CN.md`
- `AGENTS.md`
- `AGENTS.zh-CN.md`

## 10. Verification

Documentation-only changes run at least:

```bash
git diff --check
rg -n "PMMS|激光|laser|余料|leftover|废料|scrap|Template.xlsx|生产报告|MSSQL|FastAPI|Vue|PLAN|AGENTS|ROADMAP" README.md README.zh-CN.md PLAN.md PLAN.zh-CN.md AGENTS.md AGENTS.zh-CN.md docs
git status --short
```

Backend engineering commands must use `uv run` from `backend/`:

```bash
cd backend
uv run pytest
uv run alembic heads
uv run python -m compileall .
```

Only say "verification passed" after commands actually succeed.
