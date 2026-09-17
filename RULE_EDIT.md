# RULE_EDIT（编辑规则）

> 本项目规范与文档的编辑规则；Agent 与贡献者必须遵守。
> 适用边界：本文件管 **skill 本体的编辑**（`SKILL.md`、`references/`、`scripts/`、`Sample/`、`CHANGELOG.md`）；设计执行期在工程工作区创建文件与目录的范围与权限，管在 [`FILE_CREATION_POLICY.md`](FILE_CREATION_POLICY.md) 与 [`references/约束部分/约束部分.md`](references/约束部分/约束部分.md)。

## 一、约束

- 约束文本长度 ≤ 50 行。
- 使用自然语言

## 二、编辑流程

1. 识别要编辑或新建的规范、文档。
2. 询问用户：需要预留哪些部分？
3. 判断该部分是否过长（超过 50 行）：过长则用「总索引 + 子文件」拆分，否则跳过拆分。
4. 询问用户：是否需要新建文件或文件夹？
5. 执行修改（遵守「文本 ≤ 50 行 + 自然语言」）。
6. 运行 `python scripts/check-links.py`（全树悬空链接必须为 0，孤立文档需接链或说明）。
7. 修改 CHANGELOG.md（记录本次变更）。
8. 提交 git。