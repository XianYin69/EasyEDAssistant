# EasyEDAssistant Reference：连接配置与开始工作

> 本文件由 SKILL.md v0.9.0「1. 连接（双链路，原有方式必须保留）」与「2. 开始工作」逐字迁移而来（v0.10.0 主干化重构）。
> 原章节编号保持不变；SKILL.md 是唯一入口，按触发条件加载本文件。

## 1. 连接（双链路，原有方式必须保留）

### 1.1 JLCEDA MCP 链路（移植版主路径）

| 通道 | 地址 | 用途 |
|---|---|---|
| WebSocket 桥接 | `ws://127.0.0.1:8765/bridge/ws` | 动作派发、心跳、窗口上下文 |
| HTTP MCP | `http://127.0.0.1:7655/mcp` | MCP 工具/资源/提示服务入口 |

Kilocode 接入（`kilo.json`，与原有链路并存、不互斥）：

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

**链路选择策略**（单链路直用，不重试）：
- MCP 与 CLI/daemon 两条链路是**替代关系**，不是级联备用。
- 开始工作前按以下优先级检测：
  1. 先尝试 `7655` 端点（MCP HTTP）；连通则全程使用 MCP。
  2. 若 MCP 不可用，再尝试 `60832` 端口（daemon）；连通则全程使用 CLI/daemon。
- **一旦检测到可用链路就使用该链路**，不重试另一条链路，不做"莫名奇妙的检测"。
- 两条端口属于同一插件，插件未启动时 `7655`/`8765` 两条端点均不可用，
  按 §1.3 恢复流程处理。
- **确认工作区根目录（cwd）**：端口连通后，询问用户其 EDA 工程
  （原理图/PCB 文件所在目录）的绝对路径，与 Kilocode 会话的
  `workspace root` 比对；以用户指定路径作为本会话运行时根目录
  `cwd`（所有运行产物 `./tmp/`、截图、回读 JSON 的根目录）。
  用户指定路径与 Kilocode `workspace root` 不一致时以用户指定为准，
  并提示确认当前会话的工作区是否与该路径匹配。

行为约束（MCP 使用时）：

- MCP 工具与 typed action 语义一致：同一套 `eda.*` API 映射、dry-run/回读/
  `saved:true` 纪律、破坏性操作确认门控；MCP 只是另一入口，不豁免任何验证。
- 审计继续写本地 `~/.easyeda-agent/audit`，MCP 调用同样记录。

### 1.2 原有链路（兼容，不得移除）

- `easyeda` CLI + daemon + EasyEDA Agent Connector；`--project` / `--doc` 路由。
- **版本门禁（会话第一条命令）**：`easyeda update --check --exit-code`，先于任何
  项目读取、离线规划、`health` 和 EDA 操作。CLI/Skill/daemon 必须精确等于 GitHub
  latest，Connector 与 latest 共享 `major.minor` 兼容线才返回 0；仅 patch 差异通过。
  门禁非 0 时停止任务按 `Sample/easyeda-agent/references/environment-setup.md` 升级；**升级/替换组件后本会话不得
  继续，必须新开会话从第一条命令重新开始**。不得用 `--version`、`--preserve`、
  `--skip-version-check` 或仅看 `health` 绕过门禁。
- **`doc reload` 门（铁律）**：PCB mutation（rip-up/route/delete/via/track/pour）
  后读 `STALE_READ` 时按提示 `easyeda doc reload --project <name>`（自身先 save），
  再重读；确定性复位 = `rip-up → save → reload`。`pour-rebuild` 也是"铺铜连通性
  stale"的修法。绕过开关是 `--force-stale-read "<理由>"`（入审计，不是 `--force`）。
- 写操作使用 `--project` 和 `--doc`，由 CLI 在派发前实时确认目标文档；
  `windowId` 随重连变化，不作为持久身份，优先用项目/文档 UUID 路由。
- **链路选择策略**：与 MCP 相同——先检测 `60832` 端口（daemon）；连通则全程
  使用 CLI/daemon；不重试 MCP。MCP 与 CLI/daemon 是替代关系，非级联备用。
- **确认工作区根目录（cwd）**：与 §1.1 相同——端口连通后询问用户 EDA 工程
  所在目录，与 Kilocode `workspace root` 比对，以用户指定路径为运行时
  `cwd`；不一致时以用户为准并提示确认。

### 1.3 连接异常恢复

1. 没有 daemon：检查安装路径与启动日志；`easyeda daemon start` 监听 60832。
2. daemon 正常但 `windows` 为空：检查编辑器、登录态、扩展启用与"允许外部交互"。
3. 同一目标页出现多版本/windowId、反复注册或写请求超时：先回读确认最后一条写
   是否落地 → 检查扩展管理器只保留所选渠道的当前连接器 → 仅当 daemon 本身
   异常时重启 → `health` 确认只剩预期连接后再继续。不循环刷新、批量杀进程、
   重发写操作或清空 IndexedDB。

## 2. 开始工作

0. **先澄清需求与目标，再动手**（§11 详述）：用户任务含糊时先补齐
   目标、边界与验收标准；已有的确认与授权沿用，不重复索取。
   执行中遇强制/条件中断点按 §11.5 暂停等待用户确认。
1. 确认插件状态：`8765` / `7655` 端点可达；不可达走原 daemon 链路。
2. 读目标工程基线：

   ```bash
   easyeda health --project <project>
   easyeda doc ls --project <project> --json
   easyeda sch connectivity --all-pages --project <project> > project-connectivity.json
   easyeda sch list --project <project> --doc <page-uuid> \
     --include-device-identity --include-pins --include-bbox --include-wires > page-before.json
   easyeda sch sheet-geometry --project <project> --doc <page-uuid> --json
   ```

3. 写前读被改器件、引脚、网络与几何；位号或 primitiveId 不明确时不盲写。
   每个参与绘图的引脚应恰好对应：一个网络、明确 NC（`noConnected:true`）或
   显式 `connectionState:"unconnected"`，三者互斥；悬空仅当官方快照明确返回
   `net:""` 与 `noConnected:false` 时自动导出，仍保留 `unconnected-pin` 警告。
4. 按任务选子域判据（第 4 节），只加载相关参考；以 `easyeda <domain> <command>
   --help` 与 `easyeda actions` 为参数真值。
5. 临时 JSON、计划与回读结果放入**工作区**（`cwd`，非 skill 目录）下已忽略的 `./tmp/` 目录；保留原始快照，在副本中设计（详见 `FILE_CREATION_POLICY.md` §2.3：运行产物禁止写入 skill 目录，且不得逃逸出工作区）。`tmp/` 下按用途分子目录（sch/pcb/plan/design/parts/calc/datasheet/snapshots/baseline），完整目录契约与清理纪律见 §8.4。
6. **工具与插件探针**：**Agent 必须自动运行** `python3 scripts/tool-probe.py --project <project>` 获取嘉立创 EDA 内建工具与已安装插件清单；
    生成 `./tmp/eda-tools-manifest.json` 与 `./tmp/eda-tools-guide.md`；
    此清单供后续设计步骤查阅并按需调用专用工具或插件。
7. **基线截图**：读取工程基线（原理图 PDF 导图或 PCB 视口快照），**Agent 自动保存**截图到 `./tmp/baseline/`（自动按时间戳命名）；
    这条截图作为后续差异对比的参考。

8. **辅助脚本自动调用**：Agent 必须在特定设计步骤前自动运行以下脚本：
   - **P1 导入前**：运行 `python3 scripts/tool-probe-simulator.py` 生成工具调用示例文档，供用户参考
   - **P6 布线前**：运行 `python3 scripts/tool-probe.py` 扫描插件状态，自动触发 §11.5 条件中断点询问用户是否启用对应插件
   - **P8 电源铺铜前**：运行 `python3 scripts/tool-probe.py` 检查电源插件状态，决定是否启用专用工具
   - **P10 终检前**：运行 `python3 scripts/tool-probe.py` 确认工具状态，确保视觉验证完整性
   - **每个关键步骤后**：自动运行 `python3 scripts/visual-qa.py` 进行视觉质量评估
 9. **动态截图管理**：
    - 每完成关键步骤后立即截一张图（原理图用 `sch export-image`，PCB 用 `pcb snapshot --previous-sha256`）；
    - 识别截图状态：用 SHA256 校验与上次截图比对，标记是否 stale（canvas-freeze）；
    - 动态清理：每次新截之前，删除 `./tmp/snapshots/` 中的旧截图（保留最近 3 张关键快照作为回溯依据）；
    - 截图保存到 `./tmp/snapshots/step-<索引>-<时间戳>.png`，便于后续复盘与 visual-qa.py 调用。
 10. **交付工件落位与清理**：原理图/PCB 字符画蓝图、计划、方案、元器件选型与比价、
     理论计算缓存、数据手册摘要、图片全部落在 `./tmp/` 对应子目录（§8.4）；
     工作结束时先在工作区根目录生成技术手册与功能手册（§7.8），再删除 `./tmp/`
     全部产物并在交付报告（§8.2）中记录（§8.4）。
 11. **主动学习与外部资源**（§13）：遇到未知器件、异常错误、非内建工具
     行为等**信息缺口**时，Agent 主动用浏览器工具（`websearch` / `webfetch`）
     在 博客园 / Stack Overflow / 知乎 / CSDN / EEVblog / 官方 wiki 检索
     同类问题，结果整理为 markdown 落 `./tmp/learning/`；需下载资源
     （数据手册 PDF / 参考图 / 结构化数据 / EDA 库文件）时调用
     `scripts/net-download.py`，输出根强制 `./tmp/downloads/`，格式判定见
     `scripts/net-download-policy.md`（§13.1/§13.2）。
