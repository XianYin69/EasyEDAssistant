---
description: "EasyEDAssistant agent markdown mirror. The canonical Kilocode agent definition is agents/EasyEDAssistant.yaml."
---

# EasyEDAssistant Agent (mirror)

> 权威 Kilocode agent 定义：`agents/EasyEDAssistant.yaml`（`interface:` schema，
> Kilocode `agents/` 目录原生加载 `.yaml` / `.md`）。
> 本 `.md` 是人读镜像；原 `.json` 可发现性清单因与 Kilo agent schema 冲突（被自动发现为无效配置）
> 且自述「Kilocode 不加载 agents 下的 .json」，已删除。

基于 JLCEDA MCP/CLI 双链路操作嘉立创 EasyEDA（专业版）的电路设计
智能体：原理图绘制、PCB 布局布线、射频/模拟/数字/滤波器/电源设计、检查与
制造文件导出。

## 使用

会话选择本 agent 或直接触发 `@EasyEDAssistant` skill；skill 加载即注入
完整行为规范（S0–S6 / P0–P10、会话纪律、中断机制、验证分层等），
无需另外读取 `AGENT-PROMPT.md`。`references/lib/*.md`（正本）与 `references/*.md`（运行时加载）
`scripts/*.py`（设计时调用的辅助脚本）按 `SKILL.md` 指引读取与执行。
