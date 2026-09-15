---
name: EasyEDAssistant
description: "基于 JLCEDA MCP VS Code 插件桥接操作嘉立创 EDA（EasyEDA）的移植版电路设计 skill：原理图/PCB/射频/模拟/数字/滤波器/电源设计与检查。支持 MCP 与原有 CLI/daemon 双链路，内置电气规范、数据手册 PDF 阅读经验与项目文档任务（许可证/README）。SKILL.md 为唯一入口主干；会话初始化见 references/初始化部分/，其余详细文档由维护者索引 tmp/project-files-overview.md 管理。"
license: MIT
compatibility: "Requires JLCEDA MCP VS Code plugin running locally (ws://127.0.0.1:8765/bridge/ws + http://127.0.0.1:7655/mcp). Fallback: easyeda CLI/daemon/Agent Connector. Offline design planning needs no editor."
metadata:
  author: EasyEDAssistant
  version: "0.10.1"
---

# EasyEDAssistant 设计 Skill（主干）

用 JLCEDA MCP VS Code 插件桥接操作嘉立创 EDA（EasyEDA 专业版）：原理图绘制、
PCB 布局布线、射频/模拟/数字/滤波器/电源设计、检查与制造文件导出。
知识基线见同仓 `Sample/easyeda-agent-skill-behavior.md`（24–25 节为移植版专属判据）。
本 skill 是移植版行为规范；API 操作与数值判据以 `Sample/easyeda-agent/references`
与 `Sample/easyeda-agent/scripts` 为真值来源，冲突时以 daemon 规则代码为准。

> **项目级规范引用**（Agent 与贡献者必读）：
> - `CONTRIBUTING.md` — 贡献指南（开发环境、代码规范、提交格式、审查流程、版本管理）。
> - `FILE_CREATION_POLICY.md` — 新建文件/文件夹使用规范（Kilo Model 安全合规：
>   允许/禁止的文件类型、命名规范、操作流程、安全要求）。全体会话须遵守。

## 0. 主干机制（先读本节）

- **progressive disclosure 契约**：本文件只含入口判定、路由与 always-on 纪律；
  §1–§14 详细文档已移出主干，由维护者按框图重建并索引于 tmp/project-files-overview.md；CHANGELOG.md 保留版本史。**原章节编号不变**。
- **铁律**：进入路由表（§2）所列任一操作前，必须先完整读取路由表所列的主题 reference 文件；
  全文中出现的 `§N`/`§N.N` 引用一律指原文章节编号，其详细文档正本经 tmp/project-files-overview.md 索引查取（§10 在本文件）。
- SKILL.md 与 reference 文件如有出入，以 reference 文件（迁移原文）为准；数值判据
  最终以 daemon 规则代码（`pcb_rules.go` 等）为准。

## 1. 连接速览（双链路，原文 §1）

| 通道 | 地址 | 用途 |
|---|---|---|
| MCP HTTP | `http://127.0.0.1:7655/mcp` | MCP 工具/资源/提示服务入口 |
| MCP WebSocket | `ws://127.0.0.1:8765/bridge/ws` | 动作派发、心跳、窗口上下文 |
| daemon | 端口 `60832` | `easyeda` CLI + EasyEDA Agent Connector 回退 |

- **链路选择**：MCP 与 CLI/daemon 是**替代关系非级联备用**；先 `7655` 后 `60832`；
  检到可用链路即全程使用、不重试另一条；两端点同属 JLCEDA 插件。
- **cwd 确认**：端口连通后向用户索要 EDA 工程绝对路径并与 Kilocode `workspace root`
  比对，以用户指定路径为运行时 `cwd`（运行产物 `./tmp/` 根）；不一致以用户为准。
- **版本门禁**：CLI/daemon 链路会话第一条命令 `easyeda update --check --exit-code`，
  非 0 停止并报告版本差异，升级后新开会话从头开始（§1.2）。

## 2. Reference 路由表

| 触发条件 | 文件 |
|---|---|
| 会话开始的工作区初始化：向用户询问工作区路径 → 在工作区建立 tmp 文件夹 → 建立初始化文件（仅路径确认与工作区准备，不含 EDA 连接/版本门禁/基线读取） | references/初始化部分/初始化部分.md |
| 版本变更历史 | CHANGELOG.md |

> §1–§9、§11–§13 的 11 份详细文档已迁出主干，按维护者框图存放于
> `references/lib/`，由 `tmp/project-files-overview.md` 索引，SKILL.md 不再
> 逐条路由；需要细则时经该索引文件查取。
> §10 执行纪律在本主干内逐字保留（原编号不变）。

## 3. 工作主线（12 步一行式，原文 §2）

0. 先澄清需求与目标再动手（§11）；已有确认/授权沿用，执行中遇强制/条件中断点按 §11.5 暂停。
1. 确认插件状态：`8765`/`7655` 端点可达；不可达走 daemon 链路。
2. 读目标工程基线：`easyeda health` / `doc ls` / `sch connectivity --all-pages` / `sch list --include-pins --bbox --wires` / `sheet-geometry`。
3. 写前读被改器件、引脚、网络与几何；每个绘图引脚恰好对应 一个网络 / `noConnected:true` / `connectionState:"unconnected"`，三者互斥。
4. 按任务选子域判据（§4），只加载相关参考；参数真值以 `easyeda <domain> <command> --help` 与 `easyeda actions` 为准。
5. 临时 JSON、计划与回读结果放入工作区 `./tmp/`（非 skill 目录），按 §8.4 子目录分类，保留原始快照、在副本中设计。
6. 工具与插件探针：自动运行 `python3 scripts/tool-probe.py` 生成 `./tmp/eda-tools-manifest.json` 与 `eda-tools-guide.md`。
7. 基线截图：读工程基线后自动保存截图到 `./tmp/baseline/`（按时间戳命名），作为后续差异对比参考。
8. P1/P6/P8/P10 前自动跑脚本（tool-probe/tool-probe-simulator），每关键步后自动 `visual-qa.py` 视觉评估。
9. 动态截图：每关键步后立即截图（`sch export-image`/`pcb snapshot --previous-sha256`），SHA256 防 stale，保留最近 3 张，存 `./tmp/snapshots/`。
10. 交付工件落位与清理：产物全落 `./tmp/` 子目录；工作结束先在工作区根目录生成技术/功能手册（§7.8）再清 tmp（§8.4）。
11. 主动学习与外部资源（§13）：信息缺口用 `websearch`/`webfetch` 检索落 `./tmp/learning/`，下载用 `scripts/net-download.py` 落 `./tmp/downloads/`。

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
12. **Agent 必须自动调用 Python 辅助脚本**：进入特定步骤前，自动运行 `scripts/tool-probe.py`
    生成工具清单；在 PCB 铺铜/泪滴/拼板/导出等阶段前，查阅清单并触发 §11.5 条件中断点
    询问用户是否启用专用插件或工具；在关键步骤后，自动调用 `scripts/visual-qa.py` 进行视觉验证。
13. 运行产物只写工作区 `./tmp/`（§8.4 目录契约），工作结束先交付后清理，tmp 内容不得入库。
14. 交付前在工作区根目录生成技术手册与功能手册（§7.8），再清理 `./tmp/`（§8.4）；
    蓝图/框图/可行性结论（§7.5–§7.7）未拍板不进入绘制与放置阶段。
15. **PCB 设计基线（§13.3）**：进入 PCB 阶段（P0）前逐项核对
    `Sample/easyeda-agent/references/pcb-design-spec.md` §2 D1–D20 清单，
    答复落 `./tmp/design/<project>-pcb-spec.md`；D1 板框 / D2 安装孔 /
    D8 关键接口未定即触发 §11.5 P0 强制中断，不放行放置。
16. **主动学习（§13.1/§13.2）**：信息缺口主动用浏览器工具在 博客园 /
    Stack Overflow / 知乎 / 官方 wiki 检索并落 `./tmp/learning/`；下载
    外部资源用 `scripts/net-download.py`（格式白名单见
    `scripts/net-download-policy.md`），拒绝可执行/脚本/归档，输出根强制
    工作区 `./tmp/downloads/`。
17. 进入路由表所列操作前，先完整读取对应 references/ 文件；主干摘要与 reference 原文冲突时以 reference 为准。

## 5. 中断机制最小判据（原文 §11.5）

- **强制中断**：决策不可单方面定或后果不可逆（S0/`compose --replace` 清页/破坏性 `pcb clear`）须暂停；**条件中断**：信息缺失会改变设计或超授权（选型缺参数/工艺未定/门禁 `blocked`）命中才中断、齐备或已授权静默通过。
- **不中断**：guardrail（save/reload/PLANE 顺序/天线 keepout 全层）、已授权增量执行、纯读取与验证。

```
[CHECKPOINT <阶段> | <类型>]
快照：<./tmp/snapshots/step-N-*.png> + <fresh/stale>
背景：<≤3 句，含证据>
决策点：<选项+推荐默认> → 后果
影响范围：<只动哪些模块/页面/网络；不动部分列回归对照>
等待：超时/无答复保持暂停态，不自动推进
```

- 超时/无答复不自动推进，保持暂停态。
- `blocked`（检查没运行）≠ `fail`（设计不合格），不靠关检查取得通过。

## 6. tmp/ 产物与保存硬规

- 运行产物只写工作区 `./tmp/`（非 skill 目录），按 §8.4 子目录契约分类，`tmp/` 已在 `.gitignore`、不得入库。
- 工作结束先按 §7.8 在工作区根目录生成技术/功能手册并出交付报告，再删除 `./tmp/` 全部产物。
- 写操作显式 `save` 并确认 `saved:true`；autosave 仅兜底。
- PCB mutation（rip-up/route/delete/via/track/pour）后遇 `STALE_READ` 先 `doc reload` 再重读；铜形变化后 `pour-rebuild`。

## 7. 变更摘要

### v0.10.1（2026-09-15）

- **路由表收窄**：SKILL.md 仅索引 `references/初始化部分/初始化部分.md`（会话初始化：询问工作区路径→建立 tmp→建立初始化文件）与 `CHANGELOG.md`。
- 11 份详细文档（§1–§9、§11–§13）从 `references/` 根迁至维护者详细文档库，经维护者索引 `tmp/project-files-overview.md` 查取，主干不再逐条路由；全文 §N 引用含义不变。
- frontmatter 版本 0.10.0 → 0.10.1。

### v0.10.0（2026-09-15）

- **SKILL.md 主干化重构**：全文 1609 行拆分为"主干 + 按需加载 references/"。§1–§9、§11–§13 逐字迁入 `references/` 下 11 个 reference 文件（原章节编号不变），§14 迁至 `CHANGELOG.md`；§10 执行纪律留主干并新增第 17 条（路由前先读 reference）。
- frontmatter 版本 0.9.0 → 0.10.0；`FILE_CREATION_POLICY.md` v1.1 → v1.2（新增 `references/` 目录条款）；README 章节表与目录树同步。

完整历史见 CHANGELOG.md。
