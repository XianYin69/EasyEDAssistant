# EasyEDAssistant Reference：PCB绘制 — PCB设计规范

> 本文件是「PCB绘制」所需板级规范的索引与要点（自然语言）。
> 编辑遵守 RULE_EDIT.md：文本 ≤ 50 行、自然语言。

## 规范来源

- **必答清单**：[`../../lib/pcb-design-spec.md`](../../lib/pcb-design-spec.md) §2（板框/安装孔/叠层/铜厚/电源轨/接地/阻抗/接口/天线/封装下限/热预算/测试点/丝印/隔离/DFM 目标/拼板/颜色/未用脚/成本档/验收线）。
- **设计规则**：[`../../lib/pcb-design-rules.md`](../../lib/pcb-design-rules.md)、[`../../lib/fab-rules-jlcpcb.json`](../../lib/fab-rules-jlcpcb.json)（板厂能力基线）。
- **硬编码判据（电气检查同源）**：[`../../电气检查/硬编码规则/PCB/PCB规则索引.md`](../../电气检查/硬编码规则/PCB/PCB规则索引.md)——间距线宽/载流温升/过孔焊盘/阻焊丝印拼板/叠层阻抗五件通用打底；**板上电路类型对应的绘制与制版加严条款**见 [`../../电气检查/硬编码规则/PCB/绘制与制版规范/绘制与制版规范.md`](../../电气检查/硬编码规则/PCB/绘制与制版规范/绘制与制版规范.md)（电源/RF/数字高速/模拟小信号/混合隔离五型）。
- **官方入口**：[`../../官方文档映射/官方文档映射.md`](../../官方文档映射/官方文档映射.md)（菜单项 ↔ CLI 对照；官方只说明「在哪设」，数值以 daemon 规则代码为真值）。
- **运行时可读**：`pcb drc-rules`（live 规则）、`pcb layers.list`（层数）、`pcb net-classes`（线宽阶梯）。

## 要点

1. **板框与机械**：连接器、安装孔、面板件坐标由外壳定死（P0）；孔心距板边 ≥3mm；任何 outline 修改使 `outline_confirmed` 失效，须重新签核。
2. **叠层与铜厚**：默认四层（Top 信号+局部铺铜 / Inner1 GND PLANE / Inner2 PWR / Bottom）；PLANE 生成顺序为「先信号层铺铜 → `pcb stackup set --plane` → `pcb pour-rebuild`」，顺序不可反。
3. **线宽与间距**：按 net-class 分级取 live 规则（signal / power-branch / power-trunk / high-current），公制圆整；欠宽电源轨由检查门禁拦。
4. **布局**：四档顺序（T1 安装孔 → T2 板边接口 → T3 主芯片 → T4 卫星件）；开关回路贴紧、热源散开、天线 keepout 全层禁铜。
5. **布线**：走线 45°/90° 规整，差分等长、换层两侧地孔；稠密板走官方 autoroute 或交用户原生自动布线。
6. **铺铜与过孔**：netless pour 是死铜须清理；嵌入焊盘的 via 在 reload 后重新 `pcb via-bond`（平台会重置为 netless）。
7. **丝印与 DFM**：位号/极标在器件本体外且装配后可见；测试点集中、pad ≥40 mil；`pcb check` 覆盖 DFM 审计。

## 判据与动机

- 冲突优先级：手册 > 协议 > 认证 > 通例 > 板厂；硬门（短路/重叠/出框/keepout/DRC）不可放宽。
- 数值以 Go 侧代码与 JLC 官网为运行时正本，本文件只做索引；发现偏差回改文档。
- 规范是前置输入：先读规范再画，可避免返工式的整板重排。