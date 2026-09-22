# EasyEDAssistant Reference：元件检查 — PDF 可用性检查

> 本文件收录「下载/读取数据手册 PDF」前后的可用性判定规则；脚本 `scripts/pdf-read.py`（stdlib，无三方库）。
> 触发时机：元件检查第 1 步「查询技术手册」下载手册原件前，以及对已下载手册提取参数前。

## 为什么

嘉立创/厂商手册直链常见三类坑：URL 实为 HTML 报错页或 404 存根、文件截断损坏、扫描件/图片型 PDF 无文本层。
不加判定就下载并"读"，会把空文件或乱码当成手册，凭猜填封装与电气参数 → 直接污染选型与原理图（L2 回退）。

## 步骤

1. **下载前** `check-url`：`python <SKILL_DIR>/scripts/pdf-read.py check-url <URL>`——须 `usable=true`（命中 `%PDF-` 魔数或 `application/pdf`）才发起下载到 `./tmp/downloads/datasheet/`；`false`（HTML/404/取不到）即视为**未查到有效手册**，换源或走新建元件/向用户要手册，不得下载占位。
2. **下载后校验** `validate`：对落盘原件 `python <SKILL_DIR>/scripts/pdf-read.py validate <文件>`——`usable=false`（`not_pdf`/无 `%%EOF` 尾=损坏）删除该文件并回第 1 步换源；`encrypted=true` 标「加密·需密码」交用户，不猜内容。
3. **提取** `extract`：`python <SKILL_DIR>/scripts/pdf-read.py extract <文件>` 读文本层核对关键参数——`text_extractable=true` 用其文本；`false`（扫描件/图片型，脚本如实回报、绝不返乱码或假成功）改用**多模态 `read` 工具**直接读该 PDF 原件取封装图/引脚表页码。

## 判据与动机

- 参数出处仍守「来源三要素」：手册 URL+页码/版本进 `./tmp/datasheet/<型号>.md` 摘要与 `index.json`；PDF 可用性判定结果（`usable`/`pages`/`text_extractable`）一并留痕，缺判定的手册不得据以选型。
- 本检查只读、不落盘、不改 skill 本体，不豁免下载格式白名单（`.pdf` 外仍按 `net-download-policy` 拒绝）。

## 依据来源

- 用户指令 2026-09-22：新增下载数据手册前检查 PDF 是否可用，并修复 PDF 读取脚本。
- [`../查询技术手册/查询技术手册.md`](../查询技术手册/查询技术手册.md)、[`../../../scripts/net-download-policy/net-download-policy.md`](../../../scripts/net-download-policy/net-download-policy.md)、[`../../约束部分/记忆链/记忆链.md`](../../约束部分/记忆链/记忆链.md)。
