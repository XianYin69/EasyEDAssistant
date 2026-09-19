---
name: EasyEDAssistant
description: "基于 JLCEDA MCP/CLI 双链路操作嘉立创 EDA 的电路设计 skill：原理图/PCB/射频/模拟/数字/滤波器/电源设计与检查。"
license: MIT
metadata:
  author: EasyEDAssistant
  version: "0.12.31"
---

# EasyEDAssistant 设计 Skill（主干）

## 1. 流程入口（固定）

0. **逐步执行铁律（最高优先级）**：标准流程六步必须**按序逐步**执行，**禁止跳步、禁止合并步骤、禁止跳过子步骤**；
   每步完成判据未满足、且未在 `./tmp/init/progress.md` 留下「步骤名 + 时间 + 证据（命令 / 产物路径 / 结果）」账目前，
   **不得进入下一步**；**绘制期每落位一个器件必须当次产出截图产物，无新截图即该件未完成、禁止落位下一个**。
   细则见 [`references/约束部分/步骤门禁/步骤门禁.md`](references/约束部分/步骤门禁/步骤门禁.md)；账本校验 `python <SKILL_DIR>/scripts/check-progress.py`。
1. **识别用户请求**：判断用户意图与目标。
2. **运行环境不可变（与铁律同级）**：设计执行期 skill 本体只读——禁 `easyeda update`/`skill sync`/`skill status`，启动 daemon 必带 `easyeda daemon start --auto-update-skill=false`；禁下载或安装任何可执行体与 EDA 插件（含 `.eext`）；**所有检查更新/版本对齐步骤已禁用**（用户指令 2026-09-18：既不联网查 latest，本机 versionGate 也只记录不判定；**connector 版本钉定**＝只基于快照版本开发，发现新版删除回退钉定包、禁一切自动更新含市场原地更新，link-probe `pin.mismatch` 告警时报告并指引用户经 `scripts/connector-src/eext-src.py eext` 维护窗口回退，Agent 不代卸/代装），会话自检只跑 `python <SKILL_DIR>/scripts/link-probe.py`（链路探活 + compat 接口漂移探测，零联网；漂移只 WARN 并如实报告，脚本按 cli_compat 自适应，接口行为差异对照 connector 源码快照 `python <SKILL_DIR>/scripts/connector-src/eext-src.py report` 离线排查）。细则见 [`references/约束部分/运行环境不可变/运行环境不可变.md`](references/约束部分/运行环境不可变/运行环境不可变.md)。**唯一例外方向**：运行结果与 skill 承诺分歧时，只准在工作区 `./tmp/divergence/` 产出修复草稿四件套（错误说明/分歧记录/修复提示词/临时绕行脚本）移交维护窗口，skill 一字不可改（[`references/处理设计问题/分歧修复稿/分歧修复稿.md`](references/处理设计问题/分歧修复稿/分歧修复稿.md)）。
3. **判断是否为第一次设计**：
   - **是** → 执行「电路板设计标准设计流程」（见 §2）。
   - **否** → 询问用户需要执行哪一个步骤；先读取 `./tmp/` 下的上下文文件，再执行对应步骤（见 §3）。

## 2. 电路板设计标准设计流程

> 详见 [`references/电路设计标准设计流程/电路设计标准设计流程.md`](references/电路设计标准设计流程/电路设计标准设计流程.md)。
> 步骤：初始化部分 → 处理用户需求 → 检查方案及敲定 → 原理图制作 → PCB制作 → 交付与清理（按 §1 铁律逐步执行，每步留证后方可推进）。
> **走线/布线方法钉定（原理图与 PCB 同一套）**：弃用一切迷宫/盲画式自动走线（PCB `pcb autoroute`/`export-dsn`/`import-autoroute` 禁调用；原理图禁不经演算的盲画多点线），改用「网络标签-端口 + 向量-节点 + 干涉演算（PCB 落笔前 `route-check.py`；原理图画前推演+画后 `bridge-check`/`check` 即查）+ 硬编码档位」——正本 [`references/PCB绘制/干涉布线/干涉布线.md`](references/PCB绘制/干涉布线/干涉布线.md)、[`references/绘制原理图/干涉路径/干涉路径.md`](references/绘制原理图/干涉路径/干涉路径.md)；丝印支持用户板型号/版权/功能指引三类（[`references/PCB绘制/丝印标注/丝印标注.md`](references/PCB绘制/丝印标注/丝印标注.md)）。
> **放置方法钉定（与走线同源）**：放置是 **用户需求驱动**——未完成用户 PCB 配置文件（D1–D20+R1–R5）全部拍板、基线落盘 `./tmp/design/<工程>-pcb-spec.md` 前 **不得进入放置阶段**；进放置前**必须先问排布意图**（分区/固定件/信号流/热与 RF/阵列偏好，落盘 `./tmp/design/<工程>-layout-intent.md`），再用 `scripts/layout-calc.py` 按答复算出板边距/件间距/分区矩形并三行留痕；`pcb align`/`distribute`/`auto-place`/`refine`/`outline-fit`/`silk-align`/`silk-set` 仅作 **需求已定后的规整工具**（阵列对齐/卫星收敛/收口），不得无依据重排用户手摆件（手摆＝P0 immovable，先锁定快照再执行）；四档顺序（T1 安装孔→T2 板边接口→T3 主芯片→T4 卫星）逐件按意图落位，每步 `pcb list --include-pads` 对账，**走线拐角默认 45°，直角除 R1 指定圆弧档外禁止**。正本 [`references/约束部分/布局计算纪律/布局计算纪律.md`](references/约束部分/布局计算纪律/布局计算纪律.md)。

## 3. 询问步骤 + 读取 ./tmp/ + 执行对应步骤

> 详见 [`references/单步执行/单步执行.md`](references/单步执行/单步执行.md)：读取 `./tmp/` 上下文 → 列出可执行步骤并询问用户 → 只执行被选步骤 → 回写上下文与三段式报告。读中间工件一律先读 digest 摘要（判定字段+计数+指针，约束·压缩机制 #9/#10），raw 全文仅在深挖证据时读取。

## 4. 文档地图

> 全量路由见 [`references/电路设计标准设计流程/电路设计标准设计流程.md`](references/电路设计标准设计流程/电路设计标准设计流程.md)（六步 + 子步 + 运行时指令速查）；约束见 §5；重复命令序列已封装为一键脚本——`scripts/link-probe.py`（桥接探测+门禁）、`scripts/sch-verify.py`（原理图验证）、`scripts/pcb-gate.py`（PCB 门禁）、`scripts/route-check.py`（人工向量段落笔前干涉演算）、`scripts/layout-calc.py`（布局/边距/分区计算）、`scripts/calc-scientific.py` / `calc-electrical.py` / `calc-design.py`（科学/电气/设计三件计算器——数值必演算留痕，见约束·计算纪律）、`scripts/progress-log.py`（账本写入）；**运行时一律以 `python <SKILL_DIR>/scripts/<名>.py` 调用（`<SKILL_DIR>` = 含本 `SKILL.md` 的 skill 安装根目录绝对路径），cwd 保持在用户确认的工作区根，使产物落工作区 `./tmp/`**；校验用 [`scripts/check-links.py`](scripts/check-links.py)（悬空必须为 0，仅编辑期跑）与 `python <SKILL_DIR>/scripts/check-progress.py`（步骤门禁账本）。

## 5. 约束部分

> 详见 [`references/约束部分/约束部分.md`](references/约束部分/约束部分.md)：文件命名规范、垃圾处理、记忆链、逻辑链的存储、文件存储格式、处罚机制、激励机制、上下文存储压缩机制、文件与文件夹创建范围、创建操作流程、安全与合规、步骤门禁、运行环境不可变。
> 文件存储格式总则：技术文件与数据手册可用 markdown 或 pdf，其余文档一律 markdown。
> 适用范围划分：`FILE_CREATION_POLICY.md` 只管设计执行期的工作区文件与权限；编辑 skill 本体一律遵守 `RULE_EDIT.md`。
> 裁决优先级：当前用户指令与代码/CLI 自描述 > 约束部分 > 各步骤文档 > `references/lib/`。
> 故障排查：遇未知错误先查 [`references/运维与排障/常见错误速查.md`](references/运维与排障/常见错误速查.md)；低模型用户同步参考 [`references/运维与排障/低模型优化指南.md`](references/运维与排障/低模型优化指南.md)。