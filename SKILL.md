---
name: EasyEDAssistant
description: "基于 JLCEDA MCP VS Code 插件桥接操作嘉立创 EDA（EasyEDA）的移植版电路设计 skill：原理图/PCB/射频/模拟/数字/滤波器/电源设计与检查。支持 MCP 与原有 CLI/daemon 双链路，内置电气规范、数据手册 PDF 阅读经验与项目文档任务（许可证/README）。"
license: MIT
compatibility: "Requires JLCEDA MCP VS Code plugin running locally (ws://127.0.0.1:8765/bridge/ws + http://127.0.0.1:7655/mcp). Fallback: easyeda CLI/daemon/Agent Connector. Offline design planning needs no editor."
metadata:
  author: EasyEDAssistant
  version: "0.6.0"
---

# EasyEDAssistant 设计 Skill

用 JLCEDA MCP VS Code 插件桥接操作嘉立创 EDA（EasyEDA 专业版）：原理图绘制、
PCB 布局布线、射频/模拟/数字/滤波器/电源设计、检查与制造文件导出。
知识基线见同仓 `Sample/easyeda-agent-skill-behavior.md`（24–25 节为移植版专属判据）。
本 skill 是移植版行为规范；API 操作与数值判据以 `Sample/easyeda-agent/references`
与 `Sample/easyeda-agent/scripts` 为真值来源，冲突时以 daemon 规则代码为准。

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

---

## 1. 连接（双链路，原有方式必须保留）

### 1.1 JLCEDA MCP 链路（移植版主路径）

| 通道 | 地址 | 用途 |
|---|---|---|
| WebSocket 桥接 | `ws://127.0.0.1:8765/bridge/ws` | 动作派发、心跳、窗口上下文 |
| HTTP MCP | `http://127.0.0.1:7655/mcp` | MCP 工具/资源/提示服务入口 |

Kilocode 接入（`kilo.json`，与原有链路并存、不互斥）：

```jsonc
{
  "mcp": {
    "jlceda": {
      "type": "remote",
      "url": "http://127.0.0.1:7655/mcp",
      "enabled": true
    }
  }
}
```

**链路选择策略**（单链路直用，不重试）：
- MCP 与 CLI/daemon 两条链路是**替代关系**，不是级联备用。
- 开始工作前按以下优先级检测：
  1. 先尝试 `7655` 端点（MCP HTTP）；连通则全程使用 MCP。
  2. 若 MCP 不可用，再尝试 `60832` 端口（daemon）；连通则全程使用 CLI/daemon。
- **一旦检测到可用链路就使用该链路**，不重试另一条链路，不做"莫名奇妙的检测"。
- 两条端口属于同一插件，插件未启动时 `7655`/`8765` 两条端点均不可用，
  按 §1.3 恢复流程处理。

行为约束（MCP 使用时）：

- MCP 工具与 typed action 语义一致：同一套 `eda.*` API 映射、dry-run/回读/
  `saved:true` 纪律、破坏性操作确认门控；MCP 只是另一入口，不豁免任何验证。
- 审计继续写本地 `~/.easyeda-agent/audit`，MCP 调用同样记录。

### 1.2 原有链路（兼容，不得移除）

- `easyeda` CLI + daemon + EasyEDA Agent Connector；`--project` / `--doc` 路由。
- **版本门禁（会话第一条命令）**：`easyeda update --check --exit-code`，先于任何
  项目读取、离线规划、`health` 和 EDA 操作。CLI/Skill/daemon 必须精确等于 GitHub
  latest，Connector 与 latest 共享 `major.minor` 兼容线才返回 0；仅 patch 差异通过。
  门禁非 0 时停止任务按 `Sample/easyeda-agent/references/environment-setup.md` 升级；**升级/替换组件后本会话不得
  继续，必须新开会话从第一条命令重新开始**。不得用 `--version`、`--preserve`、
  `--skip-version-check` 或仅看 `health` 绕过门禁。
- **`doc reload` 门（铁律）**：PCB mutation（rip-up/route/delete/via/track/pour）
  后读 `STALE_READ` 时按提示 `easyeda doc reload --project <name>`（自身先 save），
  再重读；确定性复位 = `rip-up → save → reload`。`pour-rebuild` 也是"铺铜连通性
  stale"的修法。绕过开关是 `--force-stale-read "<理由>"`（入审计，不是 `--force`）。
- 写操作使用 `--project` 和 `--doc`，由 CLI 在派发前实时确认目标文档；
  `windowId` 随重连变化，不作为持久身份，优先用项目/文档 UUID 路由。
- **链路选择策略**：与 MCP 相同——先检测 `60832` 端口（daemon）；连通则全程
  使用 CLI/daemon；不重试 MCP。MCP 与 CLI/daemon 是替代关系，非级联备用。

### 1.3 连接异常恢复

1. 没有 daemon：检查安装路径与启动日志；`easyeda daemon start` 监听 60832。
2. daemon 正常但 `windows` 为空：检查编辑器、登录态、扩展启用与"允许外部交互"。
3. 同一目标页出现多版本/windowId、反复注册或写请求超时：先回读确认最后一条写
   是否落地 → 检查扩展管理器只保留所选渠道的当前连接器 → 仅当 daemon 本身
   异常时重启 → `health` 确认只剩预期连接后再继续。不循环刷新、批量杀进程、
   重发写操作或清空 IndexedDB。

---

## 2. 开始工作

0. **先澄清需求与目标，再动手**（§11 详述）：用户任务含糊时先补齐
   目标、边界与验收标准；已有的确认与授权沿用，不重复索取。
   执行中遇强制/条件中断点按 §11.5 暂停等待用户确认。
1. 确认插件状态：`8765` / `7655` 端点可达；不可达走原 daemon 链路。
2. 读目标工程基线：

   ```bash
   easyeda health --project <project>
   easyeda doc ls --project <project> --json
   easyeda sch connectivity --all-pages --project <project> > project-connectivity.json
   easyeda sch list --project <project> --doc <page-uuid> \
     --include-device-identity --include-pins --include-bbox --include-wires > page-before.json
   easyeda sch sheet-geometry --project <project> --doc <page-uuid> --json
   ```

3. 写前读被改器件、引脚、网络与几何；位号或 primitiveId 不明确时不盲写。
   每个参与绘图的引脚应恰好对应：一个网络、明确 NC（`noConnected:true`）或
   显式 `connectionState:"unconnected"`，三者互斥；悬空仅当官方快照明确返回
   `net:""` 与 `noConnected:false` 时自动导出，仍保留 `unconnected-pin` 警告。
4. 按任务选子域判据（第 4 节），只加载相关参考；以 `easyeda <domain> <command>
   --help` 与 `easyeda actions` 为参数真值。
5. 临时 JSON、计划与回读结果放入项目已忽略的临时目录；保留原始快照，在副本中设计。

---

## 3. 坐标、单位与数据模型（承重的地基）

| 上下文 | 单位 | 说明 |
|---|---|---|
| 原理图 | 1 raw = 0.01 inch = 0.254 mm | **y-UP**；器件 anchor 5 raw 网格；排版优先 10 raw（100 mil）节拍 |
| PCB | 1 mil = 0.001 inch | **y-UP**；SMD 25 mil / 通孔 50 mil / 精密 5 mil 子栅 |
| mm 参数 | 边界换算 | 2.54 mm = 10 raw；0.5 mm ≈ 20 mil |

数据模型要点：

- `component.id` 是不透明稳定 ID；`ref` 是显示位号；功能名存 `role`。
  保留正常位号的大小写、前导零与声明顺序；`U_RF` 这类功能名不当位号。
- `pin`：`number` 是完整物理引脚编号，`name` 是符号脚名；**保留器件全部物理引脚**，
  不删脚、不猜 NC。
- PCB 器件 `x/y` 是**锚点**（footprint 原点），不是 bbox 中心，且偏移随旋转变化
  （#105）：规划一律用 `pcb list --include-bbox` 返回的 `center`，写入用
  `pcb modify --center --x <cx> --y <cy>`；旋转与 center 不能同一调用。
- 每器件绑定 `TOP`/`BOTTOM` 层；无左右镜像，只有翻面（`pcb.component.modify`）。
- 无程序化 undo：改前取**新鲜 primitiveId**，before/after 进审计日志。

---

## 4. 设计子域判据（移植版知识库）

> 数值判据为方向性规则；落地前以数据手册与实测为准。
> 判据索引：P0–P7 优先级总则裁决冲突；硬门（layout-lint gate / DRC /
> antenna-keepout）不可放宽，`--force-unsafe`（有审计的越门选项，见
> `Sample/easyeda-agent/references/design-flow.md`）不是恢复步骤。

### 4.1 优先级总则（PCB 冲突裁决）

| 级别 | 约束 | 一句话 |
|---|---|---|
| P0 | 机械/外壳锁定坐标 | 连接器、安装孔、面板件 XY 由外壳定死，immovable，其余绕它走 |
| P1 | 安全间距/隔离 | HV/LV 爬电+电气间隙是法规硬线，压倒美观/性能 |
| P2 | EMI 热回路 + 关键去耦 | 开关器输入回路（Cin+开关管）、IC 去耦、晶振——"贴紧"赢过热散开 |
| P3 | 参考平面/回流连续性 | 高速/敏感件不摆平面分割、开槽、板边导致回流绕路处 |
| P4 | 热 keep-out | 独立热源散开、怕热件远离；**不约束** P2 的开关回路自己的陶瓷件 |
| P5 | 功能分区/模块化 | 按 net 聚簇、模拟/数字/RF 分区、块成不重叠瓦片 |
| P6 | DFM | 朝向一致/极性/扇出空间/测试点 |
| P7 | 网格/对齐/丝印 | 纯收尾美化，永远不得违反以上任何一级 |

执行顺序 = "先 P5 粗聚簇，再 P2/P4 细约束就地改写"（自动布局执行步骤见
上游 `Sample/easyeda-agent/references/pcb-layout.md` §11，本 skill 的收尾
顺序见 §12.2）。

### 4.2 PCB 布局与原理图绘制

**原理图**：

- 按功能 Lib 九宫格分区：电源左列（TL/ML/BL）、MCU 中列（MC）、RF/IO 右列（TR/MR/BR）；
  MCU 含 RF 时迁移到角落，RF pi-network + 天线引到板边。
- 模块间距经验值：R/C/L 之间 80–120；小 IC（8–16 pin）200–280；中 IC 280–400；
  MCU 邻射频/传感器 400–600；晶振邻 MCU 理想 60–120（集成 RF 放宽 ≤500）。
- 短桩（pin lead-out）：每个需要接入 wire/netflag/netport 的 pin 必须经**非零长度**
  wire 引出（坐标重合不算连接）；零长 wire 是 DRC fatal。推荐长度：power 20–40
  朝上、ground 10–40 朝下、netport 20–60 朝外、信号 10–90（p90 85）、去耦 10–20。
- 走线直角约定：所有 wire 水平或竖直；长 wire 拐两次以上或单段 >100 units 改用
  net label；线宽：信号 1、电源 2、总线 3。
- 命名约定：电源 `+5V`/`+3V3`；外设 `VDD_SPI`；低有效 `nRESET`（ESP32 `CHIP_PU`
  高有效不加 n）；差分 `USB_D+`/`USB_D-`；总线 `DATA[7..0]`；芯片 pin 直出沿 datasheet
  pin name（`SPIHD`、`GPIO0`），优先于再造别名。
- 功能框与标题：粉色虚线框 `#AA00AA` + 0.2 inch（20 raw）标题；贴边 10 raw，
  标题净距 5 raw；Z 字排版（左上起，同行顶齐，按行最高框换行）。
 可读性经验：同模块内信号流尽量单轴（左→右或上→下），避免交叉回走；
 跨模块用 netport 而不是长导线；同排器件符号方向一致（输入朝同侧）；
 每个框高度紧凑（不留大面积空白），但标题净距 5 raw 与贴边 10 raw 不牺牲。
 视觉终检（`sch export-image`）重点看：文字压线/压框、模块框是否完整包含
 内容、阅读顺序是否 Z 字、同排方向是否一致。
- 去耦电容分级：高速/RF/ADC 电源 pin SHOULD ≤30 / MUST ≤60；一般数字 SHOULD ≤60 /
  MUST ≤120；bulk 储能 200 units。每个 VCC pin 一只 0.1µF；模块电流 >50mA 并联 10µF。

**PCB 放置**：

- 放置前先生成**布局蓝图**（§7.4，Markdown + 字符画板框）：把模块/组件/
  部件及其连接可视化，经 P3 板框中断点（§11.5）拍板后再四档放置。
- 四档顺序：T1 安装孔 → T2 板边接口（USB/电源/天线，开口朝外）→ T3 主芯片 →
  T4 卫星/配套器件。用 `pcb stage confirm-tier <1|2|3|4>` 记录，`confirm-layout`
  签核布局。
- 边缘连接器 bbox 最靠板框边 ≤20 mil，插入面朝板外；**插头受体**（USB-C/Micro/
  DC jack/HDMI）mating 面突出板框 ~0.5–1mm（板框在下方内缩让位），焊盘全在框内。
- 安装孔：靠四角、孔心距板边 ≥3mm（118 mil）；keep-out 半径 = max(孔半径+40mil,
  头/垫圈半径)；M3 用 `pcb mount-holes`（碰撞检查后落 MULTI 层挖槽，不盲放坐标）。
- 边缘连接器拔插走廊：开口正前方 ≥200 mil（5mm）无遮挡。
- 板框默认圆角（铺铜前 `pcb outline-round`）；半径 ≤ 安装孔外缘距板边距离。
  两条合法路径：有机械尺寸先建 outline 再摆放；无尺寸先粗布局（临时大 outline）
  后收紧。任何 outline 修改使 `outline_confirmed` 失效，须重签。
- 手焊 profile：普通器件间距 ≥40 mil，大焊盘烙铁通道 ≥60 mil
  （`pcb stage set-assembly --profile hand-solder`；`layout-lint --gate` 机械执行，
  含 solder-access 检查：每器件 bbox 四侧至少一侧 ≥60mil 净通道）。
- 丝印：位号/极性/逐脚功能标在**器件本体外**、装配后可见（丝印压在连接器
  塑料投影内 = 等于没标）；底面器件丝印镜像 + 反向。

**美观与功能性兼顾的经验（PCB 层）**：

- 功能先行：美观（P7 收尾）永远不得违反 P0–P6；分数低不构成返工理由，
  只在功能约束已满足、还有余量时才去优化。
- 朝向：同类件共用至多两种正交朝向（0°/90°），极性件 pin-1 全朝同向
  （通常朝上或朝左）；减少反贴缺陷，也最整齐。
- 成行对齐：同前缀同尺寸"成排"件（C1..C8 去耦排、R 阵列、排针）共用
  一条轴（±2 mil）、行内中心距恒定（±5 mil，取 100/150/200 mil 栅倍数），
  体边间隙 ≥40 mil。用 `pcb.align` / `pcb.distribute` 执行，`grid_snap`
  （排除公制间距件与锁定件）落格。
- 阵列步进：等距阵列（排针、总线 pad）按 100/150/200 mil 栅取整；
  相邻步距 >500 mil 视为两簇不算同阵列。
- 板面利用率：`compact` 维双侧评分（太空和太挤都扣）；
  `pcb outline-fit` 收紧板框（默认 100 mil margin，在铺铜/布线前跑）。
- 布线视觉：90° 直角走线既违反 45° 规范又是"乱"的来源——
  `pcb beautify` 圆角化收尾；密集板按 `--net` 小范围处理，不做全板 pass。
- 同排/同列器件方向一致、位号放同一相对侧、字高统一（Designator 与
  自由字符串分开统计）；`pcb layout-score --only tidy` 给出逐器件归因，
  先整体打分、用户点名再 `--part <designator>` 聚焦。
- 移动/整理已有连线用带连接的工具（`sch group-move`、`pcb.components.move`
  带 wire/marker），单独只动器件的 align/modify 不能视为带线移动。

**PCB 叠层与电源（四层默认）**：

- 默认：`Top(信号+局部铺铜) / Inner1=GND PLANE / Inner2=PWR(信号层铺铜或 PLANE) /
  Bottom(信号+局部铺铜)`。单一主电源域时 VCC 走 PLANE（对标官方 N8R8）；≥2 个
  不共享电源域且锁 4 层时 VCC 留 SIGNAL 分区铺铜。
- **PLANE 生成顺序（顺序不能反）**：先在信号层铺该网（`pcb pour`）→
  `pcb stackup set --plane 15` 翻内电层 → `pcb pour-rebuild`；先翻类型再铺铜
  会掉到 L1 且 netless。`pcb power-planes` 自动完成整套（`--gnd-plane` 默认开）。
- via 先于铺铜：`power-planes` 逐 pad 打缝合过孔到内层，再铺铜、翻类型、rebuild。
- 新鲜板陷阱：当前会话新建且未 reload 的 PCB 按创建时规则快照 reflow；
  `doc reload` 后 `pcb pour-rebuild` 才按 live 规则生效。

### 4.3 射频（RF）

- **全层 keepout（guardrail，非决策）**：天线/ESP WROOM/WROVER/`ANT*` 在**每一层**
  （含内电层 `no-inner-electrical`）有 no-copper 区域；`pcb check` 的
  `antenna-keepout` 规则强制，命名缺失层。keepout 半径按 datasheet（一般 ≥5mm），
  净空区不压铜不走过孔。
- **阻抗匹配**：单端 50Ω / 差分 100Ω（USB）；微带/带状线宽度按板叠仿真计算，
  不套默认线宽；`pcb report` 量差分 skew（|lenP−lenN|）与等长组 spread。
- **布局**：RF 路径最短化——匹配+馈电在 λ/4（2.4GHz ≈12mm）内完成；馈线距 λ/10
  （≈200 mil）内完成匹配；RF 地缝合过孔间距 ≤λ/20；RF 簇贴板边（天线/馈线
  最短出板）；RF 与数字/电源分区 ≥200 mil；开关节点/晶振离模拟件 ≥250 mil。
- **巴伦/耦合器**：CC1101 类巴伦镜像布局（块约束 `balun-mirror`）；差分转单端
  阻抗变换网络贴 RF IC 端；做 PCB 前 `easyeda blocks show <id>` 把
  `severity=must` 的块约束抄进对应阶段。
- **ESD**：射频口串低容 ESD（<1pF，SOD-923 类）贴天线端，接地就近；USB D± 加
  22R 串阻 + 共模扼流圈（SDMM0806H-2-900T）抗扰。

### 4.4 模拟电路

- **接地**：默认单一完整地平面 + 按摆位分区，**不默认割地**；仅当设计显式存在
  ≥2 个地网络（AGND/DGND/PGND）时拆域：全 SIGNAL + 逐层分区 pour + region 划界 +
  0402 单点桥地（GND 缝合 via 可占总 via 量 1/2~2/3）。
- **电源子域**：模拟轨经磁珠/RC 滤出，命名前缀式（`AU_3V3`/`ADC_3V3`/`CODEC_3V3`）；
  安静负载在公共节点处星形分支引出，不落在噪声负载下游同段铜上。
- **去耦**：运放/ADC 每电源脚 0.1µF + bulk；高速/RF/ADC 电源 pin SHOULD ≤30 raw。
- **敏感输入**：不跨数字地平面，远离开关 FET/晶振/功率电感 ≥300–500 mil；
  桥接两域的混合信号 IC（ADC/DAC/codec）跨在边界上，模拟侧 pin 朝模拟簇。
- **小信号**：热电偶/应变片用同材质焊料、冷端补偿；屏蔽线缆入板先接 GND；
  sense/精密电阻拉出任何热半径（自热让阻值漂移）。

### 4.5 数字电路

- **晶振**：贴 MCU 振荡 pin 同层，体中心距 ≤300 mil（理想）/ 绝不 >500 mil；
  两负载电容 150–200 mil、对称（两腿差 ≤50 mil）、夹在晶振与 MCU 之间；
  晶振+两 cap 子簇外扩 200 mil 守护 keep-out，只此三件可入环；放在 MCU 朝
  开阔/板边的那个象限；晶振下方禁走线。
- **未用脚**：显式上/下拉或 NC，不悬空；开漏总线（I2C）上拉靠主控端。
- **复位**：RC 延时按 τ=RC 覆盖 Vth；低有效命名 `nRESET`；ESD/闩锁保护在入口。
- **隔离**：光耦/数字隔离器跨隔离屏障，两侧电源独立，爬电/间隙按 P1；
  隔离器件本体跨在屏障线上，两侧 keep-out 不被对侧电位元件侵入。
- **电平匹配**：不同电压域接口用电平转换 IC（N 通道双 MOS 或专用 IC），
  不跨压直连；I2C 域隔离用 2N7002DW 双向转换（NXP AN10441 类）。
- **命名即信道**：net 名 + 线宽 + designator 是原理图传给 PCB 的唯一信道；
  差分/等长/隔离网必须成对成组命名（`pcb diff-pair` / `pcb eq-group` 约束对象），
  布线前声明、布线后 `pcb report` 量 skew/spread。

### 4.6 滤波器

- **无源 LC**：L ±20%、C ±5–10% 公差决定实际 fc 偏差；RF 匹配用 C0G（温度稳定）；
  2.4GHz 天线 π 匹配（C-L-C）串联 L 代表值 2.7nH（LQG15HS2N7S02D），按实测调谐。
- **有源**：运放供电去耦齐全（每电源脚 0.1µF）；反馈电阻贴输出端；
  阶数与增益-带宽积匹配；高通/低通阶数按应用选择，元件值按目标 fc 计算。
- **数字接口**：USB 共模扼流圈串 D± + 22R 串阻 + ESD 阵列（USBLC6-2SC6，
  通道引脚 1/6=通道1、3/4=通道2、2=GND、5=VBUS）贴连接器端；RS-485 A/B 脚
  丝印警示方向（块 `silk.note`）。

### 4.7 电源设计

- **Buck**：输入回路（高 di/dt）= Cin + 高边 + 低边/续流，**不含电感**（电感
  电流连续，低 di/dt）：Cin（陶瓷）紧贴 VIN/GND ≤150 mil 同层；SW/LX 节点
  是高 dV/dt 侵略者——铜面最小化、敏感件躲开（≥200 mil）；反馈网络贴 FB pin。
  热回路合并 bbox 压到最小。
- **LDO**：入/出各 0.1µF + 10µF bulk（入口 500 mil 内）；热耗
  `(Vin−Vout)×Iout`，SOT-223 限约 0.5–1W，超则换 buck 或加散热；
  电解远离 LDO ≥200 mil（寿命每 +10℃ 减半）。
- **电流线宽（1oz 外层）**：0.15mm≈0.5A、0.25mm≈0.9A、0.5mm≈1.5A；内层 ×0.6–0.7。
  按 net-class 分级：signal 取 live 规则默认；power-branch（3V3/1V8）0.25mm；
  power-trunk（+5V）0.4mm；high-current（VBUS/VIN）0.5mm；公制圆整 0.05mm 步进。
  `pcb check width-under-spec` 门禁欠宽电源轨。
- **电源树**：外部输入 → 防反接（P-MOS/肖特基）→ 主 buck/LDO → 各子系统；
  每轨入口 bulk + 每 IC 本地去耦；多电源轨不短接同一平面；两个电源网别共享
  同一内层（复现 2 层 pour 冲突，互相把对方 pad 切成孤岛），各给独立内层需 6+ 层。
- **两层电源**：`pcb power-pour`——GND 板框贴合铺铜（默认双面），每个非 GND
  轨局部 pour（限定本轨 pad bbox + margin，顶面）；动态 pour 而非 fill。
- **铺铜禁忌**：天线/RF 下方各层禁铜；晶振底部禁铺铜穿越；差分对之间不铺铜；
  netless pour（无网络死铜）用 `pcb pour-clean --netless` 清理。

### 4.8 电气规范（行业标准）

| 标准 | 适用范围 | 关键要求 |
|---|---|---|
| IPC-2221B | PCB 通用设计 | 分层设计流程、规则化 DRC 阈值 |
| IPC-7351B | 焊盘/封装 | courtyard、SMD 最小间距 0.2mm |
| IPC-A-600 | PCB 可接受性 | 短路/断路/分层/铜剥离缺陷判据 |
| JEDEC J-STD-001 | 波峰/回流焊 | 焊接工艺参数 |
| IEC 62368-1 | 音视频/信息技术安全 | 爬电/电气间隙、隔离屏障、能量分级 |
| UL 94 V-0 | 板材阻燃 | 消费电子默认等级 |
| RoHS / REACH | 环保 | Pb/Hg/Cd/Cr6/卤素限量 |
| FCC Part 15 / CE EMC | 电磁兼容 | 辐射/传导限值、屏蔽与滤波设计 |
| JLCPCB 工艺能力 | 制造 | `fab-rules-jlcpcb.json` 基线（双层 clear 6 / width 10 / via 0.3–0.6mm） |

> 门禁数值运行时正本在 Go 代码（`pcb_rules.go` / `pcb_netclass.go` /
> `pcb_check*.go`）；本表为人读判据，冲突时以代码 + JLC 官网为准，并回改文档对齐。

### 4.9 电子电路设计经验（经验法则）

- 板面积估算：`Σ主器件 bbox + 辅助件 × 80×80 + 余量`；>80 件考虑多页或双面。
- 5τ 达稳态 99.3%；RC 复位/滤波按功能需要选值。
- 换层必打地孔（回流连续）；高速信号不跨分割/开槽/板边（距板框 ≥80–100 mil）。
- 差分对等长 ±5 mil、全程紧耦合、换层两信号孔+两地孔紧邻。
- 电解/钽电容离热源 ≥200 mil 放上游冷侧；>0.5W 器件四周 ≥500 mil 开阔铜散热。
- TVS 钳位电压 < 后级耐压 -20% 裕量；ESD 器件贴连接器端。
- 手焊封装下限 0603（0402 是噩梦）；回流焊可用 0402/QFN。
- 立碑代理检测：两 pad 一接平面 PWR/GND、一接信号 → advisory 风险。
- 测试点集中同一探测面（优先底面）、pad ≥40 mil、中心距 ≥100 mil；
  关键 net 与电源轨无 TP = DFT 覆盖提示。

### 4.10 数据手册 / PDF 阅读经验

1. **锁定身份**：厂商、完整 MPN、LCSC C 号与封装四件套；先读目录/概述定型号。
2. **电气参数表**抄条件不只抄值（Vin/Tj/负载/测试电路），保留来源 URL 与页码。
3. **典型应用电路**是外围设计基准；块库 `source`/`note` 是已验证摘要，
   不能替代型号手册；不凭外观或记忆补接线。
4. **单位换算另列**：`mΩ`=毫欧、`MΩ`=兆欧；SI 前缀大小写敏感；
   330mΩ=0.33Ω 与 33Ω 相差 100 倍。不从料号数字猜阻值，不跨系列混用
   小数点记法；只有读到该厂商该系列该编码位置的规则才解释 MPN。
5. **冲突处理**：目录/手册/库 value 不一致时记录冲突并继续查证；来源不可读
   或参数缺失标"未核实"，不填猜测值、不写回标准库、不据此完成选型/改电路。
6. **版本不匹配**（旧手册 vs 新器件）时重新核对器件身份，不沿用旧典型电路；
   同 MPN 多版本手册取最新版。
7. **曲线图**取工作点（电流/频率）对应值，不取峰值；封装图核对 courtyard
   与焊盘偏移。
8. **不靠截图推断**：未知引脚或网先导出 `sch connectivity`；PDF 参数必须读到
   原文，不靠目测图形。

---

## 5. 核心 API 操作（typed action 速查）

> 参数真值以 `easyeda <command> --help` 与 `easyeda actions` 为准；未知官方接口
> 先 `easyeda api search <query>`。typed action 已有对应能力时优先使用；
> 无对应能力且用户接受调试路径时才用 `debug.exec_js`（输出须可 JSON 序列化）。

### 5.1 原理图 1.4 数据路径

主线：**本地 Connectivity IR → Lib 局部几何 → compose → sch apply → 回读对账**。

| 目的 | CLI / action | 边界 |
|---|---|---|
| 读取连接图 | `sch connectivity [--page <p> \| --all-pages]` | 跨页逐页激活读取；浅层引脚不能用空 pins 证明无引脚 |
| 连接差异 | `sch connectivity-diff before.json after.json` | 拓扑/NC 对账，不代替库身份与几何 |
| 设计版本差异 | `sch design-diff expected.json actual.json --exit-code` | 查 `coverage.unverified`；退出码 2=不同、3=目标不符/证据不完整 |
| 框/标题差异 Apply | `sch design-diff before-plan.json after-plan.json --before fresh.json --playbook frame-diff-apply.json` | 两份完整 compose 计划 + 新鲜快照；只改有变化框 |
| Lib 内部几何 | `sch lib-layout --from layout-input.json --out composition.json` | 纯离线；有界求解器，失败不证明任意朝向无解 |
| 完整 Lib 图面 | `sch compose --from composition.json --out plan.json [--before … --replace --playbook …]` | 消费已设计模块几何；Z 字排版；不自动补电路/旋转/缩放/分页 |
| 基础放置 | `sch materialize <connectivity.json>` | 放件队列，不是完整布局/布线器 |
| 标记增量 | `sch plan before.json after.json` | 仅 power/ground/net_port 连接；NC→连接先清 NC 核对中间态再连 |
| 位号修复 | `sch designators allocate` → `plan` → `verify` → `sch apply` | 按官方库前缀分配；只改非标准项，跳过已占用编号 |
| 框与标题 | `sch frame apply/check --from frames.json` | 只操作自己登记的图元；check 按实际文本 bbox 验证 |
| 执行队列 | `sch apply <plan.json> [--dry-run \| --yes]` | 保护队列禁止 `--resume/--from/--to` 跳步；失败重新回读生成 |

Apply 队列（playbook）契约：`version:1` + `meta` + 有序 `steps`；每步
`action+payload`（typed）或 `run+flags`（Cobra）或 `notify`；`capture` 捕获
新实例 ID 供后续 `${part}` 引用；`assert` 路径相对 result；默认失败即停。
生成器（compose/designators/plan）产出的保护计划失败后只能重新读取当前图、
修正输入、完整重编译执行；已生效步骤保留在画布与 journal。

### 5.2 连线（pin-aware autoconnect）

`sch autoconnect` 拉真实几何（bbox/pin/既有 flag/port/title-block），对每个
`方向 × offset` 候选做确定性代价评分，选最低委托 `connect_pin`：

```bash
easyeda sch autoconnect --pin U1:41 --kind gnd --net GND
easyeda sch autoconnect --pin J1:VBUS* --kind power --net 5V   # 同名多脚全接
easyeda sch autoconnect --spec p1-connect.json                  # 批次
easyeda sch autoconnect --spec p1-connect.json --dry-run --json # 预览不改
```

行为要点：

- **幂等**：已连目标网的脚跳过；`--replace` 删旧 flag+wire 再连（成对删，无孤儿桩）。
- **硬拒（#64/#147）**：短桩触碰异网线 / 跨越非目标引脚 / 落入图签 keep-out
  → 候选不可用，四向全堵时响亮报 no safe candidate，拒绝落笔。
- **密集区**：候选扩到 3×offsetMax；看到的长桩是错开标签的结果，不是失控。
- **带痕候选**：score 超软阈值标 `⚠ WARN`；`--strict` 直接判失败。
- **35s 专用预算**：超时/DISPATCH_FAILED 自动轻读复核，`slowLanded` 成功返回
  且勿重试；状态未知失败绝不盲重试（可能已建成）。
- 批次后必跑 `sch check`（`duplicate-net-marker` 规则兜叠加 marker）。
- `sch connect` 不幂等，重发可能叠加导线和标记；`sch disconnect` 检查
  `alsoDisconnectedPins[]`，逐个恢复；`partial`/`survivedIds`/`notApplied`
  表示删除未完全生效。

### 5.3 PCB 基础上下文

| 命令 | 用途 |
|---|---|
| `pcb board-info` | Board（SCH+PCB 绑定）前提；`import-changes` 沿此链接 |
| `pcb components.list --include-bbox --include-pads` | 位置/尺寸/层/焊盘网络 + 真实铜宽 |
| `pcb layers.list` | `copperLayerCount`（2 vs 4+ 层判定，去耦规则开关） |
| `pcb nets.list` | 网络全集（net 名/长度/颜色） |
| `pcb report` | 逐 net 铜长、差分 skew、等长组 spread（纯读） |
| `pcb check` | Go 侧重建 DFM 审计（dangling-end/acute-angle/silkscreen-flipped/antenna-keepout/…） |
| `pcb drc --json` | 原生规则 DRC；前台窗口执行，超时装前景跑一次不循环重试 |
| `pcb drc-rules` | 读 live 规则（clearance/trackWidth/via 尺寸） |
| `pcb net-classes` | net-class → 规范线宽阶梯（角色分档） |

### 5.4 PCB 布线与铺铜

- 增量创建：`pcb.line.create`（导线，默认 6 mil）、`pcb.via.create`（过孔，
  默认 12/24 mil）；`create()` 宽松返回，每步验证 primitive 返回。
- `pcb.route.rip_up` 按网 rip-up（含 arc/via，保护板框/丝印/锁定图元）；
  `pcb clear` 一键整版复位（默认保留锁定+板框，自带 verify 复合流程）。
- `pcb via-delete`/`track-delete` 按 primitiveId 精删（CSV 或 JSON 数组）；
  嵌入焊盘的 via 前置拒绝（reload 后 re-materialize netless，用 `pcb via-bond` 合流）。
- `pcb via-hop` 复合换层：入口桩→via→换层轨→via→出口桩；via 在端点外 20 mil
  不坐 pad；track↔via 自身注册连接（不需要 bond fill）；同网 Connection Error
  是 stale pour 连通性——先 `pcb pour-rebuild` 再判。
- 铺铜：`pcb.pour.create`（net 必绑，netless pour 是死铜）；`pour-fit` 自动
  贴板框；`pour-clean --netless`；`pour-rebuild` 重流。
- 禁布区：`pcb region create --ref U1 --margin 40 --rule no-pours`（默认
  no-components/no-wires/no-pours 硬 keepout）；天线 keepout 全层。
- 填充：`pcb fill create`（静态异形铜，net 绑定；`--rect` 是两对角点不是 x,y,w,h；
  面积 > 板框 25% 防呆拒绝）；MULTI 层 fill = 板挖槽（`pcb slot`）。
- `pcb beautify` 圆角化走线（DRC 二分重试 + pour-rebuild 内置；先 `--dry-run`；
  密集板按 `--net` 小范围处理）。

### 5.5 原理图 ↔ PCB 同步

- `pcb import-changes` 从原理图同步器件/网表（自动点"应用修改"对话框，报
  before/after 计数差；`InvalidatesStage:placement_confirmed`，别为刷飞线跑它）。
- `pcb sync-designators`：按 `uniqueId`（平台首次导入铸造，跨文档同一命名空间）
  回填占位位号 `U?/C?`，只动占位符，每笔回读验证。
- `pcb sync-attrs`：器件库记录回填 PCB 属性空值（平台投影键绝不参与 merge）。
- `pcb add-component`：逐件放置 + 焊盘赋网（`--nets` padNumber→net map）+
  嵌入 via 合流；工作流 = 原理图放件接线 → `sch read` 取 net/uniqueId →
  PCB 侧放置赋网 → `pcb list --include-pads` + `pcb drc` 验证。

### 5.6 器件库与选型

- 选型顺序：先 `easyeda blocks search <keyword>` 查可复用电路块（命中后块的
  `parts` map 直接给 standard-parts role）→ `standard-parts.json` 本地库
  （确定性、已真板验证）→ `lib by-lcsc --lcsc C…` 精确解析 → `parts-select.py`
  在线比价（opt-in，显式 `--online`）。
- 排名五档：Resistance gate（阻值等式，SI 前缀大小写）→ Buildable
  （stockCount ≥ qty）→ Basic（免 feeder 费）→ Preferred → 单价。
- `parts-add.py` 把新选型写回 `standard-parts.json`；`bom-enrich.py` 把 C 号
  补进 BOM 导出的 "Supplier Part" 列。
- `sch replace --id <pid> --lcsc <C#>` 一键换件（保 designator/uniqueId/pose，
  报 `pinDiff`，非空须重连后 `sch check`）。
- 自建资产走 `lib device build`（Symbol/Footprint/3D/Device）；Footprint JSON
  单位 mil；库 API 有 beta 能力——结果不明先 get 再决定，不重复 create。

### 5.7 验证门禁

- 原理图逐页 `sch gate --strict --doc <page>`：`layout-lint → check →
  bridge-check → SDK DRC`；`pass` 才通过，`fail` 是设计问题，`blocked` 是
  检查未完成（先修环境）。`--strict` 把间距、孤儿桩等告警也列为阻塞。
- `sch check --json` 问题在 `result.findings`；SDK DRC 可能只返回聚合值，
  不能单凭它宣称官方 UI 所有警告已清除。
- PCB `layout-lint --gate`（装配感知：手焊间距地板 + solder-access + 分数/
  交叉数门）落 `pre_route_passed`；`layout-score` 九维诊断
  （partition/flow-order/edge-io/protection/tidy/compact/rf/routable/clearance）
  是质量表不是硬门——skipped/degraded 维不参与加权；短路/重叠/出板框进
  `blocking[]` 一票否决。
- 官方导图：`sch export-image`（文档渲染，不依赖视口刷新）；PCB 截图
  `pcb snapshot` 可能 stale（`--previous-sha256` 检测同帧）——数据校验
  （list/drc/check）是权威，截图只做视觉终检。
- 保存：通过阶段验证后显式 `sch save` / `pcb save` 并确认 `saved:true`；
  daemon 防抖 autosave 只是兜底。
- 视觉质量聚合：`scripts/visual-qa.py`（§8.3）聚合截图 + 上述数据源
  做三关注域（组件间距/走线间距/整齐度）交叉评估，是"呈现层"自动化，
  不替代数据层硬门。

---

## 6. 设计决策目录（S0 摊给用户拍板）

判据：**用户的回答会不会改变实际做法**——会才进本目录；只有唯一正确答案的
是 guardrail，内置在硬门里（save 纪律、mutation 后 reload、PLANE 生成顺序、
天线 keepout 全层等），不在此重复。

| 决策点 | 选项对比要点 | 推荐默认 |
|---|---|---|
| 2 层 vs 4+ 层 | 2 层多网同层铺铜互相挖岛（残留 No-Connection 修不了）；4+ 层每电源/地网专属内层 via-stitch 后铺铜可清零 | 4 层（≥2 电源/地网络即选） |
| VCC 内层 PLANE vs SIGNAL 分区 | PLANE 对称制造规范但一个层只能一个网络；多电源域锁 4 层时 SIGNAL 分区 pour | 单一主电源域走 PLANE（N8R8） |
| 地域数量 | 单 GND → 双 PLANE 最干净；≥2 地域负片无法分域 → 全 SIGNAL 分区 pour + 单点桥地 | 单 GND；显式多地才拆 |
| 线宽分级 | 全板统一 → 电源网细线是 DRC 违规大头；按角色分级（信号 6 / 支线 9.8 / 主干 15.7 / 大电流 19.7 mil 公制圆整） | 分级 |
| USB-C 单取向 vs 双取向 tie | 双取向 A6+B6/A7+B7 同接 D±（官方 N8R8，正反插通）；单取向省 B6/B7 是布线不足权宜 | 双取向 tie |
| USB 架构 | 单通道 CH340 桥（最简单）；HUB 双通道（原生 USB+串口并存）；纯原生 USB 无桥（S3/C3 SiP，省桥+省自动下载管） | 按芯片与产品形态 |
| 自动下载 | 物理键（最省）；DTR/RTS 双管（串桥产品标准做法）；原生 USB 软复位（免管） | 原生 USB 免管；串桥加双管 |
| 选型档位 | 固定 standard-parts（可复现、已验证）vs 动态比价（实时库存/价格）；basic 免 feeder 但覆盖窄；按目标量产 qty 选型防二次换料 | 常见件固定表 + 异常才比价 |
| 单面 vs 双面 | 双面省 20–40% 板面积但贴片贵/翻板调试麻烦 | 紧凑诉求强时双面 |
| 焊接工艺 | 手焊封装下限 0603；产线贴片 0402/QFN 随便用 | 原型手焊选封装，量产贴片 |

---

## 7. 项目文档任务

> 项目级文档任务，不触发版本门禁升级，但仍需 `easyeda health` 确认工程上下文
> （涉及 EDA 数据读取时）；纯本地文件任务可离线执行。

### 7.1 创建许可证（Create License）

- 生成 `LICENSE` / `LICENSE.txt`；默认 **MIT**（与 skill 本身体一致）；
  用户指定时支持 Apache-2.0、GPL-3.0、BSD-3-Clause、CC0。
- 已有 LICENSE 不覆盖，先回读确认；版权年份与主体由用户提供，不猜测。
- 生成后建议同步 `AGENTS.md` 或 README 的许可证声明段；
  提交信息注明 `generate-license`。

### 7.2 生成 README.md

- 内容只来自当前工程回读：概述、BOM 摘要（`bom-enrich.py` 产物）、
  S0–S6/P0–P10 阶段当前门状态、导出路径（gerber/BOM/placement）、许可证引用。
- 已有 README 追加/更新章节，不全量重写；破坏性改写须用户确认。
- `blocked`/`fail` 的门如实标注，不写成通过；图片引用须先 `sch export-image`
  导出官方导图，不用原生视口截图。
- 提交信息注明 `generate-readme`。

### 7.3 块贡献（提交已验证电路到块库）

- 先 `easyeda blocks search` 查重，`blocks show <id>` 读完整 JSON；
  `blocks ls --json` 只有摘要投影，不含全部连接数据。
- 贡献合同：`id/desc/category/source/author`（来源用具体型号手册或官方参考）；
  `parts`（role 表，`part` 指向 standard-parts key）；`internal_nets`
  （≥2 个 ROLE.PIN 引用，同脚只属一网）；`ports`（边界 in/out/bidir）；
  可选 `schematic_layout`（关系形式优先：anchor/flow/attach/pair/orient）/
  `pcb_layout`/`signals`/`silk`/`keepout`。
- 同名多脚全并联写 `J.VBUS*`，不省略后缀让工具猜；引脚引用优先功能名，
  同名脚用真实引脚号。
- 验证：`go test ./internal/blocks/` + `make blocks-audit`；安装态
  `python3 scripts/blocks-pin-audit.py`（离线，无源码时从 CLI 内嵌库逐项取模板）；
  `--probe` 模式清专用空白测量页、放件读脚再清页（须已获准清空该页）。
- `verification` 四项（schematic/component_selection/pcb_drc/bringup）均
  `passed` 且有证据才能设 `production_ready:true`；草稿可贡献但不能声称
  生产验证。

### 7.4 生成 PCB 布局蓝图（Markdown + 字符画边框）

> 在**物理放置/绘制 PCB 之前**，先生成一份 Markdown 布局蓝图，用模块、组件、
> 部件及它们之间的连接把整板布局可视化；板框外形用**字符画（ASCII 边框）**
> 表达。蓝图是规划/评审工件（pre-placement planning artifact），不直接产生
> EDA 图元；须经 P3 中断点（§11.5）用户确认，再驱动 `pcb import-changes`
> 与四档放置（§4.2、§5.5、§5.7）。

**何时生成**：
- 新设计需求→整板：P2（放置）之前生成，作为 P3 板框签核的评审材料。
- 改版/复用布局：重新生成做 before/after 对照（`sch design-diff` 同源）。
- 蓝图是"会改变做法"的选项载体（§6、§11.2）；已在 P3 板框/分区处摊给用户
  拍板，不重复索取许可（§11.4）。

**文件契约**（`<工程>-pcb-layout.md`）：
1. **板框字符画**：用 box-drawing 字符画出板框外形与圆角，标注长宽（mm）、
   安装孔、板边接口开口方向。字符约定：
   - 外框：`╭╮╯╰ ├ ─`（Unicode box）或纯 ASCII `+ - |`；四角圆角用 `╭╮╰╯`。
   - 模块分区：`[模块名]` 或 `+------+` 小框；keepout 区斜线阴影 `////`。
   - 器件：`ref` 缩略（`U1`/`J1`/`C1..C8`/`ANT1`）。
   - 比例尺：声明 1 字符 ≈ N mm（横/纵可不同，按板框长宽取整）。
2. **模块清单**：按 §4.2 九宫格分区（电源左列 / MCU 中列 / RF·IO 右列）
   列出每个功能 Lib 的 bbox、贴边（10 mil）、标题净距。
3. **组件/部件清单**：四档 T1（安装孔）→ T2（板边接口）→ T3（主芯片）→
   T4（卫星件）；每件含 `ref`/`role`/layer(TOP·BOTTOM)/朝向/间距约束（§4.2）。
4. **连接关系**：模块间 / 跨模块 netport 的边集合（net 名 + 起讫器件 +
   线宽档位 + 是否差分/等长/RF）；差分/等长/隔离网成对成组命名（§4.5）。
5. **决策头**：§6 已拍板的 S0 决策（叠层/地域/单双面/焊接工艺）+ 未决项
   （交 §11.5 中断点）。

**字符画示例**（示意；比例尺 1 字符 ≈ 1 mm，板框 40×30 mm）：

```text
╭────────────────────────────────────────╮
│ ┌──────┐   ┌─────────────┐  ┌──────┐ │  顶边 J1(USB) 开口朝上
│ │ PWR  │   │    MCU      │  │ RF   │ │
│ │ U1L1 │   │ U1 Y1 X1 X2 │  │ ANT1 │ │
│ │ C1.. │   │  (ESP32)    │  │ L2C5 │ │
│ └──────┘   └─────────────┘  └─////─┘ │  RF 全层 keepout(////)
│ [电源]    [数字/控制]   [射频]        │
│ ┌──────┐   ┌─────────────┐  ┌──────┐ │  底边 J2 开口朝下
│ │ J1   │   │ 接口/IO TP  │  │ J2   │ │
│ └──────┘   └─────────────┘  └──────┘ │
╰────────────────────────────────────────╯
  40 mm · 安装孔(四角) · 1 字符≈1 mm
```

**生成数据来源**（先读后画，不盲写）：
- `sch connectivity --all-pages`（§5.1）→ 模块/组件/连接真值。
- `pcb list --include-bbox` + `pcb sheet-geometry` → 板框尺寸与分区几何。
- `sch design-diff` / `sch connectivity-diff` → 新旧蓝图 before/after 对照。
- 比例尺/贴边取 §4.2 固定值（贴边 10 mil、标题净距 5 raw）；缺实测
  `sheetBorder` 时注明边界回退（§4.2、§5.1 `sch sheet-geometry`）。

**约束与边界**：
- 蓝图是**规划层**工件（§8.1 验证分层中不属任何硬门）；生成后**不直接**
  驱动写图元——物理放置仍走 `pcb import-changes` + 四档放置 +
  `layout-lint --gate`（§4.2、§5.5、§5.7）。
- 字符画是**示意**；坐标精确值以 `pcb list --include-bbox` 的 `center`
  为准（§3 锚点 vs bbox 中心），字符画不替代 `layout-score`/`pcb check`。
- 连接关系须与 `sch connectivity` pin→net 对账一致；不凭空补连接
  （§4.2 短桩、§4.10 不靠截图推断）。
- 已有蓝图文件追加/更新章节，不全量重写；破坏性改写须用户确认
  （同 §7.2 README 纪律）。提交信息注明 `generate-pcb-layout`。

**与 §11.5 中断点的关系**：蓝图生成完即触发 **P3（板框与安装孔方案）
强制中断点**——把字符画板框 + 分区 + 关键连接摊给用户拍板（单双面/
手焊回流/板框尺寸）；用户批准蓝图后才执行 P2–P10 物理放置。

---

## 8. 验证与交付

### 8.1 验证分层（不能互替）

| 层 | 工具 | 证明什么 | 不证明什么 |
|---|---|---|---|
| 拓扑 | `sch design-diff` / `connectivity-diff` | 器件/pin→net/NC 一致 | 几何、导线、框（未导出字段列 unverified） |
| 几何 | `layout-lint` / `pcb layout-score` | 无重叠/出框/间距/可布性 | 电气正确性 |
| 电气 | `sch gate --strict` / `pcb drc` / `pcb check` | DRC/DFM 门禁 | 设计意图 |
| 呈现 | `sch export-image` / `pcb snapshot` | 文字/可读性视觉终检 | 数据正确性（截图可能 stale） |
| 保存 | `sch save` / `pcb save` → `saved:true` | 落盘 | 内存中的未保存修改 |

- 官方 DRC 可能只返回聚合数；INFO/WARN 单列，不能把"0 fatal"称全部通过。
- 数据完整与绘图成功不代表电气设计合格；悬空脚仍保留电气警告。
- `layout-score` 的 `skipped/degraded` 是诊断（没测 ≠ 满分），硬门
  （short/overlap/off-board）一票否决。

### 8.2 交付报告

说明修改范围、源数据与实际图面差异、各验证层结果、已保存页面、
尚未解决的问题与未运行检查。保留输入、生成队列、回读与验证报告；
局部完成不称整板通过。

### 8.3 视觉质量与布局完整性自动评估（`scripts/visual-qa.py`）

> 用 API 截图 + 数据驱动检查**交叉**评估视觉质量，聚焦组件间距、
> 走线间距、整体整齐度。是 §8.1 "呈现层"的自动化实现，但**不替代**
> 数据层（拓扑/几何/电气/保存）。

**设计原则**（与 §5.7 / §8.1 一致）：

- 呈现层不可互替，但**数据校验是权威**——截图只做视觉终检。
  截图与数据不一致时以数据为准，但必须把"图面 stale"标为阻断项。
- PCB `snapshot` 可能 stale：用 `--previous-sha256` 检测同帧；
  `sch export-image` 是文档渲染（不依赖视口刷新），无需 sha 检测。
- `layout-score` 九维是诊断**不是硬门**；skipped/degraded 维不参与
  加权（"没测 ≠ 满分"）；短路/重叠/出框进 `blocking[]` 一票否决。

**三关注域 → 数据真值映射**：

| 关注域 | layout-score 维度 | pcb check 规则 | drc 规则 |
|---|---|---|---|
| 组件间距 component_spacing | compact, clearance | solder-access（gate） | clearance |
| 走线间距 trace_clearance | routable, clearance | acute-angle, dangling-end | clearance, trackWidth |
| 整体整齐度 layout_neatness | tidy, partition, flow-order | rotation-inconsistent（子规则） | — |

**用法**：

```bash
# PCB + 原理图双评估（需活体窗口或 daemon）
python3 scripts/visual-qa.py --project <name> --doc <page-uuid> --both

# 仅 PCB，strict（WARN 也判阻塞）
python3 scripts/visual-qa.py --project <name> --pcb --strict

# 跳过截图采集（只用已有数据打分；不触发 canvas-freeze）
python3 scripts/visual-qa.py --project <name> --pcb --no-snapshot
```

**输出**：JSON（stdout）+ 人读摘要（stderr）。退出码：
`0`=全通过（含截图非 stale）；`2`=有 WARN（低分维/带痕/stale 但数据通过）；
`3`=blocking（短路/重叠/出框/间距硬违规/stale 且数据也不全）。

**评估流程**（三层）：
1. **硬门**：`layout-score.blocking[]` 一票否决（短路/重叠/出框）。
2. **关注域**：逐域聚合维度状态（skipped/degraded/low-score<0.6）+
   DRC/check findings → pass/warn/fail。
3. **截图一致性**：stale/missing → 至少 warn（strict 且数据不全 → fail）。

**边界**：
- 该脚本**不替代** `sch gate --strict` / `pcb drc` / `pcb check`——
  它是这些数据源的聚合器 + 截图终检，不是新的硬门。
- 截图采集前的 `view fit` + 1.5s 等待是 canvas-freeze 缓解（§5.7），
  不是保证；stale 检测是最终防线。
- `--no-snapshot` 模式下只跑数据评估，不触发截图采集——适合
  CI/批量回归或已知截图 fresh 的场景。

---

## 9. 已知平台限制（承重的边界）

- `.SchDoc`/`.PcbDoc` 无程序化导入入口：Altium 工程走 EasyEDA GUI（文件→导入），
  导入后由 typed 命令核验；`importProjectByProjectFile` beta 接口实测静默
  返回 `undefined`，不能包装当成功。
- `eda.*` 无泪滴（teardrop）API——制造前在 UI 右键手动加。
- 交互式布线菜单（routing/stretch/optimize/length-tuning）无 `eda.*` API：
  程序化布线限于坐标创建 track/via/pour、rip-up、`route-short` 启发式档、
  官方文件交换 autoroute（`pcb export-dsn` 导出含 keepout，Freerouting 兜底）；
  稠密板默认交用户点 EasyEDA 原生"自动布线"（人机协作档）。
- `createNetLabel` 是 v4 BETA API，3.2.186 实测挂起——超时后回读实际连通与
  残留图元，按电气语义选受支持的 netport/netflag，不盲重试。
- `getCurrentRenderedAreaImage` 后台标签可能返回缓存旧帧；`pcb snapshot`
  用 `--previous-sha256` 检测同帧，stale 时切前台重取。
- `page.rename` 后立即 `doc ls` 读旧名（平台元数据缓存延迟）——看返回值
  `verified` 字段，不是紧接着 doc ls。
- 3D 模型导入请求体上限 32 MiB（含 base64 膨胀，原始模型 < ~24 MiB）。
- `sch_Netlist.getNetlist()` 已废弃且可能挂起——网表用
  `sch_ManufactureData.getNetlistFile()`。

---

## 10. 执行纪律（汇总）

1. 版本门禁先行（§1.2）；升级后新会话。
2. 写前读新鲜快照；保护队列不跳步；写入超时先回读不盲重试。
3. 非零导线连接；y-UP；5 raw 网格（原理图）；坐标重合不算连接。
4. 保留 NC 与物理引脚；缺数据不自动填 NC/悬空。
5. 已有用户授权持续有效，不重复索取；新的破坏性范围才需澄清。
6. 门禁失败区分"检查没运行"（blocked）与"设计不合格"（fail），
   不靠关闭检查取得通过。
7. PCB mutation 后 `doc reload`；铜形变化后 `pour-rebuild`。
8. 显式 save 并确认 `saved:true`；autosave 只是兜底。
9. MCP 与 CLI 双链路语义一致；MCP 不豁免任何验证、不改变授权范围。
10. 报告覆盖未验证项；不把 canonical 一致当作实际图面已同步。
11. 强制/条件中断点（§11.5）命中时暂停等待用户确认，不自动推进；
    超时/无答复保持暂停态，不猜默认值落笔。

---

## 11. 用户需求澄清与目标明确（动手前）

> 原则（与 `Sample/easyeda-agent/references/design-flow.md` S0 一致）：**缺信息会改变设计、或超出已有授权时
> 才问**；已有确认的需求与授权沿用，不因流程表重复索取许可；用户要求逐步
> 确认时遵守其节奏。问的是"会改变做法的选项"，不是"流程打卡"。

### 11.1 任务分类与默认行为

| 任务类型 | 默认行为 | 需要澄清的信号 |
|---|---|---|
| 已有图小修复（位号/连线/器件） | 沿用已确认需求与授权，直接读现场快照动手 | 修复范围超出"小修"（改拓扑/换架构） |
| 原理图整理/排版 | 保留电气拓扑与 NC 意图，只动几何与呈现 | 用户要求重建电路、拆分/合并模块 |
| 新设计（需求→整板） | 走 S0–S6 全流程，S0 先摊决策点 | 供电/接口/机械约束/装配工艺缺失且影响设计 |
| PCB 布局布线 | 沿用 spec/已确认叠层与工艺 | 单双面、手焊/回流、板框尺寸、未决电气/机械要求 |

### 11.2 开工前必问清单（答案会改变做法才问）

- **目标与验收**：这次要交付到哪一步（原理图 / PCB 布局 / 布线 / 制造文件）？
  验收标准是什么（`sch gate --strict` pass？`pcb drc` 0 fatal？能下单？）。
- **批量与工艺**：原型手焊还是量产贴片？——直接改变封装下限（0603 vs 0402）
  与装配间距（`--assembly-gap`）。
- **机械约束**：板框尺寸/安装孔/连接器边序与开口方向？没有机械图时按
  "无尺寸路径"（粗布局后收紧 outline，§4.2）。
- **未决电气/机械要求**：电源轨清单与电流预算、隔离/爬电要求、RF 频段与
  天线形式——缺失且影响设计时澄清，不影响（有唯一正确答案）的内置 guardrail
  不重复问。

### 11.3 目标明确化方法

- 把模糊需求落成**可验证的目标不变量**：pin→net 黄金表（连对与否）、
  位号清单、关键网长度/skew 预算、板框 bbox、DRC 目标（0 fatal + WARN 清单）。
  验收时逐项对照，不是"跑完命令就算完成"。
- 范围边界写进交付物：本次只动哪些模块/页面；"不动"的部分在报告里列明
  作为回归对照（`sch connectivity-diff` 只应出现预期差异）。
- 多页/多板工程先定归属：位号全工程不重复、网络跨页归属、源页处置步骤
  （没有跨页迁移事务，不能盲清其余页面）。
- 用户已授权的破坏性范围（如清页重建）持续有效，不重复索取；
  **新出现的**破坏性范围、未决电气/机械要求才需再澄清。

### 11.4 沟通与授权纪律

- 汇报用证据说话：回读数据（pin→net/几何/DRC 结果）+ 官方导图，
  不截图猜、不以单个 DRC 聚合数代替对账。
- 阻塞项与未运行检查如实列出（`blocked` ≠ `fail`，未评估 WARN 不能记通过）。
- 授权边界：`--yes` 只放行已授权范围；保护队列失败后重新生成，
  不用 `--resume/--from/--to` 扩大或跳步。

### 11.5 中断机制（执行中暂停与用户确认）

> §11.1–11.4 管"动手前"的澄清；本节管**执行中**的暂停。核心判据：
> **用户的选择会不会改变实际做法、或超出已有授权范围**——会才中断，
> 不会就不中断。已有确认与授权沿用，不因流程节点重复索取许可。
> 用户要求逐步确认时遵守其节奏（§11 原则）。

**两类中断点**：

| 类型 | 触发条件 | 行为 | 示例 |
|---|---|---|---|
| **强制中断（mandatory checkpoint）** | 该阶段决策不可单方面定，或后果不可逆 | 必须暂停，等用户明确答复后才继续 | S0 决策点（叠层/接地/USB 架构）；`compose --replace` 清页重建；破坏性 `pcb clear` |
| **条件中断（conditional checkpoint）** | 信息缺失会改变设计，或超出已授权范围 | 只在条件命中时中断；信息齐备或已授权则静默通过 | 选型缺数据手册参数；PCB 装配工艺未定；门禁 `blocked`（修环境需用户介入） |

**不中断的情况**（避免流程打卡）：
- 已确认的需求与授权（§11.3 目标不变量已锁定）。
- 有唯一正确答案的 guardrail（save 纪律、mutation 后 reload、PLANE 顺序、
  天线 keepout 全层）——这些是硬门，不需要用户拍板。
- 已授权范围内的增量执行（如已授权清页重建后逐模块 compose）。
- 纯读取与验证（connectivity / list / drc / export-image）。

**中断点触发协议**（统一格式）：

```
[CHECKPOINT <阶段> | <类型>]
背景：<当前状态与为什么要问，≤3 句，含证据（回读数据/DRC/快照）>
决策点：<要用户拍什么，列出选项与推荐默认>
  - 选项 A：<描述> → 后果：<对后续流程的影响>
  - 选项 B：<描述> → 后果：…
  ⚠ 推荐：<默认>（理由：…）
影响范围：<本次只动哪些模块/页面/网络；不动的部分列回归对照>
等待：用户回复 A/B 或自定；超时/无答复不自动推进，保持暂停态
```

**用户响应处理**：

| 用户回复 | 后续行为 |
|---|---|
| 选择某选项 | 记入授权（`confirmed_decisions[]`），沿用到后续阶段，不重复问 |
| 补充新信息 | 更新目标不变量（§11.3），重评估是否影响已执行步骤 |
| 要求中止 | 停止当前操作；已执行的写操作不回滚（无 undo），报告当前状态 + 已落盘步骤 |
| 超时/无答复 | **保持暂停态，不自动推进**；不猜默认值落笔（推荐默认仅供用户参考，不代表自动执行） |

**强制中断点清单**（S0–S6 / P0–P10 关键阶段）：

| 阶段 | 中断点 | 类型 | 触发条件 |
|---|---|---|---|
| S0 | 设计决策目录（§6）摊牌 | 强制 | 新设计必须先拍叠层/接地/USB/选型档位等 |
| S1 | 工程基线与纸张边界确认 | 条件 | 多页工程归属未定，或纸张 keep-out 推导有歧义 |
| S2 | 位号修复范围 | 条件 | `sch designators allocate` 要改的位号超出"非标准项"（如用户已有自定义位号） |
| S3 | Lib 几何与模块拆分 | 强制 | `compose` 前用户需确认模块划分与页数（功能拆页是设计决策） |
| S4 | `compose --replace` 清页 | 强制 | 清目标页是破坏性，须用户已授权重建范围 |
| S5 | 回读差异超出预期 | 条件 | `sch design-diff` 出现 `coverage.unverified` 或非预期 pin→net 差异 |
| P1 | PCB import-changes | 条件 | 原理图与 PCB 差异超出预期（器件数/网数变化大） |
| P3 | 板框与安装孔方案 | 强制 | 有机械约束时须用户确认 outline；无约束时按"无尺寸路径"但须告知板框尺寸 |
| P6 | 布线前门未通过 | 条件 | `layout-lint --gate` = `blocked`（需用户介入修环境）或 `fail`（需用户决定改布局还是放宽） |
| P8 | 电源铺铜策略 | 条件 | 多电源域（≥2 地网络）的铺铜/割地方案是 §6 决策点 |
| P10 | 终检 WARN 清单 | 条件 | DRC 有非 fatal WARN，须用户决定接受还是修复 |
| 交付 | 文档任务 | 条件 | 生成 LICENSE/README 须用户确认版权主体；README 内容须用户确认阶段门状态 |

**中断点与验证门禁的关系**：
- `blocked`（检查没运行/环境问题）→ 条件中断：需用户介入修环境，不自动跳过。
- `fail`（设计不合格）→ 条件中断：用户决定改设计还是放宽（放宽须授权，
  且 `--force-unsafe` 不是恢复步骤，见 §4 开头 guardrail 与上游
  `Sample/easyeda-agent/references/design-flow.md`）。
- `pass` → 不中断，静默进入下一阶段。
- 截图 stale + 数据通过 → 不中断（数据是权威），但报告中标注 stale。

**超时与恢复**：
- 中断点等待用户回复期间，不执行任何写操作；可在后台继续纯读取（如
  刷新快照检测 stale），但不推进流程。
- 用户长时间无回复时，在报告中标记 `checkpoint_pending: <阶段>`，
  会话可在后续恢复（用户回复后从该中断点继续，不从头重跑已通过的阶段）。
- 恢复时先回读当前状态确认中断前的写操作已落盘（§10 纪律 2），
  再从该点继续。

**中断期间发现新问题的处理**：
- 中断等待期间纯读取发现新问题（如 S3 等待时回读发现 S2 数据不一致）：
  不静默处理，将新问题追加到当前 CHECKPOINT 的"背景"段，升级为复合
  中断点，等用户一次性答复所有未决项；不因新问题取消原中断点。
- 中断期间活体断连：按 §1.3 恢复流程处理；恢复后重读确认中断前写操作
  落盘，再继续等用户答复；不重发写操作。

---

## 12. 原理图与 PCB 美观/功能布局经验

> 判据层（P0–P7、子域规则）见第 4 节；本节是**操作层经验**——
> 把规则落到"怎么摆才既对又好看"。

### 12.1 原理图（Schematic）可读性经验

- **信号流决定版面**：先定每个模块内部信号流（输入侧→处理→输出侧），
  再决定 Lib 在纸上的位置；阅读顺序 Z 字（左上起、同行顶齐、按行最高框换行），
  读者视线不回头。
- **框内紧凑、框间留白**：每个 Lib 框按内容紧凑包围（能嵌入现有空白就不扩高），
  同行顶齐不拉高短框；框间距与贴边固定 10 raw、标题净距 5 raw，
  这两条是"整齐"的量化定义，不为了好看牺牲。
- **同模块短连线优先**：核心器件与外围用真实短线直连（电容/电阻 10–20 raw），
  不跨模块拉长线；电源/地就近重复放局部符号，普通信号跨模块才用 netport。
  满页同名标签是"标签替代连接"的坏味道。
- **方向一致**：同排器件符号朝向一致（输入朝同侧），极性件按电流方向摆放；
  导线全部水平/竖直，拐角 ≤2 次，单段 >100 raw 改 net label。
- **文字避让**：本体 bbox 不含外置位号/型号文字——已测文字范围进障碍数据；
  导图复核重点：压线、压框、方向倒读、阅读顺序。
- **分页是功能决策**：一页装不下时按功能拆页（电源 / MCU+数字 / RF+IO），
  不是按"塞得下"拆；每页提供完整器件子集，不复制后把原件留在源页。

### 12.2 PCB 美观与功能性经验

- **分区先于对齐**：功能簇（按共享局部 net 聚簇）先成不重叠瓦片，
  块间 ≥50 mil gutter；再在块内做对齐/栅格化。先对齐后分区会把
  不相关的件拉到一起，破坏回流与功能分区。
- **朝向来乱源**：90% 的"乱"来自朝向随机（0/90/180/270 混摆）。
  规则：同类无源件全板至多两种正交朝向；极性件 pin-1 统一方向；
  晶振/LED/连接器开口方向统一。`layout-score tidy` 维的
  `rotation-inconsistent` 子规则报出离群件。
- **阵列是整齐的最大杠杆**：成排的 C/R/排针用 `pcb align`/`distribute`
  成轴 + 等距（±2 mil 共轴、行距恒定 ±5 mil、取栅倍数），
  视觉收益远大于逐件微移。
- **留白是设计**：板面利用率不追 100%——手焊可达性（烙铁通道 ≥60 mil）、
  热散开（≥200/400 mil）、拔插走廊（≥200 mil）都是"功能性留白"，
  宁可留白不可塞满；`compact` 维双侧扣分就是惩罚"太挤"。
- **丝印是最后的视觉层**：位号同侧、同字高、不被本体遮挡；
  功能标注（BOOT/RST/PWR/接口脚名）贴在器件本体外且装配后仍可见；
  底面丝印镜像。丝印压焊盘是 DFM 错误不是观感问题（`pcb check`
  silk-over-pad 管）。
- **层感知看数**：双面板的 overlap/tight 已按装配面分组
  （顶底对穿合法）——`[bottom N / top M]` 报告头可以直接信；
  异面 SMD 焊盘永不短路，通孔焊盘（multi）穿透所有层才可比。
- **收尾顺序固定**：功能位置定稿 → 清 blocking（重叠/短路/出框）→
  `pcb refine`（打分驱动精修，逐步回滚）→ `pcb beautify`（圆角）→
  丝印整理 → 全量验证。不要交替调用多个规划器覆盖同一份目标坐标。

### 12.3 设计决策与交付的美学一致性

- 交付前用 `sch export-image` / `pcb dump` + `layout-score --from` 做
  离线终检：原理图看 Z 字阅读与框标题完整，PCB 看九维分数与逐器件归因。
- 报告里把"美观项"（tidy 维、对齐、阵列）与"功能项"（blocking、间距、
  可布性）分开陈述——前者可留作后续打磨，后者必须清零。
- 用户说"再整齐一点"时，走 §12.2 的收尾顺序增量执行，
  不重做功能布局；"塞不下/太挤"时先改模块几何与功能分组，
  不放宽碰撞判据或无限外扩坐标。

---

## 13. 变更摘要

### 13.1 v0.6.0（2026-09-13）

- 新增 **§7.4 生成 PCB 布局蓝图（Markdown + 字符画边框）**：在物理放置/
  绘制 PCB 之前先生成一份 Markdown 蓝图，用模块/组件/部件及元素间连接
  可视化整板布局，板框外形用字符画（box-drawing ASCII）表达；文件含板框
  字符画、模块/组件/部件清单、连接关系、决策头；先读后画（`sch
  connectivity` / `pcb list --include-bbox` / `sch sheet-geometry`），
  经 P3 中断点（§11.5）拍板后再驱动 `import-changes` 与四档放置。
  蓝图属规划层工件，不替代 `layout-lint`/`pcb drc` 几何电气门禁。
- §4.2 PCB 放置新增"放置前先生成布局蓝图"前置步骤；§13 变更摘要新增
  v0.6.0 条目。

### 13.2 v0.5.0（2026-09-12）

- 新增 **§11.5 中断机制（执行中暂停与用户确认）**：两类中断点
  （强制 mandatory / 条件 conditional）、统一触发协议（CHECKPOINT 格式：
  背景+决策点+选项+推荐+影响范围+等待）、用户响应处理（选择/补充/中止/
  超时）、S0–S6/P0–P10 全阶段强制中断点清单、与验证门禁
  （blocked/fail/pass）的关系、超时与恢复。
- §2 开始工作第 0 步交叉引用 §11.5；§10 执行纪律新增第 11 条
  （中断点命中时暂停不自动推进）。

### 13.3 v0.4.0（2026-09-12）

- 新增 **§8.3 视觉质量与布局完整性自动评估**：`scripts/visual-qa.py`
  用 API 截图（`pcb snapshot --previous-sha256` / `sch export-image`）
  + 数据驱动检查（`layout-score` / `pcb check` / `pcb drc`）交叉评估
  组件间距、走线间距、整体整齐度；三层评估（硬门→关注域→截图一致性）；
  退出码 0/2/3；遵循"数据为权威、截图只做视觉终检"原则。
- 新增 `scripts/visual-qa.py`（Python 3，依赖 easyeda CLI）。

### 13.4 v0.3.1（2026-09-12）

- 技能名由 `jlceda-mcp-easyeda` 更名为 **`EasyEDAssistant`**（frontmatter `name`
  与文档标题同步更新；MCP server 键 `jlceda` 不变）。
- 文件移至仓库根目录（原 `.kilocode/skills/jlceda-mcp-easyeda/SKILL.md`）。

### 13.5 v0.3.0（2026-09-12）

1. 合并 `easyeda-agent-skill-behavior.md` §23–§25 的移植版判据
   （MCP 双端点、设计规范知识库、文档任务），与既有章节去重对齐。
2. 新增 **§11 用户需求澄清与目标明确**：任务分类默认行为、开工前必问清单
   （只问会改变做法的选项）、目标不变量化（pin→net 黄金表/关键网预算/
   验收标准）、授权与沟通纪律。
3. 扩充 **§4.2 美观与功能性经验**：原理图可读性（信号流、框紧凑留白、
   短连优先、方向一致、文字避让、功能分页）；PCB 美观（分区先于对齐、
   朝向归一、阵列杠杆、功能性留白、丝印层、层感知看数、收尾顺序）。
4. 新增 **§12 布局经验**（操作层，与第 4 节判据层互补）与 **§13 变更摘要**。
5. 版本号 0.2.0 → 0.3.0。

---