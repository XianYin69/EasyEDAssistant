#!/usr/bin/env python
"""progress-log.py — 按步骤门禁格式向进度账本追加/更新一条记录。

正本格式与规则见 references/约束部分/步骤门禁/步骤门禁.md；校验用 scripts/check-progress.py。

用法：
  python <SKILL_DIR>/scripts/progress-log.py --step <步骤号> --name <步骤名> --cmd <证据命令>
                                 --art <产物路径[,多个]> --result <pass|fail|blocked>
                                 [--ledger ./tmp/init/progress.md] [--t <UTC ISO>]

行为：
  - 账本不存在则按标准表头创建；同一步骤号重复记录时整体替换该行（幂等，防双记）。
  - art 以逗号分隔，逐项写入（产物缺失只提醒，由 check-progress.py 判阻断）。
  - 文件在工作区 ./tmp/ 内（FILE_CREATION_POLICY §3），不落 skill 目录。

退出码：0 写入成功；1 参数非法（result 不在枚举内 / 缺 art）；2 账本写出失败。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

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


RESULTS = ("pass", "fail", "blocked")
HEADER = ("# 步骤进度账本\n\n"
          "> 由 scripts/progress-log.py 维护；校验：python <SKILL_DIR>/scripts/check-progress.py\n"
          "> 格式：- [x] <步骤号> <名> | t: <UTC ISO> | cmd: <命令> | art: <产物> | result: <pass|fail|blocked>\n\n")


def main() -> int:
    guard_not_skill_repo()
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", required=True, help="步骤号：1-6 或子步如 4.2")
    ap.add_argument("--name", required=True)
    ap.add_argument("--cmd", required=True, help="证据命令（留空会写 n/a 但视为无效证据）")
    ap.add_argument("--art", required=True, help="证据产物路径，逗号分隔可多个")
    ap.add_argument("--result", required=True, choices=RESULTS)
    ap.add_argument("--ledger", default="./tmp/init/progress.md")
    ap.add_argument("--t", help="覆盖时间戳（UTC ISO），默认取当前时间")
    args = ap.parse_args()

    stamp = args.t or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = (f"- [{'x' if args.result == 'pass' else ' '}] {args.step} {args.name} | "
            f"t: {stamp} | cmd: {args.cmd} | art: {args.art} | result: {args.result}")

    p = Path(args.ledger)
    if not p.is_absolute():
        p = Path.cwd() / args.ledger
    try:
        rel = p.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        print(f"[progress-log] 拒绝写工作区之外：{p}", file=sys.stderr)
        return 2
    if p.exists():
        text = p.read_text(encoding="utf-8")
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        text = HEADER
    row = line.split("|", 1)[0].rstrip()
    lines = text.splitlines()
    replaced = False
    for i, l in enumerate(lines):
        ls = l.strip()
        if (ls.startswith("- [x] ") or ls.startswith("- [ ] ")) and \
           ls[6:].split(" |")[0].split(" ", 1)[0] == args.step:
            lines[i] = line
            replaced = True
            break
    if not replaced:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(line)
    try:
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as e:
        print(f"[progress-log] 写入失败：{e}", file=sys.stderr)
        return 2

    print(f"[progress-log] {'更新' if replaced else '追加'}步骤 {args.step}（{args.result}）→ {rel.as_posix()}")
    for a in [x.strip() for x in args.art.split(",") if x.strip()]:
        if a.lower() not in ("n/a", "na") and not (Path.cwd() / a).exists():
            print(f"[progress-log] 提醒：产物尚不存在 {a}（check-progress 将判阻断）", file=sys.stderr)
    auto_compress_hook()
    return 0


def auto_compress_hook() -> None:
    """步骤边界自动压缩 ./tmp/（约束·上下文存储压缩机制第 11 条）；失败只告警不阻断记账。"""
    script = Path(__file__).resolve().parent / "auto-compress.py"
    if not script.exists():
        return
    try:
        subprocess.run([sys.executable, str(script), "--apply"],
                       timeout=120, capture_output=True, check=False)
    except Exception as e:  # noqa: BLE001 钩子降级：压缩失败不影响账本
        print(f"[progress-log] 警告：自动压缩钩子未执行（{e}），可手动跑 auto-compress.py --apply",
              file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
