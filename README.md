# Production Material Management System

[中文说明](README.zh-CN.md)

Production Material Management System (PMMS) is a documentation-first project for building a production-site material management system. It focuses on daily material preparation, material usage, remaining materials, scrap records, and daily/monthly statistics that can support later performance calculation.

PMMS is the project abbreviation used here. It is not as universally standardized as ERP, MES, WMS, or WCS, but it describes the intended scope: a focused production material loop between ERP, MES, and WMS.

## Positioning

This project is intended to answer a practical production question:

> For each day, work order, production line, team, product, and material, how much material was planned, prepared, issued, consumed, left over, returned, scrapped, and different from the standard?

The system should support:

- Daily material preparation before production.
- Recording issued, consumed, remaining, returned, and scrapped materials.
- Daily and monthly summaries for material usage, leftovers, scrap, and variance.
- Structured data for later performance calculation by team, production line, work order, product, or material.

## Scope

The first stage is not a full ERP, full MES, full WMS, or WCS. It should focus on the production material management loop:

```text
Production task / work order
    ↓
BOM / standard material usage
    ↓
Daily material preparation list
    ↓
Material issue / delivery / feeding
    ↓
Actual material usage
    ↓
Remaining material / return / reuse
    ↓
Scrap material / reason classification
    ↓
Daily and monthly settlement
    ↓
Performance calculation data
```

## First-Stage Goal

The minimum useful outcome is:

> Know the planned quantity, issued quantity, actual consumed quantity, remaining quantity, scrap quantity, variance, responsible team, production line, and work order for each production day.

The first stage should prioritize clear documents, data definitions, core forms, and metric definitions before choosing or generating a concrete application stack.

## Documents

- [Documentation Index](docs/README.md)
- [System Positioning](docs/00-overview.zh-CN.md)
- [Glossary and System Relationships](docs/01-glossary.zh-CN.md)
- [Business Scope](docs/02-business-scope.zh-CN.md)
- [Data and Metrics](docs/03-data-and-metrics.zh-CN.md)
- [MVP Roadmap](docs/04-mvp-roadmap.zh-CN.md)

## Current Status

This repository is in the project initialization stage.

Completed:

- Project positioning and scope documents.
- Chinese business documentation.
- Bilingual root README files.
- MVP roadmap for the next stage.
- Git repository initialization.

Not decided yet:

- Backend framework.
- Frontend framework.
- Database.
- Deployment topology.
- Integration boundaries with ERP, MES, WMS, and WCS.

## Recommended Next Step

The next step is to define the MVP requirements and data model:

1. Confirm the first-stage users and workflows.
2. Define the core documents and approval states.
3. Draft the database entities.
4. Choose the technical stack.
5. Generate the first backend/frontend skeleton.
