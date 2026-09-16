---
description: "EasyEDAssistant agent (markdown mirror) — the canonical Kilocode agent definition is agents/EasyEDAssistant.yaml (interface: schema)."
---

# EasyEDAssistant Agent (mirror)

> 权威 Kilocode agent 定义：`agents/EasyEDAssistant.yaml`（`interface:` schema，
> Kilocode `agents/` 目录原生加载 `.yaml` / `.md`）。
> 本 `.md` 是人读镜像；`.json` 仅供 JSON 工具可发现性使用（Kilocode 不
> 从 `agents/` 加载 `.json`）。

基于 JLCEDA MCP VS Code 插件桥接操作嘉立创 EasyEDA（专业版）的电路设计
智能体：原理图绘制、PCB 布局布线、射频/模拟/数字/滤波器/电源设计、检查与
制造文件导出。

## 使用

会话选择本 agent 或直接触发 `@EasyEDAssistant` skill；skill 加载即注入
完整行为规范（S0–S6 / P0–P10、会话纪律、中断机制、验证分层等），
无需另外读取 `AGENT-PROMPT.md`。`SKILL.md` 引用的
`Sample/easyeda-agent/references/*.md`（他人总结与试错经验库）与
`scripts/*.py`（设计时调用的辅助脚本）按 `SKILL.md` 指引读取与执行。
