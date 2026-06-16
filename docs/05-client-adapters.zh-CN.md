# 客户端适配器

[English](05-client-adapters.md)

本文记录 AIIS-PMMS 与外部客户端项目的关系。它不是跨项目学习手册；
PySide6、WPF/.NET、QML/C++ 的横向对比学习笔记应放在 AIIS 级文档中。

AIIS-PMMS 仍然是后端契约源和业务真相源。客户端项目是独立仓库，通过
FastAPI OpenAPI 契约和共享接入材料对接 PMMS。

## 边界

- AIIS-PMMS 负责激光开料余料管理后端、数据库结构、OpenAPI 契约、稳定状态
  key、错误码和接入材料。
- 客户端项目不直接写 PMMS 的 MSSQL 业务数据，必须调用 FastAPI 后端。
- `pmms-integration-materials/` 是 PMMS 侧的客户端交接材料、API 样例和页面规
  格来源。
- `frontends/` 是本地开发和联调便利入口，不表示这些前端源码属于 PMMS 主仓库。
- AIIS 级横向对比学习手册放在本仓库之外。

## 本地工作区链接

本地开发时，PMMS 工作区可以用软链接暴露外部客户端仓库：

```text
frontends/
├── pyside6-frontend -> /Users/jason/Desktop/DreamCode/fastbom
├── dotnet-frontend  -> /Users/jason/Desktop/DreamCode/aiis-pmms-dotnet-frontend
└── qml-frontend     -> /Users/jason/Desktop/DreamCode/aiis-pmms-qml-frontend
```

这些链接只用于本地导航和前后端联调。默认建议在 Git 中忽略 `frontends/`。
如果以后要作为团队共享约定，应优先改成相对路径软链接或 Git submodule，避免提交
本机绝对路径。

AIIS 工程规则也可以通过 `.local-links/engineering-codex` 之类的私有链接在本地
引用。该链接应保持本地私有，不能让 PMMS 看起来在运行时依赖 AIIS 文档仓库。

## 客户端角色

| 客户端 | 仓库 | 定位 | 当前状态 | 第一阶段目标 |
| --- | --- | --- | --- | --- |
| `pyside6-frontend` | `fastbom` | 现有 PySide6 桌面工具和 PMMS 接入客户端。 | 已有本地 SolidWorks/DXF 工作流和 PMMS 库存接入材料。 | 跟随 PMMS API 维护，不重写本地处理主链路。 |
| `dotnet-frontend` | `aiis-pmms-dotnet-frontend` | 面向 Windows 工业软件和厂商 SDK 生态的 WPF/.NET 学习客户端。 | 外部仓库待搭建。 | 用 WPF/MVVM 实现同一组 PMMS 客户端功能切片。 |
| `qml-frontend` | `aiis-pmms-qml-frontend` | 面向 C++ 工程、设备端 UI、未来边缘/ROS 工作的 Qt Quick/QML + C++ 学习客户端。 | 外部仓库待搭建。 | 用 QML 展示层和 C++ services/models 实现同一组 PMMS 客户端功能切片。 |

## 共同第一切片

WPF 和 QML/C++ 新客户端的第一阶段功能应保持小而一致：

1. 服务器地址和请求超时设置。
2. 登录、登出和当前用户。
3. 用户管理。
4. 物料规格管理。
5. 板材物料库存列表、筛选和分页。
6. 新增、编辑、作废库存项。
7. XLSX 导入预览和确认导入。
8. 选中库存项导出 XLSX。
9. 一致的请求状态、空状态和错误反馈。

第一阶段不要扩展到 PDF 识别、日结、看板统计或 SolidWorks/DXF 迁移。这些内容属于
后续 PMMS 或客户端阶段。

## 架构来源

WPF 和 QML/C++ 客户端应参考 AIIS `backend-arch` 背后的核心工程思想，但要按桌面
客户端形态翻译，不照搬后端目录名。

核心翻译：

- 入口层薄：View、Page、Dialog 只收集操作意图和展示状态。
- 契约清晰：DTO、响应信封、分页、错误码放在 contract 层，不散落在 UI 代码中。
- 业务编排集中：application service 负责 API 调用、校验和客户端状态流转。
- 领域规则独立：稳定状态 key、权限判断、动作可用性规则独立于 UI 控件。
- 副作用隔离：HTTP、文件读写、设置、平台 SDK 放在 UI 和 domain 之外。
- 真相源明确：PMMS FastAPI + MSSQL 仍然是业务真相源。

建议 WPF 映射：

```text
Views / ViewModels      -> 入口和展示
Contracts               -> API DTO、StandardResponse、PageData
Application             -> 用例和客户端编排
Domain                  -> 规则、状态 key、权限
Infrastructure          -> HttpClient、设置、文件上传下载
```

建议 QML/C++ 映射：

```text
qml/pages               -> 展示
src/models              -> QObject ViewModel 和 QAbstractListModel
src/contracts           -> DTO 和响应信封
src/services            -> 用例和客户端编排
src/domain              -> 规则、状态 key、权限
src/infrastructure      -> QNetworkAccessManager、QSettings、文件读写
```

## 跟踪规则

本文只跟踪稳定的适配边界和粗粒度客户端状态。详细前端任务应放在各外部客户端仓库
自己的 `PLAN.md`、issue 或本地 checklist 中。

当 PMMS 后端 API 变化并影响客户端时，应同步更新：

1. 后端测试和 OpenAPI 契约。
2. `pmms-integration-materials/`。
3. 如果客户端边界或共同第一切片变化，更新本文。
4. 受影响客户端仓库自己的计划或实现说明。

