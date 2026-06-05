# AIIS-PMMS 后端核心计划

[English Plan](PLAN.md)

本文档作为当前阶段的实施跟踪表。当前结论是：先做核心后端是合理的，后端通过 OpenAPI 契约服务 Qt 前端、Vue 前端或其他调用方；前端形态不应反过来决定业务数据库和接口边界。

## 0. 当前决策

- 交付形态：先交付 backend API，不先实现 Vue 或 Qt 前端。
- API 契约：FastAPI 自动暴露 `/openapi.json`，必要时提供导出命令，供 Qt / Vue 生成客户端或对照接口字段。
- 数据库：生产和现场使用 Microsoft SQL Server 2016。
- 开发环境：`backend/docker-compose.dev.yml` 同时启动 backend API 容器和 MSSQL 开发容器；开发栈只用于调试，不作为最终交付依赖。
- 配置方式：宿主机本地运行和打包运行读取 `.env`；Docker 开发读取 `.env.docker`；后续 backend-only Docker 运行读取 `.env.backend.docker`。
- 交付方式：后续以 backend 可执行程序或可执行目录为主，附带 `.env.example`、migration、初始化管理员和运维说明。
- 保底账号：默认用户名 `root`，默认明文密码 `#789@root`；真实 `.env` 不提交到 GitHub，可以用 `BOOTSTRAP_ROOT_PASSWORD` 配置明文，`.env.example` 只保留占位说明。
- Docker dev 数据库密码：`.env.docker` 中 `MSSQL_SA_PASSWORD` 和 backend `DB_PASSWORD` 统一使用 `AIIS_PMMS_Dev_789!`；该密码只用于开发环境，不是现场凭证。
- 受保护的数据库维护 API 用于不方便运行源码级 Alembic 命令的现场；调用时必须具备 admin Bearer 认证、`X-Maintenance-Token`，并开启 `ENABLE_MAINTENANCE_API=true`。

## 1. 范围边界

第一版后端只围绕激光开料余料管理闭环，不扩展为完整 ERP / MES / WMS。

优先包含：

- 认证与基础用户管理。
- 物料规格、整料库存、余料库存、废料记录。
- 基于 `resources/Template.xlsx` 字段口径的开料模板数据结构。
- 每日备料单和 `Template.xlsx` 导出。
- 激光生产报告 PDF 导入记录和解析结果表的预留。
- 余料 / 废料确认、状态流转和查询统计。
- OpenAPI 契约、统一响应信封和稳定错误码。

暂不包含：

- 完整采购、销售、财务、成本核算。
- 完整 MES 排产、工序、质检和报工。
- WCS / PLC / 激光设备控制。
- 复杂绩效规则引擎。
- 多工厂、多组织复杂权限。

## 2. 样例文件取证

`resources/Template.xlsx` 当前本地样例结构：

| 列 | 表头 | 初步含义 |
| --- | --- | --- |
| A | 板材名称 | 板材或行项目名称 / 编号 |
| B | 图纸路径 | 图纸或加工文件路径 |
| C | 宽 | 板材宽度 |
| D | 长 | 板材长度 |
| E | 材质 | 材质牌号 |
| F | 厚度 | 材料厚度 |
| G | 数量 | 板材数量 |

初步建模时不要把 Excel 当数据库。Excel 是设备导入 / 导出凭证，MSSQL 才是业务状态真相源。

## 3. 后端技术方案

- Framework：FastAPI。
- ORM / Migration：SQLAlchemy 2.x + Alembic。
- DB driver：`mssql+pyodbc`，优先保证 SQL Server 2016 兼容性。
- API 响应：统一 `code / message / data` 信封，业务错误使用稳定 `errorCode`。
- API 字段：后端内部和数据库使用 `snake_case`，对外 JSON 默认输出 `camelCase`。
- Auth：JWT Bearer + refresh token + bcrypt；MVP 用用户表 `role` 字段做简单 RBAC。
- Root 初始化：`BOOTSTRAP_ROOT_USERNAME=root`，`BOOTSTRAP_ROOT_PASSWORD=#789@root`；明文只作为初始化 / 重置输入，用户表仍保存正式密码哈希。
- 状态值：数据库和接口只保存稳定英文 key，例如 `draft`、`generated`、`uploaded`、`parsed`、`confirmed`、`settled`、`voided`。
- 文件归档：上传 PDF、导出的 Template、解析原始文件都保留文件元数据；数据库保存解析结果和业务状态。
- MSSQL 2016 约束：migration 和查询保持 SQL Server 2016 兼容；除非项目明确批准，否则避免依赖 SQL Server 2017+ / 2022 才支持的语法、函数和索引能力。
- Docker dev 约束：本地开发栈可以为了可用性使用 SQL Server 2022 容器，MSSQL 服务固定为 `linux/amd64`；实现和现场验证目标仍然是 MSSQL 2016 兼容。

## 4. 核心数据表草案

第一阶段先收敛以下表，字段以实际样例和用户确认继续细化：

- `users`：账号、密码哈希、显示名、角色、状态。
- `auth_token_revocations`：撤销 token 的 `jti`、过期时间、撤销原因。
- `materials`：材质、厚度、规格描述、默认单位、启用状态。
- `material_inventory_items`：整料 / 余料库存，宽、长、厚度、材质、数量、来源、位置、状态、可复用性。
- `cutting_preparation_orders`：每日备料单主表，日期、状态、创建人、生成时间、导出文件。
- `cutting_preparation_items`：备料明细，对应 Template.xlsx 的板材名称、图纸路径、宽、长、材质、厚度、数量，并关联库存来源。
- `laser_report_files`：生产报告 PDF 文件归档和解析状态。
- `laser_report_metrics`：切割时长、切割总长、穿孔次数、设备运行参数等解析结果。
- `residual_confirmations`：生产后余料确认，关联备料项、实际宽长、数量、位置、确认人和状态。
- `scrap_confirmations`：废料确认，关联备料项、数量、原因、确认人和状态。
- `daily_settlements`：日结锁定记录，统计日期、状态、锁定人、锁定时间。

## 5. 阶段跟踪

### P0 - 契约冻结与工程骨架

目标：建立可运行 backend 骨架和稳定 API 规则。

任务：

- [x] 创建 backend 工程结构。
- [x] 配置 `.env.example`，支持现场 MSSQL 2016 连接参数。
- [x] 配置 `.env.docker.example`、`.env.backend.docker.example` 和被 Git 忽略的 `.env.docker`，支持 Docker 开发环境。
- [x] 配置 Alembic。
- [x] 提供统一响应、错误码、schema camelCase 输出。
- [x] 提供 `/health` 和 OpenAPI 文档。
- [x] 提供 `backend/docker-compose.dev.yml` backend + MSSQL dev 容器说明，明确不作为最终交付依赖。

验证：

- [x] `uv run pytest`
- [x] `uv run alembic heads`
- [x] `docker compose -f docker-compose.dev.yml config --quiet`
- [x] 获取或导出 `/openapi.json`

### P1 - 认证与用户

目标：后端具备最小可用认证能力。

任务：

- [x] 实现用户表、密码哈希和管理员初始化。
- [x] 实现 `root` 保底账号初始化 / 重置，真实 `.env` 接收 `BOOTSTRAP_ROOT_PASSWORD` 明文，`.env.example` 不保存现场真实密码。
- [x] 实现登录、刷新 token、登出、当前用户接口。
- [x] 实现角色依赖：`admin`、`operator`、`viewer`。
- [x] 受保护接口必须校验 access token。

验证：

- [x] 登录成功返回 access token 和 refresh token。
- [x] 使用 `BOOTSTRAP_ROOT_PASSWORD=#789@root` 可初始化或重置 `root`，用户表保存正式密码哈希。
- [x] 被撤销或过期 token 不能访问受保护接口。
- [x] OpenAPI 标记 BearerAuth。

### P2 - 物料与余料库存

目标：建立“剩余物料数据库”的核心表和 API。

任务：

- [x] 实现材质 / 厚度 / 规格基础数据。
- [x] 实现整料和余料库存 CRUD。
- [x] 实现状态流转：`available`、`reserved`、`consumed`、`scrapped`、`voided`。
- [x] 支持按材质、厚度、宽长、状态、位置查询可复用余料。

验证：

- [x] 可新增、查询、修改、作废余料。
- [x] 状态 key 稳定，中文只作为展示层翻译来源。
- [ ] SQL Server 2016 migration 可执行。

### P3 - 受保护数据库维护

目标：提供安全的现场数据库状态、初始化和升级入口，同时不替代 Alembic 作为 schema 版本来源。

任务：

- [x] 实现受保护的数据库状态接口。
- [x] 实现受保护的数据库初始化接口。
- [x] 实现受保护的数据库升级接口。
- [x] 要求 admin Bearer 认证、`X-Maintenance-Token` 和 `.env` 开关。
- [x] 初始化必须幂等和增量；不提供清空、drop、truncate 或 reset 行为。

验证：

- [x] 未认证请求会被拒绝。
- [x] 非 admin 用户会被拒绝。
- [x] 缺失或错误 maintenance token 会被拒绝。
- [x] 初始化可以重复调用，不会清空既有数据。
- [x] `uv run pytest`
- [x] Docker dev 栈可通过 `18080` 访问 `/api/v1/admin/database/status`。

### P4 - 每日备料与 Template.xlsx

目标：后端生成设备可导入的 `Template.xlsx`。

任务：

- [x] 实现备料单主表和明细表。
- [x] 明细字段覆盖样例列：板材名称、图纸路径、宽、长、材质、厚度、数量。
- [x] 支持从可用整料 / 余料中选择来源。
- [x] 实现导出 `Template.xlsx`，不覆盖 `resources/Template.xlsx` 原始样例。

验证：

- [x] 导出的 Excel 表头和列顺序与样例一致。
- [x] 导出文件有归档记录。
- [x] OpenAPI 覆盖备料单创建、明细维护和导出接口。
- [x] `uv run pytest`

### P5 - 报告导入与余料 / 废料确认

目标：把生产后的 PDF 报告、余料确认和废料确认接入数据库。

任务：

- [ ] 实现 PDF 上传归档。
- [ ] 保存解析状态和解析结果表。
- [ ] 实现余料确认接口，生成新的可复用库存。
- [ ] 实现废料确认接口，记录废料原因和数量。

验证：

- [ ] 上传文件不丢失，解析状态可查询。
- [ ] 余料确认后库存可再次被备料单选择。
- [ ] 废料统计可按日期、材质、厚度汇总。

### P6 - 打包交付与现场配置

目标：形成可交付 backend 可执行包。

任务：

- [ ] 明确打包工具和入口命令。
- [ ] 输出 `.env.example` 和现场配置说明。
- [ ] 输出 migration / 初始化管理员 / 启动 / 停止 / 日志路径说明。
- [ ] 输出 OpenAPI JSON 供 Qt / Vue 使用。

验证：

- [ ] 在无源码运行目录中通过 `.env` 连接指定数据库。
- [ ] 可执行包启动后 `/health` 正常。
- [ ] `/openapi.json` 可被前端调用方获取。

## 6. 近期下一步

继续进入 P5：

1. 增加生产报告 PDF 上传 / 归档记录。
2. 保存解析状态和预留解析结果字段。
3. 增加余料确认和废料确认接口。
4. 确认后的余料要能继续被后续备料单选择。
