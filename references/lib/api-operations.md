# EasyEDAssistant Reference：核心 API 操作（维护者速查）

> 本文件自 SKILL.md §5 迁移并精简；命令的完整使用场景见各步骤文档（绘制原理图、PCB绘制、元件检查、成本及预算检查、桥接联通性测试等）。
> 参数真值以 `easyeda <command> --help` 与 `easyeda actions` 为准；未知接口先 `easyeda api search <query>`。

## 命令族索引

| 域 | 命令族 | 主要落点 |
|---|---|---|
| 原理图数据路径 | connectivity → lib-layout → compose → apply → 回读对账 | [`../绘制原理图/部分绘制与截图/部分绘制与截图.md`](../绘制原理图/部分绘制与截图/部分绘制与截图.md) |
| 连线 | `sch autoconnect`（pin-aware，`--spec` 批次） | 同上 |
| 位号 / 框 / 标题 | `sch designators allocate→plan→verify`、`sch frame apply/check` | 同上 |
| PCB 上下文 | `pcb board-info` / `pcb list` / `pcb layers` / `pcb nets` / `report` / `check` / `drc` / `net-classes` | [`../PCB绘制/部分绘制与验收/部分绘制与验收.md`](../PCB绘制/部分绘制与验收/部分绘制与验收.md) |
| PCB 布线铺铜 | `line.create` / `via.create` / `route.rip_up` / `via-hop` / `pour.create` / `power-pour` / `power-planes` / `region create` / `beautify` | 同上 |
| 原理图↔PCB 同步 | `pcb import-changes` / `sync-designators` / `sync-attrs` / `add-component` | 同上 |
| 器件库与选型 | `blocks search` → `standard-parts.json` → `lib by-lcsc` → `parts-select.py` | [`../元件检查/元件检查.md`](../元件检查/元件检查.md)、[`../成本及预算检查/成本及预算检查.md`](../成本及预算检查/成本及预算检查.md) |
| 门禁与保存 | `sch gate --strict` / `layout-lint --gate` / `pcb drc` / `pcb check` / `layout-score`；`sch save` / `pcb save` | 各步骤文档的检查段 |
| 批量放置（官方 eext） | `eext-batch-place-components`：CSV 坐标批量放置（表头带单位，如 `Name,X(mm),Y(mm)`），仅作初始落位，落位后仍须回读对账 | [`../绘制原理图/部分绘制与截图/部分绘制与截图.md`](../绘制原理图/部分绘制与截图/部分绘制与截图.md) |

## 操作纪律（跨步骤复用）

1. `sch autoconnect` **幂等**：已连目标网的脚跳过；短桩触碰异网线、跨越非目标引脚或落入图签 keep-out 属硬拒，四向全堵时报 no safe candidate 并拒绝落笔。
2. autoconnect 有 35s 专用预算：超时或 DISPATCH_FAILED 后自动轻读复核，`slowLanded` 视为成功、不重试；状态未知的失败绝不盲重试（可能已建成）。
3. `sch connect` **不幂等**，重发会叠加导线与标记；删除后检查 `alsoDisconnectedPins[]` 逐个恢复，`partial`/`survivedIds`/`notApplied` 表示未删净。
4. apply 保护队列契约：`version` + `meta` + 有序 `steps`（`action+payload`／`run+flags`／`notify`），`capture` 捕获实例 ID 供后续引用，`assert` 失败即停；失败后只能重新回读、修正输入、完整重编译，不用 `--resume/--from/--to` 跳步。
5. mutation 后读到 `STALE_READ` → 先 save 再 `doc reload` 重读；确定性复位 = rip-up → save → reload；`pour-rebuild` 是「铺铜连通性 stale」的修法。
6. 嵌入焊盘的 via 在 reload 后会被平台重置为 netless → 在 reload 后、DRC/铺铜前重新执行 `pcb via-bond`。
7. 每步 apply 或批次连线后立即截图（`sch export-image` / `pcb snapshot --previous-sha256`）；批次连线后必跑 `sch check` 兜叠加 marker。
8. 写前读被改对象（器件、引脚、网络、几何），位号或 primitiveId 不明确时不盲写；保存以 `saved:true` 为准。
9. **批量优先**：一个模块一次队列派发（`sch apply` 队列、`sch autoconnect --spec` 批次），禁止逐器件逐根线多轮往返编辑器；相互独立、只读的查询与检查（`sch check`、`pcb report` 等）可同批并行发起，写操作仍保持队列内有序；大回读一律 `> ./tmp/*.json` 落盘，上下文只留统计行与路径。

## 验证分层（不能互替）

拓扑（`design-diff`/`connectivity-diff`）｜几何（`layout-lint`/`layout-score`）｜电气（`sch gate`/`pcb drc`/`pcb check`）｜呈现（`export-image`/`snapshot`，可能 stale）｜保存（`save` → `saved:true`）。截图只做视觉终检，数据回读是权威。