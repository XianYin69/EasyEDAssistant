# EasyEDAssistant Reference：主动学习与外部资源

> 本文件由 SKILL.md v0.9.0 §13 逐字迁移而来（v0.10.0 主干化重构）。
> 原章节编号保持不变；SKILL.md 是唯一入口，按触发条件加载本文件。

## 13. 主动学习与外部资源

> 会话遇到信息缺口（不认识的器件、异常错误码、非内建工具行为、数据手册
> 参数不明、参考电路缺失等）时，Agent **主动**用浏览器工具与网络下载
> 脚本补齐知识，产物落工作区 `./tmp/learning/` 与 `./tmp/downloads/`
> （§8.4）；skill 目录不写入。这是"运行时知识获取"通道，不豁免 §1.2
> 版本门禁与 §11.5 中断机制。

### 13.1 主动学习（浏览器检索）

**触发条件**（任一）：
- 未知 MPN / LCSC C 号 / 器件封装：手册关键参数、典型应用未查到
- 命令报错 / daemon 返回未知 code / 图元行为异常
- 需要跨平台核对选型、行情、库存、替代品
- 遇到 §9 已知限制外的新症状

**检索站点优先级**（不越权、不下载页面外链资源）：
| 主题 | 优先站点 |
|---|---|
| 中文经验/踩坑 | 博客园、知乎、CSDN、电子发烧友、嘉立创 论坛 |
| 英文工程问答 | Stack Overflow、Electronics Stack Exchange、EEVblog Forum、All About Circuits |
| 器件与选型 | 厂商官网、DigiKey、Mouser、立创商城、华秋、LCSC |
| 标准与规范 | IPC / JEDEC / IEC 摘要、JLCPCB 能力页 |
| 协议 | USB-IF / IEEE / SDMI 公开摘要页 |

**工具**：`websearch`（首查）、`webfetch`（取正文）；不用浏览器执行页面
JS、不做账号登录、不下载页面上的可执行体（下载走 §13.2）。

**落盘工件**：`./tmp/learning/<topic>.md`，字段固定：

```markdown
# <topic> 学习笔记

- 时间：<UTC ISO>
- 触发：<为什么查>
- 站点/URL：
  - <url1>
  - <url2>
- 摘要：<3–5 条要点>
- 关键数据/参数：<带厂商/型号/条件>
- 与本工程的映射：<怎么用；影响哪些引脚/网/参数>
- 未证实项：<标"未核实"，不回填 §4 判据或 standard-parts.json>
```

**纪律**：
- 学习笔记是**证据链**，不是新知识真值；与 `references/lib/`
  冲突时以本地经验库为准，再落"待验证"标签。
- 不将笔记内容静默合并进 `SKILL.md`；如下结论要改判据，走 §11.5 中断
  点请用户拍板，再由贡献者按 `CONTRIBUTING.md` 修订流程更新 skill 本体。
- 会话结束随 `./tmp/` 一并清理（§8.4）。

### 13.2 网络资源下载（`scripts/net-download.py`）

**用途**：需要"文件本体"（数据手册 PDF、参考图、公开 EDA 库、
结构化数据）时，用 `scripts/net-download.py` 拉取；不通过浏览器工具
抓页面资源，也不 `curl` 手工执行。

**Agent 调用规范**：
- 先按 §13.1 在 `./tmp/learning/` 记下**为什么要下载**这个 URL；
- 再执行：`python <SKILL_DIR>/scripts/net-download.py --url <URL> [--name <filename>]`；
- 输出根**强制** `Path.cwd() / "tmp/downloads"`（或 `--out-dir`
  指定的、经 `_resolve_within_workspace` 校验的子目录，如
  `tmp/downloads/datasheet/`、`tmp/downloads/images/`、
  `tmp/downloads/data/`、`tmp/downloads/edalib/`、`tmp/downloads/manufacturing/`），
   禁止 `../`、绝对路径到 skill 目录或工作区外（FILE_CREATION_POLICY.md §3）；
- 格式判定见 `scripts/net-download-policy/net-download-policy.md` §2/§3（现见 `格式白名单/` 与 `格式黑名单/` 子文件）：
  - **白名单**：`.pdf` `.md` `.txt` `.html` `.json` `.csv` `.yaml`
    `.xml` `.png` `.jpg` `.jpeg` `.gif` `.webp` `.svg` `.sch` `.pcb`
    `.brd` `.elib` `.dip` `.epow` `.esym` `.epcb` `.gbr` `.drl`
    `.nc` `.dcm` `.lib` `.kicod` `.kicad_sym` `.kicad_pcb`
  - **黑名单**（拒绝）：`.exe` `.dll` `.so` `.dylib` `.bin` `.com`
    `.sh` `.ps1` `.bat` `.cmd` `.vbs` `.js` `.jar`
    `.zip` `.rar` `.7z` `.tar` `.gz` `.bz2` `.xz` `.iso` `.img` `.dmg`
- 协议仅允许 `http(s)://`；`file://` / `ftp://` / 本地路径一律拒绝。
- 单文件默认上限 32 MiB（§9 3D 模型上限同源）；超出立即中断，不留
  部分文件；每次成功 append 到 `./tmp/downloads/index.json`（URL/时间/
  字节数/SHA256/HTTP 状态），作为工作证据链。
- `--dry-run` 只判定格式与目标路径，用于"先看会不会被拒"。

**失败处理**：
- 白名单外/黑名单内 → 不 `--force`；改为向用户报告并请求手动投递
  到工作区（用户负责校验来源），或找替代合法格式资源；
- HTTP 4xx/5xx → 报告 URL + 状态；不重试；
- 网络错误 → 检查 §1.1 端口；插件/代理不干预。

**清理**：`./tmp/downloads/` 与 `index.json` 会话结束随 §8.4 全清；
需要长期保留的（如数据手册 PDF）先由 Agent 复制到用户指定的**工作区**
正式目录（非 skill 目录），再清 tmp。

### 13.3 PCB 设计基线（`references/lib/pcb-design-spec.md`）

PCB 阶段（P0）进入前，Agent **必须**读
`references/lib/pcb-design-spec.md` §2 **必答清单**
D1–D20（板框 / 安装孔 / 叠层 / 铜厚 / 电源轨 / 接地 / 阻抗 / 接口 /
天线 / 封装下限 / 热预算 / 测试点 / 丝印 / 隔离 / DFM / 拼板 / 颜色 /
未用脚 / 成本 / 验收线），逐项问用户，答复落到**工作区**
`./tmp/design/<project>-pcb-spec.md`：

```markdown
# <project> PCB 设计基线

| 项 | 用户答复 | 依据 | 拍板时间 |
|---|---|---|---|
| D1 板框 | 60 × 40 mm，R3 圆角 | 外壳图 | 2026-… |
| D2 安装孔 | 4 × M2.5，孔心距边 3.5 mm | 结构 | … |
…
```

**强制中断**（§11.5 P0 行）：D1 板框 / D2 安装孔 / D8 关键接口三项任一
未定即不放行四档放置（immovable 参考未定）；D3 叠层、D5 电源轨、
D6 接地、D9 天线形式为条件中断——缺失会改变设计时按 §11.5 中断协议
摊牌。已拍板项在后续 P1–P10 沿用，不重复问；变更走 §11.5 中断点
重新拍板。

**与其他章节的关系**：
- 本清单**问用户要什么**；§4.2/§4.7/§4.8 是**定了之后怎么做**；
- 基线文件是 §8.2 交付报告与 §7.8 技术手册的引用来源；
- 基线里的 D15（DFM 目标）与 `references/lib/`
  `fab-rules-jlcpcb.json` 一致时走默认，否则按用户指定的厂规；
- 基线里的 D20（验收线）落到 §8.1 五层验证的具体门禁。

**skill 维护者**：新增必答项须同步更新 `pcb-design-spec.md` §2 表与本节
引用；`scripts/net-download.py` 与 `net-download-policy/net-download-policy.md` 修改格式
列表时同步 §13.2 内联白/黑名单，两处不一致以策略文件为准，脚本更新
走 `CONTRIBUTING.md` 评审。
