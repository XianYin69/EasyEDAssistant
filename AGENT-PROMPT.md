# EasyEDAssistant 智能体提示词（Agent Prompt）

> 精简原则：本 skill 的会话纪律、S0–S6 / P0–P10 流程、电气规范、中断机制、
> 验证分层等**全部**运行时规范已内嵌在 `SKILL.md`（skill 名
> `EasyEDAssistant`）中，Kilocode 加载 skill 时会自动注入其正文，
> **会话不需要再读取本文件、也不需要 `@AGENT-PROMPT.md`**。
> 直接调用 `EasyEDAssistant` skill 即可获得完整行为约束。

## 使用（唯一入口）

在 Kilocode 会话选择本 agent（`agents/EasyEDAssistant.yaml`）或直接触发
`@EasyEDAssistant` skill；skill 加载完成即注入规范，无需任何额外提示词文件。

## 精简 default_prompt（外部 one-liner）

```text
使用 EasyEDAssistant skill 设计或安全重构 EasyEDA 原理图/PCB：先跑版本门禁
（easyeda update --check --exit-code）；写前读新鲜快照；保留拓扑与 NC 意图；
按 S0–S6 / P0–P10 与子域判据执行；严格验证（sch gate --strict / pcb drc +
check / export-image）后才显式保存并确认 saved:true；报告如实列出未验证项
与 blocked/fail，不把聚合数当全部通过。
```

## 运行时边界（防工作区逃逸）

以下约束由 skill 本体（`SKILL.md`）在会话加载时自动注入，本文件不重复：

- **不读取 skill 目录内文件**：`SKILL.md` 本体已由 skill 加载器注入，会话
  期间不再 `read` `SKILL.md` / `AGENT-PROMPT.md` / `Sample/easyeda-agent/**`
  中的任何 `.md`；`Sample/` 与 `AGENT-PROMPT.md` 是移植参考与归档，仅供
  skill 维护者核对，不是运行时输入。
- **不写入 skill 目录**：所有运行产物（截图 / 临时 JSON / 计划 / 蓝图 /
  tmp 清单）只写**工作区** `./tmp/`（`Path.cwd()`，`FILE_CREATION_POLICY.md`
  §1.3/§2.4 与 §8.4）；skill 目录只读。
- **版本门禁非 0**：直接向用户报告 `CLI/Skill/daemon/Connector` 与 GitHub
  latest 的实际版本差异并请用户升级后新开会话，**不打开任何升级指引文档**。
- **API 判据真值**：以 daemon 规则代码与 `easyeda <cmd> --help` /
  `easyeda actions` 为准，与文档描述冲突时以代码为准。
