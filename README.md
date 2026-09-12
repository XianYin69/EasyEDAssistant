# EasyEDAssistant

易EDA 助手项目：将 **easyeda-agent** skill（嘉立创 EDA 专业版自动化设计 skill）
移植为基于 **JLCEDA MCP VS Code 插件**桥接的 Kilocode skill（**EasyEDAssistant**），
并维护完整的行为记录文档。

## 目录结构

```
EasyEDAssistant/
├── README.md                                  # 本文件
├── LICENSE                                    # MIT
├── SKILL.md                                   # EasyEDAssistant skill 定义（Kilocode）
└── Sample/
    ├── easyeda-agent-skill-behavior.md        # easyeda-agent skill 全部行为记录（含移植版章节）
    └── easyeda-agent/                         # 参考样本（上游 Codex skill 原样）
        ├── SKILL.md                           # 上游 skill 主入口（行为规范）
        ├── agents/openai.yaml                 # agent 接口定义
        ├── references/                        # 参考文档与数据文件
        │   ├── schematic*.md  pcb*.md        # 原理图 / PCB 操作参考
        │   ├── design-flow.md  design-decisions.md  # 设计流程与决策目录
        │   ├── part-selection.md              # 立创/JLC 选型
        │   ├── standard-parts.json            # 标准器件库（LCSC C 号 + deviceUuid）
        │   ├── symbol-pins.json               # 实测符号引脚
        │   ├── orientation.json               # 朝向单一真源
        │   ├── fab-rules-jlcpcb.json          # JLCPCB 制造规则基线
        │   ├── sheet-templates.json           # 图纸/图签 keep-out 比例表
        │   └── ...
        └── scripts/                           # 辅助脚本（lint / 选型 / 批量操作 / 测试）
```

## 概述

本项目围绕 `Sample/easyeda-agent/` 目录下的上游 skill（Codex 使用，MIT 许可，
上游项目：[zhoushoujianwork/easyeda-agent](https://github.com/zhoushoujianwork/easyeda-agent)）
构建两层内容：

1. **行为记录** — `Sample/easyeda-agent-skill-behavior.md` 记录该 skill 的全部行为：
   会话版本门禁、原理图 1.4 数据路径（connectivity IR → Lib 几何 → compose →
   sch apply → 回读对账）、设计流程 S0–S6 / P0–P10、执行与验证约束、器件选型、
   制造规则、朝向系统、图纸 keep-out 推导，以及移植版新增章节
   （§23 JLCEDA MCP 桥接、§24 现代电子产品设计规范知识库、§25 项目文档任务）。
2. **移植版 skill** — 根目录 `SKILL.md`（skill 名 **EasyEDAssistant**），
   Kilocode 合规的 skill 定义，支持双链路连接并扩充设计知识库与任务能力。

## EasyEDAssistant（SKILL.md）详细文档

> 对应根目录 `SKILL.md`（frontmatter `name: EasyEDAssistant`，
> `metadata.author: EasyEDAssistant`，当前 v0.3.1）。本节说明其组件、
> 工作流、引用的其它 SKILL 文件及其作者。

### 组件（文档结构）

| 章节 | 内容 |
|---|---|
| frontmatter | `name: EasyEDAssistant`、description、`license: MIT`、compatibility（MCP 端点 + CLI 回退）、metadata（author/version） |
| §1 连接 | JLCEDA MCP 双端点（`ws://127.0.0.1:8765/bridge/ws`、`http://127.0.0.1:7655/mcp`）+ 原有 `easyeda` CLI/daemon 链路 + 连接异常恢复 |
| §2 开始工作 | 需求澄清（→§11）→ 插件状态 → 工程基线读取 → 参数真值 |
| §3 坐标/单位/数据模型 | raw/mil、y-UP、5 raw 网格、锚点 vs bbox 中心（#105）、层/翻面、无 undo |
| §4 设计子域判据 | P0–P7 优先级总则；PCB/原理图、RF、模拟、数字、滤波器、电源子域规则；电气规范表；设计经验法则；数据手册/PDF 阅读经验 |
| §5 核心 API 操作 | 原理图 1.4 数据路径（connectivity → compose → apply）、pin-aware autoconnect、PCB 上下文/布线/铺铜、SCH↔PCB 同步、器件库与选型、验证门禁 |
| §6 设计决策目录 | 10 类 S0 决策点（叠层/接地/线宽/USB-C/自动下载/选型/单双面/焊接工艺…）与推荐默认 |
| §7 项目文档任务 | 创建许可证、生成 README、块贡献 |
| §8 验证与交付 | 五层验证（拓扑/几何/电气/呈现/保存，不可互替）+ 交付报告要求 |
| §9 已知平台限制 | 导入/泪滴/交互式布线/netLabel/截图/3D 模型/网表等承重边界 |
| §10 执行纪律 | 10 条汇总纪律（门禁、快照、连接、授权、reload、save、MCP 一致性…） |
| §11 用户需求澄清与目标明确 | 任务分类默认行为、必问清单、目标不变量化、沟通与授权纪律 |
| §12 美观/功能布局经验 | 原理图可读性、PCB 美观（分区/朝向/阵列/留白/丝印/收尾顺序）、交付美学一致性 |
| §13 变更摘要 | v0.3.1（更名 EasyEDAssistant + 移至根目录）、v0.3.0 修订记录 |

### 工作流 / 过程

1. **连接**：JLCEDA MCP（VS Code 插件）为主链路，`easyeda` CLI/daemon 为回退
   链路；两链路语义一致（同一套 `eda.*` API 映射与验证纪律）。
2. **会话门禁**：首条命令 `easyeda update --check --exit-code`；升级后新开会话。
3. **需求澄清**（§11）：按任务类型走默认行为；只问"答案会改变做法"的选项；
   把模糊需求落成可验证的目标不变量（pin→net 黄金表、skew 预算、DRC 目标）。
4. **基线读取**：`sch connectivity` / `sch list` / `pcb list --include-bbox`
   + `sheet-geometry`；写前读被改器件/引脚/网络/几何。
5. **设计执行**：按子域判据（§4）与设计决策（§6）执行；原理图走
   S0–S6（IR → Lib 几何 → compose → apply → 回读），PCB 走 P0–P10
   （放置 → 板框 → 禁布 → 丝印 → 布线门 → 布线 → 铺铜 → 标注 → 终检）。
6. **验证与保存**：分层验证（§8），`blocked`/`fail` 区分，显式 `save`
   确认 `saved:true`。
7. **收尾**（§12.2）：功能定稿 → 清 blocking → `pcb refine` →
   `pcb beautify` → 丝印整理 → 全量验证。
8. **文档任务**（§7）：按需生成 LICENSE / README（内容只来自工程回读）。

### 引用的其它 SKILL 文件与作者

| 文件 | 角色 | 作者 |
|---|---|---|
| `Sample/easyeda-agent/SKILL.md` | 上游 skill 主入口（行为规范真值，v1.4.8） | **zhoushoujianwork**（`metadata.author`，MIT；[zhoushoujianwork/easyeda-agent](https://github.com/zhoushoujianwork/easyeda-agent)） |
| `Sample/easyeda-agent/agents/openai.yaml` | 上游 agent 接口定义（display_name "EasyEDA Agent"） | zhoushoujianwork（随上游 skill 分发） |
| `Sample/easyeda-agent/references/*.md`、`*.json` | 上游参考文档与数据文件（判据原始来源） | zhoushoujianwork（随上游 skill 分发） |
| `Sample/easyeda-agent/scripts/*` | 上游辅助脚本（lint/选型/批量/测试） | zhoushoujianwork（随上游 skill 分发） |
| `Sample/easyeda-agent-skill-behavior.md` | 上游 skill 全部行为的章节化记录（本项目维护，含移植版 §23–§25 与 §25A 变更史） | 本项目（EasyEDAssistant）维护 |

## 连接方式（双链路）

EasyEDAssistant skill 同时支持两条到 EDA 引擎的链路，原有方式完整保留：

| 链路 | 端点 | 说明 |
|---|---|---|
| JLCEDA MCP（VS Code 插件） | WebSocket `ws://127.0.0.1:8765/bridge/ws` | 动作派发、心跳、窗口上下文 |
| JLCEDA MCP（VS Code 插件） | HTTP `http://127.0.0.1:7655/mcp` | MCP 工具/资源入口（Kilocode 经 `kilo.json` 接入） |
| 原有链路 | `easyeda` CLI + daemon（端口 `60832`）+ EasyEDA Agent Connector | 必须保留；MCP 端点不可用时回退 |

Kilocode 接入配置（`kilo.json`）：

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

MCP 工具与 typed CLI action 语义一致：同一套 `eda.*` API 映射、dry-run/回读/
`saved:true` 验证纪律、破坏性操作确认门控。MCP 不豁免任何验证，不改变授权范围。

## 设计知识库覆盖范围

EasyEDAssistant skill 内置的设计判据（详见根目录 `SKILL.md` 第 4 节与
行为记录 §24）：

- **PCB 布局 / 原理图绘制**：P0–P7 优先级总则、九宫格分区、模块间距、
  去耦分级、叠层与内电层 PLANE 生成顺序、手焊可达性、丝印装配可见性。
- **射频（RF）**：全层天线 keepout、50Ω/100Ω 阻抗匹配、λ/4 馈电最短化、
  地缝合过孔、巴伦镜像、低容 ESD。
- **模拟电路**：星形单点接地、割地判据（≥2 地域才拆）、模拟电源子域命名、
  敏感输入隔离距离。
- **数字电路**：晶振贴脚与守护环、未用脚处理、复位 RC、隔离屏障爬电/间隙、
  电平匹配、差分/等长命名约束。
- **滤波器**：无源 LC 公差对 fc 的影响、C0G 选型、有源反馈布局、数字接口
  共模扼流圈 + 串阻 + ESD 组合。
- **电源**：Buck 热回路定义、LDO 热耗估算、电流线宽分档、多电源域内电层策略、
  动态铺铜 vs 静态填充、netless 铺铜清理。
- **电气规范**：IPC-2221B / IPC-7351B / IPC-A-600 / IEC 62368 / UL 94 /
  RoHS / FCC Part 15 / JLCPCB 工艺能力（`fab-rules-jlcpcb.json` 基线）。
- **数据手册 PDF 阅读经验**：身份四件套锁定、参数表抄条件、典型应用基准、
  SI 前缀大小写、冲突与"未核实"处理、版本匹配、工作点取值、不靠截图推断。

## 任务能力

除 EDA 设计任务外，EasyEDAssistant skill 新增项目文档任务：

| 任务 | 说明 |
|---|---|
| 创建许可证 | 生成 `LICENSE`（默认 MIT，可选 Apache-2.0/GPL-3.0/BSD-3/CC0）；已有文件不覆盖 |
| 生成 README.md | 内容只来自工程回读（connectivity / pcb list / drc）；阶段门状态如实标注 |
| 块贡献 | 提交已验证电路到标准块库（`verification` 四项通过才能 `production_ready`） |

## 文档阅读

- **行为记录（人读）**：`Sample/easyeda-agent-skill-behavior.md` — 上游 skill
  全部行为的章节化记录，§23–§25 为移植版新增（MCP 桥接、设计规范知识库、
  文档任务），§25A 为 SKILL.md 修订历史。与 `SKILL.md` 的重叠部分为
  "精炼版 vs 完整版"关系；记录中独有内容（目录结构、任务-参考映射、环境安装、
  辅助脚本表、朝向系统、图签 keep-out 推导、关键数据文件、审计与恢复、回归
  测试）删除后将丢失，故保留。
- **skill 定义（agent 行为规范）**：根目录 `SKILL.md`（skill 名
  **EasyEDAssistant**）— 连接契约、坐标/数据模型、子域判据、API 操作速查、
  设计决策目录、验证分层与执行纪律、需求澄清与美观/功能布局经验。
- **上游参考真值**：`Sample/easyeda-agent/references/*.md` 与
  `Sample/easyeda-agent/scripts/*` — SKILL.md 中判据的原始来源；数值冲突时以
  daemon 规则代码（`pcb_rules.go` / `pcb_netclass.go` / `pcb_check*.go`）为准。

## 使用

1. 启动 JLCEDA MCP VS Code 插件（监听 `8765` / `7655`）；不可用时安装
   `easyeda` CLI/daemon 作为回退链路。
2. 在 Kilocode `kilo.json` 中启用 `jlceda` MCP server（配置见上）。
3. 会话首条命令仍为 `easyeda update --check --exit-code` 版本门禁
   （EasyEDAssistant 移植版同样适用）；升级后新开会话。
4. 按 `SKILL.md` 第 4 节判据选择设计子域；参数真值以
   `easyeda <command> --help` 与 `easyeda actions` 为准。

## 许可

本仓库文档与 EasyEDAssistant skill 定义采用 MIT 许可，见 [LICENSE](./LICENSE)。
上游 `Sample/easyeda-agent/` 样本版权归原项目
（[zhoushoujianwork/easyeda-agent](https://github.com/zhoushoujianwork/easyeda-agent)，
MIT，作者 zhoushoujianwork），见 `Sample/easyeda-agent/LICENSE`。
