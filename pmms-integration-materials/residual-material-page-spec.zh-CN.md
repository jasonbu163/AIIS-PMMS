# Qt 板材物料库存管理页面规格

## 页面定位

新增一个独立一级页面，建议名称：

```text
板材物料库存管理
```

建议文件：

```text
gui/pages/residual_material_page.py
services/remote_api.py
```

文件名可以暂时沿用 `residual_material_page.py`，但页面标题、菜单文案和用户可见文案建议使用
“板材物料库存管理”。当前功能围绕板材类物料，覆盖整板 / 余料；管材、型材等物料形态后续单独规划。

如果项目决定先做通用远程表单页，也可以先使用：

```text
gui/pages/remote_form_page.py
```

但首版 UI 不建议做成泛接口调试器。页面应直接围绕库存台账操作员工作流。

## 页面结构

建议分为四块：

1. 顶部连接状态区。
2. 筛选区。
3. 板材物料库存表格。
4. 新增 / 编辑抽屉或弹窗。

### 连接状态区

显示：

- 后端 API URL。
- 当前登录用户。
- 登录状态。
- 最近一次请求状态。

动作：

- 登录。
- 退出。
- 刷新列表。

### 筛选区

字段：

- 材质：`materialGrade`。
- 厚度：`thickness`。
- 状态：`status`。
- 是否可复用：`reusable`。
- 最小宽度：`minWidth`。
- 最小长度：`minLength`。
- 库存类型：`inventoryType`，可选全部 / 整板 / 余料。

默认筛选：

```text
status = available
```

默认不限制 `inventoryType`，让页面展示整板和余料；用户可通过筛选项切换“整板 / 余料”。

筛选语义：

- `materialGrade`：后端模糊匹配，输入 `tes` 可匹配 `test`。
- `inventoryCode`：后端模糊匹配，适合按库存编码片段定位。
- `thickness`：精确匹配，不做文本模糊。
- `status`、`inventoryType`、`reusable`、`materialId`：精确匹配。
- `minWidth`、`minLength`：大于等于筛选。
- Qt 页面只把筛选值传给 `GET /api/v1/inventory-items/page`，不要在本地表格数据上再做二次过滤。

### 表格列

推荐列：

- ID：`id`。
- 库存编码：`inventoryCode`，导出时填充到 `板材名称` 列。
- 材质：`materialGrade`。
- 厚度：`thickness`。
- 宽：`width`。
- 长：`length`。
- 数量：`quantity`。
- 备注：`remark`。
- 来源：`source`。
- 库位：`location`。
- 状态：`status` 显示中文。
- 可复用：`reusable` 显示“是 / 否”。
- 创建日期：`createdAt`。
- 更新日期：`updatedAt`。
- 操作：编辑、作废。
- 批量：勾选后可导出 XLSX，单次最多 200 条。

日期显示规则：

- `createdAt` / `updatedAt` 是后端按 `Asia/Shanghai` 输出的现场本地时间。
- Qt 首版只做格式化显示，例如 `YYYY-MM-DD HH:mm:ss`。
- 不要把这些时间当 UTC 再转换成本地时区，否则会出现重复偏移。

库存表格应直接使用分页接口：

```text
GET /api/v1/inventory-items/page?status=available&page=1&pageSize=20
```

分页响应使用 `data.items` 渲染表格，使用 `data.meta.total` 渲染总数。

### 新增 / 编辑表单

字段：

- 库存编码：`inventoryCode`，只读；新增时后端自动生成。
- 材质：选择 `materialId`，显示 `materialGrade + thickness`。
- 类型：`inventoryType`，可选 `whole_sheet` / `leftover`；新增时默认可用 `leftover`，但不要在页面概念上写死只支持余料。
- 宽：`width`。
- 长：`length`。
- 厚度：`thickness`，默认从材质带出，但允许核对。
- 数量：`quantity`，默认 `1`。
- 备注：`remark`，用于显示最近一次批量导入扣减说明，可人工修正。
- 来源：`source`，默认 `manual-entry`。
- 库位：`location`。
- 状态：`status`，新增默认 `available`。
- 可复用：`reusable`，默认 `true`。

校验建议：

- `materialId` 必填。
- `width > 0`。
- `length > 0`。
- `thickness > 0`。
- `quantity >= 1`。
- 作废动作需要二次确认。

### 入库动作

不要把现场入库做成“编辑库存项并手工改总数量”。这会让操作员分不清是在修正台账，
还是在记录一次真实入库。

建议在库存表格工具栏或行操作中新增“入库”按钮：

- 选中一条库存项后启用。
- `voided` 禁用入库。
- `reserved` / `scrapped` 不建议直接入库；如果用户尝试调用，后端会返回 `invalid_inventory_status`。
- `consumed` 显示为“已耗尽”，允许入库，入库成功后后端自动恢复为 `available`。

入库弹窗字段：

- 库存编码：只读，显示 `inventoryCode`。
- 规格：只读，显示 `materialGrade + thickness + width x length`。
- 当前数量：只读，显示当前 `quantity`。
- 当前状态：只读，按状态字典显示中文。
- 入库数量：必填，`>= 1`，表示本次增量，不是库存总数。
- 来源：默认 `site-stock-in`，可由操作员修改。
- 库位：默认带出当前 `location`，可修改。
- 备注：可选。
- 可复用：默认带出当前 `reusable`。

保存时调用：

```text
POST /api/v1/inventory-items/{inventoryItemId}/stock-in
```

请求示例：

```json
{
  "quantity": 3,
  "source": "site-stock-in",
  "location": "A-02",
  "remark": "现场补充入库",
  "reusable": true
}
```

成功后刷新当前分页列表。Qt 端不要用 `PATCH /inventory-items/{id}` 修改 `quantity`
来表达正常入库；`PATCH` 只保留给资料修正、状态修正或人工复核调整。

### 扣减 / 领用动作

正常扣减不要通过“编辑库存总数量”完成，应使用后端专用扣减接口：

```text
POST /api/v1/inventory-items/{inventoryItemId}/consume
```

建议在库存表格工具栏或行操作中新增“扣减 / 领用”按钮：

- 选中一条库存项后启用。
- `available` / `reserved` 允许扣减。
- `consumed`、`scrapped`、`voided` 禁用扣减。
- 扣减数量必须 `>= 1` 且不能大于当前 `quantity`；后端仍会以 `invalid_inventory_quantity` 兜底。

扣减弹窗字段：

- 库存编码：只读，显示 `inventoryCode`。
- 规格：只读，显示 `materialGrade + thickness + width x length`。
- 当前数量：只读，显示当前 `quantity`。
- 当前状态：只读，按状态字典显示中文。
- 扣减数量：必填，`>= 1`，表示本次增量，不是扣减后的库存总数。
- 来源：默认 `site-consume`，可由操作员修改。
- 备注：可选。

请求示例：

```json
{
  "quantity": 2,
  "source": "site-consume",
  "remark": "现场领用"
}
```

扣减成功后刷新当前分页列表。扣减到 0 时后端会把状态归一为 `consumed`。

### 批量导入 / 导出

页面新增批量处理入口：

- 导入 XLSX。
- 预览导入结果。
- 确认导入。
- 导出选中库存项为同模板 XLSX。

导入流程：

1. 用户选择 XLSX。
2. 调用 `POST /api/v1/inventory-items/import-xlsx?dryRun=true`。
3. 展示预计新增、预计更新、错误行、`使用数量`、`新增数量` 和本次 `remark`。
4. 如果存在错误行，禁用确认导入。
5. 用户确认后调用 `dryRun=false`。
6. 导入成功后刷新分页列表。

导出流程：

1. 用户在表格中勾选库存项。
2. 收集 `inventoryCode` 列表。
3. 超过 200 条时前端直接提示并禁止请求。
4. 调用 `POST /api/v1/inventory-items/export-xlsx`。
5. 保存后端返回的 `inventory-items.xlsx`。
6. 成功后提示“库存文件已导出”。

批量操作区建议：

```text
物料规格 | 导入 XLSX | 导出 XLSX
```

### 物料规格管理

当前 Qt 前端已经有“板材物料库存管理”一级页面，不建议再新增“物料规格管理”一级菜单。
建议在本页面工具栏放一个“物料规格”按钮，打开管理弹窗。

弹窗结构：

- 顶部筛选：材质 / 牌号、厚度、启用状态。
- 主表格：材质 / 牌号、厚度、规格说明、默认单位、启用状态、操作。
- 操作按钮：新增、编辑、启用 / 禁用。

推荐接口：

```text
GET /api/v1/materials/page?page=1&pageSize=20
POST /api/v1/materials
PATCH /api/v1/materials/{materialId}
GET /api/v1/materials/{materialId}
```

编辑规则：

- 已被库存项引用的规格，不允许修改 `materialGrade` / `thickness`。
- 已引用规格仍允许修改 `specDescription`、`defaultUnit`、`enabled`。
- 禁用规格不应出现在“新增库存项”的默认材质下拉框中，但历史库存仍照常显示。
- 不做删除按钮；现场误建规格先禁用。
- 首版前端可以不预先判断规格是否被库存引用；用户保存后如果后端返回
  `material_in_use`，弹出提示“该规格已用于库存，不能修改材质 / 牌号或厚度”。
- 如果后续要优化体验，可以在编辑弹窗旁边加说明文案：已用于库存的规格只能改说明、
  默认单位和启用状态。

新增库存项表单中的“材质”字段建议使用可搜索下拉框：

- 默认调用 `GET /api/v1/materials?enabled=true` 加载可用规格。
- 显示文本建议为 `{materialGrade} / {thickness}mm`。
- 选中后提交 `materialId`。
- 下拉旁边提供 `+` 快速新增规格按钮，新增成功后刷新下拉并自动选中新规格。

交互细节：

- “导出 XLSX”固定保持后端导入模板字段：`板材名称, 图纸路径, 宽, 长, 材质, 厚度, 数量, 使用数量, 新增数量`。
- `板材名称` 由后端填充为 `inventoryCode`。
- `图纸路径` 由后端导出为空字符串。
- `使用数量`、`新增数量` 由后端导出为空列，提示用户可用这两列批量扣减和批量入库新增。
- 当前不导出二维码列；二维码打印交互待后续重新规划。
- 当前 XLSX 模板和页面功能适用于板材类物料；管材、型材等物料形态的导入 / 导出字段待后续规划。
- 导出过程中显示 loading，不阻塞 UI 线程。
- 请求失败时显示后端 `errorCode` 对应中文提示。
- 导出成功后不要自动标记库存为已贴标，首版只完成文件导出。

导出模板列名固定为：

```text
板材名称, 图纸路径, 宽, 长, 材质, 厚度, 数量, 使用数量, 新增数量
```

导入模板兼容旧列 `板材名称, 图纸路径`，但后端会忽略；实际读取：

```text
宽, 长, 材质, 厚度, 数量, 使用数量, 新增数量
```

导入匹配规则：

- 用 `宽 + 长 + 材质 + 厚度` 匹配库存规格。
- 只有 `数量` 且规格不存在：新建库存项并自动生成 `inventoryCode`。
- 只有 `数量` 且规格已存在：报错，提示改填 `使用数量` 或 `新增数量`。
- `数量 + 使用数量`：允许，忽略 `数量`，执行扣减。
- `数量 + 新增数量`：允许，忽略 `数量`，执行入库新增。
- 只有 `使用数量`：扣减，要求规格存在。
- 只有 `新增数量`：入库新增，要求规格存在。
- `使用数量 + 新增数量` 或三列都填：报错。
- 三列都空：报错。
- 扣减到 0 或超扣：库存置 0，状态归一为 `consumed`，备注写差额，等待人工确认。
- 入库新增只允许匹配 `available` / `consumed`；`consumed` 入库后恢复为 `available`。

状态显示建议：

- `available`：可用。
- `reserved`：已占用。
- `consumed`：已耗尽。
- `scrapped`：已报废。
- `voided`：已作废。

### 编码定位

按库存编码定位时不要按 `id` 或 `materialId` 查找，统一调用：

```text
GET /api/v1/inventory-items/by-code?inventoryCode=<库存编码>
```

成功后可以打开详情 / 编辑弹窗，并高亮当前表格行。

## Service 边界

`services/remote_api.py` 建议提供面向业务的方法：

```python
login(username: str, password: str) -> TokenSession
get_current_user() -> User
list_materials(enabled: bool | None = True) -> list[Material]
page_materials(query: MaterialQuery, page: int, page_size: int) -> PageData[Material]
get_material(material_id: int) -> Material
create_material(payload: MaterialCreate) -> Material
update_material(material_id: int, payload: MaterialUpdate) -> Material
page_inventory_items(query: InventoryQuery, page: int, page_size: int) -> PageData[InventoryItem]
create_inventory_item(payload: InventoryCreate) -> InventoryItem
update_inventory_item(item_id: int, payload: InventoryUpdate) -> InventoryItem
stock_in_inventory_item(item_id: int, payload: InventoryStockIn) -> InventoryItem
consume_inventory_item(item_id: int, payload: InventoryConsume) -> InventoryItem
void_inventory_item(item_id: int) -> InventoryItem
get_inventory_item_by_code(inventory_code: str) -> InventoryItem
preview_inventory_xlsx(file_path: str) -> InventoryImportResult
import_inventory_xlsx(file_path: str) -> InventoryImportResult
export_inventory_xlsx(inventory_codes: list[str]) -> bytes
```

UI 页面不直接使用 `requests` / `httpx` 拼接接口。

## 线程 / UI 响应

远程请求不能阻塞 UI 线程。

可选方案：

- 复用现有 worker thread 风格。
- 新增轻量 API worker。
- 使用 Qt 的异步网络能力。

无论选哪种，页面需要显示：

- loading 状态。
- 成功摘要。
- 失败原因。
- 登录失效提示。

## 状态中文显示

建议映射：

```text
available -> 可用
reserved -> 已占用
consumed -> 已消耗
scrapped -> 已报废
voided -> 已作废
whole_sheet -> 整板
leftover -> 余料
```

注意：业务判断只使用英文 key。

## 最小验收

- 可以配置后端 API URL。
- 可以登录并保存本次会话 token，重启后不要求保持登录。
- 可以拉取材质列表。
- 可以新增材质。
- 可以拉取板材物料库存列表，默认包含整板和余料。
- 可以按库存类型筛选整板 / 余料。
- 可以新增一条库存项。
- 可以编辑库存项库位 / 状态 / 可复用标记。
- 可以通过“入库”按钮按增量增加库存，不能用编辑总数量替代。
- 可以通过“扣减 / 领用”按钮按增量扣减库存，扣减到 0 后显示已耗尽。
- 可以作废库存项。
- 可以输入 `inventoryCode` 定位一条库存项。
- 可以导入 200 行以内 XLSX 并显示预览 / 错误行。
- 可以导出 200 条以内选中库存项为同模板 XLSX。
- 401 会提示重新登录。
- 网络断开或超时不会卡死界面。
- 不提交真实账号、密码或 token。
