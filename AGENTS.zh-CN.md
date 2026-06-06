# AGENTS.zh-CN.md

[English](AGENTS.md)

本文件是 AIIS-PMMS 项目的项目级协作规则。通用编码原则仍遵循用户级 AGENTS / skills；本文件只记录本项目必须稳定遵守的业务边界、技术栈、目录治理和验证要求。

## 1. 项目定位

本项目不是通用 ERP、MES、WMS 或完整 PMMS。第一阶段应收敛为：

> 激光开料余料管理系统：负责每日备料 Excel 生成、激光生产报告 PDF 识别、激光生产统计、余料 / 废料确认、日结 / 月结辅助结算。

核心业务链路：

```text
今日排产任务
  ↓
选择整料 + 可复用往日余料
  ↓
生成可导入激光开料机的 Template.xlsx
  ↓
激光设备生产
  ↓
导入生产报告 PDF
  ↓
识别设备运行参数和加工信息
  ↓
汇总激光生产统计
  ↓
推算材料消耗
  ↓
人工确认余料 / 废料
  ↓
日结 / 月结 / 绩效结算数据
```

## 2. 第一阶段范围

第一阶段优先做：

- 首页看板：材料利用率、每日生产率、切割时长、切割总长、穿孔次数、废料率、余料趋势。
- 板材物料库存管理：整料、余料、材质、厚度、宽长、数量、来源、状态、可复用性、位置。当前库存 UI 文案使用“板材物料库存”；管材、型材库存属于后续扩展。
- 每日备料：根据今日排产任务和余料库存生成设备可导入的 `Template.xlsx`。
- 生产报告导入：上传激光设备导出的 PDF，识别设备运行参数。
- 激光生产统计：替代手工维护的年度 Excel 统计表，并支持导出。
- 余料 / 废料确认：系统推算 + 人工现场复核。
- 日结 / 月结：锁定统计结果，为绩效或结算提供基础数据。

第一阶段暂不做：

- 完整采购、销售、财务、成本核算。
- 完整 MES 排产、工序、质检和报工。
- 完整 WMS 波次、路径、上架策略。
- WCS / PLC / 激光设备控制。
- 复杂绩效规则引擎。
- 多工厂、多组织复杂权限。

## 3. 技术栈默认选择

除非用户明确调整，默认技术栈为：

```text
frontend: Vue 3 + Vite + TypeScript + Element Plus
backend: FastAPI + SQLAlchemy 2.x + Alembic
database: Microsoft SQL Server 2016
db driver: mssql+pyodbc
architecture: B/S application for LAN or internal deployment
```

关键边界：

- MSSQL 是业务真相源。
- 当前阶段后端优先，先交付 backend API、认证、数据库模型和 OpenAPI 契约；Qt / Vue 前端可以后续基于 `/openapi.json` 对接。
- Excel 和 PDF 是输入 / 输出凭证，不是主数据库。
- 原始上传文件应保留归档记录，数据库保存解析结果、业务状态和文件元数据。
- 小文件解析可以由 API 同步完成；批量 PDF、耗时统计或可重试任务应设计任务表 / 后台任务。
- 后端负责 Excel 生成、PDF 解析、统计汇总和导出；前端只负责上传、展示、编辑和触发操作。
- Docker 开发环境使用 `backend/docker-compose.dev.yml`，Compose project name 固定为 `aiis-pmms`，只保留 `api` 和 `mssql-dev` 两个常驻服务；宿主机本地运行使用 `.env`，Docker 开发使用 `.env.docker`，最终交付的 backend 可执行程序或可执行目录必须通过 `.env` 连接现场 MSSQL 2016。
- 真实 env 文件不提交 Git；只提交 `backend/.env.example`、`backend/.env.docker.example` 和 `backend/.env.backend.docker.example`。
- Docker dev 数据库密码为 `AIIS_PMMS_Dev_789!`，同时用于 `MSSQL_SA_PASSWORD` 和 backend `DB_PASSWORD`；该密码只用于开发环境。
- 宿主机本地 backend 命令必须通过项目运行时执行，优先使用 `uv run`，例如 `uv run pytest`、`uv run alembic heads`、`uv run uvicorn main:app --reload`。
- Docker dev 的 `api` 必须使用源码 bind mount 加 `uvicorn --reload`，确保修改 `backend/` 代码后容器内热更新。不要把宿主机 `.venv` 挂进容器；使用容器内 `.venv` named volume，并在容器内执行 `uv sync`，普通 Python 依赖变化可通过重启 `api` 同步，而不是每次 rebuild。
- 实现时避免依赖 SQL Server 2017+ 才支持的数据库能力。
- 允许为不方便运行源码级 Alembic 命令的现场提供受保护数据库维护 API，但必须保持 admin-only、maintenance-token 保护、`.env` 开关控制、幂等和增量；普通维护流程不得加入清空、drop、truncate 或 reset 行为。
- 保底账号为 `root`，默认明文密码为 `#789@root`；真实 `.env` 不提交到 GitHub，可以通过 `BOOTSTRAP_ROOT_PASSWORD` 配置初始化 / 重置明文，`.env.example` 只保留变量名和占位说明；代码不要硬编码该明文，用户表仍保存正式密码哈希。

## 4. 样例文件规则

`resources/` 下的文件是需求样例和解析契约来源：

- `resources/Template.xlsx`：激光开料机导入模板样例。
- `resources/生产报告单.pdf`：激光设备生产报告样例。
- `resources/2026年激光统计表.xls`：现有人工统计表样例。

规则：

- 不要随意修改、覆盖或格式化这些样例文件。
- 解析、转换、实验输出应放到后续约定的临时目录或测试夹具目录，不覆盖原始样例。
- 需求或字段判断应优先从样例文件和用户描述中取证。
- 如果样例格式和用户口述冲突，先说明冲突，再确认以哪个为准。

## 5. Skills 路由

本项目当前通过 `.codex/skills` 加载用户的工业系统 skills 套件。`.codex/` 属于本地代理配置，已在 `.gitignore` 中忽略；不要提交 `.codex/` 或 `.trae/`。

使用规则：

- 新项目边界、工业系统形态、跨端规划：使用 `industrial-system`。
- Vue 页面、看板、列表、Element Plus、ECharts、主题：使用 `frontend-ui`。
- FastAPI、SQLAlchemy、MSSQL、API、Service、Domain、响应结构：使用 `backend-arch`。
- 后端维护脚本、PDF/Excel 批处理脚本、现场导入导出工具：使用 `backend-script-tooling`；涉及 API/DB 时同时使用 `backend-arch`。
- 用户可见文案、菜单、按钮、状态、双语：使用 `i18n-workflow`。
- 新增文档索引、代码文件头、目录说明：使用 `code-document-indexer`。
- 如果未来引入 Worker / Celery 处理批量解析或定时汇总，同时使用 `backend-arch` + `backend-celery`。

说明：

- skills 套件可以很好适配本项目，但不能替代项目级业务边界。
- 本文件负责告诉 agents “本项目到底是什么”；skills 负责告诉 agents “具体怎么做”。
- 如果 skills 和本文件冲突，本文件的项目业务边界优先；通用工程实现细节按对应 skill 执行。

## 6. 后端规则

后端默认遵循 `backend-arch` 的分层规则：

- API 层保持极瘦，只做入参、权限、调用 Service、返回响应。
- Service 负责业务编排、事务和状态流转。
- CRUD / repository 只负责数据访问，不直接提交事务。
- Domain 放可复用业务规则，例如余料匹配、材料利用率、消耗推算、日结校验。
- integrations 放 PDF 解析、Excel 生成、文件存储、外部 ERP/MES/WMS 对接。
- DB 是状态真相源；不要把 Excel、PDF、Redis 或前端状态当业务主账。

API 响应默认采用统一信封：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

业务失败应使用稳定错误码或状态 key，不靠中文文案做客户端判断。

## 7. 前端规则

前端默认遵循 `frontend-ui`：

- Vue 3 + TypeScript。
- Element Plus 优先。
- 工业 B/S 页面要克制、密集、可扫描，不做营销式 hero。
- 首页看板必须体现本项目真实对象：材料、余料、废料、激光报告、开料任务、日结状态。
- 用户可见文案后续应进入 locale，不把中文硬编码散落在组件里。
- 前端不承担全局 snake_case / camelCase 转换。
- 上传、导入、导出、确认、日结等高风险动作必须有清晰状态反馈。

## 8. 数据与状态原则

核心实体至少应能追溯：

- 日期
- 排产任务 / 工单
- 图纸或加工文件
- 材料 / 余料
- 材质
- 厚度
- 宽长
- 数量
- 来源
- 设备报告
- 操作人
- 确认状态
- 日结 / 月结状态

状态值使用稳定英文 key，中文仅用于展示。典型状态包括：

- `draft`
- `generated`
- `uploaded`
- `parsed`
- `confirmed`
- `settled`
- `voided`

日结后原则上不直接修改原始记录；需要调整时，应保留调整记录或重开确认流程。

## 9. 文档同步

本项目还在初始化和需求规格阶段，文档就是当前事实来源。以下变化必须同步文档：

- 系统定位变化。
- 技术栈变化。
- 核心流程变化。
- Excel / PDF 字段口径变化。
- 数据模型变化。
- API 响应契约变化。
- 首屏和主要页面范围变化。

总领性质文档必须双语维护：

- README：`README.md` 与 `README.zh-CN.md`。
- PLAN：`PLAN.md` 与 `PLAN.zh-CN.md`。
- AGENTS：`AGENTS.md` 与 `AGENTS.zh-CN.md`。
- ROADMAP：`docs/04-mvp-roadmap.md` 与 `docs/04-mvp-roadmap.zh-CN.md`。

修改其中一个语言版本时，必须在同一任务中同步另一个语言版本，除非用户明确说明该文件只是临时单语言草稿。

优先更新：

- `README.md`
- `README.zh-CN.md`
- `PLAN.md`
- `PLAN.zh-CN.md`
- `docs/README.md`
- 对应 `docs/*.md` / `docs/*.zh-CN.md`
- 本 `AGENTS.md`
- `AGENTS.zh-CN.md`

## 10. 验证要求

仅文档变更至少运行：

```bash
git diff --check
rg -n "PMMS|激光|laser|余料|leftover|废料|scrap|Template.xlsx|生产报告|MSSQL|FastAPI|Vue|PLAN|AGENTS|ROADMAP" README.md README.zh-CN.md PLAN.md PLAN.zh-CN.md AGENTS.md AGENTS.zh-CN.md docs
git status --short
```

后端工程命令必须在 `backend/` 下使用 `uv run`：

```bash
cd backend
uv run pytest
uv run alembic heads
uv run python -m compileall .
```

只有命令实际运行成功，才能在回复中说“已通过验证”。
