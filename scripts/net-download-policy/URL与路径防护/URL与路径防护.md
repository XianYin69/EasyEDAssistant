# 网络资源下载策略 — URL 与路径防护

> 本文件收录协议规则与路径逃逸防护（总索引见 [`../net-download-policy.md`](../net-download-policy.md)）。
> 遵循 `FILE_CREATION_POLICY.md` §1.3/§2.3/§3。编辑遵守 RULE_EDIT.md：≤ 50 行、自然语言。

## URL 与协议规则

- 仅接受 `http://` 与 `https://`；`file://` / `ftp://` / 本地绝对路径 / 含 `..` 段一律拒绝。
- 单文件默认上限 **32 MiB**（`--max-bytes` 可调）；超出立即中断并**删除已写入的半成品**，不留部分文件。
- 60 秒超时；重试由调用方决定，脚本本身不重试。
- User-Agent：`EasyEDAssistant-net-download/1.0` 附项目主页。

## 路径与逃逸防护

- 输出根**强制** `Path.cwd() / "tmp/downloads"`（或 `--out-dir` 指定的、经 `_resolve_within_workspace` 校验的路径）；`resolved_path.relative_to(cwd)` 失败即 `SystemExit`，绝不写入 skill 目录或工作区外。
- 文件名 `_sanitize_filename()` 剥离路径分隔符、`..`、Windows 非法字符与控制字符，仅保留 basename；空 basename 兜底后再走格式判定。
- **cwd 守卫**：脚本启动即检测 cwd 是否为 skill 仓库本体（存在 `SKILL.md` + `RULE_EDIT.md`），是则拒绝运行并提示先切到用户确认的工作区——否则相对路径会写进 skill 目录。

## 证据链

- 每次成功下载 append 到 `./tmp/downloads/index.json`：
  `{url, path, bytes, sha256, http_status, started_utc, finished_utc}`。
- 该文件是「下载留证」的唯一入口，供 [`../../../references/元件检查/查询技术手册/查询技术手册.md`](../../../references/元件检查/查询技术手册/查询技术手册.md) 与交付报告反查出处；会话结束随 `./tmp/` 清理。