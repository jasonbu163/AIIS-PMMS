# AIIS-PMMS 后端

[English README](README.md)

本目录包含 AIIS-PMMS 后端优先方案的后端 API 实现。

## 开发命令

宿主机本地后端：

```bash
uv run pytest
uv run alembic heads
uv run uvicorn main:app --reload
```

宿主机本地项目命令应使用 `uv run`，确保测试、迁移和开发服务器都使用项目运行时，而不是 Agent 或系统 Python。

Docker 开发栈：

```bash
docker compose -f docker-compose.dev.yml up --build
```

Docker 栈使用 Compose project name `aiis-pmms` 和 `.env.docker`，启动：

- `api`：FastAPI 后端，地址为 `http://127.0.0.1:18080`。
- `mssql-dev`：SQL Server 开发容器，发布到 `127.0.0.1:1433`。

开发栈有意只保留两个长期运行的容器：`api` 和 `mssql-dev`。`api` 服务先执行 `uv sync --frozen --no-dev`，把依赖同步到容器本地名为 `.venv` 的 named volume，然后使用 `uv run --no-sync` 确认开发数据库存在、运行 Alembic 迁移，并启动 `uvicorn --reload`。

`api` 服务把本目录 bind mount 到 `/app` 并运行 `uvicorn --reload`，所以修改 `backend/` 源码后容器内会热更新。容器内部仍监听 `8000` 端口；只有宿主机发布的开发端口是 `18080`。

不要把宿主机 `.venv` bind mount 到容器。容器在 `api-venv` Docker volume 中保留自己的 Linux `.venv`，只共享源码树和 uv cache。使用 `uv add` / `uv remove` 修改 Python 依赖后，重启 API 容器，让 `uv sync` 更新容器 venv：

```bash
docker compose -f docker-compose.dev.yml restart api
```

修改 Dockerfile、基础镜像、ODBC driver、apt package 或 Python 版本后，仍然需要 rebuild。

`mssql-dev` 固定为 `linux/amd64`，因为官方 SQL Server Linux 镜像主要面向 AMD64。Apple Silicon 上可能通过 Docker Desktop 仿真运行。

用于打包后端测试的独立 MSSQL 模拟库：

```bash
docker compose -f docker-compose.mssql.yml up -d
```

当后端以打包后的可执行文件运行、且真实现场 SQL Server 暂时无法用于测试时，使用这个入口。在打包后端的 `.env` 中，将数据库配置指向宿主机发布的容器端口：

```env
DB_HOST=127.0.0.1
DB_PORT=1433
DB_USER=sa
DB_PASSWORD=AIIS_PMMS_Dev_789!
```

这个独立容器只作为模拟数据库。它为了本地可用性使用 SQL Server 2022；生产 / 现场兼容性目标仍是 Microsoft SQL Server 2016，真实目标数据库可用后仍必须再验证。

`docker-compose.mssql.yml` 默认读取 `.env.mssql.example`。只有需要保留本地覆盖配置、且不提交到 Git 时，才复制为 `.env.mssql`。

当前部署假设是中国现场运行时。API 和 SQL Server 进程应使用 `TZ=Asia/Shanghai`，使数据库 `GETDATE()` / SQLAlchemy `func.now()` 与后端 `datetime.now()` 产生一致的现场本地日期时间。Docker dev 通过 `.env.docker` 和 `docker-compose.dev.yml` 设置；宿主机本地运行和打包部署应保持 OS / SQL Server 主机时区与 `Asia/Shanghai` 对齐。

后端暴露：

- `GET /health`
- `GET /openapi.json`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/users`
- `GET /api/v1/users/page`
- `POST /api/v1/users`
- `GET /api/v1/users/{username}`
- `PATCH /api/v1/users/{username}`
- `PATCH /api/v1/users/{username}/password`
- `DELETE /api/v1/users/{username}`
- `GET /api/v1/admin/database/status`
- `POST /api/v1/admin/database/initialize`
- `POST /api/v1/admin/database/upgrade`
- `POST /api/v1/cutting-preparations`
- `GET /api/v1/cutting-preparations`
- `GET /api/v1/cutting-preparations/{order_id}`
- `POST /api/v1/cutting-preparations/{order_id}/items`
- `POST /api/v1/cutting-preparations/{order_id}/export-template`
- `GET /api/v1/cutting-preparations/template-exports/{export_id}/download`
- `POST /api/v1/materials`
- `GET /api/v1/materials`
- `POST /api/v1/inventory-items`
- `GET /api/v1/inventory-items`
- `GET /api/v1/inventory-items/page`
- `GET /api/v1/inventory-items/by-code`
- `POST /api/v1/inventory-items/import-xlsx`
- `POST /api/v1/inventory-items/export-xlsx`
- `PATCH /api/v1/inventory-items/{inventory_item_id}`
- `POST /api/v1/inventory-items/{inventory_item_id}/void`

## Root 初始化

真实 `.env` 或 `.env.docker` 不提交到 GitHub，可能包含：

```env
BOOTSTRAP_ROOT_USERNAME=root
BOOTSTRAP_ROOT_PASSWORD=#789@root
```

`.env.example`、`.env.docker.example` 和 `.env.backend.docker.example` 只保留占位值。明文值只作为初始化 / 重置输入；用户表存储正常密码哈希。

如果忘记 root 密码，可将其重置为当前 `.env` 中的 bootstrap 密码：

```bash
uv run python scripts/reset_root_password.py
```

该脚本只创建或更新配置的 root 用户，强制 `role=admin` 和 `status=active`，不会打印明文密码。

## 数据库维护

受保护维护端点用于无法方便运行源码级 Alembic 命令的现场。它们仍使用 Alembic 执行 schema upgrade，并且只做幂等、增量初始化。

必要保护：

- `admin` 用户的 Bearer token。
- `X-Maintenance-Token` 与 `MAINTENANCE_TOKEN` 匹配。
- `ENABLE_MAINTENANCE_API=true`。

维护端点不提供清表、reset、`drop` 或 `truncate` 行为。

## Template 导出

`resources/Template.xlsx` 保持为只读样例契约。导出文件写入 `backend/storage/exports/templates/`，并被 Git 忽略。

生成的 workbook 保持样例列顺序：

```text
板材名称, 图纸路径, 宽, 长, 材质, 厚度, 数量
```

## 环境文件

| 文件 | 用途 | Git |
| --- | --- | --- |
| `.env.example` | 宿主机本地或打包后端模板 | 已提交 |
| `.env` | 宿主机本地真实运行配置 | 已忽略 |
| `.env.docker.example` | Docker dev 模板 | 已提交 |
| `.env.docker` | Docker dev 真实运行配置 | 已忽略 |
| `.env.mssql.example` | 用于打包后端测试的独立 MSSQL 模拟库模板 | 已提交 |
| `.env.mssql` | 独立 MSSQL 模拟库真实配置 | 已忽略 |
| `.env.backend.docker.example` | 连接宿主机 / 现场 MSSQL 的 backend-only 容器模板 | 已提交 |
| `.env.backend.docker` | Backend-only 容器真实运行配置 | 已忽略 |

当前 Docker 开发数据库密码是：

```env
MSSQL_SA_PASSWORD=AIIS_PMMS_Dev_789!
DB_PASSWORD=AIIS_PMMS_Dev_789!
```

该密码仅用于开发。现场数据库密码必须配置在现场 `.env` 或 `.env.backend.docker` 中，且永不提交。
