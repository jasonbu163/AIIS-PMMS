# 术语与系统关系

## 本项目相关名称

| 中文名称 | 英文全称 | 常见缩写 | 说明 |
| --- | --- | --- | --- |
| 物料管理系统 | Material Management System | MMS | 常用于描述物料档案、库存、入库、出库、调拨、盘点等能力，但不是强标准缩写。 |
| 生产物料管理系统 | Production Material Management System | PMMS | 本项目推荐名称，聚焦生产现场备料、用料、剩料、废料和统计数据。 |
| 生产管理系统 | Production Management System | PMS | 容易与其他领域缩写冲突，制造业里更常见的是 MES 或 MOM。 |
| 制造执行系统 | Manufacturing Execution System | MES | 管工单执行、工序、报工、投料、质量、设备状态和生产追溯。 |
| 制造运营管理 | Manufacturing Operations Management | MOM | 比 MES 更大的生产运营管理概念。 |

## 常见行业系统

| 缩写 | 英文全称 | 中文名称 | 核心关注 |
| --- | --- | --- | --- |
| PLM | Product Lifecycle Management | 产品生命周期管理 | 产品定义、图纸、BOM、工艺版本、工程变更。 |
| ERP | Enterprise Resource Planning | 企业资源计划 | 订单、采购、库存账、生产计划、财务、成本。 |
| MES | Manufacturing Execution System | 制造执行系统 | 工单执行、工序、报工、投料、质检、生产追溯。 |
| WMS | Warehouse Management System | 仓库管理系统 | 仓库库存、库位、入库、出库、拣选、盘点。 |
| WCS | Warehouse Control System | 仓库控制系统 | 输送线、AGV、堆垛机、提升机、PLC 等设备任务执行。 |

## 关系说明

可以按职责层级理解：

```text
PLM：定义产品怎么造
  ↓ BOM / 图纸 / 工艺版本

ERP：决定买什么、生产什么、成本多少
  ↓ 采购计划 / 生产订单 / 库存账 / 财务成本

MES：管理车间怎么生产
  ↓ 工单执行 / 工序 / 报工 / 投料 / 质检 / 追溯

WMS：管理仓库物料怎么存、怎么出入库
  ↓ 入库 / 出库 / 拣选 / 补料 / 盘点 / 库位

WCS：让自动化设备真正执行动作
  ↓ 输送线 / 堆垛机 / AGV / 机械臂 / PLC
```

## 本项目在体系中的位置

本项目位于 ERP、MES、WMS 的交界处：

- 从 ERP 或基础资料中获取物料档案、标准用量、生产订单或成本口径。
- 从 MES 或生产计划中获取工单、产线、班组、产品和生产数量。
- 与 WMS 协同处理领料、退料、库存变动和仓库出入库。
- 如果现场有自动化仓储设备，WCS 只负责设备执行，本项目不直接控制设备。

一句话：

> 本项目专门负责把生产现场的备料、用料、剩料、废料数据记录清楚，并形成可用于核算和绩效的数据。
