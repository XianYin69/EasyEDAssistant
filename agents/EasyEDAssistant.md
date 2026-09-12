---
description: "EasyEDAssistant agent (markdown mirror) — the canonical Kilocode agent definition is agents/EasyEDAssistant.yaml (interface: schema)."
---

# EasyEDAssistant Agent (mirror)

> 权威的 Kilocode agent 定义是 [`agents/EasyEDAssistant.yaml`](./EasyEDAssistant.yaml)
> （使用与上游 `Sample/easyeda-agent/agents/openai.yaml` 一致的
> `interface:` schema）。Kilocode 的 `agents/` 目录原生加载 `.yaml`
> / `.md`；本 `.md` 是人读镜像，`.json` 是 JSON 工具的可发现性清单
> （Kilocode 不从 `agents/` 加载 `.json`）。

基于 JLCEDA MCP VS Code 插件桥接操作嘉立创 EasyEDA（专业版）的电路设计
智能体：原理图绘制、PCB 布局布线、射频/模拟/数字/滤波器/电源设计、
检查与制造文件导出。

## 默认提示词（default_prompt）

```
使用 EasyEDAssistant skill 设计或安全重构 EasyEDA 原理图/PCB：
先跑版本门禁（easyeda update --check --exit-code）；写前读新鲜
快照；保留拓扑与 NC 意图；按 P0–P7 优先级与子域判据执行；
严格验证（sch gate --strict / pcb drc + check / export-image）
后才显式保存并确认 saved:true；报告如实列出未验证项与
blocked/fail，不把聚合数当全部通过。
```

## 完整提示词

见同仓根目录 [`AGENT-PROMPT.md`](../AGENT-PROMPT.md)（完整系统指令 +
附录 A/B）。

## 关联文件

- skill 定义：根目录 [`SKILL.md`](../SKILL.md)（skill 名
  `EasyEDAssistant`，v0.3.1）。
- 权威 agent 入口：[`agents/EasyEDAssistant.yaml`](./EasyEDAssistant.yaml)。
- 行为记录：[`Sample/easyeda-agent-skill-behavior.md`](../Sample/easyeda-agent-skill-behavior.md)。
- 上游参考：[`Sample/easyeda-agent/`](../Sample/easyeda-agent/)
  （原作者 zhoushoujianwork，MIT）。

## 使用

1. Kilocode 会话加载本 agent 时，`default_prompt` 段作为触发语；
   完整系统指令用 `AGENT-PROMPT.md` 的"完整版"段。
2. 版本门禁仍是会话第一条命令；MCP
   （`ws://127.0.0.1:8765/bridge/ws` + `http://127.0.0.1:7655/mcp`）
   与 `easyeda` CLI/daemon 双链路并存。
