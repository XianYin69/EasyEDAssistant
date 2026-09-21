#!/usr/bin/env python
"""chain-log.py — 在工作区 ./tmp/chains/ 下建立与维护记忆链/逻辑链（JSONL，只增不改）。

正本规则：references/约束部分/记忆链/记忆链.md、references/约束部分/逻辑链的存储/逻辑链的存储.md。
数据：./tmp/chains/memory.jsonl（出处记录链）、./tmp/chains/logic.jsonl（推导链）。
JSONL 只准本脚本追加，禁止手编与改写既有行（只增不改是前缀缓存复用的前提）。

用法：
  python <SKILL_DIR>/scripts/chain-log.py init
  python <SKILL_DIR>/scripts/chain-log.py add <memory|logic> --step <号> --claim <结论/推导>
      --src <出处：URL+页码 / 命令+工件路径> --by <user|agent|unverified>
      [--from-node A --to-node B]     （logic 建议带推导节点，供连续性校验）
  python <SKILL_DIR>/scripts/chain-log.py list <memory|logic> [--last N]
  python <SKILL_DIR>/scripts/chain-log.py verify        三要素齐备 + logic 节点连续性
退出码：0 正常；1 verify 不通过（缺三要素或链断裂）；2 写盘/越界失败。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CHAINS = Path("tmp") / "chains"
BY = ("user", "agent", "unverified")
KINDS = ("memory", "logic")


def guard_not_skill_repo() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        return
    cwd = Path.cwd()
    if (cwd / "SKILL.md").exists() and (cwd / "RULE_EDIT.md").exists():
        raise SystemExit(f"[chain-log] 拒绝运行：cwd 是 skill 仓库 {cwd}；先 cd 到工作区根。")


def path_of(kind: str) -> Path:
    return CHAINS / f"{kind}.jsonl"


def init() -> int:
    guard_not_skill_repo()
    CHAINS.mkdir(parents=True, exist_ok=True)
    for kind in KINDS:
        p = path_of(kind)
        if not p.exists():
            p.touch()
            print(f"[chain-log] 已建立 {p.as_posix()}")
        else:
            print(f"[chain-log] 已存在 {p.as_posix()}（不重置，只增不改）")
    return 0


def read(kind: str) -> list[dict]:
    p = path_of(kind)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def add(kind: str, a: argparse.Namespace) -> int:
    guard_not_skill_repo()
    p = path_of(kind)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        print(f"[chain-log] 补建目录 {p.parent.as_posix()}")
    e = {"t": a.t or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
         "step": a.step, "claim": a.claim, "src": a.src, "by": a.by}
    if kind == "logic":
        e["from"], e["to"] = a.from_node, a.to_node
    with p.open("a", encoding="utf-8") as h:
        h.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"[chain-log] 追加 {kind} 链 1 条（step {a.step}, by {a.by}）→ {p.as_posix()}")
    return 0


def list_entries(kind: str, last: int) -> int:
    es = read(kind)
    for e in es[-last:] if last else es:
        print(json.dumps(e, ensure_ascii=False))
    print(f"[chain-log] {kind}: 共 {len(es)} 条")
    return 0


def verify() -> int:
    bad = 0
    for kind in KINDS:
        es = read(kind)
        miss = [i for i, e in enumerate(es, 1)
                if not (e.get("claim") and e.get("src") and e.get("by") in BY and e.get("t"))]
        print(f"[chain-log] {kind}: {len(es)} 条 / 三要素缺失 {len(miss)} 条"
              + (f"（行号 {miss[:10]}）" if miss else ""))
        bad += len(miss)
        if kind == "logic":
            br = [(x["to"], y["from"]) for x, y in zip(es, es[1:])
                  if x.get("to") and y.get("from") and x["to"] != y["from"]]
            for f, t in br:
                print(f"[chain-log] logic 断裂: {f} -> {t}")
            bad += len(br)
    if bad:
        print(f"[chain-log] verify 不通过（{bad} 处），按约束补链后重跑")
        return 1
    print("[chain-log] verify 通过")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_subparsers(dest="cmd", required=True)
    g.add_parser("init")
    a = g.add_parser("add")
    a.add_argument("kind", choices=KINDS)
    a.add_argument("--step", required=True)
    a.add_argument("--claim", required=True)
    a.add_argument("--src", required=True, help="出处：URL+页码 或 命令+工件路径")
    a.add_argument("--by", required=True, choices=BY)
    a.add_argument("--from-node", dest="from_node", default=None)
    a.add_argument("--to-node", default=None)
    a.add_argument("--t", default=None)
    l = g.add_parser("list")
    l.add_argument("kind", choices=KINDS)
    l.add_argument("--last", type=int, default=0)
    g.add_parser("verify")
    z = ap.parse_args()
    if z.cmd == "init":
        return init()
    if z.cmd == "add":
        return add(z.kind, z)
    if z.cmd == "list":
        return list_entries(z.kind, z.last)
    return verify()


if __name__ == "__main__":
    sys.exit(main())
