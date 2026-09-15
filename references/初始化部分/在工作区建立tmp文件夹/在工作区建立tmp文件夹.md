# EasyEDAssistant Reference：在工作区建立tmp文件夹

> 本文件收录在 `cwd` 确认后于工作区建立 `./tmp/` 目录与初始化子目录的规定。
> 原正本出处：`references/lib/connection-setup.md` §2.5；`references/lib/verification-delivery.md` §8.4。

## 前置

运行时根目录 `cwd` 已通过"向用户询问工作区路径"确认。本步骤在 `cwd` 下建立
`./tmp/` 及其子目录；`tmp/` 必须落在**工作区**（非 skill 目录）下。

## 操作规则（正本：`connection-setup.md` §2.5）

> 5. 临时 JSON、计划与回读结果放入**工作区**（`cwd`，非 skill 目录）下已忽略的
>    `./tmp/` 目录；保留原始快照，在副本中设计（详见 `FILE_CREATION_POLICY.md`
>    §2.4：运行产物禁止写入 skill 目录，且不得逃逸出工作区）。`tmp/` 下按用途分
>    子目录（sch/pcb/plan/design/parts/calc/datasheet/snapshots/baseline），
>    完整目录契约与清理纪律见 §8.4。

## 目录契约（正本：`verification-delivery.md` §8.4）

所有运行产物一律落在**工作区** `cwd` 下已忽略的 `./tmp/`，按用途分子目录；
路径全部相对工作区解析，禁止落入 skill 目录（`FILE_CREATION_POLICY.md` §1.3/§2.4），
`tmp/` 已在 `.gitignore` 中排除，任何 tmp 内容不得提交 git。

| 目录 | 内容 | 格式 |
|---|---|---|
| `./tmp/sch/` | 原理图字符画蓝图、官方导图 | md/json/png |
| `./tmp/pcb/` | PCB 布局蓝图、视口快照 | md/json/png |
| `./tmp/plan/` | 计划类工件（含 `<project>-sch-layout.md`） | md/json |
| `./tmp/design/` | 方案、逻辑框图、可行性结论、PCB 设计基线（§13.3） | md/json |
| `./tmp/parts/` | 元器件选型与浏览器比价缓存（§5.6） | md/json |
| `./tmp/calc/` | 理论计算数据缓存（§7.7 推导） | md/json |
| `./tmp/datasheet/` | 数据手册摘要（型号/关键参数/页码出处） | md |
| `./tmp/snapshots/` | 动态截图（§2.9 既有） | png |
| `./tmp/baseline/` | 基线截图（§2.7 既有） | png |
| `./tmp/learning/` | 主动学习笔记（§13.1，浏览器检索结果整理） | md |
| `./tmp/downloads/` | 网络资源下载（§13.2 `scripts/net-download.py`），含 datasheet/docs/images/data/edalib/manufacturing 子目录 + `index.json` | 见 `net-download-policy.md` §2 |

## 初始化最小集合

初始化阶段仅建立基础目录结构（不写任何运行内容、不连 EDA）：

- `./tmp/` —— 根目录；确认已被 `.gitignore` 排除。
- `./tmp/snapshots/`、`./tmp/baseline/` —— 截图类容器，仅建目录。

其余子目录（sch/pcb/plan/design/parts/calc/datasheet/learning/downloads）按
任务进展按需创建；所有 `tmp/` 子目录与文件会话结束时按 §8.4 清理纪律删除。

> 注：基线截图、工具探针清单等**依赖 EDA 连接的产物不在本初始化范围**，
> 属正式工作流（`references/lib/connection-setup.md` §2.6–2.7）。
