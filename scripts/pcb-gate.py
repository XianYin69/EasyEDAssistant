#!/usr/bin/env python
"""pcb-gate.py — PCB 门禁序列封装：一条命令跑完全部 PCB 门禁并聚合 JSON。

替代 references/ 中多处重复枚举的 PCB 命令清单（部分绘制与验收 / 检查是否符合
规范技术手册及方案 / 交付报告 等），消除「每次手敲 6 条命令再人肉汇总」。

用法：
  python <SKILL_DIR>/scripts/pcb-gate.py --project <工程> [--pcb-doc <PCB页>]
                             [--out ./tmp/pcb/gate-<UTC>.json] [--with-gate]

子命令（参数真值以 easyeda pcb <命令> --help 为准）：
  pcb drc --json │ check --json --strict │ layout-lint --json │
  layout-score --json │ net-classes --json │ report（无 --json，按文本捕获）
  --with-gate 追加 layout-lint --gate（会落 pre_route_passed 阶段门，需先
  `pcb stage set-assembly`；默认不跑，避免对未配置装配剖面的板意外改状态）。

退出码：0 = 全部子命令 rc 0（全过）；3 = 任一非 0 或 CLI 不可达（阻断）。
聚合 JSON 始终落盘（未跑/报错记 blocked，没测 ≠ 满分，见
references/lib/verification-delivery.md §8.1）。产物只写工作区 ./tmp/。
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
    """跑一条子命令，返回 {cmd, rc, ok, json|text, error}。CLI 不可达记 blocked。"""
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
    except Exception as e:  # 超时/解析失败等，一律 blocked 而非 pass
        return {"cmd": " ".join(cmd), "rc": None, "ok": False, "blocked": str(e)[:200]}


def within_cwd(raw: str) -> Path:
    """输出路径强制落在工作区 cwd 内（FILE_CREATION_POLICY §3）。"""
    p = Path(raw) if Path(raw).is_absolute() else Path.cwd() / raw
    p = p.resolve()
    try:
        p.relative_to(Path.cwd().resolve())
    except ValueError:
        raise SystemExit(f"[pcb-gate] 拒绝写出工作区之外：{p}")
    return p


def main() -> int:
    guard_not_skill_repo()
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--pcb-doc", help="PCB 文档 UUID/名（所有子命令统一 --doc）")
    ap.add_argument("--out", help="聚合 JSON 输出路径（默认 ./tmp/pcb/gate-<UTC>.json）")
    ap.add_argument("--with-gate", action="store_true",
                    help="追加 layout-lint --gate（会推进阶段门，需先 set-assembly）")
    ap.add_argument("--raw", action="store_true",
                    help="另存 raw-*.json 全文证据（默认只落 digest 形，约束·压缩机制 #9）")
    args = ap.parse_args()

    sel = ["--project", args.project]
    if args.pcb_doc:
        sel += ["--doc", args.pcb_doc]
    # 可选 flag（--json/--strict/--gate）经 cli_compat 探测附加：上游增删不再打断一键门禁
    d = ["easyeda", "pcb"]
    seq = [
        ("drc",          cc.with_flag([*d, "drc", *sel], "--json")),
        ("check",        cc.with_flag(cc.with_flag([*d, "check", *sel], "--json"), "--strict")),
        ("layout_lint",  cc.with_flag([*d, "layout-lint", *sel], "--json")),
        ("layout_score", cc.with_flag([*d, "layout-score", *sel], "--json")),
        ("net_classes",  cc.with_flag([*d, "net-classes", *sel], "--json")),
        ("report",       [*d, "report", *sel]),
    ]
    results, raws, failed = {}, {}, []
    if args.with_gate:
        if cc.flag_supported(["pcb", "layout-lint"], "--gate"):
            seq.append(("lint_gate", cc.with_flag([*d, "layout-lint", "--gate", *sel], "--json")))
        else:  # 探测不到推进门的能力：显式 blocked，绝不静默跳过或伪通过
            results["lint_gate"] = {"cmd": "pcb layout-lint --gate", "rc": None, "ok": False,
                                    "blocked": "cli_compat 探测：本机 CLI 不支持 --gate（接口漂移），不得当作已推进"}
            failed.append("lint_gate")
    for key, cmd in seq:
        r = run(cmd)
        raws[key] = r
        results[key] = ad.summarize(r)
        if not r["ok"]:
            failed.append(key)

    out = within_cwd(args.out or
                     f"./tmp/pcb/gate-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    raw_ref = ""
    if args.raw:
        raw_path = out.with_name(out.stem + ".raw.json")
        ad.stash_raw(raws, raw_path)
        raw_ref = str(raw_path)
    summary = {"tool": "pcb-gate", "project": args.project, "pcb_doc": args.pcb_doc or "",
               "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "digest_form": "1", "raw_ref": raw_ref,
               "all_passed": not failed, "failed_or_blocked": failed, "results": results}
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    for key in results:
        r = results[key]
        tag = "pass" if r["ok"] else ("blocked: " + r.get("blocked", "") if r.get("blocked") else f"rc={r['rc']}")
        print(f"[pcb-gate] {key:12s} {tag}")
    print(f"[pcb-gate] 聚合 JSON：{out}")
    if failed:
        print(f"[pcb-gate] 阻断/失败项：{failed}（不得进入下一步）", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
