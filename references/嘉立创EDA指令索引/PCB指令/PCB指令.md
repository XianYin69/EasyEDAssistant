# EasyEDAssistant Reference：嘉立创EDA指令索引 — PCB指令

> `easyeda pcb` 域总索引（来源版本 v1.5.1 自描述）。主流程：**import-changes → 四档放置 → 板框确认 → P6 门 → 布线 → 铺铜 → P10 终检**。
> 编辑遵守 RULE_EDIT.md：文本 ≤ 50 行、自然语言；条目见四个同名子文件。

## 阶段门（workflow/stage 状态机）

`imported → placement_ready → placement_confirmed → outline_confirmed → 布线 → post_route_checked`。任何放置/板框变更使下游确认失效；确认按文档指纹钉死，外部（GUI）改动经 `workflow status --reconcile` 暴露。布线类命令的 `--force <理由>` 是逐次审计越门，不写进确认。

## 子文件路由

1. **放置与布局**：见 [`放置与布局/放置与布局.md`](放置与布局/放置与布局.md)——同步、四档放置、板框、叠层、层与文档管理。
2. **布线与过孔**：见 [`布线与过孔/布线与过孔.md`](布线与过孔/布线与过孔.md)——track/via/route-short/rip-up 与图元动作缺口；**迷宫 autoroute 三件套已弃用禁调用**，人工向量段落笔前走 `route-check.py` 干涉演算（方法正本 [`../../PCB绘制/干涉布线/干涉布线.md`](../../PCB绘制/干涉布线/干涉布线.md)）。
3. **铺铜与区域**：见 [`铺铜与区域/铺铜与区域.md`](铺铜与区域/铺铜与区域.md)——pour/power/fill/region/keepout。
4. **检查与导出**：见 [`检查与导出/检查与导出.md`](检查与导出/检查与导出.md)——drc/check/report/约束/silk/保存与快照。

## 高频入口速查

| 场景 | 首选指令 | 备注 |
|---|---|---|
| 原理图→PCB 同步 | `pcb import-changes`（单件用 `pcb add-component`） | 报 before/after 计数差，回读身份 |
| 四档放置 | `pcb place-constrained` → `pcb stage confirm-tier` | T1 安装孔→T2 板边接口→T3 主芯片→T4 卫星件 |
| 布线前硬门 | `pcb layout-lint --gate` | 过门才得 `pre_route_passed` |
| mutation 后 | 见 `STALE_READ` 即 `doc reload`（自动先 save）→ 再验证 | 铜形变化后 `pcb pour-rebuild` |
| 终检 | `pcb drc --json` + `pcb check` + `pcb report` | INFO/WARN 单列，聚合 0 fatal≠全过 |
