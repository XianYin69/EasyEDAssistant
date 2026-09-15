# EasyEDAssistant Reference：核心 API 操作

> 本文件由 SKILL.md v0.9.0 §5 逐字迁移而来（v0.10.0 主干化重构）。
> 原章节编号保持不变；SKILL.md 是唯一入口，按触发条件加载本文件。

## 5. 核心 API 操作（typed action 速查）

> 参数真值以 `easyeda <command> --help` 与 `easyeda actions` 为准；未知官方接口
> 先 `easyeda api search <query>`。typed action 已有对应能力时优先使用；
> 无对应能力且用户接受调试路径时才用 `debug.exec_js`（输出须可 JSON 序列化）。

### 5.1 原理图 1.4 数据路径

主线：**本地 Connectivity IR → Lib 局部几何 → compose → sch apply → 回读对账**。

| 目的 | CLI / action | 边界 |
|---|---|---|
| 读取连接图 | `sch connectivity [--page <p> \| --all-pages]` | 跨页逐页激活读取；浅层引脚不能用空 pins 证明无引脚 |
| 连接差异 | `sch connectivity-diff before.json after.json` | 拓扑/NC 对账，不代替库身份与几何 |
| 设计版本差异 | `sch design-diff expected.json actual.json --exit-code` | 查 `coverage.unverified`；退出码 2=不同、3=目标不符/证据不完整 |
| 框/标题差异 Apply | `sch design-diff before-plan.json after-plan.json --before fresh.json --playbook frame-diff-apply.json` | 两份完整 compose 计划 + 新鲜快照；只改有变化框 |
| Lib 内部几何 | `sch lib-layout --from layout-input.json --out composition.json` | 纯离线；有界求解器，失败不证明任意朝向无解 |
| 完整 Lib 图面 | `sch compose --from composition.json --out plan.json [--before … --replace --playbook …]` | 消费已设计模块几何；Z 字排版；不自动补电路/旋转/缩放/分页 |
| 基础放置 | `sch materialize <connectivity.json>` | 放件队列，不是完整布局/布线器 |
| 标记增量 | `sch plan before.json after.json` | 仅 power/ground/net_port 连接；NC→连接先清 NC 核对中间态再连 |
| 位号修复 | `sch designators allocate` → `plan` → `verify` → `sch apply` | 按官方库前缀分配；只改非标准项，跳过已占用编号 |
| 框与标题 | `sch frame apply/check --from frames.json` | 只操作自己登记的图元；check 按实际文本 bbox 验证 |
| 执行队列 | `sch apply <plan.json> [--dry-run \| --yes]` | 保护队列禁止 `--resume/--from/--to` 跳步；失败重新回读生成 |
| **动态截图** | 每步 `apply` 后立即 `sch export-image`（原理图）或 `pcb snapshot`（PCB） | 保存至 `./tmp/snapshots/`；SHA256 校验与上帧比对；每 3 步自动清理旧截图 |

Apply 队列（playbook）契约：`version:1` + `meta` + 有序 `steps`；每步
`action+payload`（typed）或 `run+flags`（Cobra）或 `notify`；`capture` 捕获
新实例 ID 供后续 `${part}` 引用；`assert` 路径相对 result；默认失败即停。
生成器（compose/designators/plan）产出的保护计划失败后只能重新读取当前图、
修正输入、完整重编译执行；已生效步骤保留在画布与 journal。

### 5.2 连线（pin-aware autoconnect）

`sch autoconnect` 拉真实几何（bbox/pin/既有 flag/port/title-block），对每个
`方向 × offset` 候选做确定性代价评分，选最低委托 `connect_pin`：

```bash
easyeda sch autoconnect --pin U1:41 --kind gnd --net GND
easyeda sch autoconnect --pin J1:VBUS* --kind power --net 5V   # 同名多脚全接
easyeda sch autoconnect --spec p1-connect.json                  # 批次
easyeda sch autoconnect --spec p1-connect.json --dry-run --json # 预览不改
```

行为要点：

- **幂等**：已连目标网的脚跳过；`--replace` 删旧 flag+wire 再连（成对删，无孤儿桩）。
- **硬拒（#64/#147）**：短桩触碰异网线 / 跨越非目标引脚 / 落入图签 keep-out
  → 候选不可用，四向全堵时响亮报 no safe candidate，拒绝落笔。
- **密集区**：候选扩到 3×offsetMax；看到的长桩是错开标签的结果，不是失控。
- **带痕候选**：score 超软阈值标 `⚠ WARN`；`--strict` 直接判失败。
- **35s 专用预算**：超时/DISPATCH_FAILED 自动轻读复核，`slowLanded` 成功返回
  且勿重试；状态未知失败绝不盲重试（可能已建成）。
- 批次后必跑 `sch check`（`duplicate-net-marker` 规则兜叠加 marker）。
- `sch connect` 不幂等，重发可能叠加导线和标记；`sch disconnect` 检查
  `alsoDisconnectedPins[]`，逐个恢复；`partial`/`survivedIds`/`notApplied`
  表示删除未完全生效。
- **批次截图**：`--spec` 批量连接完成后，立即 `sch export-image` 保存当前页面，验证 netflag/netport 位置与连线完整性。

### 5.3 PCB 基础上下文

| 命令 | 用途 |
|---|---|
| `pcb board-info` | Board（SCH+PCB 绑定）前提；`import-changes` 沿此链接 |
| `pcb components.list --include-bbox --include-pads` | 位置/尺寸/层/焊盘网络 + 真实铜宽 |
| `pcb layers.list` | `copperLayerCount`（2 vs 4+ 层判定，去耦规则开关） |
| `pcb nets.list` | 网络全集（net 名/长度/颜色） |
| `pcb report` | 逐 net 铜长、差分 skew、等长组 spread（纯读） |
| `pcb check` | Go 侧重建 DFM 审计（dangling-end/acute-angle/silkscreen-flipped/antenna-keepout/…） |
| `pcb drc --json` | 原生规则 DRC；前台窗口执行，超时装前景跑一次不循环重试 |
| `pcb drc-rules` | 读 live 规则（clearance/trackWidth/via 尺寸） |
| `pcb net-classes` | net-class → 规范线宽阶梯（角色分档） |

### 5.4 PCB 布线与铺铜

- 增量创建：`pcb.line.create`（导线，默认 6 mil）、`pcb.via.create`（过孔，
  默认 12/24 mil）；`create()` 宽松返回，每步验证 primitive 返回。
- `pcb.route.rip_up` 按网 rip-up（含 arc/via，保护板框/丝印/锁定图元）；
  `pcb clear` 一键整版复位（默认保留锁定+板框，自带 verify 复合流程）。
- `pcb via-delete`/`track-delete` 按 primitiveId 精删（CSV 或 JSON 数组）；
  嵌入焊盘的 via 前置拒绝（reload 后 re-materialize netless，用 `pcb via-bond` 合流）。
- `pcb via-hop` 复合换层：入口桩→via→换层轨→via→出口桩；via 在端点外 20 mil
  不坐 pad；track↔via 自身注册连接（不需要 bond fill）；同网 Connection Error
  是 stale pour 连通性——先 `pcb pour-rebuild` 再判。
- 铺铜：`pcb.pour.create`（net 必绑，netless pour 是死铜）；`pour-fit` 自动
  贴板框；`pour-clean --netless`；`pour-rebuild` 重流。
- 禁布区：`pcb region create --ref U1 --margin 40 --rule no-pours`（默认
  no-components/no-wires/no-pours 硬 keepout）；天线 keepout 全层。
- 填充：`pcb fill create`（静态异形铜，net 绑定；`--rect` 是两对角点不是 x,y,w,h；
  面积 > 板框 25% 防呆拒绝）；MULTI 层 fill = 板挖槽（`pcb slot`）。
- `pcb beautify` 圆角化走线（DRC 二分重试 + pour-rebuild 内置；先 `--dry-run`；
  密集板按 `--net` 小范围处理）。

### 5.5 原理图 ↔ PCB 同步

- `pcb import-changes` 从原理图同步器件/网表（自动点"应用修改"对话框，报
  before/after 计数差；`InvalidatesStage:placement_confirmed`，别为刷飞线跑它）。
- **工具与插件检查**：参考 `./tmp/eda-tools-manifest.json` 和 `./tmp/eda-tools-guide.md`：
    - 若有专用导入/同步插件（如高级网表同步工具、智能飞线处理插件），触发 §11.5 条件中断点询问用户是否启用；
    - 用户确认后优先调用插件 API；用户选择标准流程或无插件时使用原生命令。
- **同步截图**：`import-changes` 成功后立即 `pcb snapshot`，可视化飞线差异，作为
  P1 中断点（§11.5）的视觉证据。
- `pcb sync-designators`：按 `uniqueId`（平台首次导入铸造，跨文档同一命名空间）
  回填占位位号 `U?/C?`，只动占位符，每笔回读验证。
- `pcb sync-attrs`：器件库记录回填 PCB 属性空值（平台投影键绝不参与 merge）。
- `pcb add-component`：逐件放置 + 焊盘赋网（`--nets` padNumber→net map）+
  嵌入 via 合流；工作流 = 原理图放件接线 → `sch read` 取 net/uniqueId →
  PCB 侧放置赋网 → `pcb list --include-pads` + `pcb drc` 验证。

### 5.6 器件库与选型

- 选型顺序：先 `easyeda blocks search <keyword>` 查可复用电路块（命中后块的
  `parts` map 直接给 standard-parts role）→ `standard-parts.json` 本地库
  （确定性、已真板验证）→ `lib by-lcsc --lcsc C…` 精确解析 → `parts-select.py`
  在线比价（opt-in，显式 `--online`）。
- 排名五档：Resistance gate（阻值等式，SI 前缀大小写）→ Buildable
  （stockCount ≥ qty）→ Basic（免 feeder 费）→ Preferred → 单价。
- **浏览器比价辅助**：当 `parts-select.py --online` 不可用、或需跨平台核对行情时，
  Agent 用浏览器工具搜索淘宝、华秋、捷配、立创商城等元器件价格与库存；结果
  （MPN/渠道/单价/库存/来源 URL/查询时间）写入 `./tmp/parts/` 的 markdown+json
  价格缓存，辅助 §7.7 方案生成与成本预算；价格为时点数据，下单前复核、不回填
  标准件表。
- `parts-add.py` 把新选型写回 `standard-parts.json`；`bom-enrich.py` 把 C 号
  补进 BOM 导出的 "Supplier Part" 列。
- `sch replace --id <pid> --lcsc <C#>` 一键换件（保 designator/uniqueId/pose，
  报 `pinDiff`，非空须重连后 `sch check`）。
- 自建资产走 `lib device build`（Symbol/Footprint/3D/Device）；Footprint JSON
  单位 mil；库 API 有 beta 能力——结果不明先 get 再决定，不重复 create。

### 5.7 验证门禁

- 原理图逐页 `sch gate --strict --doc <page>`：`layout-lint → check →
  bridge-check → SDK DRC`；`pass` 才通过，`fail` 是设计问题，`blocked` 是
  检查未完成（先修环境）。`--strict` 把间距、孤儿桩等告警也列为阻塞。
- `sch check --json` 问题在 `result.findings`；SDK DRC 可能只返回聚合值，
  不能单凭它宣称官方 UI 所有警告已清除。
- PCB `layout-lint --gate`（装配感知：手焊间距地板 + solder-access + 分数/
  交叉数门）落 `pre_route_passed`；`layout-score` 九维诊断
  （partition/flow-order/edge-io/protection/tidy/compact/rf/routable/clearance）
  是质量表不是硬门——skipped/degraded 维不参与加权；短路/重叠/出板框进
  `blocking[]` 一票否决。
- 官方导图：`sch export-image`（文档渲染，不依赖视口刷新）；PCB 截图
  `pcb snapshot` 可能 stale（`--previous-sha256` 检测同帧）——数据校验
  （list/drc/check）是权威，截图只做视觉终检。
- 保存：通过阶段验证后显式 `sch save` / `pcb save` 并确认 `saved:true`；
  daemon 防抖 autosave 只是兜底。
- 视觉质量聚合：`scripts/visual-qa.py`（§8.3）聚合截图 + 上述数据源
  做三关注域（组件间距/走线间距/整齐度）交叉评估，是"呈现层"自动化，
  不替代数据层硬门。
