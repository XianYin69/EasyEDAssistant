#!/usr/bin/env python3
"""
visual-qa.py — EasyEDAssistant 视觉质量与布局完整性自动评估

用 API 截图（pcb snapshot / sch export-image）+ 数据驱动检查
（layout-score / pcb check / pcb drc）交叉评估原理图与 PCB 的视觉质量，
聚焦：组件间距、走线间距、整体整齐度。

设计原则（见 SKILL.md §8.1 验证分层）：
  - 呈现层（截图）不可互替，但数据校验是权威——截图只做视觉终检。
  - PCB snapshot 可能 stale（--previous-sha256 检测同帧）；sch export-image
    是文档渲染，不依赖视口刷新。
  - 截图与数据不一致时以数据为准，但必须把"图面 stale"标为阻断项。
  - layout-score 九维是诊断不是硬门；短路/重叠/出框一票否决。

输出 JSON 到 stdout，人读摘要到 stderr。退出码：
  0 = 全通过（含截图非 stale）
  2 = 有 WARN（带痕候选 / 低分维 / 截图 stale 但数据通过）
  3 = 有 blocking（短路/重叠/出框/间距硬违规/截图 stale 且数据也不全）

用法：
  python3 scripts/visual-qa.py --project <name> [--doc <page-uuid>]
      [--artifacts-dir .easyeda/artifacts]
      [--schematic | --pcb | --both]   # 默认 --both
      [--strict]                        # WARN 也判阻塞（退出码 3）
      [--no-snapshot]                   # 跳过截图采集，只用已有数据打分
      [--json]                          # 完整 JSON 到 stdout（默认）
      [--summary]                       # 仅人读摘要

依赖：easyeda CLI 在 PATH；活体窗口或 daemon（端口 60832）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ───────────────────────── CLI 封装 ─────────────────────────


def _cli(args: list[str], capture: bool = True, timeout: int = 60) -> str:
    """Run easyeda CLI; return stdout (captured) or empty string."""
    cmd = ["easyeda", *args]
    r = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        timeout=timeout,
    )
    if r.returncode != 0 and capture:
        # 不静默吞错；写 stderr 但不中断（调用方按返回值判）
        sys.stderr.write(f"[cli] {cmd} -> exit {r.returncode}: {r.stderr.strip()}\n")
    return r.stdout if capture else ""


def _cli_json(args: list[str], timeout: int = 60) -> dict | list | None:
    out = _cli(args, timeout=timeout)
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


# ───────────────────────── 截图采集 ─────────────────────────

# PCB 九维（与 Go 侧 pcb_layout_score 一致；skipped/degraded 不参与加权）
PCB_DIMS = [
    "partition", "flow-order", "edge-io", "protection",
    "tidy", "compact", "rf", "routable", "clearance",
]

# 截图→关注域映射（数据驱动侧的真值来源）
FOCUS_AREAS = {
    "component_spacing": {
        "label": "组件间距",
        "dims": ["compact", "clearance"],
        "gate": "solder-access",
        "drc_rules": ["clearance"],
    },
    "trace_clearance": {
        "label": "走线间距",
        "dims": ["routable", "clearance"],
        "check_rules": ["acute-angle", "dangling-end"],
        "drc_rules": ["clearance", "trackWidth"],
    },
    "layout_neatness": {
        "label": "整体整齐度",
        "dims": ["tidy", "partition", "flow-order"],
        "sub_rules": ["rotation-inconsistent"],
    },
}


def _sha256_file(p: Path) -> str | None:
    if not p.exists():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def capture_pcb_snapshot(
    project: str, artifacts_dir: Path, prev_sha: str | None
) -> dict:
    """
    采 PCB 截图；用 --previous-sha256 检测 stale 同帧。
    返回 {path, sha256, stale, prev_sha, error?}。
    """
    out: dict = {"path": None, "sha256": None, "stale": None, "prev_sha": prev_sha}
    # 先 fit + 等待渲染（canvas-freeze 风险；见 SKILL.md §5.7）
    _cli(["view", "fit"], capture=False, timeout=30)
    time.sleep(1.5)
    snap_args = ["pcb", "snapshot", "--project", project]
    if prev_sha:
        snap_args += ["--previous-sha256", prev_sha]
    _cli(snap_args, capture=False, timeout=60)
    time.sleep(1.5)
    arts = sorted(artifacts_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not arts:
        out["error"] = "no snapshot artifact produced"
        out["stale"] = True  # 无图视同 stale（数据为权威）
        return out
    snap = arts[0]
    sha = _sha256_file(snap)
    out["path"] = str(snap)
    out["sha256"] = sha
    out["stale"] = (sha == prev_sha) if prev_sha else False
    return out


def capture_sch_image(project: str, doc: str, artifacts_dir: Path) -> dict:
    """
    采原理图官方导图（文档渲染，不依赖视口刷新；见 SKILL.md §5.7）。
    sch export-image 不需要 previous-sha256（文档渲染）。
    """
    out: dict = {"path": None, "error": None}
    args = ["sch", "export-image", "--project", project, "--doc", doc]
    _cli(args, capture=False, timeout=60)
    time.sleep(1.0)
    arts = sorted(
        artifacts_dir.glob("*.png"),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )
    if not arts:
        out["error"] = "no export-image artifact produced"
        return out
    out["path"] = str(arts[0])
    return out


# ───────────────────────── 数据采集 ─────────────────────────


def collect_pcb_data(project: str) -> dict:
    """收集 PCB 数据驱动侧（layout-score / check / drc / list）。"""
    data = {"layout_score": None, "check": None, "drc": None, "components": None}

    score = _cli_json(
        ["pcb", "layout-score", "--project", project, "--json"], timeout=60
    )
    if isinstance(score, dict):
        data["layout_score"] = score

    check = _cli_json(
        ["pcb", "check", "--project", project, "--json"], timeout=60
    )
    if isinstance(check, dict):
        data["check"] = check

    # drc 前台窗口执行；超时装前景跑一次不循环重试（SKILL.md §5.7）
    drc = _cli_json(
        ["pcb", "drc", "--project", project, "--json"], timeout=90
    )
    if isinstance(drc, dict):
        data["drc"] = drc

    comps = _cli_json(
        [
            "pcb", "components.list", "--project", project,
            "--include-bbox", "--include-pads", "--json",
        ],
        timeout=60,
    )
    if isinstance(comps, (dict, list)):
        data["components"] = comps

    return data


def collect_sch_data(project: str, doc: str) -> dict:
    """收集原理图数据驱动侧（list / connectivity 用于对账）。"""
    data = {"list": None, "connectivity": None}
    lst = _cli_json(
        [
            "sch", "list", "--project", project, "--doc", doc,
            "--include-device-identity", "--include-pins",
            "--include-bbox", "--include-wires", "--json",
        ],
        timeout=60,
    )
    if isinstance(lst, (dict, list)):
        data["list"] = lst
    conn = _cli_json(
        ["sch", "connectivity", "--project", project, "--doc", doc, "--json"],
        timeout=60,
    )
    if isinstance(conn, (dict, list)):
        data["connectivity"] = conn
    return data


# ───────────────────────── 评估 ─────────────────────────


def _score_dim(score_data: dict, dim: str) -> dict:
    """从 layout-score 取单维结果；标记 skipped/degraded。"""
    if not score_data:
        return {"score": None, "status": "skipped", "reason": "no layout-score"}
    dims = score_data.get("dimensions") or score_data.get("dims") or {}
    d = dims.get(dim) or {}
    if d.get("skipped") or d.get("status") == "skipped":
        return {"score": d.get("score"), "status": "skipped", "reason": d.get("reason")}
    if d.get("degraded") or d.get("status") == "degraded":
        return {"score": d.get("score"), "status": "degraded", "reason": d.get("reason")}
    return {"score": d.get("score"), "status": "ok", "reason": None}


def _blocking_items(score_data: dict) -> list:
    if not score_data:
        return []
    return list(score_data.get("blocking") or score_data.get("blockers") or [])


def _findings_of(check_data: dict, rule_substrings: list[str]) -> list:
    """从 pcb check findings 里筛出命中的规则。"""
    if not check_data:
        return []
    findings = check_data.get("result", {}).get("findings") or check_data.get("findings") or []
    out = []
    for f in findings:
        rule = str(f.get("rule") or f.get("type") or "")
        if any(sub in rule for sub in rule_substrings):
            out.append(f)
    return out


def _drc_violations(drc_data: dict, rule_keys: list[str]) -> list:
    if not drc_data:
        return []
    # drc --json 结构以实际为准；尝试常见键
    violations = drc_data.get("violations") or drc_data.get("errors") or []
    out = []
    for v in violations:
        rule = str(v.get("rule") or v.get("type") or v.get("name") or "")
        if any(k.lower() in rule.lower() for k in rule_keys):
            out.append(v)
    return out


def evaluate_pcb(snapshot: dict, data: dict, strict: bool) -> dict:
    """评估 PCB 视觉质量；三层：blocking 硬门 → 关注域 → 截图一致性。"""
    score = data.get("layout_score") or {}
    check = data.get("check") or {}
    drc = data.get("drc") or {}

    result = {
        "layer": "pcb",
        "blocking": _blocking_items(score),
        "focus_areas": {},
        "screenshot": {
            "path": snapshot.get("path"),
            "sha256": snapshot.get("sha256"),
            "stale": snapshot.get("stale"),
            "error": snapshot.get("error"),
        },
        "verdict": "pass",
        "issues": [],
    }

    # 1) 硬门一票否决（短路/重叠/出框）
    if result["blocking"]:
        result["verdict"] = "fail"
        result["issues"].append(
            {"level": "blocking", "area": "layout", "msg": "blocking items present",
             "count": len(result["blocking"])}
        )

    # 2) 三关注域
    for key, spec in FOCUS_AREAS.items():
        area = {"label": spec["label"], "dims": {}, "drc": [], "check": [], "status": "ok"}

        for dim in spec.get("dims", []):
            area["dims"][dim] = _score_dim(score, dim)

        if spec.get("check_rules"):
            area["check"] = _findings_of(check, spec["check_rules"])
        if spec.get("drc_rules"):
            area["drc"] = _drc_violations(drc, spec["drc_rules"])

        # 维度状态聚合
        dim_statuses = [d["status"] for d in area["dims"].values()]
        has_skip = any(s == "skipped" for s in dim_statuses)
        has_degraded = any(s == "degraded" for s in dim_statuses)
        low_score = any(
            d["score"] is not None and float(d["score"]) < 0.6
            for d in area["dims"].values()
        )
        has_violation = bool(area["drc"]) or bool(area["check"])

        if has_violation:
            area["status"] = "fail"
            result["verdict"] = "fail"
            result["issues"].append(
                {"level": "blocking", "area": key,
                 "msg": f"{len(area['drc'])} drc + {len(area['check'])} check findings"}
            )
        elif low_score or has_degraded:
            area["status"] = "warn"
            if result["verdict"] != "fail":
                result["verdict"] = "warn"
            result["issues"].append(
                {"level": "warn", "area": key, "msg": "low/degraded dimension score"}
            )
        elif has_skip:
            area["status"] = "degraded"
            if result["verdict"] == "pass":
                result["verdict"] = "warn"
            result["issues"].append(
                {"level": "warn", "area": key, "msg": "dimension skipped (没测≠满分)"}
            )

        result["focus_areas"][key] = area

    # 3) 截图一致性（stale → 至少 warn；strict 且数据不全 → fail）
    if snapshot.get("error") or snapshot.get("stale"):
        level = "blocking" if (strict and result["verdict"] == "fail") else "warn"
        result["issues"].append(
            {"level": level, "area": "screenshot",
             "msg": "snapshot stale or missing (数据校验为权威，截图只做视觉终检)"}
        )
        if result["verdict"] == "pass":
            result["verdict"] = "warn"
        if strict and snapshot.get("stale"):
            result["verdict"] = "fail"

    return result


def evaluate_sch(image: dict, data: dict, strict: bool) -> dict:
    """评估原理图视觉质量（数据较少；主要看截图 + 文字避让/方向一致）。"""
    result = {
        "layer": "schematic",
        "screenshot": {"path": image.get("path"), "error": image.get("error")},
        "data_available": {k: bool(v) for k, v in data.items()},
        "verdict": "pass",
        "issues": [],
    }
    # 原理图没有 layout-score；只能依赖 sch gate --strict（调用方应另跑）
    # 这里只做截图存在性 + 数据可用性
    if image.get("error"):
        result["verdict"] = "warn"
        result["issues"].append(
            {"level": "warn", "area": "screenshot",
             "msg": "export-image missing (文档渲染失败)"}
        )
    for k, v in data.items():
        if not v:
            result["issues"].append(
                {"level": "warn", "area": k, "msg": f"{k} data missing"}
            )
            if result["verdict"] == "pass":
                result["verdict"] = "warn"
    return result


# ───────────────────────── 主入口 ─────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--project", required=True)
    ap.add_argument("--doc", help="schematic page UUID")
    ap.add_argument("--artifacts-dir", default=".easyeda/artifacts")
    ap.add_argument("--mode", choices=["schematic", "pcb", "both"], default="both")
    ap.add_argument("--strict", action="store_true", help="WARN 也判阻塞")
    ap.add_argument("--no-snapshot", action="store_true", help="跳过截图采集")
    args = ap.parse_args()

    artifacts = Path(args.artifacts_dir)
    artifacts.mkdir(parents=True, exist_ok=True)

    # 读取上次报告的 PCB screenshot sha256（用于 stale 检测）
    prev_report_path = artifacts / f"visual-qa-{args.project}.json"
    prev_sha = None
    if prev_report_path.exists():
        try:
            prev = json.loads(prev_report_path.read_text(encoding="utf-8"))
            pcb_prev = (prev.get("pcb") or {}).get("screenshot") or {}
            prev_sha = pcb_prev.get("sha256")
        except (json.JSONDecodeError, OSError):
            pass  # 上次报告损坏 → 无 prev_sha，视为首次运行

    report = {
        "project": args.project,
        "mode": args.mode,
        "strict": args.strict,
        "pcb": None,
        "schematic": None,
        "overall_verdict": "pass",
        "exit_code": 0,
    }

    # PCB
    if args.mode in ("pcb", "both"):
        snap = ({"path": None, "sha256": None, "stale": None, "prev_sha": prev_sha, "error": "skipped"}
                if args.no_snapshot
                else capture_pcb_snapshot(args.project, artifacts, prev_sha))
        data = collect_pcb_data(args.project)
        report["pcb"] = evaluate_pcb(snap, data, args.strict)

    # Schematic
    if args.mode in ("schematic", "both"):
        if not args.doc:
            sys.stderr.write("[visual-qa] --doc required for schematic mode\n")
            report["schematic"] = {"verdict": "blocked", "issues": [
                {"level": "blocking", "area": "config", "msg": "--doc required"}
            ]}
        else:
            img = ({"path": None, "error": "skipped"}
                   if args.no_snapshot
                   else capture_sch_image(args.project, args.doc, artifacts))
            data = collect_sch_data(args.project, args.doc)
            report["schematic"] = evaluate_sch(img, data, args.strict)

    # 聚合退出码
    verdicts = []
    if report["pcb"]:
        verdicts.append(report["pcb"]["verdict"])
    if report["schematic"]:
        verdicts.append(report["schematic"]["verdict"])
    if any(v == "fail" for v in verdicts):
        report["overall_verdict"] = "fail"
        report["exit_code"] = 3
    elif any(v == "warn" for v in verdicts):
        report["overall_verdict"] = "warn"
        report["exit_code"] = 2 if not args.strict else 3
    elif any(v == "blocked" for v in verdicts):
        report["overall_verdict"] = "blocked"
        report["exit_code"] = 3
    else:
        report["overall_verdict"] = "pass"
        report["exit_code"] = 0

    print(json.dumps(report, ensure_ascii=False, indent=2))
    # 持久化报告供下次运行读 prev_sha（stale 检测闭环）
    try:
        prev_report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as e:
        sys.stderr.write(f"[visual-qa] WARN: cannot persist report for next run: {e}\n")
    # 人读摘要到 stderr
    sys.stderr.write(
        f"[visual-qa] {args.project}: {report['overall_verdict']} "
        f"(exit {report['exit_code']})\n"
    )
    if report["pcb"]:
        for iss in report["pcb"].get("issues", []):
            sys.stderr.write(f"  pcb/{iss['area']}: {iss['level']} - {iss['msg']}\n")
    if report["schematic"]:
        for iss in report["schematic"].get("issues", []):
            sys.stderr.write(f"  sch/{iss['area']}: {iss['level']} - {iss['msg']}\n")
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
