#!/usr/bin/env python
"""link-probe.py — 桥接连通性探测序列封装：一条命令完成探链路 + 本机版本记录 + 兼容性探测。

替代 references/桥接联通性测试/ 里「手敲 TCP 探测 → 环境自检 → health」的多步交互，
选定规则与正本 references/lib/connection-setup.md §1.1 一致：
先探 MCP 7655；可达仍继续探 60832；双通优先 CLI/daemon；一条通即全程使用。

**更新/版本检查已全面禁用（用户指令 2026-09-18）**：
- 不联网比对最新发行版（禁 `easyeda update`/`skill status/sync`，见 约束/运行环境不可变）；
- 本机 versionGate 也**降级为纯记录**，不再作为门禁（非 ok 只提示不阻断）；版本行为差异排查
  走本地源码快照 `scripts/connector-src/eext-src.py`（离线）+ 下方 compat 探测。
compat 兼容性探测（本机 `--help` 自描述，零网络）保留——它检测「接口漂移」，非「检查更新」。
启动 daemon 仍必须 `easyeda daemon start --auto-update-skill=false`（那是写保护，不是检查）。

用法：
  python <SKILL_DIR>/scripts/link-probe.py [--mcp-port 7655] [--bridge-port 8765]
                               [--daemon-ports 60832-60841] [--project <工程>]
                               [--out ./tmp/init/link-probe.json]

退出码：0 = 已选定链路（版本状态只记录）；3 = 两条链路都不通（终止/进排查环）。
compat.missing_* 非空 → WARN（脚本层已自适应降级，不改退出码），须在报告中如实标注。
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

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
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
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


# 会话入口兼容性基线：一键脚本/流程所依赖的「命令+flag」能力。上游 CLI 破坏任一能力时，
# 此处非空 missing 即在**会话开始**告警（而不是步骤 4 中途死锁）；脚本已经 cli_compat
# 自适应降级，故漂移不阻断门禁判定，只要求如实报告并转维护窗口按 RULE_EDIT 修复。
REQUIRED_CMDS = [["sch", "export-image"], ["sch", "gate"], ["sch", "list"],
                 ["sch", "connectivity"], ["sch", "sheet-geometry"],
                 ["pcb", "snapshot"], ["pcb", "drc"], ["pcb", "check"]]
REQUIRED_FLAGS = [(["sch", "export-image"], "--format"), (["sch", "gate"], "--json"),
                  (["sch", "sheet-geometry"], "--json"), (["pcb", "drc"], "--json"),
                  (["pcb", "check"], "--json")]


def probe_compat() -> dict:
    missing_cmds = [" ".join(c) for c in REQUIRED_CMDS if not cc.cmd_supported(c)]
    missing_flags = [f"{' '.join(c)} {f}" for c, f in REQUIRED_FLAGS
                     if not cc.flag_supported(c, f)]
    return {"easyeda_reachable": bool(cc.help_text(["sch"])),
            "missing_commands": missing_cmds, "missing_flags": missing_flags,
            "drift": bool(missing_cmds or missing_flags)}


def main() -> int:
    guard_not_skill_repo()
    ap = argparse.ArgumentParser()
    ap.add_argument("--mcp-port", type=int, default=7655)
    ap.add_argument("--bridge-port", type=int, default=8765)
    ap.add_argument("--daemon-ports", default="60832-60841")
    ap.add_argument("--project", help="健康检查带工程名（可选）")
    ap.add_argument("--out")
    args = ap.parse_args()

    host = "127.0.0.1"
    mcp = tcp_open(host, args.mcp_port)
    bridge = tcp_open(host, args.bridge_port)
    daemon_ports = port_range(args.daemon_ports)
    daemon_hit = next((p for p in daemon_ports if tcp_open(host, p, 1.0)), None)

    # 本机环境一致性自检：只用 health 的 versionGate（比对已装组件互相对齐），
    # 绝不跑 `update --check`/`skill status`（那会联网比对最新发行版，见约束/运行环境不可变）。
    version = run(["easyeda", "version"])
    health = run(["easyeda", "health", *(["--project", args.project] if args.project else [])])
    version_gate = {"source": "health.versionGate", "network": "none", "judged": False,
                    "policy": "更新/版本门禁已全面禁用（用户指令 2026-09-18），此段仅记录",
                    "cli_version": (version.get("text") or "").strip() or None}
    gate_verdict = None
    parsed = health.get("json")
    if isinstance(parsed, dict) and isinstance(parsed.get("versionGate"), dict):
        version_gate["detail"] = parsed["versionGate"]
        gate_verdict = parsed["versionGate"].get("verdict")
    else:
        raw = health.get("text") or ""
        m = re.search(r'"versionGate"\s*:\s*\{', raw)
        if m:
            brace = raw.index("{", m.end() - 1)
            depth = 0
            for j in range(brace, len(raw)):
                if raw[j] == "{":
                    depth += 1
                elif raw[j] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            version_gate["detail"] = json.loads(raw[brace:j + 1])
                            gate_verdict = (version_gate["detail"] or {}).get("verdict")
                        except Exception:
                            pass
                        break
    version_gate["verdict"] = gate_verdict
    version_gate["rc"] = health.get("rc")

    # connector 版本钉定（用户指令 2026-09-18：只基于快照 tag 版本开发；发现新版→删除回归此版）。
    # 比对≠门禁：不改变退出码，只记录+告警+给出用户手工回退指引（Agent 无权代卸/代装插件）。
    pin = {"pinned": None, "observed": {}, "mismatch": False, "action": None}
    try:
        snap = json.loads((Path(__file__).resolve().parent.parent
                           / "Sample" / "easyeda-agent-connector" / ".snapshot.json"
                           ).read_text(encoding="utf-8"))
        pv = str(snap.get("connector_version") or snap.get("tag") or "").lower().lstrip("v")
        pin["pinned"] = pv or None
    except Exception:
        pass
    det = version_gate.get("detail") or {}
    pin["observed"] = {k: str(det[k]).lower().lstrip("v") for k in ("cli", "daemon")
                       if det.get(k)}
    if pin["pinned"] and pin["observed"]:
        bad = sorted(f"{k}={v}" for k, v in pin["observed"].items() if v != pin["pinned"])
        if bad:
            pin["mismatch"] = True
            pin["action"] = (f"组件版本 {bad} 与钉定 {pin['pinned']} 不符——用户在维护窗口卸载非钉定版本"
                             "（含被插件市场/侧载自动升级的 connector），用 `eext-src.py eext` 取钉定包重导入并"
                             "关闭一切自动更新；Agent 只如实报告，不得代卸/代装。")
    version_gate["pin"] = pin

    if mcp and daemon_hit is not None:
        link = "cli-daemon"          # 双通优先 CLI/daemon（connection-setup §1.1）
    elif mcp:
        link = "mcp"
    elif daemon_hit is not None:
        link = "cli-daemon"
    else:
        link = None

    out = within_cwd(args.out or "./tmp/init/link-probe.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "tool": "link-probe", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "selected_link": link,
        "mcp": {"port": args.mcp_port, "reachable": mcp, "bridge_port": args.bridge_port,
                "bridge_reachable": bridge},
        "daemon": {"reachable": daemon_hit is not None, "port": daemon_hit,
                   "probed_range": args.daemon_ports,
                   "start_cmd": "easyeda daemon start --auto-update-skill=false"},
        "version_gate": version_gate, "health_rc": health.get("rc"),
        "compat": probe_compat(),
    }
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[link-probe] MCP:{'通' if mcp else '不通'}  daemon:{'通:' + str(daemon_hit) if daemon_hit else '不通'}"
          f"  选定:{link or '无'}  本机版本 verdict:{gate_verdict or '未取到'}")
    comp = summary["compat"]
    if comp["drift"]:
        print(f"[link-probe] WARN 接口漂移：缺失命令 {comp['missing_commands'] or '无'}、"
              f"缺失 flag {comp['missing_flags'] or '无'}——脚本经 cli_compat 已自适应降级，"
              "但须在报告中如实标注，并请用户在维护窗口按 RULE_EDIT 修复 skill（运行期禁自改）",
              file=sys.stderr)
    pin_info = version_gate.get("pin") or {}
    if pin_info.get("mismatch"):
        print("[link-probe] WARN " + (pin_info.get("action") or "connector 版本与钉定不符"), file=sys.stderr)
    print(f"[link-probe] 结果 JSON：{out}")

    if link is None:
        msg = ("[link-probe] 两条链路都不通 → 进入排查环（回桥接联通性测试总索引），不得落笔\n"
               "  → 确认 EasyEDA 主程序已打开；检查插件市场是否安装了 JLCEDA MCP 和 EasyEDA Agent 插件；\n"
               "  → 如 daemon 未启动，执行：easyeda daemon start --auto-update-skill=false\n"
               "  → 然后回到本步骤第 1 步重新发起探测。")
        print(msg, file=sys.stderr)
        return 3
    if gate_verdict != "ok":
        print("[link-probe] 提示：本机 versionGate 非 ok——按用户指令（2026-09-18）**版本对齐/更新检查已全面禁用**，"
              "仅记录不阻断；接口差异由 compat 探测与源码快照（scripts/connector-src/）解释", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
