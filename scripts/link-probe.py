#!/usr/bin/env python
"""link-probe.py — 桥接连通性探测序列封装：一条命令完成探链路 + 版本门禁 + 健康检查。

替代 references/桥接联通性测试/ 里「手敲 TCP 探测 → update --check → health」的多步交互，
选定规则与正本 references/lib/connection-setup.md §1.1 一致：
先探 MCP 7655；可达仍继续探 60832；双通优先 CLI/daemon；一条通即全程使用。

用法：
  python scripts/link-probe.py [--mcp-port 7655] [--bridge-port 8765]
                               [--daemon-ports 60832-60841] [--project <工程>]
                               [--out ./tmp/init/link-probe.json]

退出码：0 = 已选定链路且版本门禁过；2 = 版本门禁仅「无法确认」(rc=2，不阻断)；
3 = 版本门禁非 0（终止性失败：须升级 + 新开会话）或两条链路都不通。
"""
from __future__ import annotations

import argparse
import json
import socket
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


def tcp_open(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def port_range(spec: str) -> list[int]:
    if "-" in spec:
        a, b = spec.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(spec)]


def run(cmd: list[str]) -> dict:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        out = (p.stdout or "").strip()
        try:
            data = json.loads(out) if out else None
        except Exception:
            data = None
        return {"cmd": " ".join(cmd), "rc": p.returncode,
                "json": data, "text": None if data is not None else (out or (p.stderr or "").strip()[:400] or None)}
    except FileNotFoundError:
        return {"cmd": " ".join(cmd), "rc": None, "blocked": "easyeda CLI 不可达"}
    except Exception as e:
        return {"cmd": " ".join(cmd), "rc": None, "blocked": str(e)[:200]}


def within_cwd(raw: str) -> Path:
    p = Path(raw) if Path(raw).is_absolute() else Path.cwd() / raw
    p = p.resolve()
    try:
        p.relative_to(Path.cwd().resolve())
    except ValueError:
        raise SystemExit(f"[link-probe] 拒绝写出工作区之外：{p}")
    return p


def main() -> int:
    guard_not_skill_repo()
    ap = argparse.ArgumentParser()
    ap.add_argument("--mcp-port", type=int, default=7655)
    ap.add_argument("--bridge-port", type=int, default=8765)
    ap.add_argument("--daemon-ports", default="60832-60841")
    ap.add_argument("--project", help="健康检查带工程名（可选）")
    ap.add_argument("--skip-version-gate", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    host = "127.0.0.1"
    mcp = tcp_open(host, args.mcp_port)
    bridge = tcp_open(host, args.bridge_port)
    daemon_ports = port_range(args.daemon_ports)
    daemon_hit = next((p for p in daemon_ports if tcp_open(host, p, 1.0)), None)

    version_gate = ({"rc": None, "skipped": True} if args.skip_version_gate
                    else run(["easyeda", "update", "--check", "--exit-code"]))
    health = run(["easyeda", "health", *(["--project", args.project] if args.project else []), "--json"])

    if mcp and daemon_hit is not None:
        link = "cli-daemon"          # 双通优先 CLI/daemon（connection-setup §1.1）
    elif mcp:
        link = "mcp"
    elif daemon_hit is not None:
        link = "cli-daemon"
    else:
        link = None

    vrc = version_gate.get("rc")
    out = within_cwd(args.out or "./tmp/init/link-probe.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "tool": "link-probe", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "selected_link": link,
        "mcp": {"port": args.mcp_port, "reachable": mcp, "bridge_port": args.bridge_port,
                "bridge_reachable": bridge},
        "daemon": {"reachable": daemon_hit is not None, "port": daemon_hit,
                   "probed_range": args.daemon_ports},
        "version_gate": version_gate, "health": health,
    }
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[link-probe] MCP:{'通' if mcp else '不通'}  daemon:{'通:' + str(daemon_hit) if daemon_hit else '不通'}"
          f"  选定:{link or '无'}  版本门禁 rc:{vrc}")
    print(f"[link-probe] 结果 JSON：{out}")

    if link is None:
        print("[link-probe] 两条链路都不通 → 进入排查环（回桥接联通性测试总索引），不得落笔", file=sys.stderr)
        return 3
    if not args.skip_version_gate:
        if vrc == 0:
            return 0
        if vrc == 2:
            print("[link-probe] 版本门禁无法确认（rc=2）：不阻断，须在报告中记录「版本未确认」", file=sys.stderr)
            return 2
        print("[link-probe] 版本门禁未过（终止性失败）→ 升级 CLI 后新开会话", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
