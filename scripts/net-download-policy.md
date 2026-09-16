# 网络资源下载策略（`scripts/net-download.py` 配套规范）

> 本文件是 `scripts/net-download.py` 的**格式与路径规范正本**；Agent 与
> 贡献者阅读，脚本运行时不动态解析本文件（白名单在脚本内硬编码），但
> 修改任一格式须同步两处并 review。
> 遵循 `FILE_CREATION_POLICY.md` §1.3（skill 目录 vs 工作区）、§2.3
> （`tmp/` 建在工作区）、§3（Path Traversal Guard）。

---

## 1. 目标与范围

- **目的**：Agent 在设计过程中主动获取外部知识（数据手册 PDF、协议文档、
  参考实现截图、EDA 库文件、公开制造规则 JSON 等），落到工作区
  `./tmp/downloads/` 供后续步骤引用。
- **不做**：安装软件、拉取代码仓、执行远程脚本、下载可执行体。
- **触发时机**：SKILL.md §13.2 或用户在 S0/P0 阶段明确请求。

## 2. 允许格式（白名单，脚本 `ALLOWED_EXTENSIONS`）

| 类别 | 扩展名 | 典型来源 | 落到子目录 |
|---|---|---|---|
| 数据手册 / 应用笔记 | `.pdf` | 芯片厂商官网、立创商城、Mouser、DigiKey | `./tmp/downloads/datasheet/` |
| 协议 / 标准文档 | `.pdf`、`.html`、`.md`、`.txt` | IEC/IPC/JEDEC 公开摘要、厂商 wiki | `./tmp/downloads/docs/` |
| 参考图 / 截图 | `.png`、`.jpg`、`.jpeg`、`.gif`、`.webp`、`.svg` | 博客园/Stack Overflow/知乎配图 | `./tmp/downloads/images/` |
| 结构化数据 | `.json`、`.csv`、`.yaml`、`.yml`、`.xml` | JLCPCB 工艺规则、公开元器件表 | `./tmp/downloads/data/` |
| EasyEDA 原生库 | `.sch`、`.pcb`、`.brd`、`.elib`、`.dip`、`.epow`、`.esym`、`.epcb` | 嘉立创社区分享库 | `./tmp/downloads/edalib/` |
| 制造 / 钻孔 | `.gbr`、`.drl`、`.nc` | Gerber/Excellon 归档 | `./tmp/downloads/manufacturing/` |
| 其它 EDA 库 | `.dcm`、`.lib`、`.kicod`、`.kicad_sym`、`.kicad_pcb` | 跨 EDA 参考 | `./tmp/downloads/edalib/` |

> 白名单外的扩展名一律拒绝并返回 `非白名单`；无扩展名 URL 需 `--name`
> 显式给一个合法文件名，否则同样拒绝。

## 3. 禁止格式（黑名单，脚本 `FORBIDDEN_EXTENSIONS`）

**明确禁止**（哪怕 URL 直接可下载）：

| 类别 | 扩展名 | 原因 |
|---|---|---|
| 可执行 / 动态库 | `.exe` `.dll` `.so` `.dylib` `.bin` `.com` | 恶意风险、无 EDA 用途 |
| 脚本 | `.sh` `.ps1` `.bat` `.cmd` `.vbs` `.js` `.jar` | 潜在执行面 |
| 归档 | `.zip` `.rar` `.7z` `.tar` `.gz` `.bz2` `.xz` `.iso` `.img` `.dmg` | 内容不可校验，易夹带可执行 |
| 媒体容器 | 未列出的音视频 | 与本 skill 用途无关 |

## 4. URL 与协议规则

- 仅接受 `http://` 与 `https://`；`file://` / `ftp://` / 本地绝对路径 /
  含 `..` 段一律拒绝。
- 单文件默认上限 **32 MiB**（`--max-bytes` 可调，仍受 SKILL.md §9
  3D 模型上限约束）；超出立即中断，不留部分文件。
- 60 秒超时；重试由调用方决定，脚本本身不重试。
- User-Agent：`EasyEDAssistant-net-download/1.0` 附项目主页。

## 5. 路径与逃逸防护

- 输出根**强制** `Path.cwd() / "tmp/downloads"`（或 `--out-dir` 指定的、
  经 `_resolve_within_workspace` 校验的路径）；`resolved_path.relative_to(cwd)`
  失败即 `SystemExit`，绝不写入 skill 目录或工作区外。
- 文件名 `_sanitize_filename()` 剥离路径分隔符、`..`、Windows 非法字符
  与控制字符，仅保留 basename；空 basename 兜底为 `download.bin` 后再走
  格式判定。
- 每次成功下载 append 到 `./tmp/downloads/index.json`：
  `{url, path, bytes, sha256, http_status, started_utc, finished_utc}`
  作为工作证据链，会话结束随 `./tmp/` 一并清理（SKILL.md §8.4）。

## 6. 用法示例

```bash
# 单个：数据手册
python3 scripts/net-download.py \
  --url https://www.renesas.com/document/dst/ics1893ds.pdf \
  --name ics1893ds.pdf --out-dir tmp/downloads/datasheet

# 批量：从清单文件
python3 scripts/net-download.py --url-file ./tmp/plan/dl-list.txt

# 判定（不下载）
python3 scripts/net-download.py --url https://x.example/foo.zip --dry-run
# 预期：拒绝：.zip 在黑名单
```

## 7. 与会话纪律的挂钩

- Agent 调用本脚本前须已经在 `./tmp/learning/` 或 `./tmp/plan/` 记录了
  **为什么要下载这个 URL**（SKILL.md §13.1），避免"顺手抓取"。
- 下载完成后，如属数据手册或参考文档，须同步 `./tmp/datasheet/`
  摘要 markdown（SKILL.md §8.4）；`./tmp/downloads/` 本身在收尾时全清。
- 门禁失败不豁免：任何非白名单格式即使对设计"看似必需"也不打开，
  改为向用户报告并请其手动提供（`--force` 不存在，`--yes` 不越过格式判定）。

## 8. 修订历史

- **v1.0（2026-09-14）**：随 SKILL.md v0.9.0 §13.2 首版发布。
