# AIIS-PMMS 后端

[English README](README.md)

AIIS-PMMS 当前收敛为激光开料余料管理后端。现阶段采用后端优先：先建设核心 API、数据库模型、认证能力和 OpenAPI 契约，再让 Qt 前端、Vue 前端或其他调用方基于 `openapi.json` 对接。

本项目的业务真相源是 Microsoft SQL Server。Excel 和 PDF 是输入 / 输出凭证，不是主数据库。

## 项目定位

本项目要回答一个非常具体的激光开料现场问题：

> 每天激光开料前有哪些整料和可复用余料可用，系统应生成哪些可导入设备的 `Template.xlsx`，生产报告记录了哪些加工数据，生产后确认了多少余料和废料？

系统应支持：

- 认证和受保护的后端 API。
- 板材物料库存记录，覆盖整料和可复用余料，并保留废料记录。
- 每日激光开料备料。
- 导出设备可导入的 `Template.xlsx`。
- 归档并解析激光生产报告 PDF。
- 生产后确认可复用余料和废料。
- 形成日结 / 月结 / 绩效结算所需的基础统计数据。

## 系统范围

第一阶段不做完整 ERP、完整 MES、完整 WMS，也不做 WCS。系统应聚焦激光开料余料闭环：

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
人工确认余料 / 废料
    ↓
日结 / 月结 / 绩效结算数据
    ↓
绩效计算数据
```

## 后端方向

当前后端默认方案：

- Framework：FastAPI。
- ORM / Migration：SQLAlchemy 2.x + Alembic。
- 数据库：生产和现场目标为 Microsoft SQL Server 2016。
- DB driver：`mssql+pyodbc`。
- API 契约：FastAPI 自动暴露 `/openapi.json`。
- 响应信封：`code / message / data`，业务失败使用稳定 `errorCode`。
- Auth：JWT Bearer + refresh token + bcrypt，MVP 使用简单角色权限。
- 运行配置：宿主机本地运行使用 `.env`；Docker 开发栈使用 `.env.docker`。
- 开发环境：`backend/docker-compose.dev.yml` 同时启动 backend API 容器和本地 SQL Server 兼容开发容器；最终交付的 backend 可执行程序仍通过 `.env` 连接现场数据库。
- 时区：当前现场运行统一使用 `Asia/Shanghai` 中国工厂本地时间；backend 和 SQL Server 所在机器 / 容器应保持一致，API 时间戳按现场本地时间展示。

因为现场目标是 SQL Server 2016，migration 和查询默认保持 SQL Server 2016 兼容；除非明确批准，否则不依赖更高版本才支持的数据库能力。

## 开发运行分层

运行配置按 backend 进程所在位置拆分：

| 运行方式 | Env 文件 | 入口 |
| --- | --- | --- |
| 宿主机本地运行 | `backend/.env` | `cd backend && uv run uvicorn main:app --reload` |
| Docker dev 栈 | `backend/.env.docker` | `cd backend && docker compose -f docker-compose.dev.yml up --build` |
| 后续 backend-only 容器 | `backend/.env.backend.docker` | 通过 `host.docker.internal` 或真实内网 IP / DNS 连接宿主机 / 现场 MSSQL |

提交到 GitHub 的只包括示例文件：`backend/.env.example`、`backend/.env.docker.example`、`backend/.env.backend.docker.example`。真实 `.env*` 文件都被 Git 忽略。

Docker dev 数据库密码规划为：

```env
MSSQL_SA_PASSWORD=AIIS_PMMS_Dev_789!
DB_PASSWORD=AIIS_PMMS_Dev_789!
```

Docker dev 栈固定使用 Compose project name `aiis-pmms`，避免和其他 backend 项目冲突。该栈只保留两个常驻容器：`api` 和 `mssql-dev`；开发数据库存在性由 API 容器启动前确认，然后再执行 migration。API 对宿主机发布端口为 `18080`，容器内仍监听 `8000`。该栈使用 SQL Server 2022 容器作为开发便利。MSSQL 服务固定为 `linux/amd64`，因为官方 SQL Server Linux 镜像主要面向 AMD64；Apple Silicon 上可能通过 Docker Desktop 仿真运行。生产 / 现场兼容性仍必须以真实 SQL Server 2016 验证为准。

## 保底账号

后端必须支持一个可通过 `.env` 初始化或重置的保底账号：

- 用户名：`root`
- 默认明文密码：`#789@root`

真实 `.env` 不提交到 GitHub，可以直接填写明文密码，例如：

```env
BOOTSTRAP_ROOT_USERNAME=root
BOOTSTRAP_ROOT_PASSWORD=#789@root
```

推送到 GitHub 的 `.env.example` 只保留变量名和占位说明，不保存现场真实 `.env`。实现时不要把 `#789@root` 写死到业务代码；`.env` 中的明文只作为初始化 / 重置输入，写入用户表的密码仍应使用后端认证模块的正式密码哈希策略。

## 核心数据方向

`resources/Template.xlsx` 是第一版设备导出契约，当前样例表头为：

| 列 | 表头 | 含义 |
| --- | --- | --- |
| A | 板材名称 | 板材名称或行项目编号 |
| B | 图纸路径 | 图纸或加工文件路径 |
| C | 宽 | 板材宽度 |
| D | 长 | 板材长度 |
| E | 材质 | 材质牌号 |
| F | 厚度 | 材料厚度 |
| G | 数量 | 板材数量 |

第一版后端数据库应优先覆盖：

- 用户和 token 撤销记录。
- 材料定义和材质牌号。
- 板材物料库存项，覆盖整料和余料。当前第一版 XLSX 导入 / 导出契约和前端工作流都围绕板材类物料；管材、型材等库存字段后续单独规划。
- 每日备料单和备料明细。
- 导出的 `Template.xlsx` 文件元数据。
- 上传的生产报告 PDF 元数据和解析指标。
- 余料确认、废料确认和日结记录。

## 文档目录

- [后端核心计划](PLAN.md)
- [后端核心计划中文](PLAN.zh-CN.md)
- [文档入口](docs/README.md)
- [系统定位](docs/00-overview.zh-CN.md)
- [术语与系统关系](docs/01-glossary.zh-CN.md)
- [业务范围](docs/02-business-scope.zh-CN.md)
- [数据与指标](docs/03-data-and-metrics.zh-CN.md)
- [MVP 路线图](docs/04-mvp-roadmap.zh-CN.md)
- [MVP Roadmap English](docs/04-mvp-roadmap.md)

## 当前状态

当前仓库已进入后端核心功能实现阶段。后端骨架、认证、Docker dev 栈、第一版板材物料库存 API、受保护的数据库维护 API，以及每日备料 `Template.xlsx` 导出已落地。

已完成：

- 项目定位与范围文档。
- 中文业务文档。
- 根目录中英文 README。
- MVP 路线图。
- Git 仓库初始化。
- 后端优先方向和跟踪计划。
- P0 后端骨架和 API 契约。
- P1 认证与 root 保底账号。
- P2 板材物料库存 API 第一版，覆盖整料和余料。
- P3 受保护的数据库状态 / 初始化 / 升级 API。
- P4 每日备料单、备料明细、库存来源预留和 `Template.xlsx` 导出。

后端核心已决定：

- FastAPI 后端。
- 现场目标数据库为 Microsoft SQL Server 2016。
- 宿主机本地运行和打包运行通过 `.env` 配置，Docker 开发通过 `.env.docker` 配置。
- 通过 OpenAPI JSON 作为 Qt / Vue 调用方的接口契约。
- `backend/docker-compose.dev.yml` 只作为开发便利，不作为最终交付依赖。
- 受保护的数据库维护 API 用于不方便运行源码级 Alembic 命令的现场；调用时必须具备 admin Bearer 认证、`X-Maintenance-Token`，并开启 `ENABLE_MAINTENANCE_API=true`。
- `Template.xlsx` 导出以仓库中的样例文件作为列契约，生成文件写入被 Git 忽略的 backend storage。
- Docker dev 使用源码 bind mount 加容器内 `.venv` named volume。普通源码修改自动热更新；普通 Python 依赖变化在宿主机执行 `uv add` / `uv remove` 后，重启 `api`，由容器内 `uv sync` 更新自己的 Linux venv。

暂缓：

- 具体 Qt 或 Vue 前端实现。
- 完整 ERP / MES / WMS 集成。
- PDF 批处理或耗时任务明确前，暂不引入 Worker / Celery。
- 最终可执行打包工具选择。

## 建议下一步

继续进入 `PLAN.md` 的 P5：

1. 增加生产报告 PDF 上传 / 归档记录。
2. 保存解析状态和预留解析结果字段。
3. 增加余料确认和废料确认接口。
4. 确认后的余料要能继续被后续备料单选择。
