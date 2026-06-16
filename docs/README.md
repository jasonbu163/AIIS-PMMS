# Documentation

[中文 README](../README.zh-CN.md) | [English README](../README.md)

This directory records the business design for AIIS-PMMS. The current active implementation tracker is the root [Backend Core Plan](../PLAN.md), which narrows the first build to the laser-cutting remaining-material backend.

Naming note: the overall business loop is still laser-cutting remaining-material management, but the current inventory UI and API materials should call the inventory module "sheet-material inventory" because it covers both whole sheets and leftovers and is currently built around sheet dimensions. Pipe/profile inventory remains a future extension.

Client adapter note: AIIS-PMMS is the backend contract source for external client projects such as the PySide6 FastBOM integration, the planned WPF/.NET client, and the planned QML/C++ client. Cross-client learning notes belong to AIIS-level documentation; this repository only records PMMS-specific adapter boundaries.

The earlier documents in this directory are retained as business context. When they conflict with the root README, `AGENTS.md`, or `PLAN.md`, the current backend-first laser-cutting scope wins.

## Documents

| File | Purpose |
| --- | --- |
| [../PLAN.md](../PLAN.md) | Active backend-core implementation tracker. |
| [../PLAN.zh-CN.md](../PLAN.zh-CN.md) | Chinese backend-core implementation tracker. |
| [../AGENTS.md](../AGENTS.md) | English project-level agent rules. |
| [../AGENTS.zh-CN.md](../AGENTS.zh-CN.md) | Chinese project-level agent rules. |
| [00-overview.zh-CN.md](00-overview.zh-CN.md) | Defines the project name, system boundary, and first-stage goal. |
| [01-glossary.zh-CN.md](01-glossary.zh-CN.md) | Explains MMS, PMMS, MES, MOM, PLM, ERP, WMS, and WCS. |
| [02-business-scope.zh-CN.md](02-business-scope.zh-CN.md) | Defines the first-stage business modules, core forms, and excluded scope. |
| [03-data-and-metrics.zh-CN.md](03-data-and-metrics.zh-CN.md) | Defines data dimensions, quantity definitions, metrics, daily settlement, and monthly settlement. |
| [04-mvp-roadmap.md](04-mvp-roadmap.md) | English MVP roadmap. |
| [04-mvp-roadmap.zh-CN.md](04-mvp-roadmap.zh-CN.md) | Describes the recommended MVP stages after project initialization. |
| [05-client-adapters.md](05-client-adapters.md) | English external client adapter boundaries and first comparable client slice. |
| [05-client-adapters.zh-CN.md](05-client-adapters.zh-CN.md) | Chinese external client adapter boundaries and first comparable client slice. |

## 中文说明

本目录用于记录 AIIS-PMMS 的业务设计。当前有效实施跟踪以根目录 [后端核心计划](../PLAN.md) 为准，第一版已收敛为激光开料余料管理后端。

命名说明：项目整体业务链路仍是激光开料余料管理闭环，但当前库存模块在前端和接入材料中应显示为“板材物料库存”，因为它同时覆盖整料和余料，并且当前字段围绕板材宽、长、厚度展开。管材、型材等库存能力后续单独规划。

客户端适配说明：AIIS-PMMS 是外部客户端项目的后端契约源，包括 PySide6 FastBOM 接入、计划中的 WPF/.NET 客户端和计划中的 QML/C++ 客户端。跨客户端学习笔记属于 AIIS 级文档；本仓库只记录 PMMS 专属适配边界。

本目录中的早期文档作为业务背景保留；如果它们与根目录 README、`AGENTS.md` 或 `PLAN.md` 冲突，以当前 backend-first 的激光开料范围为准。

| 文件 | 用途 |
| --- | --- |
| [../PLAN.md](../PLAN.md) | 当前后端核心功能英文实施跟踪。 |
| [../PLAN.zh-CN.md](../PLAN.zh-CN.md) | 当前后端核心功能中文实施跟踪。 |
| [../AGENTS.md](../AGENTS.md) | 英文项目级 agent 规则。 |
| [../AGENTS.zh-CN.md](../AGENTS.zh-CN.md) | 中文项目级 agent 规则。 |
| [00-overview.zh-CN.md](00-overview.zh-CN.md) | 定义项目名称、系统边界和第一阶段目标。 |
| [01-glossary.zh-CN.md](01-glossary.zh-CN.md) | 解释 MMS、PMMS、MES、MOM、PLM、ERP、WMS、WCS。 |
| [02-business-scope.zh-CN.md](02-business-scope.zh-CN.md) | 定义第一阶段业务模块、核心单据和暂不纳入范围。 |
| [03-data-and-metrics.zh-CN.md](03-data-and-metrics.zh-CN.md) | 定义数据维度、数量口径、指标、日结和月结输出。 |
| [04-mvp-roadmap.md](04-mvp-roadmap.md) | 英文 MVP 路线图。 |
| [04-mvp-roadmap.zh-CN.md](04-mvp-roadmap.zh-CN.md) | 描述项目初始化后的 MVP 推进路线。 |
| [05-client-adapters.md](05-client-adapters.md) | 英文外部客户端适配边界和共同第一客户端切片。 |
| [05-client-adapters.zh-CN.md](05-client-adapters.zh-CN.md) | 中文外部客户端适配边界和共同第一客户端切片。 |
