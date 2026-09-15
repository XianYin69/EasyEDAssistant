# EasyEDAssistant Reference：官方文档与 GUI 指令映射

> 本文件由 SKILL.md v0.9.0「嘉立创EDA 官方文档（参考）」与「官方手册指令映射（GUI 菜单 ↔ 本 skill CLI）」逐字迁移而来（v0.10.0 主干化重构）。
> 原章节编号保持不变；SKILL.md 是唯一入口，按触发条件加载本文件。

## 嘉立创EDA 官方文档（参考）

嘉立创EDA专业版（EasyEDA Pro）官方文档是本 skill 的基础参考。以下文档
与本 skill 最相关（中文，由嘉立创科技集团股份有限公司所有）：

| 主题 | 文档标题 | 链接 | 相关性 |
|---|---|---|---|
| 快速入门 | 嘉立创EDA专业版快速入门 | [链接](https://prodocs.easyeda.com/cn/quick-start.html) | 必读；工程创建、界面介绍 |
| 原理图设计 | 原理图设计 | [链接](https://prodocs.easyeda.com/cn/private/designer/design-schematic.html) | **核心参考**；放置器件、电气连接、更新到PCB |
| PCB 设计 | PCB 设计 | [链接](https://prodocs.easyeda.com/cn/private/designer/design-pcb.html) | **核心参考**；网格设置、图层、布线、DRC |
| 仿真 | 仿真介绍 | [链接](https://prodocs.easyeda.com/cn/simulation/introduction) | 辅助参考；Simulide/NGSpice 引擎 |
| 文件生成 | 文件生成与导出 | [链接](https://prodocs.easyeda.com/cn/file-generation) | 辅助参考；BOM、Gerber、PDF导出 |
| 扩展 API | 嘉立创EDA专业版扩展 API | [链接](https://prodocs.easyeda.com/cn/api/reference) | 扩展开发参考 |

**注意**：
- 本 skill 的 MCP API (`eda.*`) 与 CLI (`easyeda <domain> <command>`)
  都是基于上述官方文档设计的程序化接口。
- 官方文档描述的是 GUI 操作流程；本 skill 提供的程序化路径（`sch connect`
  / `sch apply` / `pcb route-short` / `pcb drc` 等）是对等价操作的映射，
  不一定与 GUI 菜单顺序完全一致。
- 官方文档与本 skill 冲突时，以 daemon 规则代码（`pcb_rules.go` 等）为
  真值来源。

## 官方手册指令映射（GUI 菜单 ↔ 本 skill CLI）

嘉立创 EDA 官方手册的"指令"部分即 GUI 菜单栏（放置/设计/布线/布局/工具/导出）
的逐条说明。本节把官方菜单指令映射到本 skill 的程序化等价命令，并给出各
菜单页的官方文档链接（`https://prodocs.easyeda.com` + 下表路径）。
GUI 快捷键：[快捷键](https://prodocs.easyeda.com/cn/introduction/hotkeys/)；
设计流程：[设计流程](https://prodocs.easyeda.com/cn/introduction/design-flow/)。

### 原理图（Schematic）指令

官方路径前缀：`/cn/schematic/`。下表"官方手册指令"为 GUI 菜单项，
"本 skill 命令"为程序化等价（参数真值见 §5）。

| 官方手册指令 | 官方文档 | 本 skill 程序化等价 |
|---|---|---|
| 放置 - 器件 | [place-device](https://prodocs.easyeda.com/cn/schematic/place-device/) | `sch compose` / `sch materialize`（Lib 放置） |
| 放置 - 导线 | [place-wire](https://prodocs.easyeda.com/cn/schematic/place-wire/) | `sch autoconnect`（pin-aware）/ `sch connect`（不幂等） |
| 放置 - 网络标签 | [place-net-label](https://prodocs.easyeda.com/cn/schematic/place-net-label/) | `sch autoconnect --kind power/ground` 生成 netflag/netlabel |
| 放置 - 网络端口 | [place-net-port](https://prodocs.easyeda.com/cn/schematic/place-net-port/) | `sch autoconnect` 委托 connect_pin（netport 边界） |
| 放置 - 非连接标识 | [place-no-connect](https://prodocs.easyeda.com/cn/schematic/place-no-connect/) | `pin.noConnected:true`（保留物理引脚，不删脚） |
| 设计 - 更新/转换原理图到 PCB | [design-update-convert-schematic-to-pcb](https://prodocs.easyeda.com/cn/schematic/design-update-convert-schematic-to-pcb/) | `pcb import-changes`（自动点"应用修改"对话框） |
| 设计 - 检查 DRC | [design-check-drc](https://prodocs.easyeda.com/cn/schematic/design-check-drc/) | `sch gate --strict --doc <page>`（layout-lint→check→bridge-check→SDK DRC） |
| 设计 - 分配位号 | [design-annotate-designator](https://prodocs.easyeda.com/cn/schematic/design-annotate-designator/) | `sch designators allocate` → `plan` → `verify` |
| 布局 - 对齐 | [layout-align](https://prodocs.easyeda.com/cn/schematic/layout-align/) | `sch lib-layout`（Lib 内部位置）/ `sch compose`（模块 Z 字排版） |
| 导出 - 导出 BOM | [export-bill-of-materials-bom](https://prodocs.easyeda.com/cn/schematic/export-bill-of-materials-bom/) | `bom-enrich.py`（补 LCSC C 号） |
| 导出 - 导出网表 | [export-netlist](https://prodocs.easyeda.com/cn/schematic/export-netlist/) | `sch_ManufactureData.getNetlistFile()`（不用已废弃 `sch_Netlist.getNetlist()`） |

### PCB（PCB）指令

官方路径前缀：`/cn/pcb/`。

| 官方手册指令 | 官方文档 | 本 skill 程序化等价 |
|---|---|---|
| 放置 - 过孔 | [place-via](https://prodocs.easyeda.com/cn/pcb/place-via/) | `pcb.via.create`（默认 12/24 mil）/ `pcb via-hop`（复合换层） |
| 放置 - 铺铜区域 | [place-copper-region](https://prodocs.easyeda.com/cn/pcb/place-copper-region/) | `pcb.pour.create`（net 必绑）/ `pcb power-pour` / `pcb power-planes` |
| 放置 - 禁止区域 | [place-prohibited-region](https://prodocs.easyeda.com/cn/pcb/place-prohibited-region/) | `pcb region create --ref … --margin … --rule no-pours`（天线全层 keepout） |
| 布线 - 单路布线 | [route-single-routing](https://prodocs.easyeda.com/cn/pcb/route-single-routing/) | `pcb.route-short`（启发式）/ 坐标 `pcb.line.create` |
| 布线 - 差分对布线 | [route-differential-pair-routing](https://prodocs.easyeda.com/cn/pcb/route-differential-pair-routing/) | `pcb diff-pair` 约束 + 布线后 `pcb report` 量 skew |
| 布线 - 自动布线 | [route-auto-routing](https://prodocs.easyeda.com/cn/pcb/route-auto-routing/) | `pcb export-dsn`（含 keepout）→ Freerouting 兜底（§9 限制：无 `eda.*` 自动布线 API） |
| 设计 - 从原理图导入变更 | [design-import-changes-from-schematic](https://prodocs.easyeda.com/cn/pcb/design-import-changes-from-schematic/) | `pcb import-changes`（报 before/after 计数差） |
| 设计 - 检查 DRC | [design-check-drc](https://prodocs.easyeda.com/cn/pcb/design-check-drc/) | `pcb drc --json` + `pcb check`（DFM 审计） |
| 设计 - 网络类管理器 | [design-net-class-manager](https://prodocs.easyeda.com/cn/pcb/design-net-class-manager/) | `pcb net-classes`（net-class → 线宽阶梯，角色分档） |
| 设计 - 差分对管理器 | [design-differential-pair-manager](https://prodocs.easyeda.com/cn/pcb/design-differential-pair-manager/) | `pcb diff-pair` 约束 |
| 设计 - 等长网络组管理器 | [design-equal-length-group-manager](https://prodocs.easyeda.com/cn/pcb/design-equal-length-group-manager/) | `pcb eq-group` 约束 + 布线后 spread 校验 |
| 工具 - 铺铜管理器 | [tools-copper-manager](https://prodocs.easyeda.com/cn/pcb/tools-copper-manager/) | `pcb pour-clean --netless` / `pcb pour-rebuild`（stale 铺铜重流） |
| 工具 - 泪滴 | [tools-teardrop](https://prodocs.easyeda.com/cn/pcb/tools-teardrop/) | 无 `eda.*` API——制造前 UI 右键手动加（§9 已知限制） |
| 导出 - PCB 制板文件 Gerber | [export-pcb-fabrication-file-gerber](https://prodocs.easyeda.com/cn/pcb/export-pcb-fabrication-file-gerber/) | 制造文件导出（Gerber） |
| 导出 - 坐标文件 | [export-pick-and-place-file](https://prodocs.easyeda.com/cn/pcb/export-pick-and-place-file/) | 贴装坐标文件导出 |

**映射原则**：
- 官方菜单是**人机交互入口**；本 skill 命令是同一套 `eda.*` API 的
  程序化映射。GUI 操作与程序化操作产生等价图元，但本 skill 额外做
  dry-run/回读/`saved:true` 验证（GUI 路径没有这些门控）。
- 官方文档的快捷键（如 放置-导线 `Alt+W`）在 GUI 有效；本 skill 走
  MCP/CLI，不依赖键盘快捷键。
- 数值判据（线宽/间距/keepout 半径）以 daemon 规则代码为真值，
  官方菜单仅描述"在哪设"，不定义数值。
