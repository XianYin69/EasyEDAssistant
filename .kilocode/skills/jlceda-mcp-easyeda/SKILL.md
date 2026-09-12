---
name: jlceda-mcp-easyeda
description: "基于 JLCEDA MCP VS Code 插件桥接操作嘉立创 EDA（EasyEDA）的移植版电路设计 skill：原理图/PCB/射频/模拟/数字/滤波器/电源设计与检查。支持 MCP 与原有 CLI/daemon 双链路，内置电气规范、数据手册 PDF 阅读经验与项目文档任务（许可证/README）。"
license: MIT
compatibility: "Requires JLCEDA MCP VS Code plugin running locally (ws://127.0.0.1:8765/bridge/ws + http://127.0.0.1:7655/mcp). Fallback: easyeda CLI/daemon/Agent Connector. Offline design planning needs no editor."
metadata:
  author: EasyEDAssistant
  version: "0.1.0"
---

# JLCEDA MCP EasyEDA 设计 Skill

用 JLCEDA MCP VS Code 插件桥接操作嘉立创 EDA（EasyEDA 专业版）：原理图绘制、
PCB 布局布线、射频/模拟/数字/滤波器/电源设计、检查与制造文件导出。
知识基线见同仓 `easyeda-agent-skill-behavior.md`（24–25 节为移植版专属判据）。

## 1. 连接（双链路，原有方式必须保留）

### 1.1 JLCEDA MCP 链路（移植版主路径）

| 通道 | 地址 | 用途 |
|---|---|---|
| WebSocket 桥接 | `ws://127.0.0.1:8765/bridge/ws` | 动作派发、心跳、窗口上下文 |
| HTTP MCP | `http://127.0.0.1:7655/mcp` | MCP 工具/资源入口 |

Kilocode 接入（`kilo.json`）：

```jsonc
{
  "mcp": {
    "jlceda": {
      "type": "remote",
      "url": "http://127.0.0.1:7655/mcp",
      "enabled": true
    }
  }
}
```

- 端点不可用（插件未启动）时回退原有 `easyeda daemon`（`60832` 端口）链路，
  不静默降级；保留 health/journal 证据。
- MCP 工具与 typed action 语义一致：同一套 `eda.*` API 映射、dry-run/回读/
  `saved:true` 纪律、破坏性操作确认门控。

### 1.2 原有链路（兼容，不得移除）

- `easyeda` CLI + daemon + EasyEDA Agent Connector；`--project`/`--doc` 路由。
- 版本门禁：会话第一条命令 `easyeda update --check --exit-code`，先于任何
  项目读取与 EDA 操作；升级后必须新开会话。
- `doc reload` 门：PCB mutation 后读 `STALE_READ` 时按提示 reload 再读。
- 审计继续写本地 `~/.easyeda-agent/audit`，MCP 调用同样记录。

## 2. 开始工作

1. 确认插件状态：`8765/7655` 端点可达；不可达走原 daemon 链路。
2. 读目标工程：`sch connectivity`（原理图）/ `pcb list --include-bbox`（PCB）。
   写前读被改器件、引脚、网络与几何；位号或 primitiveId 不明确时不盲写。
3. 按任务选子域判据（第 3 节），只加载相关参考。
4. 参数真值以 `easyeda <domain> <command> --help` 与 `easyeda actions` 为准。

## 3. 设计子域判据（移植版知识库）

> 数值判据为方向性规则；落地前以数据手册与实测为准。

### 3.1 PCB 与原理图

- 原理图按功能 Lib 九宫格分区：电源左、MCU 中、RF/IO 右；多脚同功能逐脚核对。
- PCB 优先级 P0–P7（机械 > 安全间距 > EMI/去耦 > 回流 > 热 > 功能分区 > DFM > 网格/丝印）。
- 四层默认叠层：`Top / Inner1-GND(PLANE) / Inner2-PWR / Bottom`；内电层 PLANE 生成
  顺序：信号层先铺该网 → `pcb stackup set --plane` 翻类型 → `pcb pour-rebuild`，顺序不能反。
- 手焊 profile：器件间距 ≥40 mil，大焊盘烙铁通道 ≥60 mil。
- 丝印：位号/极性/逐脚功能标在器件本体外、装配后可见。

### 3.2 射频（RF）

- 天线全层 keepout（含内电层 `no-inner-electrical`）；keepout 半径按 datasheet。
- 50Ω 单端 / 100Ω 差分（USB）；微带宽度按叠层仿真，不套默认线宽。
- RF 路径最短化：匹配+馈电在 λ/4（2.4GHz ≈ 12mm）内完成；RF 地缝合过孔间距 ≤λ/20。
- RF 口串低容 ESD（<1pF）贴天线端；CC1101 类巴伦镜像布局。

### 3.3 模拟

- 单点接地（星形），避免地环路；多电源域经磁珠/RC 滤出干净子域。
- 运放每电源脚 0.1µF 去耦 + bulk 储能；敏感输入不跨数字地平面，远离开关/晶振
  ≥300–500 mil。
- 热电偶/应变片等小信号：同材质焊料、冷端补偿、屏蔽线缆入板先接 GND。

### 3.4 数字

- 晶振贴振荡 pin ≤300 mil（上限 500），负载电容对称 150–200 mil，晶振下方禁走线。
- 开漏总线上拉靠主控端；未用脚显式上/下拉或 NC，不悬空。
- 复位 RC 按 τ=RC≥Vth 时间常数；低有效命名 `nRESET`。
- 隔离区（光耦/数字隔离器）两侧电源独立，爬电/间隙按 P1 安全间距。
- 电平匹配用转换 IC，不跨压直连。

### 3.5 滤波器

- 无源 LC：L ±20%、C ±5–10% 公差决定 fc 偏差；RF 用 C0G。
- 有源：运放去耦齐全，反馈网络贴输出端，增益-带宽积与阶数匹配。
- 数字接口：共模扼流圈串 D± + 22R 串阻 + ESD 阵列贴连接器端。

### 3.6 电源

- Buck：Cin（陶瓷）贴 VIN/GND ≤150 mil 同层；SW 铜面最小化；反馈贴 FB。
- LDO：入/出各 0.1µF + 10µF bulk；热耗 `(Vin−Vout)×Iout`，SOT-223 限 0.5–1W。
- 电流线宽：0.15mm≈0.5A、0.25mm≈0.9A、0.5mm≈1.5A（1oz 外层，内层 60–70%）。
- 每轨入口 bulk + 每 IC 本地去耦；多电源轨不共面，独立内电层需 6+ 层。

### 3.7 电气规范

IPC-2221B（设计流程）、IPC-7351B（courtyard/间距）、IPC-A-600（缺陷判据）、
IEC 62368（爬电/间隙/隔离屏障）、JLCPCB 工艺能力（最小线宽/间距、过孔、铜边距）。
门禁数值以 daemon 规则代码为准；冲突时以代码 + JLC 官网为准。

### 3.8 数据手册 / PDF 阅读经验

1. 锁定厂商、完整 MPN、LCSC C 号与封装；先读目录/概述。
2. 电气参数表抄条件（Vin/Tj/负载），不只抄值。
3. 典型应用电路是外围设计基准；不凭外观补接线。
4. 单位换算另列：`mΩ`=毫欧、`MΩ`=兆欧，SI 前缀大小写敏感。
5. 目录/手册/库 value 冲突时记录冲突并停止自动绘图；来源不可读标"未核实"。
6. 版本不匹配（旧手册 vs 新器件）时重新核对器件身份，不沿用旧典型电路。

## 4. 项目文档任务（新增）

### 4.1 创建许可证

- 生成 `LICENSE`（默认 MIT；用户指定时支持 Apache-2.0/GPL-3.0/BSD-3/CC0）。
- 已有 LICENSE 不覆盖；版权年份与主体由用户提供。
- 纯本地文件任务，可离线执行；提交信息注明 `generate-license`。

### 4.2 生成 README.md

- 内容只来自当前工程回读（connectivity/pcb list/drc）：概述、BOM 摘要、
  S/P 阶段当前门、导出路径（gerber/BOM/placement）、许可证引用。
- 已有 README 追加/更新章节，不全量重写；破坏性改写须确认。
- `blocked`/`fail` 的门如实标注，不写成通过。
- 提交信息注明 `generate-readme`。

## 5. 验证与交付

- 原理图：`sch gate --strict` 汇总门禁；pin→net/NC 对账；`sch export-image` 导图复核。
- PCB：`pcb drc --json` + `pcb check`；`layout-lint --gate` 落 `pre_route_passed`；
  修改后 `doc reload` 再读。
- 报告：修改范围、源数据与实际图面差异、验证结果、已保存页面、未解决项。
  INFO/WARN 单列，不把"0 fatal"称全部通过。
