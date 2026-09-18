#!/usr/bin/env python
"""check-progress.py — 步骤门禁校验：进度账本完整性 + 证据产物存在性。

用法：
  python <SKILL_DIR>/scripts/check-progress.py [--ledger ./tmp/init/progress.md] [--root .]
                                   [--steps 1,2,3,4,5,6] [--json] [--quiet]

  --steps 支持逗号列表与区间混写：`1,2,3` / `1-5` / `1..5` / `1..5,6` 等价，缺省 1-6。

账本每行格式（正本见 references/约束部分/步骤门禁/步骤门禁.md）：
  - [x] <步骤号> <步骤名> | t: <UTC ISO> | cmd: <命令> | art: <产物路径> | result: <pass|fail|blocked>

判定：
  - 每个必检步骤至少一条账目；t/cmd/art/result 四字段齐全；
  - art 指向的文件/目录必须存在（确无产物时写 `art: n/a` 并在 result 说明）。
退出码：0 通过；1 有缺项；2 账本不存在。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ENTRY_RE = re.compile(r"^\s*-\s*\[[xX]\]\s*(.+)$")
FIELD_RES = {
    "t": re.compile(r"(?:^|\|)\s*t:\s*([^|]+)"),
    "cmd": re.compile(r"(?:^|\|)\s*cmd:\s*([^|]+)"),
    "art": re.compile(r"(?:^|\|)\s*art:\s*([^|]+)"),
    "result": re.compile(r"(?:^|\|)\s*result:\s*([^|]+)"),
}
STEP_RE = re.compile(r"^\s*(\d+)")


def expand_steps(raw: str) -> list[str]:
    """把 `1,2,3` / `1-5` / `1..5` / `1..5,6` 统一展开为步骤号字符串列表。"""
    out: list[str] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        m = re.match(r"^(\d+)\s*(?:\.\.|-|–)\s*(\d+)$", token)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            out += [str(i) for i in range(min(a, b), max(a, b) + 1)]
        else:
            out.append(token)
    seen = set()
    return [s for s in out if not (s in seen or seen.add(s))]


def parse_ledger(text: str):
    entries = []
    for lineno, line in enumerate(text.splitlines(), 1):
        m = ENTRY_RE.match(line)
        if not m:
            continue
        body = m.group(1)
        sm = STEP_RE.match(body)
        fields = {}
        for key, rx in FIELD_RES.items():
            fm = rx.search(body)
            fields[key] = fm.group(1).strip() if fm else ""
        entries.append({
            "line": lineno,
            "step": sm.group(1) if sm else "",
            "label": body.split("|")[0].strip(),
            "fields": fields,
        })
    return entries


def main() -> int:
    args = sys.argv[1:]
    root = Path(args[args.index("--root") + 1]).resolve() if "--root" in args else Path.cwd()
    ledger_rel = args[args.index("--ledger") + 1] if "--ledger" in args else "./tmp/init/progress.md"
    steps_raw = args[args.index("--steps") + 1] if "--steps" in args else "1,2,3,4,5,6"
    steps = expand_steps(steps_raw)
    as_json = "--json" in args
    quiet = "--quiet" in args

    ledger = Path(ledger_rel)
    if not ledger.is_absolute():
        ledger = root / ledger_rel
    if not ledger.exists():
        msg = f"[check-progress] 账本不存在：{ledger}（先按步骤门禁写账目）"
        print(json.dumps({"ok": False, "error": "ledger_missing", "ledger": str(ledger)}, ensure_ascii=False)
              if as_json else msg, file=sys.stderr)
        return 2

    entries = parse_ledger(ledger.read_text(encoding="utf-8-sig", errors="replace"))
    problems = []
    by_step = {}
    for e in entries:
        by_step.setdefault(e["step"], []).append(e)
        for key, val in e["fields"].items():
            if not val:
                problems.append(f"第 {e['line']} 行缺字段 {key}：{e['label']}")
        art = e["fields"].get("art", "")
        if art and art.lower() not in ("n/a", "na", "-"):
            ap = Path(art)
            if not ap.is_absolute():
                ap = root / art
            if not ap.exists():
                problems.append(f"第 {e['line']} 行产物不存在：{art}")
    for s in steps:
        if not by_step.get(s):
            problems.append(f"缺步骤 {s} 的账目")

    result = {
        "ok": not problems,
        "ledger": str(ledger),
        "entries": len(entries),
        "steps_present": sorted(by_step.keys()),
        "problems": problems,
    }
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif not quiet:
        for p in problems:
            print(f"[check-progress] {p}")
        print(f"[check-progress] 账目 {len(entries)} 条，步骤 {sorted(by_step.keys())}，"
              f"{'通过' if not problems else f'待补 {len(problems)} 项'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())