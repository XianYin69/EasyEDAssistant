# EasyEDAssistant 智能体提示词（Agent Prompt）

> 精简原则：本 skill 的会话纪律、S0–S6 / P0–P10 流程、电气规范、中断机制、
> 验证分层等**全部**运行时规范已内嵌在 `SKILL.md`（skill 名
> `EasyEDAssistant`）中，Kilocode 加载 skill 时会自动注入其正文，
> **会话不需要再读取本文件、也不需要 `@AGENT-PROMPT.md`**。
> 直接调用 `EasyEDAssistant` skill 即可获得完整行为约束。

## 使用（唯一入口）

在 Kilocode 会话选择本 agent（`agents/EasyEDAssistant.yaml`）或直接触发
`@EasyEDAssistant` skill；skill 加载完成即注入规范，无需任何额外提示词文件。
`SKILL.md` 内引用的 `Sample/easyeda-agent/**` 与 `scripts/*.py` 是运行时
经验库与调用脚本，按 `SKILL.md` 指引读取或执行即可。

## 精简 default_prompt（外部 one-liner）

```text
使用 EasyEDAssistant skill 设计或安全重构 EasyEDA 原理图/PCB：先跑版本门禁
（easyeda update --check --exit-code）；写前读新鲜快照；保留拓扑与 NC 意图；
按 S0–S6 / P0–P10 与子域判据执行；严格验证（sch gate --strict / pcb drc +
check / export-image）后才显式保存并确认 saved:true；报告如实列出未验证项
与 blocked/fail，不把聚合数当全部通过。
```
