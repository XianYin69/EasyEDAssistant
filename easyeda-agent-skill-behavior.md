# easyeda-agent Skill 行为记录

> 基于 `Sample/easyeda-agent/` 目录（Codex 使用的 skill，MIT 许可，版本 1.4.8）整理。
> 该项目位于 [zhoushoujianwork/easyeda-agent](https://github.com/zhoushoujianwork/easyeda-agent)。

## 1. Skill 定位

通过本地 `easyeda` CLI、daemon 和 EasyEDA Agent Connector 操作嘉立创 EDA 专业版（EasyEDA Pro）。
使用 typed CLI 经 WebSocket 调用 EasyEDA Pro 官方 `eda.*` API。CLI/daemon、Skill 与连接器是
配套组成部分；CLI/daemon 与 Skill 必须同版，连接器按 major.minor 兼容线对齐。
EasyEDA Pro 是宿主。适用于已有 EDA 工程操作及数据驱动电路设计。

## 2. 目录结构

```
easyeda-agent/
├── SKILL.md                    # Skill 主入口（给 agent 的行为规范）
├── LICENSE                     # MIT
├── .version                    # 1.4.8
├── agents/openai.yaml          # agent 接口定义（display_name / short_description / default_prompt）
├── references/                 # 参考文档（按需加载）
│   ├── actions.md                              # CLI 与 action 使用参考
│   ├── auto-layout-sop.md                      # 原理图数据计算与 Apply 验证流程
│   ├── design-decisions.md                     # 设计决策目录（ADR-0002 决策点清单）
│   ├── design-flow.md                          # 设计流程：原理图数据到实物版图（S0-S6, P0-P10）
│   ├── design-pre-analysis.md                  # 事前快速摸底（可选）
│   ├── environment-setup.md                    # 安装、连接与恢复
│   ├── fab-rules-jlcpcb.json                   # JLCPCB 制造规则基线
│   ├── orientation.json                        # netflag/netport 朝向单一真源
│   ├── part-selection.md                       # 立创/JLC 比对选型
│   ├── pcb-design-rules.md                     # PCB 设计规范手册
│   ├── pcb-layout-conventions.md               # PCB 布局约定
│   ├── pcb-layout.md                           # PCB 摆放/同步/板框命令
│   ├── pcb-routing.md                          # PCB 布线/铺铜/禁布区/填充区域
│   ├── pcb.md                                  # PCB 操作入口
│   ├── project-import.md                       # 外部工程导入与迁移（Altium GUI）
│   ├── schematic-data.md                       # 原理图数据与 SCH Apply（1.4）
│   ├── schematic-layout-conventions.md         # 原理图布局约定
│   ├── schematic-placement.md                  # 原理图布局与模块标题
│   ├── schematic-wiring.md                     # 原理图连线（pin-aware autoconnect）
│   ├── schematic.md                            # 原理图操作入口
│   ├── sheet-templates.json                    # 图纸→图签 keep-out 比例表
│   ├── standard-blocks-contributing.md         # 贡献标准电路块
│   ├── standard-parts.json                     # 标准器件库（LCSC C 号 + deviceUuid）
│   └── symbol-pins.json                        # 真实符号引脚（实测回填）
└── scripts/                          # 辅助脚本
    ├── audit-baseline.py             # 审计日志离线分析（调用分布/失败率/回退路径）
    ├── blocks-pin-audit.py         # 电路块引脚引用审计
    ├── bom-enrich.py               # BOM 导出补 LCSC C 号
    ├── bulk-connect.py             # 连接 spec 驱动的整页电气实现
    ├── bulk-place.py               # manifest 驱动的整页批量放置
    ├── calibrate.js                # 朝向表活体校准
    ├── diff.py                     # 差异感知原理图 lint
    ├── lint.py                     # 数据级原理图 linter
    ├── lint.sh                     # lint 入口（基线管理）
    ├── orient.py                   # 朝向表单一真源（Python 侧）
    ├── parts-add.py                # 器件写回 standard-parts.json
    ├── parts-select.py             # 器件选型（本地/在线比价）
    ├── probe.js                    # 全布局快照（debug.exec_js 用）
    ├── sch.py                      # 原理图执行器（place/wire/connectivity 封装）
    └── tests/                      # 测试（run.py + fixtures + golden）
```

## 3. 会话强制行为

### 3.1 版本门禁

- **每个新 Agent 会话必须先运行 `easyeda update --check --exit-code`**。这是第一条命令，
  先于项目读取、离线规划、`health` 和任何 EDA action。
- 该命令查询 GitHub latest Release；当前 CLI、已安装的当前客户端 Skill、正在运行的 daemon
  必须可验证且**精确等于 latest**，所有已连接 EasyEDA 窗口里的 Connector 必须与 latest
  共享 `major.minor` 兼容线，才返回 0。
- Connector 仅有 patch 差异属于正常兼容；`ahead`、开发构建、版本未知、daemon 未运行、
  没有连接器窗口，以及 Connector 跨 minor/major 都不是通过。
- 门禁非 0 时立即停止当前 EDA 任务，按 `environment-setup.md` 完成升级。
- **只要 CLI、Skill、daemon 或 Connector 发生过升级/替换，本会话不得继续。**
  明确要求用户关闭当前 Agent 会话并新开会话，从第一条命令重新开始。
- 不得用固定旧 `--version`、`--preserve`、`--skip-version-check` 或仅看 `health` 绕过门禁。

### 3.2 门禁通过后

1. 按用户任务选择 `SKILL.md` 中的流程表，只加载相关参考。
2. 运行 `easyeda health` 确认工程、活动页和连接器。
3. 手动命令用 `--project <project>` 指定工程；变更带 `--doc <page>`。
4. 以 `easyeda <domain> <command> --help` 和 `easyeda actions` 为参数真值。

## 4. 任务-参考映射

| 任务 | 先读 |
|---|---|
| 本地原理图数据、版本对账、Lib 组合、修复位号、Apply | `schematic-data.md` |
| 已有原理图检查或器件/连线小修 | `schematic.md`；具体接线见 `schematic-wiring.md` |
| 原理图排版、已有连线的移动/整理 | `schematic-placement.md`、`auto-layout-sop.md` |
| 从需求到整板、原理图转 PCB | `design-flow.md`；未确定的设计选项见 `design-decisions.md` |
| PCB 放置/布线/检查 | `pcb.md`，再按任务读 `pcb-layout.md` 或 `pcb-routing.md` |
| 选型、库器件、手册与标准电路 | `part-selection.md`、`standard-parts.json`；先 `easyeda blocks search` |
| Altium Designer / 外部工程导入 | `project-import.md` |
| 原理图/PCB 绘图规范 | `schematic-layout-conventions.md`、`pcb-layout-conventions.md` |
| 制造规则 | `pcb-design-rules.md`、`fab-rules-jlcpcb.json` |
| action 或队列字段 | `actions.md`；未知官方接口先 `easyeda api search/show` |
| 提交已验证电路到块库 | `standard-blocks-contributing.md` |

## 5. 原理图主流程（1.4）

**核心原则：先确定连接数据，再计算几何，最后转换与回读。**

1. 新设计依据具体型号的数据手册和典型电路；已有图先导出 `sch connectivity`，
   未知引脚或网不能靠截图推断。
2. 器件参数按 `part-selection.md` 留存来源原文和单位换算；不从料号数字猜阻值，
   区分 `mΩ` 与 `MΩ`，参数未核实或相互冲突时不能据此落图。
3. `component.id` 是不透明稳定 ID，`ref` 是显示位号，功能名存 `role`。
   保留正常位号的拼写、前导零与顺序；错误名称用 `sch designators` 按官方库前缀修复。
4. 按功能组织 Lib：核心器件加外围，以真实短线连接。VCC/GND 可局部重复放置；
   标签用于电源或模块边界，不替代连接图。
5. 从官方接口读取器件与引脚几何，保留测量源；用 `sch lib-layout` 从连接图与测量计算
   Lib 内部位置与导线。自编计算须保留脚本和参数。
6. `sch compose` 消费已设计的模块几何，计算端子直线错长、紧凑标题和左上起排的 Z 字布局。
7. 每个 Lib 带粉色虚线框和 **0.2 inch = 20 raw** 标题。固定贴边尺寸为 **10 raw**，
   标题与内容净距 **5 raw**。
8. 生成 `sch apply` 队列前读取目标页新鲜快照。覆盖不同图面用 `compose --replace`。
9. 完整执行队列，回读全部 pin→net/NC、器件身份、线段及模块框；运行检查并显式保存。

### 5.1 数据分层

| 对象 | 约束 |
|---|---|
| `component` | `id` 稳定不透明；`ref` 显示位号；`role` 功能名 |
| `pin` | `number` 物理引脚；`name` 符号脚名；NC 用 `noConnected:true`；悬空用 `connectionState:"unconnected"` |
| `net` | 稳定 `id`、`name`、可选 `scope/role` |
| `connections` | 每条为 `{componentId, pinNumber, netId, kind}` |
| `modules` | Lib 的 `id/name/coreComponents/peripheralComponents/internalNets/ports` |
| 几何 | 器件位置、朝向、实测 bbox/引脚位置、导线、标记、框与文字 |

### 5.2 转换入口

| 需求 | CLI |
|---|---|
| 读取连接图 | `sch connectivity [--page <page> \| --all-pages]` |
| 本地连接差异 | `sch connectivity-diff before.json after.json` |
| 本地设计版本差异 | `sch design-diff expected.json actual.json --exit-code` |
| 既有框/标题差异 Apply | `sch design-diff before-plan.json after-plan.json --before fresh.json --playbook frame-diff-apply.json` |
| 由实测引脚计算 Lib 内部 | `sch lib-layout --from layout-input.json --out composition.json` |
| 非标准位号修复 | `sch designators allocate` → `plan` → `verify` |
| 完整 Lib 图面 | `sch compose` |
| 基础放置 | `sch materialize` |
| 明确的标记增量 | `sch plan before.json after.json` |
| 只画框和标题 | `sch frame apply/check --from frames.json` |
| 执行队列 | `sch apply plan.json` |

### 5.3 位号修复

正常位号使用英文字母前缀加数字。保留已有合法编号的大小写、前导零和声明顺序；
`U_RF`、`J_AUDIO_MOD` 属于功能名，放入 role，不当成原始合法编号继续重放。
官方库默认前缀可能是 `U?`、`CN?` 等，不能假定端子必定是 `J`。

流程：
1. 用 `lib device get --uuid <deviceUuid> --library <libraryUuid>` 查询官方记录。
2. 将 `result.device.property.designator` 汇成 `prefixes.json`。
3. `sch designators allocate` → `plan` → `apply`。

### 5.4 连线（pin-aware autoconnect）

`sch autoconnect` 从真实几何（part bboxes、pin coords、existing flag/port/label bboxes、
title-block keep-out）评分每个 `up/down/left/right × offset` 候选，使用确定性代价函数
（flag-collision / through-part penalties, shortest-offset + outward-side + kind-default
bonuses），选择最低代价项，委托给 `connect_pin` 执行变更。

关键行为：
- **幂等**：已连接目标网的脚自动跳过。
- **硬拒（#64）**：短桩端点/路径触碰异网线、短桩跨越非目标引脚 → 候选不可用。
- **图签侵入（#147）**：标签落入 A4 图签 keep-out → 硬拒。
- **密集区**：候选范围扩到 3×offsetMax 继续找干净位置。
- **带痕候选**：选中候选 score 超软阈值或含碰撞惩罚时标 `⚠ WARN`；`--strict` 直接判失败。
- **平台随机吞连接（stuck-at-99%）**：失败后重试一次，但只在连接器明确声明回滚之后。
- **35s 专用预算**：`connect_pin` 用 35s 而非默认 20s；超时/DISPATCH_FAILED 自动做一次轻读复核。

## 6. 设计流程（S0-S6, P0-P10）

### 6.1 原理图 S0-S6

| 阶段 | 工作与检查点 |
|---|---|
| S0 — 明确需求和数据来源 | 记录供电、接口、电气要求、板框/装配约束；按功能划分 Lib；选型使用官方器件库身份 |
| S1 — 建立可信快照与纸张边界 | 读取当前连接关系，保存本地基线；确认纸张与图签禁放区 |
| S2 — 分配位号并完成模块数据 | 缺失/非标准位号用 `sch designators allocate`；同步本地模块、接口、placement 的引用 |
| S3 — 计算放置、导线和模块框 | 先放核心，再依据引脚方向放外围；`sch lib-layout` + `sch compose` |
| S4 — 编译与执行 SCH Apply | 用新鲜目标页快照编译队列；`--dry-run` 后执行 |
| S5 — 回读验证 | 导出新 `sch connectivity`，`sch design-diff` 对照；逐页 `sch gate --strict` |
| S6 — 修复、保存和交付 | 依据 finding 修改本地数据；保存最终原理图并确认成功 |

### 6.2 PCB P0-P10

| 阶段 | 工作与检查点 |
|---|---|
| P0 新建/选择板 | `pcb board-info` 核实原理图与 Board 关联 |
| P1 导入 | `pcb import-changes` 同步原理图 |
| P2 放置 | 从 spec 读取装配工艺；实测 bbox/pads 后放置 |
| P3 板框 | 有机械约束时先建约束板框 |
| P4 禁布 | 在布线前落实天线、RF、安装及开槽禁布区 |
| P5 丝印占位 | `pcb silk-align` 校正位号 |
| P6 布线前门 | `pcb layout-lint --gate` |
| P7 布线 | 先关键网、后普通信号 |
| P8 电源与铺铜 | 按已确定的叠层/电源策略完成铜面、缝合和回流 |
| P9 标注 | 核对接口逐脚标记、极性、板名版本 |
| P10 终检 | `pcb drc --json`、`pcb check`，完成 `post_route_checked` 门 |

### 6.3 PCB 放置与阶段门

- 装配工艺确定后用 `pcb stage set-assembly` 持久化。
- 手焊 profile 的普通器件间距下限为 40 mil，大焊盘烙铁通道默认 60 mil。
- 四档：孔/结构件 → 边缘接口 → 主芯片与 RF → 卫星件。
- `pcb layout-lint --gate` 要求装配 profile、无重叠/出板框/过紧间距。

### 6.4 PCB 布线、电源与工艺

- 布线前核对真实叠层、网络类别、差分/等长预算和禁布区。
- `pcb route-critical --spec <S0.json> --dry-run` 先核对真实铜层与需求。
- 两层可用 `pcb power-pour`；四层 `pcb power-planes` 默认 GND 在层 15（内电层）。
- PCB 写后按 `STALE_READ` 提示用 `doc reload` 刷新；铜形变化后 `pcb pour-rebuild`。

## 7. 执行与验证约束

- typed action 已有对应能力时使用它；无对应能力且用户接受调试路径时，才用 `debug.exec_js`。
- `.SchDoc` / `.PcbDoc` 当前没有可用的程序化工程导入入口；按 `project-import.md` 走 GUI。
- 使用真实非零导线连接 netflag 与 pin，坐标重合不算连接。原理图坐标 **y 向上**，网格 5 raw。
- 保留明确 NC，不删除器件物理引脚，也不将缺失连接自动改为 NC。
- 写入超时或部分成功后先回读，不盲重试。受保护队列不能用 `--resume/--from/--to` 跳过守卫。
- Apply 不提供事务撤销；autosave 仅兜底，检查点须显式 `sch save` / `pcb save`。
- 已有用户授权持续有效，不因流程表重复索取许可。
- PCB 变更后按命令提示 `doc reload` 再检查。

## 8. 验证交付

- `layout-lint` 检查几何，pin→net 黄金表检查接对与否，`sch gate --strict` 汇总原理图门禁。
- 官方 DRC 可能只返回聚合数；INFO/WARN 应单列，不能把"0 fatal"称为全部通过。
- `layout-score` 的逐维结果、`skipped/degraded` 是诊断，不代替硬门。
- 用 `sch export-image` 生成官方导图辅助确认文字与可读性。
- PCB 制造交付还须确认层叠、GND、电源、丝印与导出文件。

## 9. 设计决策（S0 摊给用户拍板）

判据：用户的回答会不会改变实际做法——会才进设计决策，不会（只有唯一正确答案）就是
guardrail，以硬门禁形式内置在 `pcb-layout-conventions.md` / `auto-layout-sop.md` /
`design-flow.md` 里。

| 决策点 | 选项 |
|---|---|
| 叠层与层数 | 2 层 vs 4 层（及以上） |
| 接地策略 | 单一 GND PLANE vs 多地域全 SIGNAL 分区铺铜 + 单点桥地 |
| 外层铺铜策略 | 整面单一 GND vs 电源密集区分区 pour |
| 线宽分级 | 全板统一默认 vs 按网络角色分级 |
| RF/天线禁布区 | guardrail 锚点（非决策，覆盖全层） |
| 接口取向 | USB-C 单取向 vs 双取向 tie |
| USB 接口架构 | 单通道串口桥 vs 双通道 vs 纯原生 USB |
| 自动下载电路 | 仅物理按键 vs 加装 DTR/RTS 管 vs 走原生 USB 免管 |
| 选型成本档位 | 固定 standard-parts.json vs 动态比价 |
| Basic vs Extended | 强制 basic-only vs 允许 extended |
| 目标建构批量 | 小批量原型 qty vs 直接按量产 qty |
| JLC SMT 可选件 | 仅组装可选 vs 允许非组装 |
| 单面 vs 双面布局 | 全 TOP vs 允许 BOTTOM |
| 焊接工艺 | 产线贴片 vs 手工焊接 |

## 10. 器件选型

- 先查 `standard-parts.json` 和 `easyeda blocks show <id>`。
- 已知 C 号用 `easyeda lib by-lcsc --lcsc C…` 精确解析。
- 从官方器件记录的 Datasheet 地址查典型应用、引脚和外围参数。
- 参数核验保留原始单位，不从料号猜数值。
- `parts-select.py` 排名：Resistance gate → Buildable → Basic → Preferred → Cheapest。
- 新选型用 `parts-add.py` 写回 `standard-parts.json`。

## 11. PCB 布局约定

### 11.1 优先级总则（冲突裁决顺序）

| 级别 | 约束 |
|---|---|
| P0 | 机械/外壳锁定坐标 |
| P1 | 安全间距/隔离 |
| P2 | EMI 热回路 + 关键去耦贴近 |
| P3 | 参考平面/回流连续性 |
| P4 | 热 keep-out |
| P5 | 功能分区/模块化 |
| P6 | DFM |
| P7 | 网格/对齐/丝印（纯收尾，永远不得违反以上） |

### 11.2 去耦电容

去耦有效性由电容自身的安装回路电感主导，不是"离 IC 多近"：
- 2 层板：横向距离主导，目标 50-100 mil、硬上限 150 mil。
- 4 层以上：横向距离降级为 should，上限放宽到 250 mil。

### 11.3 板框

- 默认四角做圆角。
- 圆角必须在铺铜/布线之前做。
- 两条合法路径：有机械尺寸先建 outline；无机械尺寸先粗布局后收紧。

### 11.4 布局质量打分（`pcb layout-score`）

九维：partition、flow-order、edge-io、protection、tidy、compact、rf、routable、clearance。
三条硬约定：
1. "没测" ≠ "测了满分"。
2. 硬错不抹平分数。
3. 计数与判定同源。

## 12. PCB 布线与铺铜

- 导线（`pcb.line.create`）、过孔（`pcb.via.create`）为增量创建，无确认。
- `pcb.route.rip_up` 可靠 rip-up（删除 tracks+arcs+vias）。
- `pcb clear` 一键整版复位（默认保留锁定图元 + 板框）。
- 铺铜（`pcb.pour.create`）绑定网络，动态 reflow。
- Keep-out region（`pcb region create`）禁止区域。
- 填充区域（`pcb fill create`）静态填充。
- 差分对/等长组约束（`pcb diff-pair` / `pcb eq-group`）。
- 连通性键合真值表：track↔via 自动注册连接，不需要 bond fill。

## 13. PCB 制造规则

基于 JLC嘉立创工艺能力 + IPC-2221 + 业界最佳实践：
- 线宽/间距/过孔参数（JLC 工艺极限 vs 推荐设计值）。
- 走线规范（45° 折线、相邻层正交、回流路径连续）。
- 铺铜规范（动态 pour 优于静态 fill，天线/RF 下方禁铜）。
- 电源与地（单 GND 平面优先，割地为专用工具）。
- 差分对与高速信号（等长、紧耦合、过孔成对）。
- 叠层设计（默认 4 层：Top/Inner1-GND/Inner2-PWR/Bottom）。
- DRC 检查清单（FATAL/ERROR/WARN 分级）。

## 14. 外部工程导入

- Altium Designer `.SchDoc` / `.PcbDoc` 当前没有可用的 typed action。
- 需要迁移 AD 工程时，在 EasyEDA Pro 中使用 GUI 流程（文件 → 导入 → Altium Designer）。
- GUI 完成后，重新确认当前工程和文档，再由 easyeda-agent 接管后续读取、修复和验证。
- 官方 beta 方法 `eda.sys_FileManager.importProjectByProjectFile` 实测会静默返回 `undefined`，
  不能包装后当成功。

## 15. 环境安装与连接

### 15.1 安装链

- 发布版安装：`curl -fsSL https://raw.githubusercontent.com/zhoushoujianwork/easyeda-agent/main/install.sh | bash`
- 升级：`easyeda update`（CLI + Skill），daemon 需用新二进制重启。
- 连接器：GitHub Release `.eext` 侧载 或 立创插件市场。
- Windows：下载 `easyeda_windows_amd64.exe` 并命名为 `easyeda.exe`，把所在目录加入 PATH。

### 15.2 连接确认

- `easyeda daemon start` 监听 **60832**。
- `easyeda health --project "<project>"` 确认连接。
- 写操作使用 `--project` 和 `--doc`，由 CLI 在派发前实时确认目标文档。

### 15.3 上下文与缓存

- `windowId` 会随重连变化，不作为持久身份。优先用项目和文档 UUID 路由。
- 刷新编辑器文档状态：`easyeda doc reload`（先保存，再关闭并重开文档）。

## 16. 辅助脚本

| 脚本 | 用途 |
|---|---|
| `lint.sh` | 数据级原理图 linter（基线管理，差异感知） |
| `bom-enrich.py` | BOM 导出补 LCSC C 号 |
| `parts-select.py` | 器件选型（本地 standard-parts 优先，在线比价 opt-in） |
| `parts-add.py` | 器件写回 standard-parts.json |
| `blocks-pin-audit.py` | 电路块引脚引用审计（`--probe` 实测刷新 symbol-pins.json） |
| `bulk-place.py` | manifest 驱动的整页批量放置 |
| `bulk-connect.py` | 连接 spec 驱动的整页电气实现 + 验证门 + 悬空脚修复 |
| `audit-baseline.py` | 审计日志离线分析（调用分布/失败率/回退路径） |
| `calibrate.js` | 朝向表活体校准（对 `getPrimitivesBBox` 实测复核） |
| `sch.py` | 原理图执行器（place/wire/connectivity/snapshot 封装） |
| `probe.js` | 全布局快照（通过 `debug.exec_js` 拉取 parts+pins+flags+wires） |
| `tests/run.py` | 规则信任测试（朝向表一致性 + fixture 金标准） |

## 17. 朝向系统（单一真源）

`orientation.json` 是 netflag/netport body 朝向的单一真源。整张表由 4 个事实决定：

- `rotationCycle`：`up → left → down → right`（2026-08-12 重新校准）
- `bodyAnchorAtRot0`：`power=up, ground=down, port=right`

消费者：
- `scripts/orient.py`（linter 的 Python 侧检查）
- `extension/src/actions.ts` `deriveBodyRotation()`（connect_pin 写入侧）

`tests/run.py` 断言两者推导的表一致，防止语言间漂移。
`calibrate.js` 对活体 `getPrimitivesBBox` 校准 3 个锚点。

## 18. 图纸边界与图签 keep-out

EasyEDA Pro 没有 set-paper-size API，图签 keep-out 几何只能推导：

1. 读取 sheet bbox（`componentType == "sheet"` 的图元）。
2. 用 sheet bbox 的长宽比匹配已知模板（A 系列横/纵向 ≈ √2）。
3. 按匹配模板的归一化比例在 sheet bbox 的右下角切出子矩形。
4. `schematic.titleblock.get` 的 `showTitleBlock` 控制可见性。

`sheet-templates.json` 是 Go 表 `sheetTemplates` 的人读镜像，运行时权威在
`easyeda sch sheet-geometry --json`。

## 19. 块贡献（标准电路块）

- 先 `easyeda blocks search <keyword>` 查已有块，`easyeda blocks show <id>` 读取完整 JSON。
- 模板与 1.4 Lib 的边界：模板的 `parts.<ROLE>` 与实例的稳定 component ID、ref、role
  属于不同层，模板 JSON 不能直接作为 composition 输入。
- `block-apply` 每次创建新实例，并非幂等修复命令。
- 验证必须实际通过 `sch block-apply` 生成电路，保存 manifest，回读全部 pin→net/NC。
- `verification` 记录 `schematic/component_selection/pcb_drc/bringup` 四项。
- 只有四项均通过才能设 `production_ready:true`。

## 20. 关键数据文件

### 20.1 standard-parts.json

- 约 120 个器件条目，含 `deviceUuid`、`lcsc` C 号、`footprint`、`basic` 标记。
- 覆盖：MCU（ESP32-S3 系列）、IC（CH340C、INA226、CH334F 等）、无源（R/C/L/D）、
  连接器（USB-C、SIM、TF、IPEX）、电源（buck、charger、PMU）、天线、传感器、音频等。
- 所有 `deviceUuid`/`lcsc` 值来自活体 `lib_Device.search`，经真板放置验证。

### 20.2 symbol-pins.json

- 真实符号引脚，从已放置器件回读。
- 用 `blocks-pin-audit.py --probe` 刷新（需活体 EasyEDA 窗口）。
- 按 `standard-parts.json` 的 key 索引。

### 20.3 fab-rules-jlcpcb.json

- JLCPCB 制造能力基线（最小线宽/间距、过孔、焊环、铜到板边、丝印）。
- 按层数 + 铜厚分类。
- 作为 `pcb.drc.rules` 的 fallback seed 和 clamp floor。

## 21. 坐标与单位

| 上下文 | 单位 | 说明 |
|---|---|---|
| 原理图 | 1 raw = 0.01 inch = 0.254 mm | y-UP，5 raw 网格 |
| PCB | 1 mil = 0.001 inch | y-UP，常用 25/50 mil 网格 |
| mm 参数 | 边界换算 | 2.54 mm = 10 raw units |

## 22. 已知平台限制

- `.SchDoc` / `.PcbDoc` 无程序化导入入口。
- `eda.*` 无 create/apply-teardrop API（泪滴只能在 UI 手动）。
- 交互式布线菜单（单/多/差分 routing、stretch、optimize）无 `eda.*` API。
- `pcb_Document.autoRouting` 在 3.2.148 未定义。
- `createNetLabel` 在 EasyEDA 3.2.186 实测挂起（标注 EDA v4 BETA）。
- `getCurrentRenderedAreaImage` 在后台标签可能返回缓存旧渲染。
- 3D 模型导入的 `/action` 请求体上限为 32 MiB。

## 23. 审计与恢复

- 49 天 171554 条审计记录，脏读率 18.1%（1780 次）→ PCB mutation 后读升级为机械门
  （`STALE_READ` 拒绝）。
- `audit export --playbook` 可从审计生成复现用队列。
- `audit-baseline.py` 离线分析调用分布/失败率/回退路径。
- 单连接恢复：先回读确认 → 检查扩展管理器 → 重启 daemon → `health` 确认。

## 23. 移植版本（JLCEDA MCP VS Code 插件桥接）

> 本节描述将 easyeda-agent skill 移植到基于 **JLCEDA MCP VS Code 插件** 运行时的
> 连接方式与新增行为要求。移植版本必须**同时保留原有 CLI/daemon/连接器链路**
> （第 15 节），不得以 MCP 桥接替代；两条路径按可用性与权限共存。

### 23.1 连接端点

| 通道 | 地址 | 用途 |
|---|---|---|
| WebSocket 桥接 | `ws://127.0.0.1:8765/bridge/ws` | JLCEDA MCP VS Code 插件 ↔ 本地 EDA 引擎的实时双向通道（动作派发、心跳、窗口上下文） |
| HTTP MCP 端点 | `http://127.0.0.1:7655/mcp` | MCP（Model Context Protocol）工具/资源/提示服务入口；Kilocode 以 remote/local MCP server 接入 |

Kilocode `kilo.json` 中的接入示例（与原有链路并存，不互斥）：

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

- WebSocket 桥接由 JLCEDA MCP 插件在本地监听 `8765`，Kilocode 侧通过插件提供的
  工具调用完成动作派发；`bridge/ws` 路径不可用时必须回退到原有的
  `easyeda daemon`（`60832` 端口）链路，不能静默降级或跳过回读验证。
- HTTP `7655` 与 WS `8765` 属于同一插件的两个端口；插件未启动时两条端点均不可用，
  按 `environment-setup.md` 的连接异常恢复流程处理（保留 health/journal 证据）。
- 版本门禁（第 3.1 节）对移植版本同样适用：会话第一条命令仍为
  `easyeda update --check --exit-code`；MCP 工具不替代该门禁。

### 23.2 兼容约束

- 原有连接方式（`easyeda` CLI、daemon、EasyEDA Agent Connector、`--project`/`--doc`
  路由、`doc reload` 门、`STALE_READ` 机制）全部保留，移植版不得移除或弱化。
- MCP 工具调用与 typed CLI action 语义一致：同一套 `eda.*` API 映射，同一套
  dry-run / 回读 / `saved:true` 验证纪律；MCP 只是另一个入口（同第 3 节末条）。
- 破坏性操作（clear、delete、import-changes、批量 arrange）仍须确认门控；
  MCP 通道不免除用户授权。
- 审计与 journal 继续写入本地 `~/.easyeda-agent/audit`，MCP 调用同样记录。

## 24. 现代电子产品设计规范知识库（移植版新增）

> 本节为移植版本扩充的设计知识面，作为 skill 在 RF / 模拟 / 数字 / 滤波器 /
> 电源等子域上的设计判据来源；与第 11–13 节的 PCB 约定互补，不替代
> `pcb-design-rules.md` 的 JLC 工艺基线。数值判据仍须以数据手册与实测为准，
> 本节给出的是**方向性规则与经验值**。

### 24.1 PCB 布局与原理图绘制

- **原理图**：按功能 Lib 分组（第 5 节）；九宫格分区（`schematic-layout-conventions.md` §1）；
  信号流左→右（电源左列、MCU 中列、RF/IO 右列）；多脚同功能逐脚核对；
  全局电源/地符号可就近重复放置，信号用 netlabel/netport 跨模块互连。
- **PCB**：P0–P7 优先级总则（第 11.1 节）；机械件先放先锁；去耦贴脚按叠层条件化
  （第 11.2 节）；四层默认叠层 `Top/Inner1-GND(PLANE)/Inner2-PWR/Bottom`；
  丝印可读性与装配后可见性（§9.4.1）；安装孔与板边净空（§8.5 分层带）。
- **BGA/细间距**：fan-out halo 40–80 mil；dog-bone 优先，via-in-pad 需填孔盖铜工艺。
- **手焊可达性**：手焊 profile 普通器件间距 ≥40 mil，大焊盘烙铁通道 ≥60 mil
  （第 6.3 节 `pcb layout-lint --gate` 已机械化）。

### 24.2 射频（RF）设计

- **全层 keepout**：天线/Wi-Fi/BLE 模组下方所有铜层（含内电层）禁铜
  （`pcb check antenna-keepout` 强制）；keepout 半径按 datasheet 标注，一般 ≥5mm。
- **馈线阻抗匹配**：50Ω 单端 / 100Ω 差分（USB/以太网）；微带/带状线宽度按板叠
  仿真计算，不用默认线宽；端接 50Ω 或共模扼流圈（USB D± 建议 22R + 共模扼流圈）。
- **布局**：RF 路径最短化（λ/4 @2.4GHz ≈ 12mm 内完成匹配+馈电）；晶振远离
  RF 馈线；RF 地缝合过孔密集（间距 ≤ λ/20）；RF 与数字/电源分区 ≥200 mil。
- **天线净空**：天线元件四周及下方全层无铜无器件；IPEX/u.FL 天线座贴板边
  突出或靠边，净空区不压铜；天线馈电 pad 与匹配网络（L-C-L π 型）同层直连。
- **ESD 保护**：射频口串 ESD 器件（低容 <1pF）贴天线端，接地就近。

### 24.3 模拟电路

- **单点接地**：模拟地与数字地单点汇合（星形），避免地环路；精密 ADC 前端
  独立模拟电源域（经磁珠/RC 滤出），模拟电源子域命名 `AU_3V3` / `ADC_3V3`
  （第 6.2 节 design-decisions 判据）。
- **去耦**：模拟 IC 电源脚 0.1µF 陶瓷 + 10µF 低频储能，贴脚 ≤30 mil（高速）/
  ≤60 mil（一般）；运放电源端加 10µF 钽/电解远离热区。
- **信号隔离**：模拟输入通道不跨数字地平面；高速/开关电源远离模拟敏感区
  ≥300–500 mil；热电势敏感电路（热电偶/应变片）用同材质焊丝与冷端补偿。
- **反馈环路**：运放反馈网络贴输出端，避免前级耦合长走线；补偿电容贴反馈跨接。

### 24.4 数字电路

- **时钟**：晶振贴 MCU 振荡 pin ≤300 mil（理想）/ ≤500 mil（上限），两负载电容
  对称 150–200 mil；晶振下方禁走线，包地处理；时钟树扇出注意占空比与边沿。
- **上拉/下拉**：开漏总线（I2C）上拉电阻靠主控端；未用 GPIO 必须显式上/下拉
  或 NC 标记，不悬空。
- **复位**：复位电路 RC 延时计算（t_reset ≥ Vth 对应的 RC 时间常数），复位信号
  低有效命名 `nRESET`；ESD/闩锁保护在入口。
- **隔离**：数字隔离器（光耦/数字隔离 IC）跨隔离屏障，两侧电源独立、爬电距离
  满足 P1 安全间距（第 11.1 节）；隔离区禁止地平面连续（单点桥接或开槽）。
- **电平匹配**：不同电压域接口用电平转换器（N 通道双 MOS / 专用电平转换 IC），
  不直接跨压。

### 24.5 滤波器

- **无源 LC 滤波器**：L/C 值按目标截止频率计算，元件公差（L ±20%、C ±5–10%）
  决定实际 fc 偏差；C0G 电容用于 RF 滤波（温度稳定），PC 介质用于低频大值。
- **有源滤波器**：运放供电去耦（每电源脚 0.1µF）；反馈电阻贴输出端；
  高通/低通阶数与增益-带宽积匹配。
- **巴伦/耦合器**：CC1101 类巴伦镜像布局（块约束 `balun-mirror`，第 6 节块 PCB
  约束）；差分转单端的阻抗变换网络贴 RF IC 端。
- **数字接口滤波**：USB/HDMI 共模扼流圈（SDMM0806H-2-900T）串 D±，22R 串阻
  抗振铃；ESD 阵列（USBLC6-2SC6）贴连接器端。

### 24.6 电源（Power）

- **Buck**：输入电容（陶瓷，贴 VIN/GND ≤150 mil 同层）+ 续流二极管/Sync FET +
  输出电感 + 输出电容；SW 节点铜面最小化，远离敏感器件；反馈网络贴 FB pin。
- **LDO**：输入/输出各 0.1µF + 10µF bulk（入口 bulk 500 mil 内）；热耗计算
  `(Vin−Vout)×Iout`，SOT-223 限约 0.5–1W，超则换 buck 或加散热。
- **电源树**：外部输入 → 防反接（P-MOS/肖特基）→ 主 buck/LDO → 各子系统；
  每轨入口 bulk + 每 IC 本地去耦；电源走线按电流分级线宽（第 12.1.2 表），
  大电流用铺铜/内电层，不用细走线。
- **多电源域**：4 层板各域独立内电层（≥6 层才各给独立 PLANE）；
  多电源轨不短接同一平面；局部铜和零散轨单独处理（第 6.4 节）。
- **电池管理**：充电 IC 的 PROG/ISET 电阻按手册公式计算；NTC 串联低温禁充；
  防过充/过放/短路保护；电量计（PMU）按采样电阻精度匹配。

### 24.7 电气规范（行业标准）

| 标准 | 适用范围 | 关键要求 |
|---|---|---|
| IPC-2221B | PCB 通用设计 | 分层设计流程、规则化 DRC 阈值 |
| IPC-7351B | 焊盘/封装 | courtyard、最小间距 0.2mm（SMD） |
| IPC-A-600 | PCB 可接受性 | 缺陷判据（短路/断路/分层/铜剥离） |
| JEDEC J-STD-001 | 波峰/回流焊 | 焊接工艺参数 |
| IEC 60950 / IEC 62368 | 安全（信息技术设备） | 爬电/电气间隙、隔离屏障 |
| UL 94 | 板材阻燃 | V-0 级别（消费电子默认） |
| RoHS / REACH | 环保 | 禁用物质限量（Pb/Hg/Cd/Cr6/卤素） |
| FCC Part 15 / CE EMC | 电磁兼容 | 辐射/传导限值、屏蔽与滤波设计 |
| JLCPCB 工艺能力 | 制造 | 第 13 节 `fab-rules-jlcpcb.json` 基线 |

> 数值门禁的运行时正本在 Go 代码（`pcb_rules.go` / `pcb_netclass.go` /
> `pcb_check*.go`）；本表为人读判据，冲突时以代码 + JLC 官网为准。

### 24.8 电子电路设计经验（经验法则）

- **电流估算**：1oz 外层 0.15mm ≈ 0.5A、0.25mm ≈ 0.9A、0.5mm ≈ 1.5A（§1.3 表）；
  内层打 60–70% 折减。
- **去耦原则**：每个 IC 每个电源脚 0.1µF；大电流路径 10µF bulk 入口；
  去耦有效性由安装回路电感（pad→via→平面）主导，不是距离。
- **RC 时间常数**：τ=RC；5τ 达稳态 99.3%；复位/滤波按功能需要选值。
- **阻抗匹配**：单端 50Ω、USB 差分 90Ω、HDMI 100Ω；长走线（>λ/20 @ 最高频率）
  需端接。
- **PCB 面积估算**：`Σ主器件 bbox + 辅助件 × 80×80 + 余量`；>80 件考虑多页
  或双面。
- **信号完整性**：换层必打地孔（回流连续）；高速信号不跨分割/开槽/板边；
  差分对等长 ±5 mil，对内紧耦合。
- **热设计**：电解电容远离热源 ≥200 mil；热焊盘下散热过孔阵列（0.3mm 孔/1mm
  间距）；>0.5W 器件四周 ≥500 mil 开阔铜。
- **ESD 入口**：每个对外口串 ESD 器件（USBLC6 类），TVS 钳位电压 < 后级耐压强 20%。
- **命名即信道**：net 名 + 线宽 + designator 是原理图传给 PCB 的唯一信道
  （`design-pre-analysis.md`），差分/等长/隔离网必须成对成组命名。

### 24.9 数据文件 / PDF 阅读经验

- **数据手册**：`standard-parts.json` 的 `datasheetUrl`/`datasheetPdfUrl` 为
  器件选型依据；读 PDF 时先定位「电气特性 / 典型应用 / 引脚表」三节。
- **参数核验**（第 10 节 `part-selection.md` 流程）：
  1. 锁定厂商、完整 MPN、LCSC C 号与封装。
  2. 读目录具名参数与对应手册，保留来源 URL、原始文字、手册页码/表名。
  3. 单位换算另列（`mΩ` = 毫欧、`MΩ` = 兆欧；SI 前缀大小写敏感）。
  4. 目录/手册/库 value 不一致时记录冲突，来源不可读时标"未核实"，
     不填猜测值、不写回标准库。
- **PDF 提取要点**：
  - 先读目录/概述（Abstract/Features/Description）定型号与封装。
  - 电气参数表（Electrical Characteristics）带条件（Vin/Tj/负载）——抄条件不只抄值。
  - 典型应用电路（Typical Application）是外围设计的基准，不凭外观补接线。
  - 封装图（Package/Dimensions）用于 footprint 核对，注意 courtyard 与焊盘偏移。
  - 曲线图（效率/纹波/频率响应）取工作点（电流/频率）对应值，不取峰值。
- **不靠截图推断**：第 5 节主流程要求——已有图先导出 `sch connectivity`，
  未知引脚或网不能靠截图推断；PDF 同理，参数必须读到原文，不靠目测图形。
- **手册版本**：同一 MPN 多版本手册取最新版；旧版典型电路与新版引脚可能不一致，
  版本不匹配时停止自动绘图并重新核对器件身份（第 10 节）。

## 25. 新增任务能力

> 移植版本在原有 EDA 任务（第 4 节任务-参考映射）之外，新增以下两类项目任务：

### 25.1 创建许可证（Create License）

- 为 EDA 项目/工程仓库生成许可证文件（`LICENSE` / `LICENSE.txt`）。
- 默认 **MIT**（与 easyeda-agent skill 本身体一致）；用户指定时支持
  Apache-2.0、GPL-3.0、BSD-3-Clause、CC0 等常见许可证。
- 行为约束：
  - 仅写文件与提交记录，不改 EDA 工程数据。
  - 已有 `LICENSE` 时不覆盖，先回读确认；用户明确授权才替换。
  - 版权行年份与版权主体由用户提供，不猜测。
- 关联动作：生成后建议同步到 `AGENTS.md` 或 README 的许可证声明段。

### 25.2 生成 README.md

- 为 EDA 项目生成或更新 `README.md`：项目概述、BOM 摘要（来自
  `bom-enrich.py` 产物）、原理图/PCB 阶段状态（S0–S6/P0–P10 当前门）、
  构建与导出说明（gerber/BOM/placement 路径）、许可证引用。
- 行为约束：
  - 内容必须来自当前工程回读（`sch connectivity` / `pcb list` / `pcb drc`），
    不写未验证的数据。
  - 不替代 `sch export-image` 的官方导图；README 中图片引用须先导出。
  - 已有 README 时追加/更新章节，不全量重写；破坏性改写须用户确认。
  - 未完成的门（`blocked`/`fail`）在 README 中如实标注，不写成通过。

### 25.3 任务调度规则

- 两类任务属于**项目级文档任务**，不触发版本门禁升级（第 3.1 节），
  但仍需 `easyeda health` 确认工程上下文（涉及 EDA 数据读取时）。
- 纯本地文件任务（写 LICENSE/README）可离线执行，不要求活体窗口。
- 任务产物与 EDA 工程文件同仓管理，纳入 `git` 版本控制；提交信息注明
  生成来源（`generate-license` / `generate-readme`）。

## 26. 回归测试


- 本仓库完整端到端回归按 `AGENTS.md` 使用 `esp32MiniRequire.md` 第一节原始需求作为输入，
  在 `ceshi` 测试工程走完对应 S/P 阶段。
- 不能喂预制 BOM/UUID/网表代替选型验证。
- 完整回归记录 `easyeda audit cost` 成本台账。
- `pcb dump` 生成离线 fixture，`pcb layout-score --from <file>` 可重放。
