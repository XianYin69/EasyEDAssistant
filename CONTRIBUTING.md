# EasyEDAssistant 贡献指南

> 本文件只讲**人怎么参与本项目**。职责边界：**skill 本体的一切编辑以 [`RULE_EDIT.md`](RULE_EDIT.md) 为准**；设计执行期在工程工作区创建文件的范围与权限以 [`FILE_CREATION_POLICY.md`](FILE_CREATION_POLICY.md) 为准。冲突时以二者为准。

## 1. 仓库构成速览

- `SKILL.md`：主干入口（≤50 行），只做流程入口与路由。
- `references/`：步骤文档（总索引 + 同名子文件，单文件 ≤50 行）；`电气检查/硬编码规则/` 为判据库；`嘉立创EDA指令索引/` 为运行时指令入口；`lib/` 为维护者文档（不参与运行时加载）。
- `references/lib/`：上游 SKILL 正文迁入的**维护者存档**（不参与运行时加载、裁决优先级最低）；其中出现的 `AGENTS.md`、`standard-parts.json`、`concepts.md`、`make blocks-audit` 等指向上游仓库工件，本仓库不含，勿在本树追这些路径。
- `scripts/`：设计执行期调用的辅助脚本，全部 **Python 标准库实现，无第三方依赖、无 requirements.txt**；命名用连字符（`tool-probe.py`）。写产物的脚本自带 cwd 守卫：在 skill 仓库内运行会被拒绝。
- `Sample/`：上游行为记录存档；上游正文已迁入 `references/lib/`。
- `agents/`：外部 agent 定义（yaml 权威、md 人读镜像）。
- `CHANGELOG.md`：每次变更必须登记（RULE_EDIT 第 7 步）。

## 2. 环境要求

- Windows 10/11 / macOS / Linux；Python 3.9+（仅需标准库）；Git。
- 联调需嘉立创 EDA 专业版 + JLCEDA MCP 插件（`7655`）或 `easyeda` CLI/daemon（`60832-60841`）。

## 3. 修改后的验证（替代传统单测）

本项目是文档驱动的 skill，正确性靠**结构检查 + 运行时门禁**保证（无 pytest 测试套件，勿凭 CI 猜测）：

```bash
python scripts/check-links.py          # 全树 markdown 链接：悬空必须为 0（退出码 1 即失败；编辑期在仓库内跑）
python -m py_compile scripts/*.py      # 脚本语法
# 运行时门禁工具带 skill 仓库 cwd 守卫，须任选一个工作区目录、以 <SKILL_DIR> 绝对路径调用：
python <SKILL_DIR>/scripts/link-probe.py     # 本机环境自检 + 接口漂移 compat 探测（不联网查 latest）
python <SKILL_DIR>/scripts/check-progress.py # 设计执行期步骤门禁：账本齐全、证据产物存在
```

行为验证以真实工程走查：按 `references/电路设计标准设计流程/` 跑通相关步骤，门禁命令（`sch gate --strict`、`pcb drc` 等）结果为证。

## 4. 贡献流程

1. 在 `dev` 分支工作；较大改动先按 RULE_EDIT 第 2 步与用户确认预留结构。
2. 新建文件前确认命名与格式符合 `references/约束部分/`（≤50 行、markdown、总索引 + 同名子文件）。
3. 改完跑第 3 节验证；更新 `CHANGELOG.md` 并同步 SKILL.md 的 `metadata.version`；提交并推送 `dev`。
4. PR 审查关注：链接可达、判据有出处、不与硬门冲突。

## 5. 发布（dev → main）

`git checkout main` → `git merge --no-ff dev`（保留合并历史）→ `git push origin main` → `git checkout dev`；版本号遵循语义化，打 tag `v<版本>`。

## 6. 红线

- 不得放宽硬门（`sch gate`、`pcb drc`、格式白/黑名单、运行环境不可变）来让检查「通过」。
- 不得为「更快」跳步、合并步骤、省略进度账目，或跳过绘制期逐件截图（见 `references/约束部分/步骤门禁/步骤门禁.md`）。
- 运行产物（截图/JSON/tmp）一律不入库；skill 目录不得被设计执行期写入。
- 历史 `CHANGELOG.md` 条目不改写；数值判据冲突以 daemon 规则代码（Go）与 JLC 官网为准并回改文档。