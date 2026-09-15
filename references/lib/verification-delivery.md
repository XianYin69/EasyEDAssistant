# EasyEDAssistant Reference：验证与交付（§8、§9）

> 本文件由 SKILL.md v0.9.0 §8、§9 逐字迁移而来（v0.10.0 主干化重构）。
> 原章节编号保持不变；SKILL.md 是唯一入口，按触发条件加载本文件。

## 8. 验证与交付

### 8.1 验证分层（不能互替）

| 层 | 工具 | 证明什么 | 不证明什么 |
|---|---|---|---|
| 拓扑 | `sch design-diff` / `connectivity-diff` | 器件/pin→net/NC 一致 | 几何、导线、框（未导出字段列 unverified） |
| 几何 | `layout-lint` / `pcb layout-score` | 无重叠/出框/间距/可布性 | 电气正确性 |
| 电气 | `sch gate --strict` / `pcb drc` / `pcb check` | DRC/DFM 门禁 | 设计意图 |
| 呈现 | `sch export-image` / `pcb snapshot` | 文字/可读性视觉终检 | 数据正确性（截图可能 stale） |
| 保存 | `sch save` / `pcb save` → `saved:true` | 落盘 | 内存中的未保存修改 |

- 官方 DRC 可能只返回聚合数；INFO/WARN 单列，不能把"0 fatal"称全部通过。
- 数据完整与绘图成功不代表电气设计合格；悬空脚仍保留电气警告。
- `layout-score` 的 `skipped/degraded` 是诊断（没测 ≠ 满分），硬门
  （short/overlap/off-board）一票否决。

### 8.2 交付报告

说明修改范围、源数据与实际图面差异、各验证层结果、已保存页面、
尚未解决的问题与未运行检查。保留输入、生成队列、回读与验证报告；
局部完成不称整板通过。

### 8.3 视觉质量与布局完整性自动评估（`scripts/visual-qa.py`）

> 用 API 截图 + 数据驱动检查**交叉**评估视觉质量，聚焦组件间距、
> 走线间距、整体整齐度。是 §8.1 "呈现层"的自动化实现，但**不替代**
> 数据层（拓扑/几何/电气/保存）。

**设计原则**（与 §5.7 / §8.1 一致）：

- 呈现层不可互替，但**数据校验是权威**——截图只做视觉终检。
  截图与数据不一致时以数据为准，但必须把"图面 stale"标为阻断项。
- PCB `snapshot` 可能 stale：用 `--previous-sha256` 检测同帧；
  `sch export-image` 是文档渲染（不依赖视口刷新），无需 sha 检测。
- `layout-score` 九维是诊断**不是硬门**；skipped/degraded 维不参与
  加权（"没测 ≠ 满分"）；短路/重叠/出框进 `blocking[]` 一票否决。

**三关注域 → 数据真值映射**：

| 关注域 | layout-score 维度 | pcb check 规则 | drc 规则 |
|---|---|---|---|
| 组件间距 component_spacing | compact, clearance | solder-access（gate） | clearance |
| 走线间距 trace_clearance | routable, clearance | acute-angle, dangling-end | clearance, trackWidth |
| 整体整齐度 layout_neatness | tidy, partition, flow-order | rotation-inconsistent（子规则） | — |

**用法**：

```bash
# PCB + 原理图双评估（需活体窗口或 daemon）
python3 scripts/visual-qa.py --project <name> --doc <page-uuid> --both

# 仅 PCB，strict（WARN 也判阻塞）
python3 scripts/visual-qa.py --project <name> --pcb --strict

# 跳过截图采集（只用已有数据打分；不触发 canvas-freeze）
python3 scripts/visual-qa.py --project <name> --pcb --no-snapshot
```

**输出**：JSON（stdout）+ 人读摘要（stderr）。退出码：
`0`=全通过（含截图非 stale）；`2`=有 WARN（低分维/带痕/stale 但数据通过）；
`3`=blocking（短路/重叠/出框/间距硬违规/stale 且数据也不全）。

**评估流程**（三层）：
1. **硬门**：`layout-score.blocking[]` 一票否决（短路/重叠/出框）。
2. **关注域**：逐域聚合维度状态（skipped/degraded/low-score<0.6）+
   DRC/check findings → pass/warn/fail。
3. **截图一致性**：stale/missing → 至少 warn（strict 且数据不全 → fail）。

**边界**：
- 该脚本**不替代** `sch gate --strict` / `pcb drc` / `pcb check`——
  它是这些数据源的聚合器 + 截图终检，不是新的硬门。
- 截图采集前的 `view fit` + 1.5s 等待是 canvas-freeze 缓解（§5.7），
  不是保证；stale 检测是最终防线。
- `--no-snapshot` 模式下只跑数据评估，不触发截图采集——适合
  CI/批量回归或已知截图 fresh 的场景。

**动态截图生命周期**（v0.7.0）：
- **保存策略**：截图保存在 `./tmp/snapshots/step-<index>-<timestamp>.png`，
  基线图保存在 `./tmp/baseline/`；两目录皆在 `.gitignore` 中排除。
- **清理策略**：每次新截图生成前，自动删除 snapshots 目录中最旧的截图
  （保留最近 3 张关键快照作为回溯）；基线截图在会话结束后清理。
- **状态识别**：`visual-qa.py` 用 `--previous-sha256` 检测同帧，stale 标记
  视为 "canvas-freeze"，触发 `easyeda view --fit` + 重取。脚本自动维护
  `prev_sha` 闭环（上次报告 JSON → 下次 stale 检测）。

### 8.4 工作区 tmp/ 产物目录生命周期（保存与清理）

所有运行产物一律落在**工作区** `cwd` 下已忽略的 `./tmp/`，按用途分子目录；
路径全部相对工作区解析，禁止落入 skill 目录（`FILE_CREATION_POLICY.md` §1.3/§2.4），
`tmp/` 已在 `.gitignore` 中排除，任何 tmp 内容不得提交 git。

**目录契约**：

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

**清理纪律**（工作结束时执行）：
1. 先按 §7.8 在**工作区根目录**生成技术手册与功能手册，按 §8.2 出交付报告。
2. 需保留的图片先导出到手册引用路径（工作区根目录，或用户指定的正式交付目录）。
3. 然后**删除 `./tmp/` 全部子目录与文件**（含未引用的中间产物）。
4. 交付报告中记录"tmp 已清理"及删除清单摘要（目录 → 文件数）。

会话中断/异常结束时同样执行清理；未完成部分在报告中注明缺失工件。
**例外**：用户明确要求保留 tmp 产物时不删除，改为提示其不入库
（`.gitignore` 已生效）。

---

## 9. 已知平台限制（承重的边界）

- `.SchDoc`/`.PcbDoc` 无程序化导入入口：Altium 工程走 EasyEDA GUI（文件→导入），
  导入后由 typed 命令核验；`importProjectByProjectFile` beta 接口实测静默
  返回 `undefined`，不能包装当成功。
- `eda.*` 无泪滴（teardrop）API——制造前在 UI 右键手动加。
- 交互式布线菜单（routing/stretch/optimize/length-tuning）无 `eda.*` API：
  程序化布线限于坐标创建 track/via/pour、rip-up、`route-short` 启发式档、
  官方文件交换 autoroute（`pcb export-dsn` 导出含 keepout，Freerouting 兜底）；
  稠密板默认交用户点 EasyEDA 原生"自动布线"（人机协作档）。
- `createNetLabel` 是 v4 BETA API，3.2.186 实测挂起——超时后回读实际连通与
  残留图元，按电气语义选受支持的 netport/netflag，不盲重试。
- `getCurrentRenderedAreaImage` 后台标签可能返回缓存旧帧；`pcb snapshot`
  用 `--previous-sha256` 检测同帧，stale 时切前台重取。
- `page.rename` 后立即 `doc ls` 读旧名（平台元数据缓存延迟）——看返回值
  `verified` 字段，不是紧接着 doc ls。
- 3D 模型导入请求体上限 32 MiB（含 base64 膨胀，原始模型 < ~24 MiB）。
- `sch_Netlist.getNetlist()` 已废弃且可能挂起——网表用
  `sch_ManufactureData.getNetlistFile()`。
