# AIIS-PMMS 后端打包

[English](BUILD.md)

本说明用于把后端 API 打包成适合 Windows 现场运行的可执行文件，适用于现场不能使用 Docker 的情况。

## 环境准备

打包机使用 Windows、Python 3.11+、`uv`，目标机器需安装 Microsoft ODBC Driver for SQL Server。SQL Server 仍然是业务数据源；打包产物只包含 API 服务、Alembic 迁移和必要运行资源。

在 `backend/` 目录同步依赖：

```powershell
uv sync
```

## 打包

在 `backend/` 目录运行：

```powershell
uv run --with pyinstaller python build.py
```

脚本打包的是生产入口 `main.py`，不会打包开发用的 reload 启动命令。如需为受控现场包复制本机真实 `backend/.env`：

```powershell
uv run --with pyinstaller python build.py --include-env
```

不加 `--include-env` 时，产物只包含 `.env.example`。现场运行前请复制或重命名为 `.env` 并填写真实配置。

打包脚本会按中文步骤输出当前流程：检查 PyInstaller 和必要资源、清理旧产物、执行 PyInstaller、整理现场配置与 storage 目录、校验产物结构。脚本也会补充 SQLAlchemy MSSQL、Uvicorn、ODBC、openpyxl 等 Windows 打包常见动态导入。

## 产物目录

打包输出目录：

```text
backend/dist/aiis-pmms-backend/
```

关键文件应包含：

- `aiis-pmms-backend.exe`
- `.env` 或 `.env.example`
- `storage/exports/templates/`
- 已打入包内的 `alembic.ini` 和 `alembic/`
- 可选：存在样例文件时打入包内的 `resources/Template.xlsx`

`resources/Template.xlsx` 是设备导出样例模板，不是打包硬依赖。缺少该文件时，后端导出功能会使用代码内置表头生成基础工作簿。

## 现场配置

编辑可执行文件同目录的 `.env`。至少配置：

```env
APP_ENV=production
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DB_DIALECT=mssql
DB_HOST=127.0.0.1
DB_PORT=1433
DB_NAME=AIIS_PMMS
DB_USER=sa
DB_PASSWORD=change-me
DB_DRIVER=ODBC Driver 18 for SQL Server
JWT_SECRET_KEY=change-me-in-site-env
BOOTSTRAP_ROOT_USERNAME=root
BOOTSTRAP_ROOT_PASSWORD=change-me-in-real-env
ENABLE_MAINTENANCE_API=false
MAINTENANCE_TOKEN=change-me-maintenance-token
```

真实现场 `.env` 不要提交到 Git。

## 打包后端连接独立 MSSQL

当真实现场 SQL Server 暂时不能用于测试时，可以在 `backend/` 目录启动本项目自带的独立 MSSQL 模拟库：

```powershell
docker compose -f docker-compose.mssql.yml up -d
```

然后在打包后端同目录的 `.env` 中，通过宿主机发布端口连接：

```env
DB_HOST=127.0.0.1
DB_PORT=1433
DB_USER=sa
DB_PASSWORD=AIIS_PMMS_Dev_789!
```

这种方式适合打包服务冒烟测试、维护 API 初始化测试和 API 流程检查。它不是生产兼容性证明：容器使用 SQL Server 2022，而现场目标仍是 Microsoft SQL Server 2016。现场数据库准备好后，把同一个打包后端 `.env` 切换为真实现场主机、端口、账号和密码即可。

`docker-compose.mssql.yml` 默认读取 `.env.mssql.example`。只有需要保留本地覆盖配置、且不提交到 Git 时，才复制为 `.env.mssql`。

如果不是 Windows 可执行文件，而是单后端 Docker 服务，使用：

```powershell
docker compose -f docker-compose.backend.yml up --build
```

该 compose 只启动后端容器，默认读取 `.env.backend.docker.example`，存在 `.env.backend.docker` 时再覆盖；它不包含数据库服务。

## 启动

进入 `backend/dist/aiis-pmms-backend/` 后运行：

```powershell
.\aiis-pmms-backend.exe
```

最小冒烟检查：

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/openapi.json
```

## 数据库升级

源码环境首选命令仍是：

```powershell
uv run alembic upgrade head
```

如果现场只能使用打包服务，可临时开启受保护维护 API，使用管理员 bearer token 和 `X-Maintenance-Token` 调用数据库维护接口。维护流程是增量、幂等的，不提供清库、drop、truncate 或 reset 能力。

## 常见问题

- `No module named PyInstaller`：使用带 `--with pyinstaller` 的打包命令。
- `打包产物缺少以下内容`：检查 `alembic.ini`、`alembic/` 是否存在，并确认 PyInstaller 命令没有被安全软件或权限策略中断。`resources/Template.xlsx` 是可选样例模板，缺失不会阻止打包。
- SQL Server 连接失败：安装 `.env` 中 `DB_DRIVER` 指定的 ODBC 驱动，并检查主机、端口、账号、密码和 SQL Server TCP 设置。
- 维护 API 提示未启用：只在受控初始化或升级期间设置 `ENABLE_MAINTENANCE_API=true`，完成后再关闭。
