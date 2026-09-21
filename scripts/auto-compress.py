#!/usr/bin/env python
"""auto-compress.py — 自动压缩工作区 ./tmp/ 上下文工件（步骤边界由 progress-log.py 钩子触发）。

正本规则：references/约束部分/上下文存储压缩机制/上下文存储压缩机制.md。
行为：
  1) JSON 工件（> --max-bytes）→ 复用 artifact_digest 落 digest 形（判定字段不压缩，
     带 src_cmd/raw_ref 指针），原文件删除；仅 --keep-raw 时改名 raw-<名> 另存。
     跳过：chains/、downloads/ 审计 index.json、已是 digest 的文件。
  2) snapshots/ 与 baseline/ 的 png 按修改时间只保留最近 --keep 张（默认 3，约束第 5 条）。
默认 --dry-run 只报告不动盘；--apply 才执行。cwd 在 skill 仓库直接拒绝。
退出码：0 成功；2 写盘失败。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artifact_digest import digest_json  # noqa: E402

SKIP_NAMES = ("index.json",)
SKIP_DIRS = ("chains", "divergence")


def guard_not_skill_repo() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        return
    cwd = Path.cwd()
    if (cwd / "SKILL.md").exists() and (cwd / "RULE_EDIT.md").exists():
        raise SystemExit(f"[auto-compress] 拒绝运行：cwd 是 skill 仓库 {cwd}；先 cd 到工作区根。")


def is_digest(d) -> bool:
    return isinstance(d, dict) and d.get("form") == "digest"


def plan_json(tmp: Path, max_bytes: int):
    out = []
    for p in sorted(tmp.rglob("*.json")):
        rel_parts = p.relative_to(tmp).parts
        if rel_parts[0] in SKIP_DIRS or p.name in SKIP_NAMES or p.name.startswith("digest-"):
            continue
        if p.stat().st_size <= max_bytes and not p.name.startswith("raw-"):
            continue
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if is_digest(j):
            continue
        out.append((p, j))
    return out


def do_json(p: Path, j, apply: bool, keep_raw: bool) -> None:
    d = digest_json(j)
    d["raw_ref"] = None if keep_raw else "dropped"
    d["compressed_from"] = {"path": p.name, "bytes": p.stat().st_size}
    tgt = p.parent / f"digest-{p.name}"
    if apply:
        tgt.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        if keep_raw:
            raw = p.parent / f"raw-{p.name}"
            p.replace(raw)
        else:
            p.unlink()
    print(f"[auto-compress] {'digest' if apply else '将转 digest'}: {p.as_posix()} "
          f"({d['compressed_from']['bytes']}B)" + ("" if keep_raw else " → 原文件删除"))


def plan_png(tmp: Path, keep: int):
    doomed = []
    for sub in ("snapshots", "baseline"):
        d = tmp / sub
        if not d.is_dir():
            continue
        fs = sorted(d.rglob("*.png"), key=lambda f: f.stat().st_mtime, reverse=True)
        doomed += fs[keep:]
    return doomed


def main() -> int:
    guard_not_skill_repo()
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmp", default="./tmp")
    ap.add_argument("--max-bytes", type=int, default=20480)
    ap.add_argument("--keep", type=int, default=3, help="快照/基线各保留最近 N 张")
    ap.add_argument("--apply", action="store_true", help="实际写盘（默认 dry-run）")
    ap.add_argument("--keep-raw", action="store_true", help="原文改名 raw-* 另存而非删除")
    a = ap.parse_args()
    tmp = Path(a.tmp)
    if not tmp.is_dir():
        print(f"[auto-compress] 无 {tmp}，跳过")
        return 0
    if not a.apply:
        print("[auto-compress] dry-run（加 --apply 执行）")
    n = 0
    try:
        for p, j in plan_json(tmp, a.max_bytes):
            do_json(p, j, a.apply, a.keep_raw)
            n += 1
        for f in plan_png(tmp, a.keep):
            if a.apply:
                f.unlink()
            print(f"[auto-compress] {'删除' if a.apply else '将删除'}过期快照: {f.as_posix()}")
            n += 1
    except OSError as e:
        print(f"[auto-compress] 写盘失败：{e}", file=sys.stderr)
        return 2
    print(f"[auto-compress] 完成：处理 {n} 项（JSON digest + 快照裁剪）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
