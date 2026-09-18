# 变更摘要

> 本文件由 SKILL.md v0.9.0 §14 逐字迁移而来（v0.10.0 主干化重构）。新版本条目加在本文件顶部。

### v0.12.22（2026-09-18）

**connector 版本钉定策略（用户指令：只用/只基于快照版本开发；不要任何自动更新含市场原地更新；发现新版→删除回退此版本）**：

- **检测落地 `link-probe.py` 增 `version_gate.pin`**：读 `Sample/easyeda-agent-connector/.snapshot.json` 的 `connector_version` 为钉定值（权威单源，文档不复制数字），与 `versionGate.cli/daemon` 版本比对；mismatch → stderr WARN + JSON `action` 给出「维护窗口卸载新版→`eext-src.py eext` 重导入→关闭自动更新」指引。**比对不判门**（不改退出码，与「判定与处置脱节」教训一致）；快照缺失时静默跳过。实测本机全 1.5.1 → `pinned:1.5.1, mismatch:false`，rc=0。（CLI 无直接 connector 版本上报口——`api search plugin` 空、health 仅 cli/daemon——connector 版本以扩展管理器人工核对 + 三件套整体钉定近似覆盖，指引中已注明。）
- **约束正本 `运行环境不可变` 新增 §四「connector 版本钉定（只回退，不升级）」**（11–13 条：钉定值单源、自动更新全关（市场原地更新/daemon 自同步/升级弹窗）、发现非钉定版→用户删除回退、Agent 报告+指引不代卸/代装）；违规后果补「检测偏离未报告 / 代装卸 / 接受市场自动更新 = L3」；文件 42 行 ≤50。
- **README 安装章重写为钉定版**：顶部加版本钉定声明与「发现新版只回退」方向；`eext` 命令 `--tag` 缺省即钉定版；导入步骤①改「卸载现装版本（含更高版本）」、④加 `pin.mismatch=false` 验收；市场渠道从「任选」降级为「**不推荐**——原地自动更新与钉定冲突，若用须关自动更新并核对版本」。
- **同步链**：`eext-src.py` `eext` 输出 JSON 补 `pinned` 字段与回退语义、`connector-src.md` 纪律新增第 6 条钉定、`约束部分` #13 摘要、`SKILL.md` §1.2、`AGENT-PROMPT.md` 速览第 3 条、`lib/environment-setup.md` 渠道表加「本项目不适用自动更新」服从句（lib 服从严肃约束优先级）。
- 校验：14 脚本 py_compile 过；link-probe 活体 rc=0 pin 段正确；`check-links` 190 md 悬空 0/孤立 0；约束文件全部 ≤50 行；`eext-src verify` 快照 39 文件不回归。版本对齐 **0.12.22**。

### v0.12.21（2026-09-18）

**README 新增「安装扩展插件」条目 + 封装脚本增 `eext` 取包子命令（用户指令）**：

- `scripts/connector-src/eext-src.py` 新增 `eext [--tag] [--out]`：默认取**与源码快照同 tag** 的官方发行资产 `easyeda-agent-connector.eext`，按 release `checksums.txt` 独立校验 sha256（不符即丢弃勿导入），成功后 JSON 输出四步导入指引（扩展管理器卸载同 UUID 旧项 → 导入 → 完全重启 EDA → 新会话 link-probe 验链路）+ 立创市场替代渠道；实测 v1.5.1 资产下载校验通过（`b92a963e…bbfc`，3,013,845 B），测试产物已清理未入库。维护窗口/用户手工语义写入 docstring 与 `connector-src.md` 纪律第 1 条（Agent 代下载/安装 `.eext` 仍属 L3）。
- **README 新增「## 安装扩展插件（easyeda-agent-connector，用户手工动作）」**（连接方式小节后）：触发时机（60832 不通/connector 异常）、通道 1＝封装脚本取包+导入步骤、通道 2＝立创插件市场（原地自动更新、major.minor 同线即可），两条既有渠道语义与 `lib/environment-setup.md` 安装渠道正本对齐；目录树 connector-src 行同步能力清单。
- 校验：14 脚本 py_compile 全过；`check-links` 悬空 0/孤立 0；connector-src.md ≤50 行；`eext-src verify` 快照清单不回归（39 文件）。版本对齐 **0.12.21**。

### v0.12.20（2026-09-18）

**connector 源码快照入库 + 封装脚本 + 所有检查更新/版本门禁全面禁用（用户指令）**：

- **新增 `Sample/easyeda-agent-connector/`（40 文件 ≈1.2MB 纯文本）**：上游 easyeda-agent tag **v1.5.1**（commit `24eb9800`）`extension/` 目录源码快照——28 个 `.ts` 全部插件源、`extension.json` 清单、config/scripts/build 脚本、上游 CHANGELOG（226KB 逐版接口史，排查漂移的富矿）与 LICENSE；按维护者决定排除 `images/`（二进制图标）与 `package-lock.json`（机器工件）；出处/时间/sha256 全清单固化在 `.snapshot.json`。抓取方式：维护期 `git clone --depth 1 --branch v1.5.1`（blob:none 过滤），非设计执行期行为，用户指令授权。
- **新增 `scripts/connector-src/`（独立文件夹，封装脚本+政策）**：`eext-src.py` 四子命令——`verify`（对照 .snapshot.json 重算 sha256，防篡改/漏文件，实测 40/40 全绿）、`report`（快照元数据+manifest+菜单+API 域统计+本机 CLI 版本**仅记录**聚合 JSON）、`apis [--domain sch]`（从 TS 源提取 **59 域/193 个 `eda.*` API** 实现清单，离线查「插件到底实现了什么」）、`fetch --tag vX --out <目录>`（维护窗口下载新 tag extension/ 并打印与现快照 diff，**不自动覆盖仓库**；解包同样排除 images/lock）。配套 `connector-src.md` 政策：编辑期专用、快照只读、真值优先级不变（运行时仍以 `--help`/actions 自描述为准）、与 cli_compat 的分工（探测漂移 vs 解释漂移）。
- **检查更新/版本门禁全面禁用**（用户指令 2026-09-18；根因：v0.12.19 的 versionGate 门禁自身成为工作流断点，而合法修复渠道——升级——又被运行环境不可变禁止，判定与处置脱节）：`link-probe.py` 退出码**只由链路连通性决定**，`version_gate` 段落 JSON 标 `judged:false` 仅记录，删除 `--skip-version-gate` 参数，非 ok 从 blocked 分支降为提示；compat 接口漂移探测保留（本机 `--help`，零联网，非「检查更新」）。文档全链改写：`运行环境不可变` §三改名「更新检查全面禁用」并新增第 9 条离线源码真值通道、`门禁检查` 检查项 1 改「组件版本记录（只记录不判定）」并删 blocked 分支、`桥接联通性测试` 第 5 步与判据同步、`SKILL.md` §1.2、`AGENT-PROMPT.md` 两条、`会话与文档` 三条目（`--skip-version-check` 出现即异常/`update --check`/`skill status` 行去掉「改用 versionGate 判定」语义）、`指令索引` 刷新方法（核对＝对照 compat+源码快照，非查版本号）、`约束部分` 第 13 条摘要、`处罚机制` L3（执行任何检查更新/版本门禁步骤均违规；顺带修复上轮编辑截断拼接的残句）。
- **配套修例**：`文件与文件夹创建范围` 第 4 条增「编辑期经用户明确指令可新增上游归档子目录」例外（运行期仍全禁）；README 目录树（connector-src/、Sample/easyeda-agent-connector/、许可证出处）、scripts/ 清单行、快速开始第 3 条；`agents/EasyEDAssistant.yaml` one-liner 残留的相对路径 `python scripts/link-probe.py` 补 `<SKILL_DIR>` 并同步新语义（v0.12.17 批量替换未覆盖 yaml 的漏网）。
- 校验：`check-links` 189+ md 悬空 0/孤立 0；14 脚本 py_compile 全过；非 lib references ≤50 行；功能实测——`eext-src verify` 40 文件全匹配、`apis` 59 域输出、`report` 聚合正常、`link-probe` 健康链路 rc=0（versionGate 已无判定路径）、cli_compat 断言不回归。版本对齐 **0.12.20**。

### v0.12.19（2026-09-18）

**防上游接口漂移的系统性机制（用户判据：「上游新版本发布后，针对老版本的 skill 完全没法用了」）**。v0.12.18 只修了 v1.5.1 当次断点；本轮把「CLI 自描述为唯一真值」的既有裁决落到脚本层，使 skill 对未来的 1.5.x/1.6.x 破坏性变更自适应降级、并在会话开始即报警：

- **新增 `scripts/cli_compat.py`（共享探测库）**：`flag_supported`/`cmd_supported`/`pick_cmd`/`with_flag` 把「某 flag/子命令是否存在」从硬编码改为运行时向 `--help` 提问（进程内缓存；命令路径提取容忍 easyeda 前缀与 flag 值混排；探测失败一律按不支持、fail-closed 由调用方兜底）。12+11 断言对活 v1.5.1 全过（含 `sch list --json` 假、`pcb components` 假、`pcb snapshot` 真等）。
- **五个脚本去硬编码**：`visual-qa`（export-image `--format/--out` 探测+无 `--out` 时退 mtime 找图；sheet-geometry/`--json` 探测；PCB 组件收集 `pcb list`→`pcb components` 候选 + `--json/--include-*` 逐个探测；layout-score/check/drc `--json` 探测）、`sch-verify`（gate `--json`、connectivity/list `--all-pages`、`--include-*`、check `--all` 全探测）、`pcb-gate`（五个 `--json`/`--strict` 探测；`--with-gate` 时 `--gate` 不受支持 → 显式 `blocked` 记录，不静默不伪过）、`tool-probe`（`health --json`/`api search --json` 探测——**该脚本在 v1.5.1 上本已误报 cli_unavailable，顺带修复**，实测恢复 rc=0 产出 manifest）。
- **link-probe 增 compat 兼容性基线探测**：REQUIRED 命令/flag 表（sch export-image/gate/list/…、pcb snapshot/drc/check/…）会话开始跑一遍，`compat.missing_*` 非空 → **WARN + 落 `link-probe.json`，不改退出码**（脚本已自适应，漂移=降级非阻断），把「步骤 4 中途死锁」变成「第 1 步就知道并转维护窗口」——补上「预想每步出错、机制早发现」在环境层缺的一环。
- **文档接链**：`门禁检查` 增第 4 项「兼容性探针」判据（漂移只报告不阻断、报告须如实列 missing、维护期外禁改 skill 本体）；`桥接联通性测试`/`门禁检查` 脚本输出字段补 `compat`；`指令索引` 刷新方法增「漂移机器探测」条；`SKILL.md` §1.2 自检描述补 compat；README 脚本清单 + 两处漏改的运行时 `python scripts/` 补 `<SKILL_DIR>`；**CONTRIBUTING 验证块修正**——link-probe/check-progress 有仓库 cwd 守卫，原文档教的仓库内跑法必被拒（维护文档自身不可执行的低级错误）。
- 校验：13 脚本 py_compile 全过；`check-links` 188 md 悬空 0/孤立 0；非 lib references ≤50 行；端到端实测——link-probe rc=0 且 `compat:{drift:false}`（当前 v1.5.1 全基线在位）、`visual-qa --schematic` 对进行中工程 pass(exit 0)、`tool-probe` 恢复产出、`sch-verify` 四项 pass、仅 gate rc=1（U1 未连线，真设计态非接口错）。版本对齐 **0.12.19**。

### v0.12.18（2026-09-18）

**修复 `visual-qa.py` 与 easyeda CLI v1.5.1 的接口漂移（用户实测：步骤 4 截图硬门命中中断点，重试 2 次同因失败、账目 4.1 blocked，写操作冻结）**。经本机 v1.5.1 `--help` 实测 + 上游 release notes 核对（v1.5.0 起 `sch snapshot` 移除、`sch export-image` 为官方导图且**默认 SVG**；v1.5.1 延续）：

- **逐件截图硬门恢复（阻断根因）**：`capture_sch_image` 原样调用 `sch export-image`（默认导出 SVG）→ 脚本只认 PNG → 永远「无新截图 = exit 3」。现显式 `--format png --out <精确路径>`，产物直接盖 `sch-` 前缀进滚动轨；页面定位改用官方 `--page` 参数（`--doc` 只钉写操作）。
- **数据回读三项修复**：`sch list`/`sch connectivity` 在 v1.5.1 **无 `--json` 标志**（传了即 unknown flag、rc=1），其原生输出本就是 JSON——去标志、直接解析；`sch sheet-geometry --json` 仍支持（保留）。输出现为 `{id,ok,result}` 信封，新增 `_unwrap_env` 统一剥壳；器件/边界 bbox 新键形 `{minX,minY,maxX,maxY}` 纳入 `_item_bounds`/`_extract_sheet_bounds`（原三键形解析器对新输出全部空转 → 越界核验静默变 no-op，属「假通过」隐患，一并堵上）。
- **禁区核验增强（顺带补的真检测项）**：解析 `sheet-geometry.keepouts[]` 的 hard 禁区（标题栏），器件压入 = blocking（exit 3）；图框/板框基元（`componentType=sheet/board/frame`，bbox 按定义覆盖全幅）不参与判定，排除假阳性。实测样例：U1 工程跑通 `pass (exit 0)`（修复前 exit 3 死门）。
- **PCB 数据侧陈旧命令修复**：`collect_pcb_data` 原调 `pcb components.list ... --json`（v1.5.1 已并入 `pcb list`，且 `pcb list` 无 `--json`）→ 组件收集恒失败；改 `pcb list --include-bbox --include-pads` + 信封剥壳。`pcb layout-score/check/drc --json` 经实测仍存在，不动。
- **脚本 docstring 调用式对齐 `<SKILL_DIR>` 约定**（12 处，v0.12.17 批量替换只覆盖了 .md）；`check-links.py`（编辑期工具）保持相对路径。
- 文档同步：`原理图指令` 索引 export-image 行标注「默认 SVG，PNG 须 --format png --out」；`部分绘制与截图` 截图硬门条写明 PNG 导图 + hard keepout（标题栏）核验。
- 校验：`check-links` 188 md 悬空 0/孤立 0；12 脚本 py_compile 全过；非 lib references ≤50 行；**端到端实测**——对进行中设计会话（指点杆/P1，U1 已落位）跑 `visual-qa --schematic` 得 `pass (exit 0)` 且滚动轨产出 `sch-*.png`。设计执行期无需豁免即可续跑步骤 4。版本对齐 **0.12.18**。

### v0.12.17（2026-09-18）

本轮为「运行环境不可变」(约束 13) 的收尾 + 全维度审计整改，逐项带实证：

- **修高危可用性 bug：脚本路径与 cwd 互斥**。全流程 53 处运行时命令写 `python scripts/<名>.py` 且要求 cwd=工作区，但脚本实体在 skill 仓库——cwd=工作区时 `No such file`，cwd=skill 仓库时守卫拒跑，**照抄文档的模型（低/高级皆然）会话第一条自检命令即失败**。统一改为 `python <SKILL_DIR>/scripts/<名>.py`（`<SKILL_DIR>` = 含 `SKILL.md` 的 skill 安装根绝对路径），在 SKILL.md §4 与 `嘉立创EDA指令索引` 使用纪律第 5 条定义为唯一正本；编辑期工具 `check-links.py` 仍按相对路径（在 skill 仓库跑）。实测：以工作区为 cwd、绝对路径调 `link-probe.py` 正常产出 `./tmp/init/link-probe.json`。
- **修机器门禁崩溃（健壮性）**：`link-probe / sch-verify / pcb-gate / tool-probe / tool-probe-simulator / visual-qa` 六个脚本的 `subprocess.run(..., text=True)` 未指定编码，在中文 Windows 上按 cp936 解码 `easyeda` 的 UTF-8 中文输出（`✓ 版本一致性…`）抛 `UnicodeDecodeError`，致 **健康机器被误判 `blocked`、工作流在第 1 步即死锁**。六处一律补 `encoding="utf-8", errors="replace"`；`easyeda health` 实测 `versionGate.verdict: ok` → link-probe 由 exit 3 转 exit 0。
- **删除残留禁用指令**：`AGENT-PROMPT.md` 与 `agents/*.yaml` 的 one-liner、`lib/connection-setup.md` §1.2 仍把 `easyeda update --check --exit-code` 写成「会话第一条命令/版本门禁」，与约束 13 直接冲突（模型照抄即 L3 违规）。全部改为本机 `health` 的 `versionGate` 自检；`运行环境不可变.md` 与 `门禁检查.md` 补 `link-probe` 实跑 `easyeda version`+`easyeda health`（脚本据此新增 version 调用并落 `cli_version`）。
- **指令索引速查表标注禁用项**：`会话与文档.md` 给 `skill status/sync`、裸 `daemon start`、`--skip-version-check` 补「本 skill 禁用 / 必带 `--auto-update-skill=false`」标记（与既有 `update --check` 禁用标注对齐）；`端口探测与插件确认.md` 排查分支的裸 `daemon start` 补强制参数；`桥接联通性测试.md` 指向 `lib/environment-setup.md` 处标注「维护者历史存档、Agent 禁照做」。本机 `easyeda daemon start --help`/`skill --help` 实证约束 13 三条禁令为真（`--auto-update-skill` 默认 on、`skill status/sync` 比对 latest）。
- **修门禁自锁（产物路径矛盾）**：`生成最终方案`「最终方案不入 `./tmp/`」与第 3 步账目 `--art ./tmp/design/<工程>-final-plan.md`、`读取上下文` 读 `./tmp/design/` 互相打架 → `check-progress` 永判产物缺失。统一为方案落 `./tmp/design/<工程>-final-plan.md`。`处理用户需求` 补「构建初步需求落 `<工程>-requirement.md`」，使其第 2 步账目 `art` 有实体。
- **补 6 处无界回环熔断**（沿用 ≤3 惯例）：处理用户需求澄清往返、原理图/PCB「绘制↔对照检查」整步回退、电气检查「检查↔处理」重查、系统框图/关系图/连接图「绘制↔确认」与连接图上游冲突往返、交付「确认↔修改」均加上限并满轮转 `处理设计问题`/用户拍板。
- **补缺失失败分支**：`专业技术规范检查`「既不修改又不豁免」原为死胡同 → 判未通过交回 `检查方案及敲定` 按未通过处理；`原理图制作/检查…` 补 `blocked`（环境异常先回桥接修环境，不当设计 fail）与整步回退 3 轮上限，与 PCB 侧对称；`系统框图`「未落实」节点补处置；`清理` 删除失败/占用补「记残留路径、不谎报已清理」。
- **纠错与低模型可用性**：`文件命名规范` 截图命名式 `step-<索引>-…` 系过时（实际 `sch-`/`pcb-` 前缀被 visual-qa 滚动清理与账目 `art` 依赖）→ 改正并修其依据来源；`net-download` 政策/约束正文臆造的 `--yes`/`--force` 参数实际不存在 → 改「无任何越过开关」；`GUI指令映射` BOM 行的 `bom-enrich.py` 改完整调用式；`原理图/检查…` 门禁复核改用一键 `sch-verify.py`（与 PCB `pcb-gate.py` 对称）；`用户PCB配置文件` 两处裸文件名/目录碎片路径补正确相对链接。
- **门禁脚本增强**：`check-progress.py --steps` 支持 `1-5`/`1..5`/`1..5,6` 区间混写（消除 `--steps 1..N-1` 被当单步名的隐患），步骤门禁正本同步示例。
- 校验：`check-links` → **188 个 md，悬空 0、孤立 0**；12 脚本 `py_compile` 全过；非 lib references 与 net-download-policy 子文件全部 ≤50 行；从 SKILL.md BFS 不可达仅 6 份（均为根文档/Sample 存档/agent 定义/lib，非运行时断链）；功能实测——link-probe exit 0（本机 versionGate ok→选定 cli-daemon）、`check-progress --steps 1-5` 通过且 `--steps 1..6` 正确报「缺步骤 6」、`net-download` 拒 `.eext`(exit 1)；`easyeda health/version/daemon start --help/skill --help` 本机 v1.5.1 实测。版本对齐 **0.12.17**（SKILL.md / agents yaml）。

### v0.12.16（2026-09-18）

- **账本钩子补齐六步（修「门禁只管两步」）**：此前仅「初始化」与「交付」提到账本，中间四步（处理用户需求 / 检查方案及敲定 / 原理图制作 / PCB制作）文档内无写入点，弱模型走完整流程时会在中段漏记。现每步末尾各有一条 `progress-log.py --step N --name … --cmd … --art … --result …` 钩子，并写明「未记账 = 本步未完成，不得进入下一步」。
- **修账本自锁（鸡生蛋死锁）**：交付第 1 步原以 `check-progress` 默认「六步齐全」为前置，而第 6 步账目只能在交付过程中写入 → 永远进不了交付。改为**门禁校验 `--steps 1,2,3,4,5`**，第 6 步账目在**删除 `./tmp/` 之前**写入且 `--art` 指向不随清理消失的工作区根交付报告；`步骤门禁.md` 同步写明时序规则，杜绝「账目产物被自己清掉后永久悬空」。
- **暂停态可跨会话恢复**：`处理设计问题` 新增第 5 步——进入摊牌/暂停即记 `--result blocked`，拍板后改 `pass`；新会话据 `result: blocked` 行识别「上次停在哪、为何停」，不靠对话记忆（与中断恢复、读取上下文闭环）。
- **三处无界回环补熔断**：原理图与 PCB 的「双通道互验 → 回绘制」各加**同一部分最多 3 轮**、满轮转 `处理设计问题` 摊牌（此前只说「任一发现错误即回退」，遇环境性错误会无限重画）；`引脚索引` 与框图/连接图之间的「回上游修正」加**同一悬空引脚最多往返 3 次**，禁止三文档互踢。
- **写产物脚本 cwd 守卫全量覆盖**：此前只有 4 个新脚本有守卫，`visual-qa / tool-probe / tool-probe-simulator / net-download / bom-enrich` 仍可能在 skill 仓库内跑出 `skill仓库/tmp/` 污染（实测复现）。现 9 个写文件脚本一律拒绝以 skill 仓库为 cwd 运行（`--help`/`-h` 放行，便于查用法），FILE_CREATION_POLICY §1/§2.3 由文字升级为机器强制；指令索引使用纪律第 5 条同步记录该行为。
- **策略文档合规拆分**：`scripts/net-download-policy.md`（93 行，违反 RULE_EDIT ≤50）拆为**总索引 + 4 子文件**（`格式白名单/`、`格式黑名单/`、`URL与路径防护/`、`用法与会话纪律/`，均 ≤50 行）；顺带修掉 5 处指向已不存在的旧 `SKILL.md §13.2/§13.1/§8.4/§9` 节号，改指现行 `references/` 正本；`net-download.py` 的 `POLICY_DOC` 与拒绝报错文案改为精确指向子文件（实测 `.zip` 拒绝、无扩展名拒绝、`.pdf` 放行三条信息均正确）；11 个引用点全部重连，0 悬空。
- **低模型可用性**：`元件连接图` 的「具体命令以 `--help`/`actions` 为准」改为 `python scripts/sch-verify.py --project <工程>` 一键取 pin→net 真值。
- **仓库清理**：删除 `references/lib/` 下 13 个历史拆分残留的**空目录**（未被 git 跟踪、无文件）；README 中 lib 份数自相矛盾（一处 13 一份 8）统一为 **12 md + 1 json**，并去掉三处裸 `§11.5/§13.3` 旧节号（补指 `references/lib/discipline-checkpoints.md` 等真本）；README 不再硬编码 SKILL 版本号（改指 frontmatter 为唯一真值，防每次发版漂移）。
- 校验：`check-links` → **187 个 md，悬空 0、孤立 0**；4 个策略子文件入链各 1–3 处；12 个脚本 `py_compile` 全过；references/ 与 scripts/（非 lib）全部 ≤50 行；从 SKILL.md BFS 可达 181 个 md、活动树不可达 0；账本功能实测（模板 `- [ ]` → `progress-log` 幂等翻转 `- [x]`、缺产物 exit 1）；`net-download` 守卫与三条格式判定实测通过。版本对齐 **0.12.16**。

### v0.12.15（2026-09-18）

- **重复交互操作脚本化（用户拍板 4 项全做）**：把散落在多份 markdown 里反复手敲的命令序列固化为一键脚本，markdown 改为连接脚本调用。新增：
  - [`scripts/link-probe.py`](scripts/link-probe.py)：桥接探测一键（MCP 7655 / 桥接 8765 / daemon 60832-60841 TCP 探活 → `update --check --exit-code` 版本门禁 → `health --json` → 按 connection-setup §1.1 输出选定链路），聚合落 `./tmp/init/link-probe.json`，退出码 0/2/3 即门禁结论。
  - [`scripts/sch-verify.py`](scripts/sch-verify.py)：原理图验证一键（`sch gate --strict --json` 四联超集 + `connectivity --all-pages` + `list --include-device-identity --include-pins` + `sheet-geometry`；gate blocked 时兜底补 `sch check`），聚合落 `./tmp/sch/verify-*.json`。
  - [`scripts/pcb-gate.py`](scripts/pcb-gate.py)：PCB 门禁一键（`drc --json` + `check --json --strict` + `layout-lint --json` + `layout-score --json` + `net-classes --json` + `report` 文本；可选 `--with-gate` 推进 `pre_route_passed`），聚合落 `./tmp/pcb/gate-*.json`。
  - [`scripts/progress-log.py`](scripts/progress-log.py)：进度账本一键写入（按步骤门禁格式幂等追加/替换同步进步骤行），替代 Agent 手编 markdown。
- **子命令 JSON 支持实测**（本机 CLI v1.4.8 `--help`）：`sch gate --json`（含每阶段原生报告，四联超集）、`pcb check --json --strict`、`layout-lint/--score --json`、`net-classes --json` 可用；`report`/`connectivity`/`list`/`sheet-geometry` 无 `--json`，脚本按文本原样捕获，判据以 rc 为准。
- **脚本层防污染守卫**：4 个新脚本启动即检测 `cwd` 是否为 skill 仓库（存在 SKILL.md+RULE_EDIT.md 即拒绝运行并提示先 cd 工作区），把 FILE_CREATION_POLICY §1/§2.3 从文字约束升级为机器强制；实测从 skill 目录跑 `progress-log.py` 被拒（此前实测确会写出 `skill仓库/tmp/` 污染，已清理）。
- **markdown 接链改写（10 处）**：`桥接联通性测试`（流程前置脚本说明，人工步骤降为判据描述与失败兜底）、`门禁检查`、`端口探测与插件确认`、`部分绘制与验收`（数据层四条→一条）、`检查是否符合规范技术手册及方案`（规范硬门→一条）、`部分绘制与截图`（每步对账+数据层→一条）、`交付报告`（门禁明细改引用聚合 JSON，保留 not_run 纪律）、`校验与对账`/`检查与导出`（索引表各加一键脚本行）、`步骤门禁`+`执行与回写`（账本一律走 progress-log.py）、指令索引使用纪律加第 6 条「重复序列优先走封装脚本」、SKILL.md §4 文档地图登记 4 脚本。README 脚本清单同步。
- 校验：`check-links` → **183 个 md，悬空 0、孤立 0**；12 个脚本 `py_compile` 全过；非 lib references 全部 ≤50 行；功能实测——link-probe 真实检出本机双链路连通→选定 cli-daemon、版本门禁 rc=10 → exit 3（终止性）；pcb-gate 对不存在工程逐项 rc=1 → 聚合 JSON + exit 3（不误报通过）；progress-log ↔ check-progress 账本往返一致。SKILL.md/agent 版本对齐 **0.12.15**。

### v0.12.14（2026-09-18）

- **修复漏问 PCB 走线宽度**：用户实测反馈「仍然没有问我 PCB 走线角度和宽度」。根因：R1 只问了拐角角度，**没把走线宽度作为独立必答项**；且 `硬编码规则/PCB/间距与线宽.md` 正本里只有图形质量条、无走线宽度档位表，导致实际执行时宽度被漏问。
  - 拆解：原 R1 → **R1 走线拐角角度** + **R1b 走线宽度分级**（全板统一线宽 vs 按角色分级，含信号 / 时钟 / 差分 / 电源主干 / GND 回流各档位拍板）。
  - 正本补强：在 [`references/电气检查/硬编码规则/PCB/间距与线宽.md`](references/电气检查/硬编码规则/PCB/间距与线宽.md) 新增「**走线宽度档位表（按角色分级，正本）**」（覆盖 1 oz/2 oz、内层/外层），并说明与电流换算（载流与温升.md）、阻抗目标（叠层与阻抗控制.md）的联动关系；用户拍板档位后 `pcb net-classes` 回读须与所选档位一致。
  - 门禁强化：「R1/R1b 未问或未答 = 不得开工（P0 强制中断等答复）」；「沿用须有出处」已写入第 11 行。SKILL.md 版本 0.12.13 → **0.12.14**。
- 连带更新：`用户PCB配置文件.md` R 系列表格拆分为 R1/R1b/R2–R5（共 5 项，原 4 项）；引用路径修正为正确相对路径（`../../电气检查/...`）。校验：`check-links` → **183 个 md，悬空 0、孤立 0**；非 lib references 全部 ≤50 行。

### v0.12.13（2026-09-17）

- **修复运行时缺陷：会跳步骤**（用户实测反馈）。根因：六步主流程只有「链接清单」，无任何强制门禁——`easyeda workflow` 状态机只覆盖 PCB 子阶段（imported→…→routing_authorized），管不到 skill 六步；文档也未禁止跳步/合并步骤，模型可自由取舍。新增**约束第 12 项「步骤门禁」**（[`references/约束部分/步骤门禁/步骤门禁.md`](references/约束部分/步骤门禁/步骤门禁.md) 正本）：逐步铁律（禁止跳步/合并/跳子步骤）、**未留证不推进**、步骤边界三问自检、机器门禁优先、失败不得静默跳过；SKILL.md §1 置顶「逐步执行铁律」（主干始终注入，不再依赖按需加载才会看到）。
- **进度账本（可机器校验）**：新增 `./tmp/init/progress.md`（初始化时建六步占位表头），每步完成须追加 `- [x] <步骤号> <名> | t: | cmd: | art: | result:` 账目，缺字段或 `art:` 产物路径不存在即判该步未完成。新增 [`scripts/check-progress.py`](scripts/check-progress.py) 校验（缺步/缺字段/产物不存在 → exit 1 并列出待补项；账本缺失 → exit 2），并作为**交付与清理第 1 步前置卡点**（未通过不得交付）；单步执行的读取上下文/选择步骤/回写、中断恢复也统一改为先读账本，不凭对话记忆判断进度。
- **修复运行时缺陷：绘制过程中不截图**（用户实测反馈）。根因：截图要求只写在按需加载的子文档、且是「应当做」而非「无产物即未完成」的可验证判据，未禁止整批落位后补截，也没有失败兜底。现升级为**截图硬门**：每落位/移动/修改一个器件必须**当次**产出截图（`sch-`/`pcb-` 前缀）且 `exit 0`，**「退出码 0 且本次落位产出新截图产物」为唯一通过判据，缺一即该件未完成、禁止落位下一个**；明确禁止整批落位后统一补截、禁止「稍后补」；同一件重试 ≤2 次仍失败 → 命中中断点暂停上报，不得跳过继续画。已接入 `绘制原理图`/`部分绘制与截图`、`PCB绘制`/`部分绘制与验收`（拆为逐件核验子条目，判据/失败/禁止分列）。
- **违规挂钩**：跳步、合并步骤、未写账目即推进、绘制期无当次截图仍继续落位 → 处罚机制 **L2**（撤销该步结论、回退到最早未完成步骤）；同一会话重复 ≥2 次 → **L4** 收回授权。约束总则新增第 5 条「步骤门禁优先于进度压力」，堵住「为了快」的绕行借口。
- 连带更新：`目录契约` 的 `./tmp/init/` 行纳入 `progress.md`；`建立的文件` 增账本模板与完成判据；`交付报告` 增「步骤账目」字段；`读取上下文` 必读项与编号顺延；README/约束部分 的「十一项」改「十二项」并说明第 12 项不依附 FILE_CREATION_POLICY；README 脚本清单补 `check-progress.py`。SKILL.md 版本 0.12.12 → **0.12.13**，主干压到 41 行（§4 文档地图压缩为路由指针）。
- 校验：`check-links` → **183 个 md，悬空 0、孤立 0**；9 个脚本 `py_compile` 全过；references/（非 lib）全部 ≤50 行；**门禁功能实测**——构造只记 1/2/3/5 步的账本 → 检出「缺步骤 4、6」exit 1；构造缺 `art:` 字段的绘制账目 → 检出「缺字段 art」exit 1，证明跳步与漏截图可被机器发现而非仅靠自觉。

### v0.12.12（2026-09-16）

- **阻断级修复：SKILL.md frontmatter YAML 解析失败**。`metadata.version` 缩进多 2 空格使整个 frontmatter 报 `mapping values are not allowed here`，skill 可能整体加载失败；已对齐为 2 空格并通过 `yaml.safe_load` 校验。
- **路径逃逸修复：`/tmp` → `./tmp/`（7 处）**。SKILL.md §1/§3、AGENT-PROMPT、README、单步执行索引、读取上下文、记忆链把工作区运行产物目录写成 Unix 绝对路径 `/tmp`；统一为工作区相对 `./tmp/`，杜绝产物落错位置。
- **新增 PCB 侧阶段对照检查文档（补断链）**：新建 [`references/PCB制作/检查是否符合规范技术手册及方案/`](references/PCB制作/检查是否符合规范技术手册及方案/检查是否符合规范技术手册及方案.md)（五项检查 + 分支 + 依据），与原理图侧同名文档对称；PCB制作第 3 步与流程索引、电路设计标准设计流程均接链。此前 PCB 侧「检查是否符合规范/手册/方案」整步无承接文档。
- **修复三处硬矛盾**：① 链路选定规则——`端口探测与插件确认`「MCP 可达即不再探测」与正本 `connection-setup.md §1.1`「可达仍探 60832，双通优先 CLI/daemon」冲突，子文件与 AGENT-PROMPT 已按正本改写；② 版本门禁——总索引把门禁失败并入 10s×3 重试环，与「版本门禁非 0 属终止性失败」冲突，已加例外分支；③ 方案回退幅度——`生成最终方案`「回成本及预算检查重新执行」与 `检查方案及敲定`「只重跑未通过项」冲突，已统一为「只重跑未通过项，实质变更才回成本/元件重算」。
- **纠错闭环补强**：`处理设计问题` 增「同一问题重新搜索并征询最多 3 轮，满轮摊牌」熔断（此前无上限、可无限循环）；`元件检查` 总索引补「同一元件最多 2 次新建尝试」上限；`门禁检查` 通过后出口由写死「进入原理图制作」改为「返回调用方阶段」；`电气检查` 触发时机编号 ⑧ → 第 7 项。
- **命令真值对齐 CLI v1.4.8（本机 `--help` 实证）**：`pcb nets.list`→`pcb nets`、`pcb components.list`→`pcb list --include-bbox --include-pads`、`pcb layers.list`→`pcb layers`；删除不存在的 `pcb apply`（保留 `sch apply`/`easyeda apply`）；`pcb stage` 子命令补 `confirm-tier`（已被 CLI 证实存在）；`布线与过孔` 索引把「CLI 无顶层封装」更正为真实命令族（`pcb via`/`via-bond`/`via-hop`/`via-list`/`via-stitch`/`via-delete`）；`检查与导出` 补 `pcb nets`；制造文件导出明确「经官方 GUI，程序化无入口」。
- **低级模型可用性**：`python3 scripts/...` 统一为 `python scripts/...`（win32 通用入口，并写入指令索引使用纪律第 5 条）；`visual-qa.py` 示例补必填 `--project`（此前裸 `--pcb` 直接 argparse 报错）；`封装与引脚检查`/`检查是否符合技术手册及方案` 补具体回读命令（`sch list --include-device-identity/--include-pins`、`lib footprint get`、`sch connectivity --all-pages`、`pcb list --include-pads`）；`系统框图` 确认形式、`元件关系图` 对账基准、「差异超预期」判据（新增/消失网络非 0 或器件数不符）、成本损耗率默认值均量化落文；`目录契约` 补 `./tmp/init/` 行；数值正本表述统一为「daemon 规则代码（Go）+ JLC 官网」。
- **脚本裁剪与加固（判据：被流程挂接 + 可运行）**：删 7 个无挂接且断链脚本（`lint.py`/`lint.sh`/`diff.py`/`orient.py`/`sch.py`/`probe.js`/`blocks-pin-audit.py`，均依赖已删数据文件 `orientation.json`/`standard-parts.json`/`symbol-pins.json`）；修 6 个保留脚本——`tool-probe.py` 探针失败不再产出「伪清单」（加 `probe_status` 并 exit 2）、`net-download.py` 超限删除半成品文件、`bom-enrich.py` 缺失标准件库时优雅退出并加 `--out` 工作区校验、`visual-qa.py` 默认 `--artifacts-dir` 改为 `./tmp/snapshots` 并修过时节号、`tool-probe-simulator.py` 文档串与实际输出对齐；新增 [`scripts/check-links.py`](scripts/check-links.py) 全树链接扫描（悬空必须 0），并写入 RULE_EDIT 第 6 步。
- **文档事实修复**：README 重写失实内容（v0.12.2→v0.12.11、虚构的 `Sample/easyeda-agent/` 目录树、脚本清单、链路选定规则、失效的 §4/§8 节号引用、重复行与编号错乱）；CONTRIBUTING 重写（删除不存在 `requirements.txt`/pytest 测试套件与错误命名约定，首行声明 RULE_EDIT 优先，发布流程改 `git merge --no-ff dev`）；agents yaml 的 `default_prompt` 由 v0.6.0 旧纪律同步为现行 one-liner 并升版本、homepage 修正为真实远端 `XianYin69/EasyEDAssistant`；删除 `agents/EasyEDAssistant.json`（Kilo 客户端 config validator 会把 skill 目录下 `agents/*.json` 当 agent 定义发现并报警，且文件自述「Kilocode 不加载 agents 下的 .json」，纯冗余）；lib 内 `project-docs` 去 `blocks-pin-audit` 悬挂引用、`discipline-checkpoints` 快照命名对齐滚动轨、脚本旧节号 §5.2/§2.3 与 `.gitignore` §2.4 修正。
- 校验：`python scripts/check-links.py` → **182 个 md，悬空 0，孤立 0**；7 个脚本 `py_compile` 全过；references/（非 lib）全部 ≤50 行；SKILL.md 44 行、frontmatter 可解析；版本对齐 0.12.12。

### v0.12.11（2026-09-16）

- **用户PCB配置文件补 R1–R5 扩展必答项 + 硬门禁（测试未被确认事故的整改）**：新增 R1 走线拐角角度、R2 走线策略（关键网/等长组/换层/是否允许自动布线）、R3 铺铜策略、R4 **版权信息与标识**（文本/层/字号下限，「不加」也要记录）、R5 其它偏好兜底（防逐项漏问）。门禁升级：D1–D20+R1–R5 **逐条闭环**——未问或未答即不得开工（P0 强制中断）；「沿用」必须出示出处，无出处视为未问过；禁止代用户填默认值、禁止把「用户没提」当「同意默认」。原「只问会改变做法的项」措辞系漏问根因，已改写。
- **PCB设计规范挂接硬编码规则**：规范来源新增 PCB规则索引（五件通用打底）+ 按电路类型绘制与制版条款（加严），与电气检查同源。
- **硬编码规则大扩充：`PCB/绘制与制版规范/`（1 索引 + 5 类型文件 × 10 条 = 50 条）**：电源电路（环路最小化/SW 铜最小化/铺铜代替细线/挂锡/铣槽隔离/2oz 制版升档）、RF与高频（完整参考层/Z0 外部计算声明/λ20 缝合/禁 V-Cut 穿天线区/0402 C0G/枝节 λ20 判废）、数字高速（4 层起/阻抗网清单先行/换层双地孔 50mil/BGA 出线档/SMT 0.5mm 间距）、模拟小信号（guard 环/独立回流孔/8mil 精度档/热对称成对）、混合信号与隔离（接地架构拍板前置/禁跨分割/隔离带三要素/UL 声明）。通例数值标注「通例」，可查数值引用正本（fab-rules-jlcpcb.json/既有子域文件），不另造第二套真值。
- 接线：PCB规则索引子文件表 + 硬编码规则总览 PCB 行；全树悬空链接 0；本轮文件 ≤50 行（最大 38）。SKILL.md 版本对齐 0.12.11。

### v0.12.10（2026-09-16）

- **图片回收机制脚本化（逐件截图后滚动 3 张纪律的落地修复）**：v0.12.9 起每器件产一张验证图，但「删到最近 3 张」只写在文档、无执行方，且 CLI 产物名无 `sch-`/`pcb-` 前缀致分开计数不成立——现由 `visual-qa.py` 强制回收：新增 `_stamp_and_prune`（截图产物自动盖 `<sch|pcb>-<时间戳>-<ns尾>` 前缀名、组内按 mtime 保留最近 3 张、删其余，前缀互不侵占）与 `_discard`（PCB stale 废帧即删，不占滚动配额）；滚动纪律不再依赖 Agent 手动清理。归档轨（`./tmp/sch/`、`./tmp/pcb/` 逐部分两张）与会话末 tmp 清理不受影响。
- 同步措辞：`绘制原理图/部分绘制与截图` 验证图条、`PCB绘制/部分绘制与验收` 验证图条、`lib/verification-delivery.md` §8.3 滚动轨——均改为「脚本自动回收，Agent 无需手动清理」。
- 滚动回收单元冒烟 8 项断言全过（改名/保留3/无残留/前缀隔离/废帧丢弃/None 安全）；悬空链接 0；SKILL.md 版本对齐 0.12.10。

### v0.12.9（2026-09-16）

- **PCB 放置纠错粒度对齐原理图为逐件（用户拍板）**：`PCB绘制` 总索引第 4/5 步与 `部分绘制与验收` 放置步——每放置/移动/修改一个器件即跑 `visual-qa.py --pcb --pcb-doc <页> --artifacts-dir ./tmp/snapshots`（截图 + 重叠/出框/drc 数据核验，stale 自动切前台重试），exit 0 才画下一个；`stage confirm-tier` 只签档位汇总不替代逐件核验。截图清理改双轨：验证图逐件滚动 3 张（snapshots），归档图逐部分两张（./tmp/pcb/）。
- **元件编辑补「试放双通道验证」（用户拍板）**：`新建元件与替代方案` 新增建元件节——命令行建立（blocks search → lib symbol/footprint create→build → lib device build，官方件 copy 后改）+ 数据层（create 回读 + `lib footprint/symbol get` 逐项对照手册）+ 呈现层（临时页/板试放一件 → export-image/snapshot → `visual-qa.py` 阻断判定 + 目检）；任一通道不过不算建立完成；通过后清理试放件与临时文档、验证截图归档 `./tmp/sch/` 登记进检查结论。
- 三处文件仍 ≤50 行（36/30/32），全树悬空链接 0；SKILL.md 版本对齐 0.12.9。

### v0.12.8（2026-09-16）

- **指令索引补「新建对象」链路（用户问询触发，经 `easyeda actions`/`api search`/子命令 help 实测）**：
  - 总索引新增**新建对象速查**跨域表：新建工程——**CLI 与 138 个 typed action 均无入口**，官方仅 `eda.dmt_Project.createProject`（@beta），推荐 GUI、程序化只作 debug exec 确认门控例外；新建页/板/元件/封装条目与子文件锚点。
  - `器件库与块` 展开 `lib footprint|symbol|device` 全套子命令：`create`（空资产+回读验证）/`build`（JSON spec 编写，**封装/符号编辑主入口**，全量重写式）/`copy`（官方件改前先复制到可写库）/`get`/`delete`/`model3d`，`device build` 为新建元件一条龙；已放置件换绑指向 `sch rebind-footprint/rebind-symbol`。
- 两文件仍 ≤50 行（45/43），悬空链接 0；`SKILL.md` frontmatter 版本 0.12.2 → **0.12.8** 与 CHANGELOG 对齐。

### v0.12.7（2026-09-16）

- **新增 `references/嘉立创EDA指令索引/`（总索引 + 12 子文件，共 13 份，用户批准建子文件夹）**：嘉立创 EDA（`easyeda` CLI v1.4.8 自描述 + MCP typed action）的**运行时指令入口索引**——条目 + 一句话语义 + 流程落点，参数真值仍指向 `--help` 与 `easyeda actions`。补上上游 `actions.md` 随 Sample 清理后缺失的运行时命令目录层（`lib/api-operations.md` 为维护者速查、不参与运行时加载）。
- **结构**：总索引（真值优先级/刷新方法/使用纪律）→ 会话与文档（全局 flag、门禁、doc/view/board/workflow/apply/spec/audit）；原理图指令 →（放置与编辑 / 连线与网络 / 校验与对账）；PCB指令 →（放置与布局 / 布线与过孔 / 铺铜与区域 / 检查与导出）；器件库与块（lib/blocks/bom + parts-select 管道 + eext 批量放置）；动作目录与队列（actions/call/api/debug 与 apply playbook 契约）。
- **条目来源**：`easyeda --help`、`easyeda sch/pcb/lib/blocks/bom/board/doc/workflow/apply/spec/view/api/call/debug/audit/project/daemon/update/skill/notify --help` 实测采集（v1.4.8）；发现 v1.4.8 顶层无 `pcb via-hop/via-bond/line.create` CLI 封装——过孔等图元操作归入「动作目录与队列」经 `actions`/`call`，与 `easyeda workflow` 帮助中 `pcb.line.create`/`pcb.via.create` 为 action 名的表述一致。
- **流程关键步骤挂接 7 处**：`SKILL.md` §4 路由登记；`绘制原理图/输入读取`（原理图指令索引）、`绘制原理图/部分绘制与截图`（对账步查索引）、`PCB绘制/输入读取`（PCB 指令索引）、`PCB绘制/部分绘制与验收`（对账步）、`元件检查`（器件库与块）、`桥接联通性测试`（会话与文档 + 动作目录与队列）。
- 全部新文件 ≤50 行、自然语言；主文档与文件夹同名、子文件与其子文件夹同名；全树相对链接悬空 0。

### v0.12.6（2026-09-16）

- **逐件截图纠错（用户拍板：画一个元件截一次图，不等整页画完）**：`绘制原理图/部分绘制与截图` 绘制与截图节重写——器件落位按件推进，每落位一个器件运行 `visual-qa.py --schematic` 截图 + 越界核验，exit 3 当场回移/重画后才画下一个；eext CSV 批量落位改为「落位后逐件核验整批」；验证图（滚动 3 张）与归档图（逐部分两张）双轨分离。
- **图纸几何前置**：`绘制原理图/输入读取` 第 1 步并入 `sch sheet-geometry`（图纸大小、可绘制边界与坐标），输入不齐（含图纸边界）不动笔；逐件 bbox 必须完整落在边界内（针对测试中「原理图画到图纸外」事故）。
- **`scripts/visual-qa.py` 审查与修复（确认可后台截图、无 OS 鼠标操作）**：
  - **修复「压根没截图」三连**：① `--both/--pcb/--schematic` 为文档示例用法，但旧 argparse 只有 `--mode`，按文档调用直接 argparse 报错 exit 2（与 WARN 语义混淆）——现 flags 全部实现；② `capture=False` 路径（`view fit`/`pcb snapshot`）失败此前完全静默——现在非零退出码一律上报；③ 截图产物按「本次调用后 mtime」新鲜度过滤，不再可能误拿旧 PNG 冒充新截图，无新产物 = 阻断（exit 3）。
  - **新增原理图越界核验**：采集 `sch sheet-geometry`，逐器件 bbox（兼容 `[x,y,w,h]`/`{x,y,width,height}`/`{x0,y0,x1,y1}`）对图纸边界判定，越界 = blocking 并列位号；边界或器件数据缺失 → 越界检查标「未运行」判 WARN，不得当作通过（单元冒烟 7 项断言全过）。
  - **stale 自动恢复**：PCB 截图检出 canvas-freeze 后经 `doc switch`（--pcb-doc）切前台自动重试 ≤2 次；`view fit`/`doc switch` 均为 easyeda CLI/daemon API——**不发送任何 OS 级鼠标/键盘事件**；`sch export-image` 文档渲染天然支持后台。
  - 新增 `--prev-sha`、`--summary`、`--out`（工作区内强制）；报告继续维护 `prev_sha` 闭环。
- 同步正本与步骤文档：`lib/connection-setup.md` §2.8 的 visual-qa 命令改为含必填参数的完整示例并写明逐件 `--schematic` 要求；`lib/verification-delivery.md` §8.3 用法示例、退出码语义、边界与生命周期条目更新；`绘制原理图.md` 第 4 步挂逐件核验。
- 全树相对链接悬空 0；本轮所改步骤文件均 ≤50 行。

### v0.12.5（2026-09-16）

- **高速推理/工具/绘图优化（联网检索结论经用户批准入判据，共六条）**：
  - **① 主干静态化 + 只增不改升格性能判据**（依据：Anthropic Claude Code prompt-cache 前缀匹配经验、arXiv 2605.26289 相邻轮 85–95% 前缀复用）：`约束部分/上下文存储压缩机制` 新增第 8 条——SKILL.md 主干与路由表会话内保持静态、变更走文末追加或子文件，按需加载以消息注入不回写主干；`逻辑链的存储` 第 5 条「只增不改」补注缓存复用前提并互链。
  - **② 批量优先**（依据：Anthropic code-execution-with-MCP、mcp-batchit、claudecodeguides 批处理模式）：`lib/api-operations.md` 新增操作纪律 9——一模块一队列（apply 队列、`autoconnect --spec`），禁止逐器件多轮编辑器往返，独立只读检查同批并行，写操作队列内有序。
  - **③ 大输出落盘、上下文只进摘要**：`上下文存储压缩机制` 第 4 条强化为硬判据——大回读一律 `> ./tmp/<子目录>/<名>.json`，上下文只留统计行与路径（`api-operations` 纪律 9 同步）。
  - **④ 写路径首选 CLI/daemon**（依据：MindStudio MCP-vs-CLI token 研究）：`lib/connection-setup.md` §1.1 与 `桥接联通性测试` 链路选择更新——两条链路都连通时优先 CLI/daemon（批量写一次派发、开销低），MCP 留作交互式细查；选定后仍全程单链路不切换。
  - **⑤ 每页 ≤150 元件**（依据：官方 place-device 文档，原理图引擎非新引擎超限卡顿）：写入 `部分绘制与截图` 技术细节拍板判据，拆页优先于密排。
  - **⑥ 官方批量放置 eext 入流程**（依据：github.com/easyeda/eext-batch-place-components）：`api-operations` 命令族索引与 `部分绘制与截图` 绘制步挂接——用户装有该扩展（tool-probe 清单可查）时可用 CSV 坐标批量初始落位（表头带单位），之后照常回读对账；此为官方路径，替代已删的 bulk-place.py。
- 全树相对链接悬空 0；本轮修改的步骤文件均 ≤50 行、自然语言。

### v0.12.4（2026-09-16）

- **脚本裁剪（设计流程调用审计）**：`references/` 全树扫描确认 5 个上游脚本无任何流程调用点——`audit-baseline.py`（离线审计分析）、`bulk-connect.py`/`bulk-place.py`（无调用入口的批量操作）、`parts-add.py`（写回的 standard-parts.json 已删）、`calibrate.js`（依赖的 orientation.json 已删），全部删除；保留的 13 个脚本均有 `references/` 或 `lib/` 挂接点（含 `orient.py` 被 `lint.py` import）。
- **截图逻辑修复（用户意图：绘制期「截图 + 命令行」双通道纠错，交付期归档图作技术手册插图）**：
  - **归档 + 滚动双轨**：每部分验收通过时局部图+全图即时归档 `./tmp/sch/`、`./tmp/pcb/`（命名 `<sch|pcb>-<部件号>-<局部|全图>-<时间戳>.png`，交付插图来源，不随清理删除）；`./tmp/snapshots/` 降为纯滚动工作快照（留最近 3 张，`sch-`/`pcb-` 前缀分开计数）。修复原「滚动 3 张上限」与「验收保存各部分局部截图」的硬矛盾。
  - **stale 判定归位**：fresh/stale（`--previous-sha256`/canvas-freeze）仅适用于 PCB 视口快照；原理图 `sch export-image` 为文档渲染、无需上帧比对（原原理图子文档误套 stale 逻辑，已删改）。
  - **双通道纠错挂接**：原理图/PCB「检查美观和正确」呈现层挂接归档截图判读 + `python3 scripts/visual-qa.py`（0/2/3 退出码），与数据层门禁互验，任一发现错误即回修；补上 visual-qa.py 从未被步骤文档触发的路由缺口。
  - **交付文档插图来源放宽**：手册插图原理图用官方导图、PCB 用 fresh 归档快照；技术手册内容清单改引 `./tmp/sch/`、`./tmp/pcb/` 归档截图（引用前导出到手册路径）。
  - 同步正本：`lib/verification-delivery.md` §8.3 改「截图生命周期（归档+滚动双轨）」；`lib/connection-setup.md` §2.9 改「截图双轨管理」并修正 stale 适用范围。
  - 涉及文件：`绘制原理图/`（总索引+2 子文件）、`PCB绘制/`（总索引+1 子文件）、`交付与清理/交付文档/`、`lib/verification-delivery.md`、`lib/connection-setup.md`；步骤文件均 ≤50 行、自然语言；全树相对链接悬空 0。

### v0.12.3（2026-09-16）

- **移除上游 skill 注册根源，Sample 降级为存档**：删除 `Sample/easyeda-agent/SKILL.md`（去 frontmatter，不再被 Kilo 注册为独立 skill，根除运行时劫持本项目流程的根因）、`.version`、`agents/openai.yaml`；`Sample/` 仅保留 `README.md`（本项目自撰的去注册说明）与 `LICENSE`（上游 MIT 原版）。
- **参考正本迁入 `references/lib/`**：被 `references/` 引用的 5 份上游文档（`environment-setup.md`、`design-flow.md`、`pcb-design-spec.md`、`pcb-design-rules.md`、`fab-rules-jlcpcb.json`）整体迁入 `lib/`；`lib/design-flow.md` 内指向已删上游文档的链接改为本项目 `references/绘制原理图/`、`references/坐标与数据模型/`、`references/PCB绘制/` 等路径。
- **14 个脚本迁入 `scripts/`**：`audit-baseline.py`、`blocks-pin-audit.py`、`bom-enrich.py`、`bulk-connect.py`、`bulk-place.py`、`calibrate.js`、`diff.py`、`lint.py`、`lint.sh`、`orient.py`、`parts-add.py`、`parts-select.py`、`probe.js`、`sch.py`；删除 `tests/`（fixtures/golden 随上游 skill 一并退场）。
- **清空余下 Sample references**：`Sample/easyeda-agent/references/` 下未引用的 20 份（schematic*/pcb*/design-*/part-selection/actions/orientation/sheet-templates/standard-parts/symbol-pins 等）与 14 份 tests/ 目录整体删除，因逻辑多已在本项目 `lib/` 与步骤文档实现。
- **跨目录链接改写**：`references/PCB绘制/PCB设计规范/`、`用户PCB配置文件/`、`输入读取/`、`桥接联通性测试/`（含 `门禁检查/`）、`references/lib/`（connection-setup / discipline-checkpoints / external-resources / design-rules）中的 `Sample/easyeda-agent/references/` 前缀统一改为 `references/lib/` 或本项目对应路径。
- **`约束部分/文件与文件夹创建范围.md` 更新**：第 2 项将「`Sample/easyeda-agent/` 存参考件」改为「`Sample/` 存上游存档（仅 `.md` 与 `LICENSE`）」，并新增「`references/lib/` 存 `.md`/`.json` 正本」；第 4 项「禁止位置」的 `Sample/easyeda-agent/` 改为 `Sample/`。
- **README / AGENT-PROMPT 同步**：组件表把 `Sample/easyeda-agent/references/*.md`、`agents/openai.yaml` 等上游条目替换为 `references/*.md`、`agents/EasyEDAssistant.yaml` 等本项目正本；删除 `Sample/easyeda-agent/agents/openai.yaml` 与 `references/*.md` 上游条目。
- 全树相对链接经脚本核验悬空数 0；`references/`（不含 `lib/`）仍 ≤50 行、自然语言。

### v0.12.2（2026-09-16）

- **新增 `references/交付与清理/`（总索引 + 3 子文件）** 作为标准流程第 6 步：流程为前置条件（检查全过、原理图/PCB 验收）→ 生成交付文档 → 用户确认 → 交付报告 → 清理 `./tmp/`（先交付后清理）。子文件：`交付文档/`（技术/功能手册，只来自回读+分析+蓝图引用，`blocked`/`fail` 不得写通过）、`交付报告/`（六字段报告 + 验证分层结果 + 清理摘要）、`清理/`（先导出保留图片再删 tmp、例外与异常收尾）。`PCB制作` 收尾指向本步骤；内容引用 `lib/project-docs.md §7.8` 与 `lib/verification-delivery.md §8.1–§8.4`。
- **新增 `references/单步执行/`（总索引 + 3 子文件）** 填补 SKILL.md §3「待补」：流程为读取上下文（`./tmp/init/workspace-init.md` + 方案/基线/检查结论/图纸/报告，缺失即标注缺失工件）→ 选择步骤（列出六步与单动作，询问用户不代选）→ 执行与回写（只跑被选步骤、写前读、验证后保存 `saved:true`、三段式报告）。子文件：`读取上下文/`、`选择步骤/`、`执行与回写/`。
- **健壮性门限（循环/重试上限）**：桥接连通性测试门禁不通过等待 10s 重试，同一会话最多 3 轮，超限转用户摊牌（继续重试/换链路/查安装/中止），`端口探测与插件确认`、`门禁检查` 同步并入 3 轮额度；元件检查新建元件同一元件最多 2 次，超限转替代方案；成本及预算检查替代方案第 5～7 步最多 3 轮，超限转用户（继续检索/接受原方案/调整需求或预算/中止）。
- **去重与确认门**：检查方案及敲定未通过改为只重跑未通过项（方案实质变更才回成本/元件重算），并删除与 `生成最终方案` 重复的决策句（该询问只在一处发生）；专业技术规范检查豁免须用户明确回答「接受该风险并豁免」才登记，仅记录原因不构成豁免，未获明确同意仍判未通过；成本及预算检查未超预算自动通过须在方案文件与交付报告留痕（成本数字/批量档/取价时间）。
- **AGENT-PROMPT.md 重写为当前版本**：入口速览列六步、单步执行、链路 3 轮门、不可省略的用户确认项（预算/替代、元件新建与豁免、规范检查豁免、原理图/PCB 验收、最终方案与交付文档）、交付与清理收尾；更新 one-liner。
- **README 对齐当前版本（不拆分）**：目录树与章节表加交付与清理/单步执行；流程图综述改六步、非首次设计走单步执行；连接方式改「互为替代、非级联备用」、重试 3 轮；收尾与文档任务指向交付与清理；版本标注 0.12.0 → 0.12.2。
- **`stream.html` 入库**：用户用 draw.io 绘制的流程图（基于 diagrams.net viewer CDN 渲染），原样提交，不改内容。
- 标准设计流程索引补第 6/7 条（交付与清理、单步续跑入口），后续子步顺延；SKILL.md §2 步骤补交付与清理、§3 改为已写并链接单步执行、§4 待补表更新；全部新增文件 ≤ 50 行、自然语言。

### v0.12.1（2026-09-16）

- **核对 `references/lib/` 的引用与实现状态**：11 份中 6 份被 `references/` 引用（connection-setup / design-rules / discipline-checkpoints / external-resources / project-docs / verification-delivery，保留为正本）；5 份仅被 README 与维护者索引提及，其中 3 份内容已由步骤文档实现、2 份未实现。
- **已实现项简化**：删除 `references/lib/design-decisions.md`（23 行，PCB 侧由 `references/PCB绘制/用户PCB配置文件/` 的 D1–D20 承接，未覆盖的 9 个决策点（叠层/VCC 内层/地域/线宽分级/USB 架构/自动下载/选型档位/单双面/焊接工艺）已补入该文件的「附加决策点」段）；压缩 `references/lib/api-operations.md`（153 → 32 行，保留命令族索引与跨步骤操作纪律：autoconnect 幂等与硬拒与 35s 预算、`sch connect` 不幂等、apply 保护队列契约、`doc reload` 铁律、via-bond、截图与验证分层）；压缩 `references/lib/layout-aesthetics.md`（63 → 27 行，保留原理图可读性与 PCB 美观经验要点）。
- **未实现项迁出后删除**：`coordinates-model.md` → 新建 `references/坐标与数据模型/坐标与数据模型.md`（raw/mil/mm 与 y-UP、数据模型五要点）；`official-docs.md` → 新建 `references/官方文档映射/`（总索引 + `官方文档索引/` + `GUI指令映射/`，含原理图 11 项、PCB 15 项菜单→命令对照）。
- **接入引用**：`引脚索引`、`绘制原理图/输入读取`、`PCB绘制/输入读取` 挂接坐标与数据模型；`桥接联通性测试`、`PCB绘制/PCB设计规范` 挂接官方文档映射，避免新文档成为孤链。
- **README 改为目录级说明**：目录树与章节表不再逐条列 lib 文件（原 11 条路径写作 `references/xxx.md` 已失效），改述 `references/<步骤>/`、`references/约束部分/`、`references/lib/`（8 份，维护者文档，不参与运行时加载）；两处 `references/design-rules.md` 更正为 `references/lib/design-rules.md`，版本标注 0.10.0 → 0.12.0。
- lib 精简后为 8 份（早前 1524 行 → 1145 行），全部文件 ≤ 50 行、自然语言。

### v0.12.0（2026-09-16）

- **`FILE_CREATION_POLICY.md` 瘦身为 v2.0（203 行 → 50 行，符合 RULE_EDIT ≤50 行）**：只保留「设计执行期大模型使用文件的范围、工作区的范围及权限」——§1 概述与 skill 目录/工作区边界、§2 文件使用范围（允许/禁止/运行产物落位）、§3 路径逃逸防护、§4 权限与审批、§5 细则索引、§6 修订历史；节号迁移 §2.4 → §2.3、§5.2 → §3。
- **§1.2 新增适用边界（解决 §2.1 冲突）**：本政策只适用于 PCB / 原理图**设计执行期**在工作区创建文件；编辑 skill 本体（`SKILL.md`、`references/`、`scripts/`、`Sample/`、`CHANGELOG.md`、`RULE_EDIT.md`）一律改由 `RULE_EDIT.md` 管辖，不受政策目录白名单限制。`RULE_EDIT.md` 同步写明该边界。
- **`references/约束部分/` 扩为 11 项（新增 3 个同名子文件承接迁出内容）**：`文件与文件夹创建范围/`（工作区与 skill 仓库两侧的允许/禁止类型与位置、tmp 例外）、`创建操作流程/`（需求分析→方案→审批→创建→验证→版本控制六步与紧急修复/文档更新/脚本修改特例）、`安全与合规/`（内容安全与密钥自查、路径与下载门禁、权限与 `.gitignore` 纪律）。
- **入站引用重指向**：`scripts/net-download-policy.md`、`references/lib/connection-setup.md`、`references/lib/verification-delivery.md`、`references/lib/external-resources.md`、`references/初始化部分/`（5 处）与 `references/约束部分/`（5 处「依据来源」）中的 `FILE_CREATION_POLICY.md §N` 全部改指 v2.0 新节号或迁出后的正本文件；CHANGELOG 历史条目不改写。
- `SKILL.md` frontmatter 版本 0.11.0 → **0.12.0**，§4 待补表与 §5 约束部分改列十一项并写明适用范围划分。

### v0.11.11（2026-09-16）

- **`references/约束部分/` 由占位改写为总索引 + 8 项同名子文件**（每项统一结构：约束条款 → 违规后果 → 依据来源）：`文件命名规范/`（用途可辨、禁随机名、工件与手册与截图与提交信息命名式）、`垃圾处理/`（产物只落工作区 `./tmp/`、先交付后清理、快照留 3 张、被禁格式与 `.gitignore`、暂存自律）、`记忆链/`（来源三要素 = 出处/时间/定责；最小链 init → design → parts/datasheet → 检查图纸 → 交付；证据链不是真值；断链标注缺失工件）、`逻辑链的存储/`（输入→推导→结论→拍板四段齐备，推导落 `./tmp/calc/`，数值带页码出处、未核实不推进，只增不改）、`文件存储格式/`（技术文件与数据手册可用 markdown 或 pdf，其余文档一律 markdown；机器工件不算文档；入库白名单）、`处罚机制/`（L1 立即改正 / L2 回退重做 / L3 停止并通报 / L4 收回授权；已落盘写操作不偷偷回滚；处罚不换豁免）、`激励机制/`（留证完整免重复核对、授权沉淀跨阶段沿用、`pass` 静默推进、检索复用、入库晋升、可信度积累；激励不得绕门）、`上下文存储压缩机制/`（≤50 行拆分、主干分层、按需加载子域、大回读落盘引用代替贴对话、数量体积上限、续跑只读上下文、出处与门禁结果不可压缩）。
- **`FILE_CREATION_POLICY.md` 升 v1.3**：§3.1 `references/` 行改为允许按 RULE_EDIT「总索引 + 子文件」建子文件夹（主文档与文件夹同名、子文件与其子文件夹同名），消除与现行 `电气检查/硬编码规则/`、`元件检查/`、`约束部分/` 等结构的矛盾；路由表登记要求不变，§7.2 补修订历史、版本落款 1.2 → 1.3。
- `SKILL.md` §2/§4/§5 同步：约束部分由「预留」改为已写并列出八项与存储格式总则、裁决优先级；`电路设计标准设计流程.md` 的「约束部分（留空）」改为八项已写。全部新增文件 ≤ 50 行、自然语言，相对链接经脚本核验可解析。

### v0.11.10（2026-09-16）

- **`references/电路设计标准设计流程/电路设计标准设计流程.md` 补全链接**：「流程」正文中的五个步骤（初始化部分 / 处理用户需求 / 检查方案及敲定 / 原理图制作 / PCB制作）此前只有「各步骤连接 markdown」有链接，现正文逐项内链；正文内的原理图制作与 PCB制作子流程概括改为「桥接连通性测试 → 绘制原理图 → 对照检查 → 保存」「读取 PCB 设计规范与用户配置文件 → 绘制 PCB → DRC 检查 → 保存」。
- 「各步骤连接 markdown」新增第 6～8 条：初始化部分三子步（向用户询问工作区路径 / 在工作区建立tmp文件夹 / 建立初始化文件）、原理图制作子步（桥接联通性测试 / 绘制原理图）、PCB制作子步（PCB绘制 / PCB设计规范 / 用户PCB配置文件）。
- 全 `references/`（不含 `lib/`）markdown 相对链接经脚本核验：悬空链接 0 处。

### v0.11.9（2026-09-16）

- **新增 `references/PCB绘制/`（总索引 + 4 子文件）**：流程与 `绘制原理图` 大致相同，新增「读取 PCB 设计规范」与「事先生成用户 PCB 配置文件」两步——读取方案与手册及规范 → 生成用户 PCB 配置文件（D1–D20 逐项核对，落 `./tmp/design/<工程>-pcb-spec.md`，D1 板框 / D2 安装孔 / D8 关键接口未定不得开工）→ 用户拍板叠层/接地/电源轨等细节 → 逐部分绘制（`import-changes` → 四档放置 → 布线铺铜，`doc reload` 后重跑 `via-bond`）→ 每部分截局部图与全图、`./tmp/snapshots/` 截图超 3 次丢弃三次前 → 检查美观与正确（`layout-lint --gate` / `pcb drc` / `pcb check` / `layout-score`）→ 全部完成判定 → 用户验收（接受则保存全部与部分截图并 `pcb save` 确认 `saved:true`；不接受则询问修改处回绘制）。子文件：`输入读取/`、`PCB设计规范/`、`用户PCB配置文件/`、`部分绘制与验收/`。
- **新增 `references/PCB制作/PCB制作.md`（阶段总索引）**：桥接连通性测试（沿用原理图阶段结论，不重复探测）→ 绘制 PCB → 检查是否符合规范、技术手册及方案（不符回绘制）→ 保存交付；同时使 `电路设计标准设计流程.md` 第 5 步链接可达。
- **新增 `references/约束部分/约束部分.md`（占位）**：SKILL.md §5 与标准设计流程均声明「预留」，补占位文件消除最后一处悬空链接；写入正文前不作为判据，也不得借「未约束」放宽硬门。
- 全部新增文件 ≤ 50 行、自然语言；新建文件相对链接经脚本核验全部可解析。

### v0.11.8（2026-09-16）

- **新增 `references/原理图制作/`（总索引 + 1 子文件）**：`原理图制作.md` 流程为桥接连通性测试 → 绘制原理图 → 检查原理图是否符合技术手册及方案（不符合回绘制；符合则保存原理图、截图与说明文件并确认 `saved:true`）；子文件 `检查是否符合技术手册及方案/` 列明器件与手册、连接与方案、模块与图纸、`sch gate --strict` 门禁四项对账。
- **新增 `references/桥接联通性测试/`（总索引 + 2 子文件）**，逻辑取自 `references/lib/connection-setup.md` §1.1～§1.3：先探测 `7655`（JLCEDA MCP 插件）→ 不可达则探测 `60832`（EasyEDA Agent 插件）→ 均不可达则依次询问插件是否安装、嘉立创 EDA 是否打开，是则等待 10s 重发探测，均否则提示安装；随后门禁检查（版本门禁 `easyeda update --check --exit-code`、链路健康、cwd 确认），通过标记「桥接连通性测试通过」，否则等待 10s 重发。子文件：`端口探测与插件确认/`、`门禁检查/`。
- **新增 `references/绘制原理图/`（总索引 + 3 子文件）**：流程为读取方案文件与已下载技术手册、读取绘制规则、询问用户图纸信息与技术细节、逐部分绘制、每部分截局部图与全图并在 `./tmp/snapshots/` 截图次数大于 3 时丢弃三次前截图、检查美观与正确（不通过回绘制）、判定全部完成、请用户验收（接受则保存全部与部分截图，否则询问修改处回绘制）。子文件：`输入读取/`、`部分绘制与截图/`、`用户验收与保存/`。
- 修正 `references/电路设计标准设计流程/电路设计标准设计流程.md` 5 处子步骤链接缺少 `../` 前缀（处理用户需求 / 检查方案及敲定 / 原理图制作现可达；PCB制作、约束部分 目标文件仍待建）。全部新增文件 ≤ 50 行、自然语言。

### v0.11.7（2026-09-16）

- **统一「中断并处理设计问题请求」指向**：`检查方案及敲定`（流程与判据各一处）、`元件检查`（第 4、5 步）、`元件检查/新建元件与替代方案`（校验用户手册分支）此前仅有文字、无链接，现全部挂接 [`references/处理设计问题/处理设计问题.md`](references/处理设计问题/处理设计问题.md)；全仓库该措辞共 13 处，经逐行核对均已带链接。
- `references/浏览器检索/浏览器检索.md` 与 `references/中断恢复/中断恢复.md` 的「用于『处理设计问题』第 N 步」引言补回指向 `处理设计问题.md` 的链接，形成双向可达。

### v0.11.6（2026-09-16）

- **补齐 `检查方案及敲定` 的 5 个缺失子项（每项一个同名文件夹）**：新增 `references/系统框图/系统框图.md`（字符画系统框图：模块框 + 信号/电源流向，节点须映射到实际器件，映射不到标「未落实」，落 `./tmp/design/<工程>-block-diagram.md`）、`references/元件关系图/元件关系图.md`（整体→部分→组件→元件分层归属，覆盖清单全部元件、单一归属，落 `-part-tree.md`）、`references/元件连接图/元件连接图.md`（元件为节点、net 为边，电源/地/信号记号与 netport 边界，连接真值以回读为准，未绘制时标注「待原理图核对」）、`references/引脚索引/引脚索引.md`（元件→引脚→net 黄金表，NC 显式标注、悬空即不合格，落 `-pin-index.md` + `.json`）、`references/生成最终方案/生成最终方案.md`（汇总结论与四份图纸 → 未全通过则中断处理 → 提醒并询问用户 → 同意则生成结束、不同意回退处理用户需求）。
- `references/检查方案及敲定/检查方案及敲定.md` 流程为上述 4 项可视化与「生成最终方案」挂接文档链接，消除悬空子项；全部文件 ≤ 50 行、自然语言。

### v0.11.5（2026-09-16）

- **新增 `references/元件检查/`（总索引 + 3 子文件）**：`元件检查.md` 总索引写流程——联网查询元件技术手册（查到→检查当前元件封装；查不到→询问是否建立新元件）→ 封装及引脚定义有问题则询问是否建立新元件（同意则新建元件后回查；不同意则询问是否使用替代方案：同意则中断处理设计问题；不同意则请求用户发送技术手册：提供且有效则回封装检查，否则中断处理）→ 无问题则标记「单个元件检查通过」并建立元件与技术手册的所有者关系；按元件清单逐个执行、全部通过才算通过。
- 子文件：`查询技术手册/`（检索入口与命中判定，笔记落 `./tmp/learning/`）、`封装与引脚检查/`（逐项核对封装型号与引脚定义、登记 MPN/URL/版本/页码）、`新建元件与替代方案/`（建立新元件、替代方案、请用户补交手册的三条出路）；查价以外的检索调用 `references/浏览器检索/浏览器检索.md`，中断与恢复调用 `references/处理设计问题/` 与 `references/中断恢复/`。
- `references/检查方案及敲定/检查方案及敲定.md` 流程中「元件检查」挂接新步骤文档链接。

### v0.11.4（2026-09-16）

- **新增 `references/成本及预算检查/成本及预算检查.md`**：流程为询问用户预算及期望成本 → 联网查询价格 → 计算成本 → 判是否超预算（未超标记「通过成本及预算检查」；超则联网查询替代方案 → 询问用户是否接受：接受则修改方案并回查重算后标记通过，不接受则询问是否采用原方案：接受则标记通过并记录超预算原因，不接受则回到联网查询替代方案循环）；查价与替代品检索均调用 `references/浏览器检索/浏览器检索.md`，价格记录含时间/渠道/批量档三要素。
- `references/检查方案及敲定/检查方案及敲定.md` 流程中「成本及预算检查」挂接新步骤文档链接。

### v0.11.3（2026-09-16）

- **新增 `references/专业技术规范检查/专业技术规范检查.md`**：流程为调用专业知识库逐项检查 → 通过则标记「专业技术要求检查通过」→ 不符询问用户是否修改方案（是→中断处理设计问题后回查；否→询问原因并登记豁免后返回知识库续查）；知识库未命中判据时索引 `references/浏览器检索/` 联网补充并留证 `./tmp/learning/`。
- **`references/检查方案及敲定/检查方案及敲定.md` 补链接**：电气检查挂接 `../电气检查/电气检查.md`，并在电气检查后串入专业技术规范检查步骤（挂接 `../专业技术规范检查/专业技术规范检查.md`）。
- **专业知识库大规模扩充 `references/电气检查/硬编码规则/`**：新增 6 域 15 文件——`工控与通信/`（CAN·LIN / RS-232·485 / 数字隔离与工业IO）、`电机与执行器/`（H桥有刷 / 三相FOC / 步进伺服）、`显示与光电/`（LED·OLED驱动 / 激光与光电安全）、`音频/`、`汽车电子/`（ISO 7637·16750 瞬态 / 车载接口·CISPR 25）、`测量与传感器/`；总览表同步收录并标注其为专业技术规范检查的知识库入口。

### v0.11.2（2026-09-16）

- **新增 `references/电气检查/硬编码规则/公式/` 域**：按 RULE_EDIT「总索引 + 子文件」固化电气检查所需全量计算真值——`公式索引.md` + 7 份子文件（直流电路 / 暂态与一阶二阶 / 交流谐振与磁 / 模拟与运算 / 电源与半导体 / 射频与传输线 / 物理通用 / 数学与换算），覆盖欧姆·基尔霍夫·戴维南、RC/RL/RLC 暂态与阻尼、谐振与磁、运放八式与稳定性判据、DC-DC 变换与半导体方程、传输线与 dB 链路预算、电磁热学通用式、对数相量与单位换算。
- `硬编码规则总览.md` 目录表新增「公式」域行，使用说明新增定量判据先取公式实算再对照阈值的流程要求；全部文件 ≤ 50 行、自然语言。

### v0.11.1（2026-09-15）

- **扩充 `references/电气检查/硬编码规则/`**：6 份平铺规则文件改为「域索引 + 判据子文件」结构并大幅扩充硬编码数值判据（IPC-2221B/2152/7351B、IEC 62368-1/61000-4-2/4-5、JEDEC、USB-IF、IEEE 802.3 及 TI/ADI 应用通例）。
- 原有 6 域（PCB/电源/模拟/数字/射频/滤波器）每域拆为索引 + 3~8 个判据子文件：Buck 热回路、Boost 拓扑、LDO 热耗、输入保护、电池充电、去耦接地、多轨时序、AC-DC 隔离；运放、转换器、基准 PLL、小信号前端；晶振、去耦、高速布线、总线存储、复位启动、调试口；阻抗匹配、天线 keepout、地缝合屏蔽、RF 电源偏置；无源 LC、有源滤波、接口 ESD 组合等。
- 新增 5 域：`安全与EMC/`（间隙爬电 / ESD 浪涌 / EMC 布局 / 保护器件协调）、`接口连接器/`（USB / 以太网 PHY / HDMI·DP·MIPI·LVDS）、`热设计/`、`测试与可制造性/`（DFM·DFT）、`原理图/`（ERC 与器件降额）。
- `硬编码规则总览.md` 重写为 11 域目录表并定义判据冲突优先级（手册 > 协议 > 认证 > 通例 > 板厂）；删除被取代的 6 份旧文件；全部子文件遵守 RULE_EDIT ≤ 50 行、自然语言。

### v0.11.0（2026-09-15）

- **SKILL.md 重写为流程入口主干**（≤ 50 行）：识别用户请求 → 判断是否第一次设计——是则走「电路板设计标准设计流程」，否则询问用户执行哪个步骤、读取 `/tmp` 上下文文件后执行对应步骤；标准流程与单步/续跑流程 markdown 占位；预留「约束部分」；frontmatter 0.10.1 → 0.11.0。
- 新增根目录 `RULE_EDIT.md`（编辑规则）：约束文本长度 ≤ 50 行；使用流程图逻辑编写；编辑前询问预留内容、过长时以「总索引 + 子文件」拆分、是否新建文件/文件夹；修改后更新 CHANGELOG.md 并提交 git。
- 新增 `references/电路设计标准设计流程/`：`电路设计标准设计流程.md` 总索引（流程图逻辑，≤ 50 行）写「初始化部分 → 处理用户需求 → 检查方案及敲定 → 原理图制作 → PCB制作」五步流程，初始化部分连接既有 `references/初始化部分/`；处理用户需求、检查方案及敲定、原理图制作、PCB制作、约束部分五份子 markdown 正文留空待写；SKILL.md §2 据此建立连接。
- 新增 `references/处理用户需求/处理用户需求.md`（流程图逻辑：用户提出需求 → 识别 → 明确性判断 → 构建初步需求 → 征得同意后生成初步方案，含「提问需求」两处回环）。
- 新增 `references/检查方案及敲定/检查方案及敲定.md`（流程图逻辑：获取初步方案 → 成本及预算检查 → 元件检查 → 字符画系统框图/关系图/连接图 → 引脚索引 → 电气检查 → 通过后征得同意生成最终方案；未通过则中断处理设计问题并回查；不同意则回退到处理用户需求）。
- 将 `references/处理用户需求/处理用户需求.md`、`references/电路设计标准设计流程/电路设计标准设计流程.md`、`references/检查方案及敲定/检查方案及敲定.md` 三份文件的流程图改以自然语言描述流程逻辑。
- 按 RULE_EDIT「总索引 + 子文件」拆分 `references/初始化部分/` 下的长文件：《向用户询问工作区路径》拆出 `原文引用/原文引用.md`；《在工作区建立tmp文件夹》拆出 `目录契约/目录契约.md`；《建立初始化文件》拆出 `建立的文件/建立的文件.md`；总索引从「两步」补正为「三步」并新增第 3 步「建立初始化文件」入口。
- 修改 `RULE_EDIT.md` 自洽：约束「使用流程图逻辑」改为「使用自然语言」，并将「§二 编辑流程」的文本框图改写为自然语言编号步骤。
- 新增 `references/处理设计问题/`：`处理设计问题.md`（自然语言流程：联网搜索可能的解决方案 → 询问用户如何处理错误 → 认可则更改方案并返回被中断步骤，不认可则跳回重新搜索）。
- 将 `references/处理设计问题/浏览器检索/` 与 `references/处理设计问题/中断恢复/` 提升至 `references/浏览器检索/` 与 `references/中断恢复/`（被多处复用）。
- 新增 `references/电气检查/`：`电气检查.md` 主流程（查询电气规则 → 是否通过 → 否则中断并处理设计问题）；`硬编码规则/` 按子域拆分（PCB/射频/模拟电路/数字电路/电源/滤波器 各自一份规则文件，硬编码 IPC/RF/Analog/Digital/Power/Filter 判据），联网补充查询复用 `../浏览器检索/浏览器检索.md`。
- README.md 新增「流程图综述」章节，链接 `stream.html` 并附主要流程摘要。

### v0.10.1（2026-09-15）

- **路由表收窄**：SKILL.md 仅索引 `references/初始化部分/初始化部分.md`（会话初始化：询问工作区路径→建立 tmp→建立初始化文件）与 `CHANGELOG.md`。
- 11 份详细文档（§1–§9、§11–§13）从 `references/` 根迁至维护者详细文档库（git 位置：references/lib/，重命名随本次提交入库），经维护者索引 `tmp/project-files-overview.md` 查取，主干不再逐条路由；全文 §N 引用含义不变。
- frontmatter 版本 0.10.0 → 0.10.1。

### v0.10.0（2026-09-15）

- **SKILL.md 主干化重构**：全文 1609 行拆分为"主干 + 按需加载 references/"。
  官方文档与 GUI 指令映射、§1–§9、§11–§13 逐字迁入 `references/` 下 11 个
  reference 文件（原章节编号不变），§14 变更摘要迁至本文件；主干保留
  frontmatter、§0 主干机制、连接速览、Reference 路由表、工作主线、§10
  执行纪律（全文 17 条）、§11.5 中断最小判据、tmp/ 硬规与本版变更摘要。
- frontmatter 版本 0.9.0 → 0.10.0；`FILE_CREATION_POLICY.md` v1.1 → v1.2
  （新增 `references/` 目录条款）；README 章节表与目录树同步。

### 14.- v0.9.0（2026-09-14）

- **新增 §13 主动学习与外部资源**：
  - §13.1 主动学习——Agent 用 `websearch`/`webfetch` 在博客园/Stack
    Overflow/知乎/CSDN/EEVblog/厂商官网/立创商城 等检索同类问题，笔记
    落 `./tmp/learning/<topic>.md`（字段：触发/URL/摘要/关键数据/工程
    映射/未证实项），是证据链不是新知识真值；不静默改 §4 判据。
  - §13.2 网络资源下载——新增 `scripts/net-download.py`（stdlib urllib
    封装，含路径逃逸防护、格式白/黑名单、32 MiB 上限、`index.json`
    审计），配套 `scripts/net-download-policy.md` 规定允许/禁止格式；
    输出根强制 `Path.cwd()/tmp/downloads`，`file://` / `..` / 可执行
    格式一律拒绝；Agent 调用规范含"先记为什么下（§13.1）再执行"。
  - §13.3 PCB 设计基线——新增 `Sample/easyeda-agent/references/`
    `pcb-design-spec.md` 定义 D1–D20 必答清单（板框/安装孔/叠层/铜厚/
    电源轨/接地/阻抗/接口/天线/封装/热/测试点/丝印/隔离/DFM/拼板/
    颜色/未用脚/成本/验收线），PCB 阶段前逐项向用户核对，答复落到
    `./tmp/design/<project>-pcb-spec.md`；D1/D2/D8 未定即触发 §11.5 P0
    强制中断。
- **§2 开始工作** 新增第 11 步主动学习与外部资源；
- **§4.2 PCB 放置** 首行加入进入 P0 前核对 pcb-design-spec.md §2 必答
  清单的前置要求；
- **§8.4 tmp 目录契约** 新增 `./tmp/learning/` 与 `./tmp/downloads/` 两
  行；
- **§10 执行纪律** 新增第 15 条（PCB 设计基线）与第 16 条（主动学习）；
- **§11.2 必问清单** 新增"PCB 设计细节"项引用 pcb-design-spec.md；
- **§11.5 中断点表** 新增 P0 强制中断"PCB 设计基线"行；
- 版本号 0.8.1 → 0.9.0。

### 14.0 v0.8.1（2026-09-14）

- **§1.1 / §1.2 新增"确认工作区根目录（cwd）"步骤**：连接端口（MCP `7655`
  或 daemon `60832`）成功后，Agent **主动向用户询问 EDA 工程（原理图/PCB
  文件所在目录）的绝对路径**，与 Kilocode 会话报告的 `workspace root` 比对；
  以用户指定路径作为本会话运行时根目录 `cwd`（`./tmp/`、截图、回读 JSON
  等运行产物的落地根）。用户指定与 Kilocode 报告不一致时以用户指定为准，
  同时提示确认当前会话工作区是否与该路径匹配。此举把"运行时根目录"的
  决定权从"隐式继承 Kilocode `workspace root`"改为"显式向用户核对"，
  避免运行产物落入 skill 目录或错误工程目录。

### 14.1 v0.8.0（2026-09-14）

- 新增 **§7.5 生成原理图布局蓝图（Markdown + 字符画）**：沿用 §7.4 PCB 蓝图范式，
  在 `sch compose`/`sch apply`（§5.1）物理绘制前生成字符画蓝图；`./tmp/plan/` 文件
  契约、§4.2 九宫格分区、短桩/netflag/netport 记号（P/⏚/>>）、去耦贴邻、信号流
  箭头与 box-drawing 示例；先读后画（`sch connectivity`/`blocks show`/选型引脚表），
  经 §11.5 **S3** 拍板后才 compose/apply，提交信息 `generate-sch-layout`。
- 新增 **§7.6 数字系统逻辑框图（Markdown + 字符画）**：组合/时序/FSM/总线握手/
  时钟复位域；IEC 门符号（`&`/`≥1`/`1`/`=1`/`o`）、MUX `]`、寄存器 `[D Q]`、
  `S0 --条件--> S1` 转移表、虚线域框 + CDC 标注；节点须可映射到标准件/块库 IP/
  可编程逻辑，映射不到标"未落实"；`./tmp/design/<project>-logic.md`，不替代仿真，
  提交信息 `generate-logic-diagram`。
- 新增 **§7.7 静态数据分析与系统可行性评估**：不依赖仿真/实板，逐项分析功耗电流
  预算（裕量 ≥30%）、电压域与电平转换、IO/引脚预算、存储/带宽、热耗（>0.5W 散热
  判据）、静态时序裕量、协议兼容与 TVS 钳位、BOM 成本；推导落 `./tmp/calc/`，
  数值须带手册页码/来源、缺失标"未核实"；结论三档（可行/有条件可行/不可行）写
  `./tmp/design/<project>-feasibility.md`；"不可行"或条件未接受不得进 S1 之后
  绘制阶段，结论在 §11.5 S0 摊给用户拍板。
- 新增 **§7.8 生成技术手册与功能手册（工作区根目录交付物）**：工作结束、`./tmp/`
  清理（§8.4）前生成；根目录命名 `<板名>-technical-manual.md` /
  `<板名>-user-manual.md`；内容只来自工程回读 + §7.7 静态分析 + 蓝图工件引用
  （不重复绘制）；`blocked`/`fail` 不得写成通过；提交信息 `generate-manuals`。
- 新增 **§8.4 工作区 tmp/ 产物目录生命周期**：sch/pcb/plan/design/parts/calc/
  datasheet/snapshots/baseline 目录契约表（相对工作区 cwd，禁入 skill 目录，
  `tmp/` 已在 `.gitignore`）；工作结束"先交付后清理"纪律与中断/异常收尾、
  用户保留例外。
- **§5.6** 新增**浏览器比价辅助**：`parts-select.py --online` 不可用或需跨平台
  核对行情时，浏览器搜索淘宝/华秋/捷配/立创商城价格库存，结果落 `./tmp/parts/`
  markdown+json 价格缓存，辅助 §7.7 成本预算；时点数据、下单前复核、不回填
  标准件表。
- **§4.5** 新增**逻辑先行**：数字系统逻辑在进原理图前先用逻辑框图（§7.6）表达
  并评审，节点须能映射可实现器件/IP，与 `sch connectivity` 网表可对账。
- **§2** 第 5 步补充 tmp 分子目录指引（§8.4）；**§2 第 10 步**新增"交付工件落位
  与清理"；修正原两个"8."编号重复（动态截图管理改为第 9 步）。
- **§10 执行纪律**新增第 13 条（产物只写工作区 `./tmp/`、先交付后清理、tmp 不入库）
  与第 14 条（根目录手册先行 + `./tmp/` 清理；§7.5–§7.7 未拍板不进绘制/放置）。
- **§11.5 强制中断点清单**更新：S0 行含静态可行性摊牌条件；S3 行含原理图字符画
  蓝图一并拍板；新增"原理图/PCB 蓝图与逻辑框图评审"行；"交付 文档任务"行追加
  技术/功能手册（§7.8）用户确认。
- 版本号 0.7.0 → 0.8.0。

### 14.2 v0.7.0（2026-09-14）

- 新增 **§2 动态截图管理**（§2.7、§2.9）：每关键步骤后自动截图（原理图 `sch export-image` / PCB `pcb snapshot`），SHA256 校验识别 stale 状态，动态清理旧截图（保留最近 3 张关键快照），截图路径 `./tmp/snapshots/step-<index>-<timestamp>.png`。
- **§5.1 执行队列**新增"动态截图"操作：每步 `apply` 后立即截图保存至 snapshots 目录。
- **§5.2 批量连接**新增截图验证：`--spec` 批量 `sch autoconnect` 完成后立即 `sch export-image` 验证 netflag/netport 位置。
- **§5.5 原理图↔PCB 同步**新增同步截图：`import-changes` 后立即 `pcb snapshot` 可视化飞线差异，作为 P1 中断点视觉证据。
- **§8.3 视觉质量评估**新增"动态截图生命周期"三段：保存策略（step/baseline 双目录）、清理策略（保留 3 张）、状态识别（SHA256 stale 闭环）。
- **§11.5 中断协议**新增 `快照` 字段：CHECKPOINT 输出当前截图路径与 fresh/stale 状态。

### 14.3 v0.6.0（2026-09-13）

- 新增 **§7.4 生成 PCB 布局蓝图（Markdown + 字符画边框）**：在物理放置/
  绘制 PCB 之前先生成一份 Markdown 蓝图，用模块/组件/部件及元素间连接
  可视化整板布局，板框外形用字符画（box-drawing ASCII）表达；文件含板框
  字符画、模块/组件/部件清单、连接关系、决策头；先读后画（`sch
  connectivity` / `pcb list --include-bbox` / `sch sheet-geometry`），
  经 P3 中断点（§11.5）拍板后再驱动 `import-changes` 与四档放置。
  蓝图属规划层工件，不替代 `layout-lint`/`pcb drc` 几何电气门禁。
- §4.2 PCB 放置新增"放置前先生成布局蓝图"前置步骤；§14 变更摘要新增
  v0.6.0 条目。

### 14.4 v0.5.0（2026-09-12）

- 新增 **§11.5 中断机制（执行中暂停与用户确认）**：两类中断点
  （强制 mandatory / 条件 conditional）、统一触发协议（CHECKPOINT 格式：
  背景+决策点+选项+推荐+影响范围+等待）、用户响应处理（选择/补充/中止/
  超时）、S0–S6/P0–P10 全阶段强制中断点清单、与验证门禁
  （blocked/fail/pass）的关系、超时与恢复。
- §2 开始工作第 0 步交叉引用 §11.5；§10 执行纪律新增第 11 条
  （中断点命中时暂停不自动推进）。

### 14.5 v0.4.0（2026-09-12）

- 新增 **§8.3 视觉质量与布局完整性自动评估**：`scripts/visual-qa.py`
  用 API 截图（`pcb snapshot --previous-sha256` / `sch export-image`）
  + 数据驱动检查（`layout-score` / `pcb check` / `pcb drc`）交叉评估
  组件间距、走线间距、整体整齐度；三层评估（硬门→关注域→截图一致性）；
  退出码 0/2/3；遵循"数据为权威、截图只做视觉终检"原则。
- 新增 `scripts/visual-qa.py`（Python 3，依赖 easyeda CLI）。

### 14.6 v0.3.1（2026-09-12）

- 技能名由 `jlceda-mcp-easyeda` 更名为 **`EasyEDAssistant`**（frontmatter `name`
  与文档标题同步更新；MCP server 键 `jlceda` 不变）。
- 文件移至仓库根目录（原 `.kilocode/skills/jlceda-mcp-easyeda/SKILL.md`）。

### 14.7 v0.3.0（2026-09-12）

1. 合并 `easyeda-agent-skill-behavior.md` §23–§25 的移植版判据
   （MCP 双端点、设计规范知识库、文档任务），与既有章节去重对齐。
2. 新增 **§11 用户需求澄清与目标明确**：任务分类默认行为、开工前必问清单
   （只问会改变做法的选项）、目标不变量化（pin→net 黄金表/关键网预算/
   验收标准）、授权与沟通纪律。
3. 扩充 **§4.2 美观与功能性经验**：原理图可读性（信号流、框紧凑留白、
   短连优先、方向一致、文字避让、功能分页）；PCB 美观（分区先于对齐、
   朝向归一、阵列杠杆、功能性留白、丝印层、层感知看数、收尾顺序）。
4. 新增 **§12 布局经验**（操作层，与第 4 节判据层互补）与 **§14 变更摘要**（v0.9.0 把变更摘要从 §13 移到 §14，腾出 §13 主动学习与外部资源）。
5. 版本号 0.2.0 → 0.3.0。

---
