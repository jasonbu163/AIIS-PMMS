# Client Adapters

[中文](05-client-adapters.zh-CN.md)

This document records how AIIS-PMMS relates to external client projects. It is
not the cross-project learning handbook; the comparative learning notes for
PySide6, WPF/.NET, and QML/C++ belong to the AIIS-level documentation.

AIIS-PMMS remains the backend contract source and business source of truth. The
client projects are independent repositories that consume the FastAPI OpenAPI
contract and the shared integration materials.

## Boundaries

- AIIS-PMMS owns the laser-cutting remaining-material backend, database schema,
  OpenAPI contract, stable status keys, error codes, and integration materials.
- Client projects do not write PMMS business data directly to MSSQL. They call
  the FastAPI backend.
- `pmms-integration-materials/` is the PMMS-side source for client handoff
  notes, API samples, and page specs.
- `frontends/` is a local workspace convenience for development and debugging.
  It should not be treated as PMMS-owned source code.
- The AIIS-level comparison handbook belongs outside this repository.

## Local Workspace Links

For local development, the PMMS workspace may expose external client
repositories with symbolic links:

```text
frontends/
├── pyside6-frontend -> /Users/jason/Desktop/DreamCode/fastbom
├── dotnet-frontend  -> /Users/jason/Desktop/DreamCode/aiis-pmms-dotnet-frontend
└── qml-frontend     -> /Users/jason/Desktop/DreamCode/aiis-pmms-qml-frontend
```

These links are for local navigation and frontend/backend debugging. The
recommended default is to ignore `frontends/` in Git. If the links ever become a
shared team convention, prefer relative links or Git submodules instead of
absolute local paths.

Local references to AIIS engineering rules may also be exposed with a private
link such as `.local-links/engineering-codex`. That link should stay local and
must not make PMMS appear to depend on the AIIS documentation repository at
runtime.

## Client Roles

| Client | Repository | Role | Current State | First Target |
| --- | --- | --- | --- | --- |
| `pyside6-frontend` | `fastbom` | Existing PySide6 desktop tool and PMMS integration client. | Has local SolidWorks/DXF workflow and PMMS inventory integration material. | Keep aligned with PMMS API; do not rewrite the local processing chain. |
| `dotnet-frontend` | `aiis-pmms-dotnet-frontend` | WPF/.NET learning client for Windows industrial software and vendor SDK ecosystems. | Planned external repository. | Build the same PMMS client slice with WPF/MVVM. |
| `qml-frontend` | `aiis-pmms-qml-frontend` | Qt Quick/QML + C++ learning client for C++ engineering, device-side UI, and future edge/ROS work. | Planned external repository. | Build the same PMMS client slice with QML UI and C++ services/models. |

## Shared First Slice

The first comparable client slice should stay small and identical across the
new WPF and QML/C++ clients:

1. Server URL and request timeout settings.
2. Login, logout, and current user.
3. User management.
4. Material specification management.
5. Sheet-material inventory list, filters, and pagination.
6. Create, edit, and void inventory items.
7. XLSX import preview and confirmed import.
8. XLSX export for selected inventory items.
9. Consistent request state, empty state, and error feedback.

Do not expand the first slice into PDF recognition, daily settlement, dashboard
analytics, or SolidWorks/DXF migration. Those belong to later PMMS or client
phases.

## Architecture Influence

The WPF and QML/C++ clients should reference the core engineering ideas behind
AIIS `backend-arch`, adapted for desktop clients instead of copied as backend
folder names.

Core translations:

- Thin entry layer: views, pages, and dialogs collect operator intent and
  display state only.
- Contract boundary: DTOs, response envelopes, pagination, and error codes live
  in a contract layer, not in UI code.
- Application services: use cases coordinate API calls, validation, and client
  state transitions.
- Domain rules: stable status keys, permission checks, and action availability
  rules stay independent from UI widgets.
- Infrastructure isolation: HTTP, file I/O, settings, and platform SDKs stay
  outside UI and domain code.
- Clear source of truth: PMMS FastAPI + MSSQL remain the business truth source.

Suggested WPF mapping:

```text
Views / ViewModels      -> entry and presentation
Contracts               -> API DTOs, StandardResponse, PageData
Application             -> use cases and client orchestration
Domain                  -> rules, status keys, permissions
Infrastructure          -> HttpClient, settings, file upload/download
```

Suggested QML/C++ mapping:

```text
qml/pages               -> presentation
src/models              -> QObject view models and QAbstractListModel
src/contracts           -> DTOs and response envelope
src/services            -> use cases and client orchestration
src/domain              -> rules, status keys, permissions
src/infrastructure      -> QNetworkAccessManager, QSettings, file I/O
```

## Tracking Rules

This document tracks stable adapter boundaries and coarse client status only.
Detailed frontend tasks belong in each external client repository's `PLAN.md`,
issues, or local checklist.

When a PMMS backend API changes in a way that affects clients, update:

1. Backend tests and OpenAPI contract.
2. `pmms-integration-materials/`.
3. This document if the client boundary or first comparable slice changes.
4. Each affected client repository's own plan or implementation notes.

