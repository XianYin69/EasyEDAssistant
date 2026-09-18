# EasyEDAssistant

嘉立创EDA 助手项目：将 **easyeda-agent** skill（嘉立创 EDA 专业版自动化设计 skill）
移植为基于 **JLCEDA MCP VS Code 插件**桥接的 Kilocode skill（**EasyEDAssistant**），
并维护完整的行为记录文档。

## 目录结构

```
EasyEDAssistant/
├── README.md                                  # 本文件
├── LICENSE                                    # MIT
├── SKILL.md                                   # EasyEDAssistant skill 主干（Kilocode，版本见 SKILL.md frontmatter）
├── RULE_EDIT.md                               # skill 本体编辑规则（≤50 行、总索引+子文件、CHANGELOG、git）
├── FILE_CREATION_POLICY.md                    # 设计执行期工作区文件范围与权限
├── CHANGELOG.md                               # 变更摘要（按版本倒序）
├── stream.html                                # 流程图（draw.io 导出，README 内嵌渲染）
├── references/                                # 步骤文档：每步骤一个同名目录（总索引 + 子文件）
│   ├── 初始化部分/ … 交付与清理/                # 六步：初始化 → 处理用户需求 → 检查方案及敲定 → 原理图制作 → PCB制作 → 交付与清理
│   ├── 单步执行/                              # 非首次设计：读 ./tmp/ 上下文 → 选步骤 → 只执行该步骤 → 回写报告
│   ├── 约束部分/                              # 十三项约束（命名/格式/垃圾/记忆链/逻辑链/压缩/处罚/激励/创建范围/流程/安全/步骤门禁/运行环境不可变）
│   ├── 嘉立创EDA指令索引/                     # easyeda CLI v1.5.1 运行时指令入口（总索引 + 12 子文件）
│   ├── 电气检查/硬编码规则/                   # 子域判据与公式（电气检查与 PCB 规范同源）
│   └── lib/                                   # 维护者文档（13 份，原 SKILL.md §1–§13 正文，不参与运行时加载）
├── AGENT-PROMPT.md                            # 精简使用指引（规范回归 SKILL.md）
├── .gitignore                                 # 忽略 .kilo/ 环境注入文件与 tmp/ 运行产物等
├── agents/
│   ├── EasyEDAssistant.yaml                   # Kilocode agent 定义（权威，interface: schema）
│   └── EasyEDAssistant.md                     # 人读镜像（原 .json 可发现性清单已删）
├── scripts/
│   ├── check-links.py                         # 全树 markdown 链接扫描（悬空必须为 0；RULE_EDIT 第 6 步）
│   ├── check-progress.py                      # 步骤门禁校验：进度账本完整性 + 证据产物存在性
│   ├── progress-log.py                        # 进度账本写入（幂等追加 ./tmp/init/progress.md）
│   ├── link-probe.py                          # 桥接探测序列：MCP/daemon 探活 + 版本记录（无门禁）+ 接口漂移 compat 探测 → 选定链路 JSON
│   ├── cli_compat.py                          # CLI 能力探测库（--help 自描述防上游接口漂移；被各一键脚本 import）
│   ├── sch-verify.py                          # 原理图验证序列：gate/connectivity/list/sheet-geometry → 聚合 JSON
│   ├── pcb-gate.py                            # PCB 门禁序列：drc/check/lint/score/report/net-classes → 聚合 JSON
│   ├── visual-qa.py                           # 视觉质量与布局完整性自动评估（截图+数据双检，滚动保留 3 张）
│   ├── tool-probe.py                          # 内建工具与插件探针（生成 ./tmp/eda-tools-manifest.json）
│   ├── tool-probe-simulator.py                # 工具调用示例文档生成器
│   ├── parts-select.py                        # 选型查询（离线库已随上游清理移除，实时目录走 --online）
│   ├── bom-enrich.py                          # BOM 补 LCSC C 号（需自备 --parts 标准件库）
│   ├── net-download.py                        # 网络资源下载器（白名单 + 逃逸防护）
│   ├── net-download-policy/                   # 网络资源下载策略（总索引 + 格式白名单/格式黑名单/URL与路径防护/用法与会话纪律）
│   └── connector-src/                         # connector 源码快照封装（编辑期维护：eext-src.py verify/report/apis/fetch/eext + 政策）
└── Sample/
    ├── easyeda-agent-skill-behavior.md        # easyeda-agent skill 全部行为记录（含移植版章节）
    ├── easyeda-agent/                         # 上游样本存档（仅 README + LICENSE；
    │   ├── README.md                          #   正文已迁为 references/lib/ 维护者文档与 嘉立创EDA指令索引）
    │   └── LICENSE
    └── easyeda-agent-connector/               # eext 插件上游源码快照（tag v1.5.1 全 TS 源+清单，
        ├── .snapshot.json                     #   出处/commit/sha256 校验清单；更新检查禁用后的离线真值）
        └── extension.json · src/ · config/ · scripts/ · README.md · CHANGELOG.md · LICENSE
```

## 概述

本项目围绕上游 **easyeda-agent** skill（Codex 使用，MIT 许可，上游项目：
[zhoushoujianwork/easyeda-agent](https://github.com/zhoushoujianwork/easyeda-agent)，
其正文已迁入 `references/lib/` 与 `references/嘉立创EDA指令索引/`，`Sample/easyeda-agent/` 仅存 README + LICENSE 存档）
构建两层内容：

1. **行为记录** — `Sample/easyeda-agent-skill-behavior.md` 记录该 skill 的全部行为：
   本机环境自检、原理图 1.4 数据路径（connectivity IR → Lib 几何 → compose →
   sch apply → 回读对账）、设计流程 S0–S6 / P0–P10、执行与验证约束、器件选型、
   制造规则、朝向系统、图纸 keep-out 推导，以及移植版新增章节
   （§23 JLCEDA MCP 桥接、§24 现代电子产品设计规范知识库、§25 项目文档任务）。
2. **移植版 skill** — 根目录 `SKILL.md`（skill 名 **EasyEDAssistant**），
   Kilocode 合规的 skill 定义，支持双链路连接并扩充设计知识库与任务能力。

### 流程图综述

<iframe src="./stream.html" title="EasyEDAssistant 流程图" style="width:100%; height:40vh; border:1px solid #ddd"></iframe>

> 交互式流程图源文件为同目录 [`stream.html`](./stream.html)（draw.io 导出，依赖 diagrams.net viewer 脚本渲染）。若当前渲染环境屏蔽内联框架（如 GitHub 网页版会过滤 `<iframe>`），请点击上方链接直接打开。

> 主要流程：用户输入请求 → 识别用户意图 → 判断首次设计 → 是则走「电路板设计标准设计流程」六步（初始化 → 处理用户需求 → 检查方案及敲定 → 原理图制作 → PCB制作 → 交付与清理），否则走「单步执行」（读取 ./tmp/ 上下文 → 询问并选择步骤 → 只执行该步骤 → 回写与报告）。

## EasyEDAssistant（SKILL.md）详细文档

> 对应根目录 `SKILL.md`（frontmatter `name: EasyEDAssistant`，
> `metadata.author` + `metadata.version` 为版本唯一真值，本文件不复制版本号），主干 + 按需加载 references/。本节说明其组件、
> 工作流、引用的其它文件及其作者。

### 组件（文档结构）

SKILL.md 主干只含流程入口、路由与约束总则（§1–§5）；详细内容按触发条件存放在 `references/` 与 `CHANGELOG.md`。

| 内容 | 位置 |
|---|---|
| 流程入口、路由、执行纪律 | `SKILL.md` 主干内联 |
| 各步骤流程（六步：初始化 → 处理用户需求 → 检查方案及敲定 → 原理图制作 → PCB制作 → 交付与清理） | `references/<步骤>/`（总索引 + 子文件） |
| 非首次设计的续跑与单步执行 | `references/单步执行/`（读取上下文、选择步骤、执行与回写） |
| 步骤级细则（桥接联通性测试、绘制原理图、绘制 PCB、检查步骤等） | 同上，各步骤目录内的同名子文件 |
| 坐标与数据模型、官方文档与 GUI 映射 | `references/坐标与数据模型/`、`references/官方文档映射/` |
| 约束（命名、格式、清理、证据链、处置、逐步执行门禁、运行环境不可变等十三项） | `references/约束部分/` |
| 原 SKILL.md §1–§13 正文与子域判据（维护者参考，不参与运行时加载） | `references/lib/`（12 份 md + 1 份 json） |
| 变更历史 | `CHANGELOG.md` |

### 工作流 / 过程

1. **连接**：JLCEDA MCP（VS Code 插件）与 `easyeda` CLI/daemon 互为**替代链路**
   （不是级联备用）：先测 MCP `7655`，可达再测 `60832`，双通优先 CLI/daemon，
   一旦选定全程使用，重试最多 3 轮后转用户；两链路语义一致（同一套 `eda.*` API 映射与验证纪律）。
   本机组件版本（`easyeda health` 的 `versionGate`）**只记录进报告、不作门禁**（更新检查全面禁用，用户指令 2026-09-18）；行为异常对照 connector 源码快照离线排查（`scripts/connector-src/`）；**不查最新发行版**。
2. **会话门禁**：首条命令 `python <SKILL_DIR>/scripts/link-probe.py`（`<SKILL_DIR>`=skill 安装根；只探链路 + compat 接口漂移探测，零联网、零版本判定）；组件升级由用户自行完成后新开会话。
3. **需求澄清**（§11）：按任务类型走默认行为；只问"答案会改变做法"的选项；
   把模糊需求落成可验证的目标不变量（pin→net 黄金表、skew 预算、DRC 目标）。
   执行中遇强制/条件中断点（正本 `references/lib/discipline-checkpoints.md` §11.5）按 CHECKPOINT 协议暂停等用户确认。
4. **基线读取**：`sch connectivity` / `sch list` / `pcb list --include-bbox`
   + `sheet-geometry`；写前读被改器件/引脚/网络/几何。
5. **工具探针**：**Agent 自动执行** `python <SKILL_DIR>/scripts/tool-probe.py --project <name>`，生成
   `./tmp/eda-tools-manifest.json` 与 `eda-tools-guide.md`（CLI 不可达时 exit 2，清单标注未经运行时验证）；
   在 P1/P6/P8/P10 等关键步骤前查阅清单，按需触发条件中断点（`references/lib/discipline-checkpoints.md` §11.5）询问用户是否启用专用插件。
6. **设计执行**：按子域判据（[`references/电气检查/硬编码规则/硬编码规则总览.md`](references/电气检查/硬编码规则/硬编码规则总览.md)，维护者全文见 `references/lib/design-rules.md`）与用户已拍板的决策点执行；原理图走 S0–S6
   （IR → Lib 几何 → compose → apply + 动态截图），PCB 走 P0–P10
   （放置 → 板框 → 禁布 → 丝印 → 布线门 → 布线 → 铺铜 → 标注 → 终检）；
   关键步骤后截图（`./tmp/snapshots/`），SHA256 校验 stale，
   旧图自动清理。
7. **验证与保存**：分层验证（§8），`blocked`/`fail` 区分，显式 `save`
   确认 `saved:true`。
8. **收尾与交付**（见 `references/交付与清理/`）：功能定稿 → 清 blocking → `pcb refine` →
   `pcb beautify` → 丝印整理 → 全量验证 → 出技术手册/功能手册与交付报告（用户确认）
   → 清理 `./tmp/`（先交付后清理，blocked/fail 如实列出）。
9. **文档任务**（随交付与清理生成）：按需生成 LICENSE / README（内容只来自工程回读）。

### 引用的其它 SKILL 文件与作者

| 文件 | 角色 | 作者 |
|---|---|---|
| `agents/EasyEDAssistant.yaml` | Kilocode agent 定义（权威，interface: schema） | 本项目（EasyEDAssistant）维护 |
| `references/*.md`、`*.json` | 正本/维护者参考文件（判据原始来源） | 本项目（EasyEDAssistant）维护 |
| `scripts/`（根） | 运行时辅助脚本：门禁/账本类 check-links、check-progress、progress-log、link-probe、sch-verify、pcb-gate；视觉/探针类 visual-qa、tool-probe、tool-probe-simulator；选型与下载类 parts-select、bom-enrich、net-download；`connector-src/`＝connector 源码快照封装（编辑期维护）、`net-download-policy/`＝下载政策 | 本项目（EasyEDAssistant）维护（上游同名脚本已迁入并按挂接判据裁剪；重复命令序列已封装为一键脚本） |
| `scripts/visual-qa.py` | 视觉质量与布局完整性自动评估（API 截图 + 数据驱动交叉评估 + 动态截图生命周期管理，§8.3） | 本项目（EasyEDAssistant）维护 |
| `scripts/tool-probe.py` / `tool-probe-simulator.py` | 嘉立创 EDA 内建工具与已安装插件探针（生成 `./tmp/eda-tools-manifest.json` 与 `eda-tools-guide.md`） | 本项目（EasyEDAssistant）维护 |
| `scripts/net-download.py` + `scripts/net-download-policy/`（总索引 + 4 子文件） | 网络资源下载器（格式白/黑名单 + 路径逃逸防护 + `index.json` 审计）与配套策略文档 | 本项目（EasyEDAssistant）维护 |
| `references/lib/pcb-design-spec.md` | PCB 设计规范与 D1–D20 必答清单（PCB 阶段前向用户核对，落 `./tmp/design/<project>-pcb-spec.md`；流程侧挂接见 `references/PCB绘制/用户PCB配置文件/`） | 本项目（EasyEDAssistant）维护 |
| `AGENT-PROMPT.md` | 精简使用指引（触发入口 + one-liner default_prompt；规范回归 SKILL.md） | 本项目（EasyEDAssistant）维护 |
| `Sample/easyeda-agent-skill-behavior.md` | 上游 skill 全部行为的章节化记录（本项目维护，含移植版 §23–§25 与 §25A 变更史） | 本项目（EasyEDAssistant）维护 |

## 连接方式（双链路）

EasyEDAssistant skill 同时支持两条到 EDA 引擎的链路，原有方式完整保留：

| 链路 | 端点 | 说明 |
|---|---|---|
| JLCEDA MCP（VS Code 插件） | WebSocket `ws://127.0.0.1:8765/bridge/ws` | 动作派发、心跳、窗口上下文 |
| JLCEDA MCP（VS Code 插件） | HTTP `http://127.0.0.1:7655/mcp` | MCP 工具/资源入口（Kilocode 经 `kilo.json` 接入） |
| 原有链路 | `easyeda` CLI + daemon（端口 `60832`）+ EasyEDA Agent Connector | 与 MCP 互为替代（非级联备用）；MCP 可达仍再探 `60832`，双通优先 CLI/daemon；一旦选定全程使用 |

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

## 安装扩展插件（easyeda-agent-connector，用户手工动作）

**版本钉定（本项目只基于此版本开发）**：connector 钉定为本 skill 源码快照版本（当前 **v1.5.1**，
权威值见 `Sample/easyeda-agent-connector/.snapshot.json` 的 `connector_version`）。**所有自动更新一律关闭**——
不使用/关闭插件市场的「原地自动更新」，daemon 保持 `--auto-update-skill=false`，EDA 升级弹窗不响应；
**若发现任何新版本（含市场自动升级），处置方向是删除新版、回到钉定版**，而不是升级适配。
会话首条命令 `link-probe.py` 会做钉定比对（`version_gate.pin`），不符即 WARN 并给出回退指引。

CLI/daemon 链路依赖 EDA 内的 **EDA Agent Connector** 插件（link-probe 探测 60832 不通、
或 pin/mismatch 告警、compat 报告 connector 异常时需要安装/回退）。**插件装卸一律由用户本人完成**——设计执行期
Agent 禁下载/安装/卸载 `.eext`（运行环境不可变 L3），且 Agent 检测到偏离钉定版本必须如实报告：

**取钉定包（推荐：与源码快照同 tag，带校验）**

```bash
# 用户在终端运行（维护窗口，非设计会话内）；--tag 缺省即取快照钉定版本：
python <SKILL_DIR>/scripts/connector-src/eext-src.py eext --out <你的下载目录>
```

脚本下载钉定 tag 的 `easyeda-agent-connector.eext` 并按 release `checksums.txt` 校验 sha256，
随后打印导入步骤：① EasyEDA Pro 扩展管理器**卸载现装版本（含更高版本）**（平台按 UUID 去重）→ ② 导入钉定 `.eext`
→ ③ 完全退出并重开 EasyEDA（仅重导不保证已打开页面执行新代码）→ ④ 新会话跑 `link-probe` 确认链路且 `pin.mismatch=false`。
产物是工具输出物，**不要放回 skill 仓库**。

**替代渠道（不推荐）**：立创插件市场 <https://jlc-ext.com/item/zhoushoujian/easyeda-agent-connector>
支持原地自动更新——**与版本钉定冲突**；若因故从市场安装，装后必须关闭自动更新并确认版本号＝钉定版。
安装渠道机制正本见 [`references/lib/environment-setup.md`](references/lib/environment-setup.md)（其自动更新描述服从此钉定政策）；
源码级行为排查见 `scripts/connector-src/connector-src.md`（本地快照，零联网）。

## 设计知识库覆盖范围

EasyEDAssistant skill 内置的设计判据（详见 [`references/电气检查/硬编码规则/硬编码规则总览.md`](references/电气检查/硬编码规则/硬编码规则总览.md)，维护者全文见 `references/lib/design-rules.md`）与
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
   设计决策目录、验证分层（§8.3 视觉质量自动评估 + 动态截图生命周期）、
   执行纪律、需求澄清与美观/功能布局经验。v0.10.0 起为入口主干，详细内容按触发条件存放于 `references/` 与 `CHANGELOG.md`。
- **智能体提示词**：根目录 `AGENT-PROMPT.md` — 精简使用指引（对应 SKILL v0.12.x）：
  仅保留触发入口与 one-liner `default_prompt`；完整规范（会话纪律、
   需求澄清、设计执行、PDF 阅读、验证分层、文档任务、中断机制等）回归
   `SKILL.md` 主干（详细内容在 `references/`）由 Kilocode 自动注入，不再复制到提示词层。
  `SKILL.md` 引用的 `Sample/easyeda-agent/**` 与 `scripts/*.py` 是运行时
  经验库与设计时调用的脚本，按 `SKILL.md` 指引读取与执行。
- **视觉质量评估脚本**：`scripts/visual-qa.py` — API 截图 + 数据驱动检查
   交叉评估组件间距/走线间距/整齐度（§8.3），含动态截图生命周期管理
   （每步截图、stale 识别、旧图清理）。
- **判据原始来源**：`references/lib/*.md`（上游 SKILL 正文迁移而来的维护者文档）与
  `Sample/easyeda-agent-skill-behavior.md`（行为记录）；数值冲突时以
  daemon 规则代码（`pcb_rules.go` / `pcb_netclass.go` / `pcb_check*.go`）与 JLC 官网为准。

## 使用

1. 启动 JLCEDA MCP VS Code 插件（监听 `8765` / `7655`）；MCP 不通时安装
   `easyeda` CLI/daemon 作为替代链路（选定后全程使用，不重复探测）。
2. 在 Kilocode `kilo.json` 中启用 `jlceda` MCP server（配置见上）。
 3. 会话首条命令为 `python <SKILL_DIR>/scripts/link-probe.py`（只探链路与 compat 接口漂移；
    更新检查/版本判定已全面禁用）；组件升级由用户自行完成后新开会话。
4. 按 [`references/电气检查/硬编码规则/硬编码规则总览.md`](references/电气检查/硬编码规则/硬编码规则总览.md) 选择设计子域判据（维护者全文见 `references/lib/design-rules.md`）；参数真值以
   `easyeda <command> --help` 与 `easyeda actions` 为准。

## 许可

本仓库文档与 EasyEDAssistant skill 定义采用 MIT 许可，见 [LICENSE](./LICENSE)。
上游 `Sample/easyeda-agent/` 样本与 `Sample/easyeda-agent-connector/` 插件源码快照版权归原项目
（[zhoushoujianwork/easyeda-agent](https://github.com/zhoushoujianwork/easyeda-agent)，
MIT，作者 zhoushoujianwork），见各自 `LICENSE`；connector 快照的 tag/commit/文件哈希见
`Sample/easyeda-agent-connector/.snapshot.json`。
