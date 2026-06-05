# MVP Roadmap

[中文路线图](04-mvp-roadmap.zh-CN.md)

> Current update: the first version of this project is narrowed to a backend-first laser-cutting remaining-material management backend. The root `PLAN.md` is the active implementation tracker; this document keeps the broader MVP stage view and records the confirmed backend, database, and delivery boundaries.

## Goal

After project initialization, the next stage should turn the "laser-cutting remaining-material management system" idea into a buildable MVP. The MVP does not aim to become a full ERP, MES, or WMS. It should first complete the whole-sheet / leftover / scrap loop and backend API contract for the laser-cutting site.

## Stage 0: Project Initialization

Current goals:

- Define system name and English abbreviation.
- Define what the system does not do.
- Record business scope, glossary relationships, data metrics, and roadmap.
- Create Git repository and base README.

Completion criteria:

- Root bilingual README files exist.
- `docs/` has a documentation entry.
- Documents cover system positioning, glossary relationships, business scope, data metrics, and MVP route.
- Git repository has been initialized.

## Stage 1: Backend Core Contract

Goal: turn business language into a backend contract that Qt / Vue clients can consume.

Suggested outputs:

- API contract: unified response envelope, error codes, pagination structure, OpenAPI output.
- Authentication boundary: JWT Bearer, refresh token, user roles, protected business endpoints.
- Core workflow: preparation, Template.xlsx export, production report import, leftover confirmation, scrap confirmation, daily settlement.
- Core statuses: `draft`, `generated`, `uploaded`, `parsed`, `confirmed`, `settled`, `voided`.
- Sample evidence: field decisions come from `resources/Template.xlsx`, `resources/生产报告单.pdf`, and `resources/2026年激光统计表.xls`.

Completion criteria:

- Root `PLAN.md` records phases, tasks, and verification commands.
- README explains backend-first, MSSQL 2016, OpenAPI, and `.env` delivery.
- API fields, status keys, auth mode, and database target are no longer undecided.

## Stage 2: Data Model

Goal: design a traceable and reportable data structure that can be stored in the database.

Start with these entities:

- Users and token revocation records.
- Material grade, thickness, and material specs.
- Whole-sheet inventory.
- Leftover inventory.
- Scrap records.
- Daily preparation order.
- Preparation details covering Template.xlsx columns: sheet name, drawing path, width, length, material, thickness, quantity.
- Production report PDF file records.
- Production report parsed metrics.
- Leftover confirmation records.
- Scrap confirmation records.
- Daily settlement records.

Completion criteria:

- Core entities have primary key, business code, status, created time, and updated time.
- Whole-sheet, leftover, and scrap records trace date, source, material, thickness, width, length, quantity, and status.
- After daily settlement, original records are generally not edited directly; adjustments keep records or reopen confirmation.

## Stage 3: Technical Stack

Current backend stack:

- Backend: FastAPI.
- ORM / Migration: SQLAlchemy 2.x + Alembic.
- Database: Microsoft SQL Server 2016.
- DB driver: `mssql+pyodbc`.
- Auth: MVP uses JWT + simple role permissions.
- Development environment: `docker-compose` can support local database and smoke checks.
- Delivery: backend executable or executable directory connects to the site database through `.env`.

Deferred decisions:

- Concrete Qt or Vue frontend implementation order.
- Whether to introduce Worker / Celery, after PDF batch or long-running task scale is clear.
- Final executable packaging tool.

Completion criteria:

- Development environment and runtime method are clear.
- Database and migration approach are clear.
- First version is explicitly backend API first, with OpenAPI for Qt / Vue.

## Stage 4: Engineering Skeleton

Goal: create a runnable minimum backend project, not all business functions at once.

Current order:

1. Backend project skeleton: done.
2. Database migration mechanism: done.
3. `.env.example` and MSSQL 2016 connection configuration: done.
4. Health check, unified response, OpenAPI contract, and authentication: done.
5. Material / leftover inventory API first version: done.
6. Next: daily preparation order, source selection, and `Template.xlsx` export.

Completion criteria:

- Backend can start locally.
- Minimum test or check commands exist.
- README records runtime commands.
- Material / leftover inventory API can be demonstrated; the first preparation/export loop is next.

## Stage 5: MVP Loop

Goal: complete the first usable business chain:

```text
Daily production task
  ↓
Whole-sheet / leftover inventory
  ↓
Daily preparation order
  ↓
Template.xlsx export
  ↓
Production report PDF import
  ↓
Leftover / scrap confirmation
  ↓
Daily settlement
  ↓
Monthly settlement
```

Completion criteria:

- Whole-sheet and leftover inventory can be maintained.
- Machine-importable `Template.xlsx` can be generated.
- Production report PDFs can be imported and parse status is stored.
- Leftover and scrap confirmation results can be recorded.
- Daily settlement data can be generated.
- Basic monthly metrics can be summarized.
- Performance-calculation base data can be exported.

## Deferred Items

First version defers:

- Automated equipment control.
- Complex performance-rule engine.
- Full procurement, sales, and finance modules.
- Advanced scheduling.
- Warehouse wave and path optimization.
- Multi-factory or complex multi-organization permissions.

These can be split into later stages after the MVP loop works.
