# EasyEDAssistant

易EDA 助手项目：将 **easyeda-agent** skill（嘉立创 EDA 专业版自动化设计 skill）
移植为基于 **JLCEDA MCP VS Code 插件**桥接的 Kilocode skill，并维护完整的行为
记录文档。

## 目录结构

```
EasyEDAssistant/
├── README.md                                  # 本文件
├── LICENSE                                    # MIT
├── easyeda-agent-skill-behavior.md            # easyeda-agent skill 全部行为记录（含移植版章节）
├── .kilocode/skills/jlceda-mcp-easyeda/
│   └── SKILL.md                               # 移植版 Kilocode skill 定义
└── Sample/easyeda-agent/                      # 参考样本（上游 Codex skill 原样）
    ├── SKILL.md                               # 上游 skill 主入口（行为规范）
    ├── agents/openai.yaml                     # agent 接口定义
    ├── references/                            # 参考文档与数据文件
    │   ├── schematic*.md  pcb*.md            # 原理图 / PCB 操作参考
    │   ├── design-flow.md  design-decisions.md  # 设计流程与决策目录
    │   ├── part-selection.md                  # 立创/JLC 选型
    │   ├── standard-parts.json                # 标准器件库（LCSC C 号 + deviceUuid）
    │   ├── symbol-pins.json                   # 实测符号引脚
    │   ├── orientation.json                   # 朝向单一真源
    │   ├── fab-rules-jlcpcb.json              # JLCPCB 制造规则基线
    │   ├── sheet-templates.json               # 图纸/图签 keep-out 比例表
    │   └── ...
    └── scripts/                               # 辅助脚本（lint / 选型 / 批量操作 / 测试）
```

## 概述

本项目围绕 `Sample/easyeda-agent/` 目录下的上游 skill（Codex 使用，MIT 许可，
上游项目：[zhoushoujianwork/easyeda-agent](https://github.com/zhoushoujianwork/easyeda-agent)）
构建两层内容：

1. **行为记录** — `easyeda-agent-skill-behavior.md` 记录该 skill 的全部行为：
   会话版本门禁、原理图 1.4 数据路径（connectivity IR → Lib 几何 → compose →
   sch apply → 回读对账）、设计流程 S0–S6 / P0–P10、执行与验证约束、器件选型、
   制造规则、朝向系统、图纸 keep-out 推导，以及移植版新增章节
   （§23 JLCEDA MCP 桥接、§24 现代电子产品设计规范知识库、§25 项目文档任务）。
2. **移植版 skill** — `.kilocode/skills/jlceda-mcp-easyeda/SKILL.md`，
   Kilocode 合规的 skill 定义，支持双链路连接并扩充设计知识库与任务能力。

## 连接方式（双链路）

移植版 skill 同时支持两条到 EDA 引擎的链路，原有方式完整保留：

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

skill 内置的设计判据（详见 SKILL.md 第 4 节与行为记录 §24）：

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

除 EDA 设计任务外，移植版 skill 新增项目文档任务：

| 任务 | 说明 |
|---|---|
| 创建许可证 | 生成 `LICENSE`（默认 MIT，可选 Apache-2.0/GPL-3.0/BSD-3/CC0）；已有文件不覆盖 |
| 生成 README.md | 内容只来自工程回读（connectivity / pcb list / drc）；阶段门状态如实标注 |
| 块贡献 | 提交已验证电路到标准块库（`verification` 四项通过才能 `production_ready`） |

## 文档阅读

- **行为记录（人读）**：`easyeda-agent-skill-behavior.md` — 上游 skill 全部行为
  的章节化记录，§23–§25 为移植版新增（MCP 桥接、设计规范知识库、文档任务）。
- **skill 定义（agent 行为规范）**：`.kilocode/skills/jlceda-mcp-easyeda/SKILL.md`
  — 连接契约、坐标/数据模型、子域判据、API 操作速查、设计决策目录、验证分层
  与执行纪律。
- **上游参考真值**：`Sample/easyeda-agent/references/*.md` 与
  `Sample/easyeda-agent/scripts/*` — SKILL.md 中判据的原始来源；数值冲突时以
  daemon 规则代码（`pcb_rules.go` / `pcb_netclass.go` / `pcb_check*.go`）为准。

## 使用

1. 启动 JLCEDA MCP VS Code 插件（监听 `8765` / `7655`）；不可用时安装
   `easyeda` CLI/daemon 作为回退链路。
2. 在 Kilocode `kilo.json` 中启用 `jlceda` MCP server（配置见上）。
3. 会话首条命令仍为 `easyeda update --check --exit-code` 版本门禁
   （移植版同样适用）；升级后新开会话。
4. 按 SKILL.md 第 4 节任务表选择设计子域判据；参数真值以
   `easyeda <command> --help` 与 `easyeda actions` 为准。

## 许可

本仓库文档与 skill 定义采用 MIT 许可，见 [LICENSE](./LICENSE)。
上游 `Sample/easyeda-agent/` 样本版权归原项目
（[zhoushoujianwork/easyeda-agent](https://github.com/zhoushoujianwork/easyeda-agent)，
MIT），见 `Sample/easyeda-agent/LICENSE`。
