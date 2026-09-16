# EasyEDAssistant Reference：USB

> 硬编码判据，来源 USB-IF 设计规范通例。
> 编辑遵守 RULE_EDIT.md：文本 ≤ 50 行、自然语言。

## USB 2.0（480 Mbps）

- D+/D− 差分 90 Ω ±10%（USB2 规范容差较宽，按 ±15% 上限自查），对内等长 ≤ 5 mm 内取 ≤ 25 mil 实际目标。
- 走线总长（连接器→Hub/PHY）≤ 3"（76 mm）超出做损耗预算；禁止跨分割与换层（必要时对称双孔）。
- VBUS：线宽按 ≥ 1.5 A（含 Type-C 5 V/3 A 场景按 5 A 认证路径）；入口 TVS（standoff 6.8~10 V 档）+ 保险丝/PDC（≥ 500 mA 按设备等级）。
- 去耦：设备侧 VBUS 本地 ≥ 120 µF（Bus-Powered 规范值）或按自供电策略。
- ESD：D+/D− 用低容（≤ 3 pF）阵列贴连接器。

## USB 3.x（5 Gbps+）

- 两对 TX/RX 差分 90 Ω，对内 ≤ 2 mil、对间（组）等长按 Gen 规范（± 5 mil 级）。
- 每对过孔 ≤ 2 个，残桩 > 15 mil 评估背钻；禁止在 pair 间布线或地孔打穿对间耦合区。
- 走线长度 > 80 mm 加 RETimer/Redriver 预算。
- TX 端交流耦合电容 100~240 nF（规范 235~260 nF 范围按主机/设备角色），贴连接器侧、对称双 0402 实现低感。

## Type-C

- CC1/CC2：Rp/Rd 下拉上拉电阻按角色（默认 USB host Rp 5.1 kΩ 档），1:1 精确匹配，禁止共用一颗。
- VBUS 开关（负载开关/eFuse）+ 5 V 短路失效分析；SBU 走差分等效线（用于 DP alt-mode 时按高速规则）。
- 壳体 GND（Shield）经 1 MΩ ∥ 4.7 nF（可选）到信号地按整机 EMC 定，连接器固定脚焊接到厚地铜。
