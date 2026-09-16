# EasyEDAssistant Reference：在工作区建立tmp文件夹

> 本文件收录在 `cwd` 确认后于工作区建立 `./tmp/` 目录与初始化子目录的规定。
> 原正本出处：`references/lib/connection-setup.md` §2.5；`references/lib/verification-delivery.md` §8.4。

## 前置

运行时根目录 `cwd` 已通过"向用户询问工作区路径"确认。本步骤在 `cwd` 下建立
`./tmp/` 及其子目录；`tmp/` 必须落在**工作区**（非 skill 目录）下。

## 操作规则（正本：`connection-setup.md` §2.5）

> 5. 临时 JSON、计划与回读结果放入**工作区**（`cwd`，非 skill 目录）下已忽略的
>    `./tmp/` 目录；保留原始快照，在副本中设计（详见 `FILE_CREATION_POLICY.md`
>    §2.3：运行产物禁止写入 skill 目录，且不得逃逸出工作区）。`tmp/` 下按用途分
>    子目录（sch/pcb/plan/design/parts/calc/datasheet/snapshots/baseline），
>    完整目录契约与清理纪律见 §8.4。

## 目录契约

> 详见 [`目录契约/目录契约.md`](目录契约/目录契约.md)（含子目录用途/格式表）。

## 初始化最小集合

初始化阶段仅建立基础目录结构（不写任何运行内容、不连 EDA）：

- `./tmp/` —— 根目录；确认已被 `.gitignore` 排除。
- `./tmp/snapshots/`、`./tmp/baseline/` —— 截图类容器，仅建目录。

其余子目录（sch/pcb/plan/design/parts/calc/datasheet/learning/downloads）按
任务进展按需创建；所有 `tmp/` 子目录与文件会话结束时按 §8.4 清理纪律删除。

> 注：基线截图、工具探针清单等**依赖 EDA 连接的产物不在本初始化范围**，
> 属正式工作流（`references/lib/connection-setup.md` §2.6–2.7）。