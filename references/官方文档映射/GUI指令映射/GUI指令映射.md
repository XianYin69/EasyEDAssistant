# EasyEDAssistant Reference：官方文档映射 — GUI 指令映射

> 本文件把官方 GUI 菜单指令映射为等价程序化命令（自然语言），自 `references/lib/official-docs.md` 迁入。
> 编辑遵守 RULE_EDIT.md：文本 ≤ 50 行、自然语言；路径前缀为 `https://prodocs.easyeda.com`。

## 原理图（前缀 `/cn/schematic/`）

| 官方手册指令 | 官方文档 | 本 skill 程序化等价 |
|---|---|---|
| 放置 - 器件 | `place-device` | `sch compose` / `sch materialize`（Lib 放置） |
| 放置 - 导线 | `place-wire` | `sch autoconnect`（pin-aware）/ `sch connect`（不幂等） |
| 放置 - 网络标签 | `place-net-label` | `sch autoconnect --kind power/ground` 生成 netflag/netlabel |
| 放置 - 网络端口 | `place-net-port` | `sch autoconnect` 委托 connect_pin（netport 边界） |
| 放置 - 非连接标识 | `place-no-connect` | `pin.noConnected:true`（保留物理引脚，不删脚） |
| 设计 - 更新/转换到 PCB | `design-update-convert-schematic-to-pcb` | `pcb import-changes`（自动点「应用修改」对话框） |
| 设计 - 检查 DRC | `design-check-drc` | `sch gate --strict --doc <page>`（layout-lint→check→bridge-check→SDK DRC） |
| 设计 - 分配位号 | `design-annotate-designator` | `sch designators allocate` → `plan` → `verify` |
| 布局 - 对齐 | `layout-align` | `sch lib-layout`（Lib 内部位置）/ `sch compose`（模块 Z 字排版） |
| 导出 - BOM | `export-bill-of-materials-bom` | `bom-enrich.py`（补 LCSC C 号） |
| 导出 - 网表 | `export-netlist` | `sch_ManufactureData.getNetlistFile()`（不用已废弃的 `sch_Netlist.getNetlist()`） |

## PCB（前缀 `/cn/pcb/`）

| 官方手册指令 | 官方文档 | 本 skill 程序化等价 |
|---|---|---|
| 放置 - 过孔 | `place-via` | `pcb.via.create`（默认 12/24 mil）/ `pcb via-hop` |
| 放置 - 铺铜区域 | `place-copper-region` | `pcb.pour.create`（net 必绑）/ `pcb power-pour` / `pcb power-planes` |
| 放置 - 禁止区域 | `place-prohibited-region` | `pcb region create --rule no-pours`（天线全层 keepout） |
| 布线 - 单路布线 | `route-single-routing` | `pcb.route-short`（启发式）/ 坐标 `pcb.line.create` |
| 布线 - 差分对 | `route-differential-pair-routing` | `pcb diff-pair` 约束 + `pcb report` 量 skew |
| 布线 - 自动布线 | `route-auto-routing` | `pcb export-dsn` → Freerouting 兜底（无 `eda.*` 自动布线 API） |
| 设计 - 导入变更 | `design-import-changes-from-schematic` | `pcb import-changes`（报 before/after 计数差） |
| 设计 - 检查 DRC | `design-check-drc` | `pcb drc --json` + `pcb check`（DFM 审计） |
| 设计 - 网络类管理器 | `design-net-class-manager` | `pcb net-classes`（线宽阶梯，角色分档） |
| 设计 - 差分对管理器 | `design-differential-pair-manager` | `pcb diff-pair` 约束 |
| 设计 - 等长网络组 | `design-equal-length-group-manager` | `pcb eq-group` 约束 + `pcb report` 校验 spread |
| 工具 - 铺铜管理器 | `tools-copper-manager` | `pcb pour-clean --netless` / `pcb pour-rebuild` |
| 工具 - 泪滴 | `tools-teardrop` | 无 `eda.*` API——制造前在 UI 右键手动加 |
| 导出 - Gerber | `export-pcb-fabrication-file-gerber` | 制造文件导出（Gerber） |
| 导出 - 坐标文件 | `export-pick-and-place-file` | 贴装坐标文件导出 |

## 映射原则

1. 官方菜单是人机交互入口，本 skill 命令是同一套 `eda.*` API 的程序化映射；等价图元，但本 skill 额外做 dry-run / 回读 / `saved:true` 验证。
2. 数值判据以 daemon 规则代码（Go）与 JLC 官网为真值，官方菜单只描述「在哪设」，不定义数值。

## 依据来源

- 原正本 `references/lib/official-docs.md`（已迁入）。
- 程序化等价命令的参数真值：`easyeda <command> --help` 与 `easyeda actions`。