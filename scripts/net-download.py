#!/usr/bin/env python3
"""
net-download.py — 网络资源下载器（配合 scripts/net-download-policy/net-download-policy.md 使用）

功能：
  1. 从 http(s):// URL 抓取远程资源（curl 兼容封装，优先 stdlib urllib）
  2. 按 scripts/net-download-policy/net-download-policy.md 定义的**格式白名单**过滤，非白名单直接拒绝
  3. 输出根**强制**落在工作区 `./tmp/downloads/`（`Path.cwd()` 派生），拒绝逃逸
  4. 记录元数据（URL/时间戳/HTTP 状态/字节数/SHA256）到 `./tmp/downloads/index.json`

用法：
  python scripts/net-download.py --url <URL> [--name <filename>] [--out-dir ./tmp/downloads]
  python scripts/net-download.py --url-file list.txt          # 每行一个 URL
  python scripts/net-download.py --url <URL> --dry-run        # 只判定格式与目标路径

安全：
  - 拒绝 `file://`、`ftp://`、本地绝对路径、`..` 段与转义
  - 拒绝可执行/脚本扩展名（见 net-download-policy/格式黑名单/ 子文件）
  - 单文件默认上限 32 MiB（`--max-bytes` 可调，仍受策略文件约束）
  - 遵守 FILE_CREATION_POLICY.md §1.3/§2.3/§3：只写工作区 `./tmp/`，不写 skill 目录
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# 策略文件位置（人读文档，脚本运行时参考；不在运行时读取，只作对照）
POLICY_DOC = "scripts/net-download-policy/net-download-policy.md"
POLICY_FORBIDDEN = "scripts/net-download-policy/格式黑名单/格式黑名单.md"
POLICY_ALLOWED = "scripts/net-download-policy/格式白名单/格式白名单.md"

# 格式白名单（详见 net-download-policy/格式白名单/ 子文件）
ALLOWED_EXTENSIONS = {
    ".pdf", ".md", ".txt", ".html", ".htm",
    ".json", ".csv", ".yaml", ".yml", ".xml",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    ".sch", ".pcb", ".brd", ".elib", ".dip", ".epow", ".esym", ".epcb",
    ".gbr", ".drl", ".nc", ".txt",  # 制造/钻孔文件
    ".dcm", ".lib", ".kicod", ".kicad_sym", ".kicad_pcb",  # 常见 EDA 库
}

# 格式黑名单（明确禁止）
FORBIDDEN_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".com",
    ".bat", ".cmd", ".sh", ".ps1", ".vbs", ".js", ".jar",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
    ".iso", ".img", ".dmg",
}

MAX_BYTES_DEFAULT = 32 * 1024 * 1024  # 32 MiB
USER_AGENT = "EasyEDAssistant-net-download/1.0 (+https://github.com/EasyEDAssistant/easyeda-agent)"


def guard_not_skill_repo() -> None:
    """cwd 疑似 skill 仓库本体时拒绝运行（FILE_CREATION_POLICY §1/§2.3：产物只落工作区）。"""
    if "--help" in sys.argv or "-h" in sys.argv:
        return
    _cwd = Path.cwd()
    if (_cwd / "SKILL.md").exists() and (_cwd / "RULE_EDIT.md").exists():
        raise SystemExit(
            "[{}] 拒绝运行：cwd 是 skill 仓库 {}。先 cd 到用户确认的工作区根目录再执行"
            "（产物只写工作区 ./tmp/）。".format(Path(__file__).name, _cwd)
        )


def _resolve_within_workspace(raw: str) -> Path:
    """把 raw 解析为绝对路径并强制落在工作区 cwd 内；逃逸则拒绝（FILE_CREATION_POLICY §3）。"""
    workspace = Path.cwd().resolve()
    p = Path(raw)
    candidate = (p if p.is_absolute() else workspace / p).resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError:
        raise SystemExit(
            f"[net-download] 安全拒绝：目标目录 {candidate} 逃逸出工作区 {workspace}"
        )
    return candidate


def _sanitize_filename(name: str) -> str:
    """剥离路径分隔符与 `..` 段，仅保留 basename 并过滤非法字符。"""
    base = Path(name).name
    base = re.sub(r'[<>:"\\|?*\x00-\x1f]', "_", base).strip(" .")
    return base or "download.bin"


def _validate_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise SystemExit(
            f"[net-download] 拒绝：URL 协议 {parsed.scheme!r} 不在允许集合 http/https"
        )
    if not parsed.netloc:
        raise SystemExit("[net-download] 拒绝：URL 缺少 host")
    return url


def _extension_of(name_or_url: str) -> str:
    tail = urllib.parse.urlparse(name_or_url).path if "://" in name_or_url else name_or_url
    return Path(tail).suffix.lower()


def _check_format(ext: str) -> None:
    if ext in FORBIDDEN_EXTENSIONS:
        raise SystemExit(
            f"[net-download] 拒绝：{ext} 在黑名单（可执行/脚本/归档，见 {POLICY_FORBIDDEN}）"
        )
    if ext not in ALLOWED_EXTENSIONS:
        raise SystemExit(
            f"[net-download] 拒绝：{ext or '<no-extension>'} 不在白名单（见 {POLICY_ALLOWED}）"
        )


def _download(url: str, dest: Path, max_bytes: int) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    started = datetime.now(timezone.utc).isoformat()
    sha = hashlib.sha256()
    total = 0
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, dest.open("wb") as fh:
            status = getattr(resp, "status", 200)
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    fh.close()
                    dest.unlink(missing_ok=True)  # 超限不留半成品（net-download-policy §4）
                    raise SystemExit(
                        f"[net-download] 拒绝：下载字节数 {total} 超过上限 {max_bytes}"
                    )
                sha.update(chunk)
                fh.write(chunk)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"[net-download] HTTP 错误：{url} → {e.code} {e.reason}")
    except urllib.error.URLError as e:
        raise SystemExit(f"[net-download] 网络错误：{url} → {e.reason}")
    return {
        "url": url,
        "path": str(dest),
        "bytes": total,
        "sha256": sha.hexdigest(),
        "http_status": status,
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    guard_not_skill_repo()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", help="单个下载 URL（http/https）")
    ap.add_argument("--url-file", help="URL 列表文件（每行一个 URL，`#` 起注释）")
    ap.add_argument("--name", help="保存文件名；缺省从 URL 末段推断")
    ap.add_argument(
        "--out-dir", default="tmp/downloads",
        help="输出目录（相对工作区 cwd，默认 ./tmp/downloads，禁止逃逸）",
    )
    ap.add_argument("--max-bytes", type=int, default=MAX_BYTES_DEFAULT,
                    help="单文件大小上限，默认 32 MiB")
    ap.add_argument("--dry-run", action="store_true",
                    help="只判定格式与目标路径，不下载")
    args = ap.parse_args()

    if not args.url and not args.url_file:
        ap.error("--url 与 --url-file 至少提供一个")

    urls: list[str] = []
    if args.url:
        urls.append(args.url)
    if args.url_file:
        list_path = Path(args.url_file)
        if not list_path.is_absolute():
            list_path = Path.cwd() / list_path
        for line in list_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                urls.append(s)

    out_dir = _resolve_within_workspace(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []

    for url in urls:
        _validate_url(url)
        if args.name and url == urls[0]:
            filename = _sanitize_filename(args.name)
        else:
            tail = urllib.parse.urlsplit(url).path.rsplit("/", 1)[-1] or "download"
            filename = _sanitize_filename(urllib.parse.unquote(tail))
        ext = _extension_of(filename) or _extension_of(url)
        _check_format(ext)
        dest = out_dir / filename
        if args.dry_run:
            sys.stderr.write(f"[net-download] DRY-RUN OK: {url} → {dest}\n")
            continue
        sys.stderr.write(f"[net-download] 下载 {url} → {dest}\n")
        record = _download(url, dest, args.max_bytes)
        index.append(record)
        sys.stderr.write(
            f"[net-download] 完成 bytes={record['bytes']} sha256={record['sha256'][:12]}…\n"
        )

    if not args.dry_run:
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.stderr.write(f"[net-download] 索引更新 {index_path}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
