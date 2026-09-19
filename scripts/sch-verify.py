#!/usr/bin/env python
"""sch-verify.py — 原理图验证序列封装：一条命令跑完四联门禁与回读对账。

替代 references/ 中多处重复枚举的原理图命令清单（部分绘制与截图 / 检查是否符合
技术手册及方案 / 校验与对账 等）。

用法：
  python <SKILL_DIR>/scripts/sch-verify.py --project <工程> [--doc <原理图页>]
                               [--out ./tmp/sch/verify-<UTC>.json]

子命令（参数真值以 easyeda sch <命令> --help 为准）：
  sch gate --strict --json      # 聚合四联（layout-lint → check → bridge-check → SDK DRC），
                                 # --json 已含每阶段原生报告，无需二次跑单命令
  sch connectivity --all-pages  # pin→net 真值（无 --json，按文本捕获）
  sch list --all-pages --include-device-identity --include-pins
  sch sheet-geometry            # 图框与内框（越界/对账基准）
  sch check（仅 gate 缺失时兜底补跑）

退出码：0 = gate 通过；3 = gate 失败/任一命令报错或 CLI 不可达（阻断）。
聚合 JSON 始终落盘（没测 ≠ 满分，见 references/lib/verification-delivery.md §8.1）。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import artifact_digest as ad  # 同目录：无人审阅工件 digest 抽象（约束·压缩机制 #9/#10）
import cli_compat as cc  # 同目录共享模块：接口漂移运行时探测（见其 docstring）


def guard_not_skill_repo() -> None:
    """cwd 疑似 skill 仓库本体时拒绝运行（FILE_CREATION_POLICY §1/§2.3：产物只落工作区）。"""
    if "--help" in sys.argv or "-h" in sys.argv:
        return
    cwd = Path.cwd()
    if (cwd / "SKILL.md").exists() and (cwd / "RULE_EDIT.md").exists():
        raise SystemExit(
            f"[{sys.argv[0].split(chr(92))[-1].split('/')[-1]}] 拒绝运行：cwd 是 skill 仓库 {cwd}。"
            "先 cd 到用户确认的工作区根目录再执行（产物只写工作区 ./tmp/）。"
        )


def run(cmd: list[str]) -> dict:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        out = (p.stdout or "").strip()
        try:
            return {"cmd": " ".join(cmd), "rc": p.returncode, "ok": p.returncode == 0,
                    "json": json.loads(out) if out else None}
        except Exception:
            return {"cmd": " ".join(cmd), "rc": p.returncode, "ok": p.returncode == 0,
                    "text": out or None, "stderr": (p.stderr or "").strip()[:500] or None}
    except FileNotFoundError:
        return {"cmd": " ".join(cmd), "rc": None, "ok": False, "blocked": "easyeda CLI 不可达"}
    except Exception as e:
        return {"cmd": " ".join(cmd), "rc": None, "ok": False, "blocked": str(e)[:200]}


def within_cwd(raw: str) -> Path:
    p = Path(raw) if Path(raw).is_absolute() else Path.cwd() / raw
    p = p.resolve()
    try:
        p.relative_to(Path.cwd().resolve())
    except ValueError:
        raise SystemExit(f"[sch-verify] 拒绝写出工作区之外：{p}")
    return p


def main() -> int:
    guard_not_skill_repo()
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--doc", help="原理图页 UUID/名（多页工程建议不传，走 --all-pages）")
    ap.add_argument("--out")
    ap.add_argument("--raw", action="store_true",
                    help="另存 raw-*.json 全文证据（默认只落 digest 形，约束·压缩机制 #9）")
    args = ap.parse_args()

    sel = ["--project", args.project]
    if args.doc:
        sel += ["--doc", args.doc]
    # 可选 flag 一律经 cli_compat 探测后附加：上游跨版本增删 flag 不再打断一键验证（fail-closed 自适应）
    gate_cmd = cc.with_flag(["easyeda", "sch", "gate", "--strict", *sel], "--json")
    conn_cmd = cc.with_flag(["easyeda", "sch", "connectivity", *sel], "--all-pages")
    list_args = cc.with_flag(["easyeda", "sch", "list", *sel], "--all-pages")
    for f in ("--include-device-identity", "--include-pins"):
        list_args = cc.with_flag(list_args, f)
    seq = [
        ("gate",          gate_cmd),
        ("connectivity",  conn_cmd),
        ("list",          list_args),
        ("sheet_geometry", ["easyeda", "sch", "sheet-geometry", *sel]),
    ]
    results, raws, failed = {}, {}, []
    for key, cmd in seq:
        r = run(cmd)
        raws[key] = r
        results[key] = ad.summarize(r)
        if not r["ok"]:
            failed.append(key)
    if results["gate"].get("blocked"):
        rc = run(cc.with_flag(["easyeda", "sch", "check", *sel], "--all"))
        raws["check"] = rc
        results["check"] = ad.summarize(rc)
        if not rc["ok"]:
            failed.append("check")

    out = within_cwd(args.out or
                     f"./tmp/sch/verify-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    raw_ref = ""
    if args.raw:
        raw_path = out.with_name(out.stem.replace("verify-", "verify-") + ".raw.json")
        ad.stash_raw(raws, raw_path)
        raw_ref = str(raw_path)
    summary = {"tool": "sch-verify", "project": args.project, "doc": args.doc or "",
               "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "digest_form": "1", "raw_ref": raw_ref,
               "all_passed": not failed, "failed_or_blocked": failed, "results": results}
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    for key in results:
        r = results[key]
        tag = "pass" if r["ok"] else ("blocked: " + r.get("blocked", "") if r.get("blocked") else f"rc={r['rc']}")
        print(f"[sch-verify] {key:14s} {tag}")
    print(f"[sch-verify] 聚合 JSON：{out}")
    if failed:
        print(f"[sch-verify] 阻断/失败项：{failed}（不得进入下一步）", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
