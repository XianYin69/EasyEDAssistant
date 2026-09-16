# EasyEDAssistant Reference：嘉立创EDA指令索引

> 本文件是 `easyeda` CLI（easyeda-agent，来源版本 v1.4.8）与 MCP 动作目录的**运行时指令入口索引**：只给指令条目与一句话语义，供流程关键步骤速查「有什么命令、去哪一步用」。
> 编辑遵守 RULE_EDIT.md：文本 ≤ 50 行、自然语言；各子文件与其子文件夹同名。

## 真值优先级

1. `easyeda <域> <命令> --help` 与 `easyeda actions`——参数与行为的**唯一真值**，CLI 升级即变。
2. 本索引——条目导航 + 一句话语义，不定义参数、不复制数值判据。
3. 各步骤文档——命令的使用场景与门禁顺序。索引与 CLI 自描述不符时以 CLI 为准并回改本索引。

## 子文件路由

1. **会话与文档**：见 [`会话与文档/会话与文档.md`](会话与文档/会话与文档.md)——update/health/doc/project/view/board/workflow/apply/spec/audit/notify 等顶层域。
2. **原理图指令**：见 [`原理图指令/原理图指令.md`](原理图指令/原理图指令.md)——`sch` 域总索引（下分放置与编辑、连线与网络、校验与对账）。
3. **PCB指令**：见 [`PCB指令/PCB指令.md`](PCB指令/PCB指令.md)——`pcb` 域总索引（下分放置与布局、布线与过孔、铺铜与区域、检查与导出）。
4. **器件库与块**：见 [`器件库与块/器件库与块.md`](器件库与块/器件库与块.md)——`lib`/`blocks`/`bom` 与选型脚本管道。
5. **动作目录与队列**：见 [`动作目录与队列/动作目录与队列.md`](动作目录与队列/动作目录与队列.md)——`actions`/`call`/`api`/`debug` 与 apply playbook 契约。

## 使用纪律

1. 写命令进流程前先查本索引定位域，再以 `--help`/`easyeda actions` 确认参数；不凭记忆猜 flag。
2. 索引未收录的新命令：走 `easyeda actions` 或 `easyeda api search <query>` 发现后**回补本索引对应子文件**（追加行，不改写既有条目）。
3. 单位红线：PCB 坐标 mil、原理图 0.01inch（y 向上），详见 [`../坐标与数据模型/坐标与数据模型.md`](../坐标与数据模型/坐标与数据模型.md)。
4. 操作纪律（幂等性、STALE_READ、批量优先）正本在 [`../lib/api-operations.md`](../lib/api-operations.md)，本索引不重复。

## 刷新方法

- `easyeda --help` 全量顶层域、`easyeda sch --help`、`easyeda pcb --help` 与本子文件条目数对照；缺项即回补。
- CLI/daemon/Connector 升级后（版本门禁通过的新会话内）做一次核对，结果记 `CHANGELOG.md`。

## 依据来源

- `easyeda version` = easyeda-agent v1.4.8（本索引采集快照）；上游存档见 [`../../Sample/easyeda-agent/README.md`](../../Sample/easyeda-agent/README.md)。
- GUI 菜单 ↔ 命令对照见 [`../官方文档映射/官方文档映射.md`](../官方文档映射/官方文档映射.md)（人读入口，不定义真值）。
