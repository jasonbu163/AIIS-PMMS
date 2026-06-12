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
- 首次启动时自动创建的 `logs/`
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
LOG_DIR=logs
```

真实现场 `.env` 不要提交到 Git。

`LOG_DIR` 可以是相对路径或绝对路径。相对路径在源码运行时从 `backend/` 解析，打包运行时从可执行文件目录解析。使用默认值时，源码运行写入 `backend/logs/`，打包运行写入 `dist/aiis-pmms-backend/logs/`。

## 现场连通性检查

启动打包可执行文件前，先在 PMMS 后端所在服务器上执行：

```powershell
Get-OdbcDriver | Where-Object { $_.Name -like "*SQL Server*" } | Select-Object Name
Test-NetConnection <db-host> -Port <db-port>
```

`DB_DRIVER` 必须和 PMMS 后端服务器上已安装的驱动名称完全一致，不是看数据库服务器上装了什么驱动。生产部署建议在 PMMS 后端服务器安装 Microsoft ODBC Driver 17 或 18 for SQL Server。Driver 11 可以用于临时验证配置路径，但版本较老，后续可能出现兼容性问题。

`Test-NetConnection` 应返回：

```text
TcpTestSucceeded : True
```

如果 ping 成功但 TCP 失败，先处理数据库服务器上的 SQL Server TCP/IP、固定端口或 Windows 防火墙，再排查账号密码。默认现场端口建议在 SQL Server Configuration Manager 中启用 TCP/IP，将 `IPAll -> TCP Dynamic Ports` 清空，并把 `IPAll -> TCP Port` 设置为 `1433`；修改后重启 SQL Server 服务。如果现场使用命名实例或动态端口，则把 `.env` 中的 `DB_PORT` 改为实际监听端口。

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

端口以 `.env` 中的 `SERVER_PORT` 为准。例如 `.env` 配置了 `SERVER_PORT=18080`，则检查 `http://127.0.0.1:18080/health`。

运行日志写入 `LOG_DIR`，其中 `api.log` 记录普通 `INFO+` 输出，`api-error.log` 记录 `ERROR+` 输出。

## Windows 开机启动

现场部署可以选两种常用开机启动方式。

### 任务计划程序

在可执行文件目录创建 `start-pmms.bat`：

```bat
@echo off
cd /d C:\pmms-backend
.\aiis-pmms-backend.exe
```

在 Windows 任务计划程序中创建任务：

- 常规：名称填写 `AIIS-PMMS Backend`，选择“不管用户是否登录都要运行”，并勾选“使用最高权限运行”。
- 触发器：选择“启动时”。
- 操作：启动 `C:\pmms-backend\start-pmms.bat`。
- 起始于：填写 `C:\pmms-backend`。
- 设置：启用失败后重启，例如每 1 分钟重启一次，最多尝试 3 次。

这种方式不需要额外安装工具，适合作为最快的现场启动方案。

### NSSM 注册 Windows 服务

如果希望按服务方式运行，可在 PMMS 后端服务器安装 NSSM，然后执行：

```powershell
nssm install AIIS-PMMS-Backend
```

在 NSSM 弹窗中填写：

```text
Path: C:\pmms-backend\aiis-pmms-backend.exe
Startup directory: C:\pmms-backend
```

然后启动服务：

```powershell
nssm start AIIS-PMMS-Backend
```

必须把启动目录设置为可执行文件目录，确保后端读取同目录下正确的 `.env`。

## 现场更新

不要把历史现场日志打进新包，也不要在更新时覆盖历史日志。`logs/` 是运行时数据，服务启动时会自动创建。

替换现场程序前：

1. 停止后端服务。
2. 备份当前程序目录，至少备份：
   - `.env`
   - `logs/`
   - `storage/`
3. 复制新版程序文件到现场目录。
4. 恢复或保留现场自己的 `.env`、`logs/` 和 `storage/`。
5. 启动后端服务。
6. 检查 `/health`，再查看 `logs/api.log` 和 `logs/api-error.log`。

常规更新时，应保留这些现场运行时路径：

```text
.env
logs/
storage/
```

可以从新版包替换这些程序文件：

```text
aiis-pmms-backend.exe
_internal/
alembic.ini
alembic/
.env.example
```

`storage/` 可能包含导出文件、上传文件、原始归档文件或其他业务凭证。除非有单独的数据迁移或清理方案，否则应按现场数据处理。

## 数据库升级

源码环境首选命令仍是：

```powershell
uv run alembic upgrade head
```

如果现场只能使用打包服务，可临时开启受保护维护 API，使用管理员 bearer token 和 `X-Maintenance-Token` 调用数据库维护接口。维护流程是增量、幂等的，不提供清库、drop、truncate 或 reset 能力。

## 常见问题

- `No module named PyInstaller`：使用带 `--with pyinstaller` 的打包命令。
- `打包产物缺少以下内容`：检查 `alembic.ini`、`alembic/` 是否存在，并确认 PyInstaller 命令没有被安全软件或权限策略中断。`resources/Template.xlsx` 是可选样例模板，缺失不会阻止打包。
- `IM002` / `未发现数据源名称`：PMMS 后端服务器找不到 `DB_DRIVER` 指定的驱动。请在 PMMS 服务器上运行 `Get-OdbcDriver ...`，把输出的驱动名称原样填入 `.env`，或在 PMMS 服务器安装 ODBC Driver 17/18。
- `08001` / `10061` / 目标计算机积极拒绝连接：驱动已经找到，但数据库端口不可达。请在 PMMS 服务器执行 `Test-NetConnection <db-host> -Port <db-port>`，处理数据库服务器的 SQL Server TCP/IP 或防火墙，直到 `TcpTestSucceeded` 为 `True`。
- 登录失败或数据库不存在：网络已经打通，继续检查 `DB_USER`、`DB_PASSWORD`、`DB_NAME`、SQL Server 混合认证模式和用户权限。
- 维护 API 提示未启用：只在受控初始化或升级期间设置 `ENABLE_MAINTENANCE_API=true`，完成后再关闭。
