# EasyEDAssistant 智能体提示词（Agent Prompt）

> 精简原则：会话纪律、流程、判据与中断机制全部在 `SKILL.md` 主干与 `references/` 步骤文档中，Kilocode 加载 skill 时自动注入主干正文，**会话不需要读取本文件**。
> 本文件只保留外部调用用的 one-liner 与入口速览，规范以仓库文档为准（当前 `SKILL.md` v0.12.x）。

## 入口速览

1. **首次设计**：走 `references/电路设计标准设计流程/`——初始化部分 → 处理用户需求 → 检查方案及敲定 → 原理图制作 → PCB制作 → 交付与清理。
2. **续跑或单步**：走 `references/单步执行/`——读 `/tmp` 上下文 → 询问并选择步骤 → 只执行被选步骤 → 回写与报告。
3. **动手前先测链路**：`references/桥接联通性测试/`——MCP `7655` 优先，不通再测 Agent `60832`；一条通即全程使用，重试最多 3 轮后转用户。
4. **不可省略的用户确认**：预算与替代方案、元件新建与豁免、规范检查豁免（须明确接受风险）、原理图/PCB 验收、最终方案与交付文档。
5. **收尾**：`references/交付与清理/`——先出手册与交付报告，再清理 `./tmp/`。

## default_prompt（外部 one-liner）

```text
使用 EasyEDAssistant skill 设计或安全重构嘉立创 EDA 原理图/PCB：先完成桥接连通性测试与版本门禁（easyeda update --check --exit-code，升级后新开会话）；写前读新鲜快照与数据手册，参数真值以 CLI 自描述为准；按标准流程六步执行，凡改变做法或超出已授权范围的选择一律中断等用户拍板，检查失败只重跑未通过项；验证分层（拓扑/几何/电气/呈现/保存）全过并确认 saved:true 才算完成；收尾先出技术手册、功能手册与交付报告（blocked/fail 与未运行检查如实列出），再清理 ./tmp/；运行产物只写工作区，禁止落入 skill 目录。
```

## 说明

- `SKILL.md` 引用的 `Sample/easyeda-agent/**` 与 `scripts/*.py` 是运行时经验库与设计时调用的辅助脚本，按主干指引读取与执行。
- 编辑 skill 本体遵守 `RULE_EDIT.md`；设计执行期的文件范围与权限遵守 `FILE_CREATION_POLICY.md`；其余约束见 `references/约束部分/`。