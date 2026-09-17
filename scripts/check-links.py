#!/usr/bin/env python
"""check-links.py — 全树 markdown 相对链接扫描：悬空链接与孤立文档检查。

用法：
  python scripts/check-links.py [--root DIR] [--quiet]

规则（与 references/约束部分 及 CHANGELOG 惯例对齐）：
  - 悬空链接：相对链接解析后目标文件不存在 → 必须为 0（退出码 1）。
  - 孤立文档：references/（不含 lib/）下无任何入链的 .md → 警告列出（不判失败，
    总索引允许经 SKILL.md 文本提及）。
退出码：0 无悬空；1 有悬空链接；2 找不到根目录。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)")
SKIP_DIRS = {".git", ".kilo", ".kilocode", ".opencode", "node_modules", "__pycache__", "tmp"}
EXTERNAL = ("http://", "https://", "mailto:", "#", "file://", "data:", "tel:")


def md_files(root: Path):
    for p in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        yield p


def main() -> int:
    args = sys.argv[1:]
    root = Path(__file__).resolve().parent.parent
    if "--root" in args:
        root = Path(args[args.index("--root") + 1])
    quiet = "--quiet" in args
    if not root.is_dir():
        print(f"[check-links] 根目录不存在：{root}", file=sys.stderr)
        return 2

    dangling = []
    incoming: dict[Path, set[str]] = {}
    for f in md_files(root):
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in LINK_RE.finditer(text):
            href = m.group(1).split("#")[0]
            if not href or href.startswith(EXTERNAL):
                continue
            target = (f.parent / unquote(href.replace("\\", "/"))).resolve()
            line = text[: m.start()].count("\n") + 1
            rel = str(f.relative_to(root)).replace("\\", "/")
            if not target.exists():
                dangling.append((rel, line, href))
            else:
                incoming.setdefault(target, set()).add(rel)

    orphans = []
    for f in md_files(root):
        rel = str(f.relative_to(root)).replace("\\", "/")
        if not rel.startswith("references/") or rel.startswith("references/lib/"):
            continue
        if f.resolve() not in incoming:
            orphans.append(rel)

    total = sum(1 for _ in md_files(root))
    if not quiet:
        for rel, line, href in dangling:
            print(f"悬空 {rel}:{line} -> {href}")
        for o in orphans:
            print(f"孤立 {o}")
        print(f"[check-links] {total} 个 md：悬空 {len(dangling)}，references/ 孤立 {len(orphans)}")
    return 1 if dangling else 0


if __name__ == "__main__":
    sys.exit(main())
