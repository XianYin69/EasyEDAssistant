---
name: EasyEDAssistant
description: "基于 JLCEDA MCP/CLI 双链路操作嘉立创 EDA 的电路设计 skill：原理图/PCB/射频/模拟/数字/滤波器/电源设计与检查。"
license: MIT
metadata:
  author: EasyEDAssistant
  version: "0.12.14"
---

# EasyEDAssistant 设计 Skill（主干）

## 1. 流程入口（固定）

0. **逐步执行铁律（最高优先级）**：标准流程六步必须**按序逐步**执行，**禁止跳步、禁止合并步骤、禁止跳过子步骤**；
   每步完成判据未满足、且未在 `./tmp/init/progress.md` 留下「步骤名 + 时间 + 证据（命令 / 产物路径 / 结果）」账目前，
   **不得进入下一步**；**绘制期每落位一个器件必须当次产出截图产物，无新截图即该件未完成、禁止落位下一个**。
   细则见 [`references/约束部分/步骤门禁/步骤门禁.md`](references/约束部分/步骤门禁/步骤门禁.md)；账本校验 `python scripts/check-progress.py`。
1. **识别用户请求**：判断用户意图与目标。
2. **判断是否为第一次设计**：
   - **是** → 执行「电路板设计标准设计流程」（见 §2）。
   - **否** → 询问用户需要执行哪一个步骤；先读取 `./tmp/` 下的上下文文件，再执行对应步骤（见 §3）。

## 2. 电路板设计标准设计流程

> 详见 [`references/电路设计标准设计流程/电路设计标准设计流程.md`](references/电路设计标准设计流程/电路设计标准设计流程.md)。
> 步骤：初始化部分 → 处理用户需求 → 检查方案及敲定 → 原理图制作 → PCB制作 → 交付与清理（按 §1 铁律逐步执行，每步留证后方可推进）。

## 3. 询问步骤 + 读取 ./tmp/ + 执行对应步骤

> 详见 [`references/单步执行/单步执行.md`](references/单步执行/单步执行.md)：读取 `./tmp/` 上下文 → 列出可执行步骤并询问用户 → 只执行被选步骤 → 回写上下文与三段式报告。

## 4. 文档地图

> 全量路由见 [`references/电路设计标准设计流程/电路设计标准设计流程.md`](references/电路设计标准设计流程/电路设计标准设计流程.md)（六步 + 子步 + 运行时指令速查）；约束见 §5；维护工具 [`scripts/check-links.py`](scripts/check-links.py)（悬空链接必须为 0）与 [`scripts/check-progress.py`](scripts/check-progress.py)（步骤门禁账本校验）。

## 5. 约束部分

> 详见 [`references/约束部分/约束部分.md`](references/约束部分/约束部分.md)：文件命名规范、垃圾处理、记忆链、逻辑链的存储、文件存储格式、处罚机制、激励机制、上下文存储压缩机制、文件与文件夹创建范围、创建操作流程、安全与合规、步骤门禁。
> 文件存储格式总则：技术文件与数据手册可用 markdown 或 pdf，其余文档一律 markdown。
> 适用范围划分：`FILE_CREATION_POLICY.md` 只管设计执行期的工作区文件与权限；编辑 skill 本体一律遵守 `RULE_EDIT.md`。
> 裁决优先级：当前用户指令与代码/CLI 自描述 > 约束部分 > 各步骤文档 > `references/lib/`。