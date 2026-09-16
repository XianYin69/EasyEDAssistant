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
  python3 scripts/visual-qa.py --project <name> [--doc <原理图页>] [--pcb-doc <PCB页>]
      [--artifacts-dir ./tmp/snapshots]   # 工作区相对路径，禁止逃逸 cwd
      [--schematic | --pcb | --both]      # 默认 --both
      [--strict]                          # WARN 也判阻塞（退出码 3）
      [--no-snapshot]                     # 跳过截图采集，只用已有数据打分
      [--prev-sha <sha256>]               # 手动指定上次 PCB 截图帧（优先于报告文件）
      [--summary]                         # 仅人读摘要（不打印 JSON）
      [--out <path>]                      # JSON 报告另存（强制工作区内）

截图与后台/前台行为：
  - 原理图走 `sch export-image`（文档渲染，真后台执行，无需 stale 检测）；
  - PCB 走 `pcb snapshot`（视口渲染）；检测到 stale（canvas-freeze）时经 `doc switch`
    自动切前台重试，最多 2 次；
  - 全程仅经 easyeda CLI/daemon API（view fit / doc switch）操作编辑器视口，
    **不发送任何 OS 级鼠标/键盘事件**，不劫持用户指针；
  - 只认本次调用后新产生的 PNG（mtime 新鲜度门槛），不再静默复用旧图；
  - 原理图器件 bbox 与 `sch sheet-geometry` 图纸边界核验：画出图纸外 = 阻断（exit 3）。
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
    """Run easyeda CLI; return stdout (captured) or empty string.

    非零退出码一律上报 stderr——capture=False 下失败不再静默，
    否则「压根没截出图」无从得知。
    """
    cmd = ["easyeda", *args]
    r = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        timeout=timeout,
    )
    if r.returncode != 0:
        detail = (r.stderr or "").strip() if (capture and r.stderr) else ""
        sys.stderr.write(f"[cli] {cmd} -> exit {r.returncode}{': ' + detail if detail else ''}\n")
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


def _latest_new_png(artifacts_dir: Path, since: float) -> Path | None:
    """只认本次调用后新产生的 PNG（mtime 新鲜度门槛），避免误抓旧图当新截图。"""
    fresh = [p for p in artifacts_dir.glob("*.png") if p.stat().st_mtime >= since]
    if not fresh:
        return None
    return max(fresh, key=lambda x: x.stat().st_mtime)


def capture_pcb_snapshot(
    project: str, artifacts_dir: Path, prev_sha: str | None,
    pcb_doc: str | None = None, max_retry: int = 2,
) -> dict:
    """
    采 PCB 截图；--previous-sha256 检测 stale 同帧。
    stale（canvas-freeze）时经 `doc switch` 把目标页切前台后重取，最多 max_retry 次。
    全程走 easyeda CLI/daemon API（view fit / doc switch），不触碰 OS 鼠标。
    返回 {path, sha256, stale, prev_sha, attempts, error?}。
    """
    out: dict = {"path": None, "sha256": None, "stale": None,
                 "prev_sha": prev_sha, "attempts": 0}
    for attempt in range(max_retry + 1):
        out["attempts"] = attempt + 1
        start = time.time() - 1.0
        _cli(["view", "fit"], capture=False, timeout=30)
        time.sleep(1.5)
        snap_args = ["pcb", "snapshot", "--project", project]
        if prev_sha:
            snap_args += ["--previous-sha256", prev_sha]
        _cli(snap_args, capture=False, timeout=60)
        time.sleep(1.5)
        snap = _latest_new_png(artifacts_dir, start)
        if snap is None:
            out["error"] = "no snapshot artifact produced (见上方 [cli] 错误行)"
            out["stale"] = True  # 无图视同 stale（数据为权威）
            break
        sha = _sha256_file(snap)
        out["path"] = str(snap)
        out["sha256"] = sha
        out["stale"] = bool(prev_sha) and sha == prev_sha
        if not out["stale"]:
            out["error"] = None
            break
        if attempt < max_retry and pcb_doc:
            sys.stderr.write(
                f"[visual-qa] PCB 截图 stale（canvas-freeze），切前台重取 "
                f"{attempt + 1}/{max_retry}\n"
            )
            _cli(["doc", "switch", pcb_doc, "--project", project],
                 capture=False, timeout=30)
            time.sleep(1.5)
            continue
        break
    return out


def capture_sch_image(project: str, doc: str, artifacts_dir: Path) -> dict:
    """
    采原理图官方导图（文档渲染，不依赖视口刷新；见 SKILL.md §5.7）。
    sch export-image 不需要 previous-sha256（文档渲染），支持后台执行。
    只认本次调用后新产生的 PNG；无新产物即报错，不再静默复用旧图。
    """
    out: dict = {"path": None, "sha256": None, "error": None}
    start = time.time() - 1.0
    args = ["sch", "export-image", "--project", project, "--doc", doc]
    _cli(args, capture=False, timeout=60)
    time.sleep(1.0)
    img = _latest_new_png(artifacts_dir, start)
    if img is None:
        out["error"] = "no export-image artifact produced (见上方 [cli] 错误行)"
        return out
    out["path"] = str(img)
    out["sha256"] = _sha256_file(img)
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
    """收集原理图数据驱动侧（list / connectivity / sheet-geometry 用于对账与越界核验）。"""
    data = {"list": None, "connectivity": None, "sheet_geometry": None}
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
    geom = _cli_json(
        ["sch", "sheet-geometry", "--project", project, "--doc", doc, "--json"],
        timeout=60,
    )
    if isinstance(geom, dict):
        data["sheet_geometry"] = geom
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


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _rect_to_bounds(x, y, w, h):
    if all(_num(v) for v in (x, y, w, h)):
        x, y, w, h = float(x), float(y), float(w), float(h)
        return (min(x, x + w), min(y, y + h), max(x, x + w), max(y, y + h))
    return None


def _extract_sheet_bounds(geom):
    """从 sheet-geometry JSON 尽力提取可绘制边界 (x0,y0,x1,y1)（兼容多种键形，单位 raw）。"""
    if not isinstance(geom, dict):
        return None
    candidates = [geom]
    for key in ("drawArea", "sheetBorder", "border", "bounds", "area", "geometry"):
        if isinstance(geom.get(key), dict):
            candidates.append(geom[key])
    for b in candidates:
        r = _rect_to_bounds(b.get("x"), b.get("y"), b.get("width"), b.get("height"))
        if r:
            return r
        l, rr, t, bo = b.get("left"), b.get("right"), b.get("top"), b.get("bottom")
        if all(_num(v) for v in (l, rr, t, bo)):
            return (float(l), float(bo), float(rr), float(t))
    return None


def _item_bounds(item: dict):
    """从器件记录提取 bbox (x0,y0,x1,y1)；支持 [x,y,w,h]、{x,y,width,height}、{x0,y0,x1,y1}。"""
    raw = item.get("bbox") or item.get("boundingBox") or item.get("box")
    if isinstance(raw, (list, tuple)) and len(raw) >= 4 and all(_num(v) for v in raw[:4]):
        x, y, w, h = [float(v) for v in raw[:4]]
        return (min(x, x + w), min(y, y + h), max(x, x + w), max(y, y + h))
    if isinstance(raw, dict):
        r = _rect_to_bounds(raw.get("x"), raw.get("y"), raw.get("width"), raw.get("height"))
        if r:
            return r
        x0, y0, x1, y1 = raw.get("x0"), raw.get("y0"), raw.get("x1"), raw.get("y1")
        if all(_num(v) for v in (x0, y0, x1, y1)):
            return (float(x0), float(y0), float(x1), float(y1))
    return None


def _iter_components(lst_data):
    if isinstance(lst_data, dict):
        for key in ("components", "devices", "items", "list"):
            if isinstance(lst_data.get(key), list):
                return lst_data[key]
        return []
    if isinstance(lst_data, list):
        return [x for x in lst_data if isinstance(x, dict)]
    return []


def evaluate_sch(image: dict, data: dict, strict: bool) -> dict:
    """评估原理图：截图存在性 + 数据可用性 + 图纸边界核验（越界 = 阻断）。"""
    result = {
        "layer": "schematic",
        "screenshot": {"path": image.get("path"), "sha256": image.get("sha256"),
                       "error": image.get("error")},
        "data_available": {k: bool(v) for k, v in data.items()},
        "bounds_check": "skipped",
        "out_of_bounds": [],
        "verdict": "pass",
        "issues": [],
    }
    # 截图是逐件纠错主通道：没有新导图 = 阻断，不允许静默通过
    if image.get("error"):
        result["verdict"] = "fail"
        result["issues"].append(
            {"level": "blocking", "area": "screenshot",
             "msg": "export-image 未产出新图（截图缺失，查 [cli] 错误行）"}
        )
    # 图纸边界核验：器件 bbox 必须完整落在可绘制边界内（y-UP，raw 单位）
    bounds = _extract_sheet_bounds(data.get("sheet_geometry"))
    comps = _iter_components(data.get("list"))
    if not bounds:
        result["issues"].append(
            {"level": "warn", "area": "sheet_geometry",
             "msg": "图纸边界不可解析 → 越界检查未运行（不得当作通过）"}
        )
        if result["verdict"] == "pass":
            result["verdict"] = "warn"
    elif not comps:
        result["issues"].append(
            {"level": "warn", "area": "components",
             "msg": "无器件记录 → 越界检查未运行（不得当作通过）"}
        )
        if result["verdict"] == "pass":
            result["verdict"] = "warn"
    else:
        result["bounds_check"] = "run"
        for item in comps:
            bb = _item_bounds(item)
            if not bb:
                continue
            if bb[0] < bounds[0] or bb[1] < bounds[1] or bb[2] > bounds[2] or bb[3] > bounds[3]:
                ref = item.get("ref") or item.get("designator") or item.get("name") or "?"
                result["out_of_bounds"].append({"ref": ref, "bbox": list(bb)})
        if result["out_of_bounds"]:
            result["verdict"] = "fail"
            refs = ", ".join(str(o["ref"]) for o in result["out_of_bounds"][:20])
            result["issues"].append(
                {"level": "blocking", "area": "out_of_bounds",
                 "msg": f"{len(result['out_of_bounds'])} 个器件画出图纸边界: {refs}"}
            )
    for k, v in data.items():
        if not v and k != "sheet_geometry":
            result["issues"].append(
                {"level": "warn", "area": k, "msg": f"{k} data missing"}
            )
            if result["verdict"] == "pass":
                result["verdict"] = "warn"
    return result


# ───────────────────────── 主入口 ─────────────────────────


def _sanitize_project(name: str) -> str:
    """剥离任何路径分隔符与 .. 序列，防止注入到文件名/路径（FILE_CREATION_POLICY §5.2）。"""
    return Path(name).name or "default"


def _resolve_within_workspace(raw: str) -> Path:
    """解析为绝对路径并强制落在工作区(cwd)内；逃逸则拒绝。"""
    workspace = Path.cwd().resolve()
    p = Path(raw)
    candidate = (p if p.is_absolute() else workspace / p).resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError:
        raise SystemExit(
            f"[visual-qa] 安全拒绝：产物目录 {candidate} 逃逸出工作区 {workspace}"
        )
    return candidate


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--project", required=True)
    ap.add_argument("--doc", help="原理图页 UUID/名（导图与越界核验用）")
    ap.add_argument("--pcb-doc", help="PCB 文档 UUID/名（stale 时切前台重试）")
    ap.add_argument("--artifacts-dir", default="tmp")
    mode_g = ap.add_mutually_exclusive_group()
    mode_g.add_argument("--schematic", dest="mode", action="store_const",
                        const="schematic", help="仅原理图评估")
    mode_g.add_argument("--pcb", dest="mode", action="store_const",
                        const="pcb", help="仅 PCB 评估")
    mode_g.add_argument("--both", dest="mode", action="store_const",
                        const="both", help="双侧评估（默认）")
    ap.set_defaults(mode="both")
    ap.add_argument("--strict", action="store_true", help="WARN 也判阻塞")
    ap.add_argument("--no-snapshot", action="store_true", help="跳过截图采集")
    ap.add_argument("--prev-sha", help="上次 PCB 截图 sha256（优先于报告文件，stale 检测）")
    ap.add_argument("--summary", action="store_true", help="仅人读摘要，不打印 JSON")
    ap.add_argument("--out", help="完整 JSON 报告另存路径（强制工作区内）")
    args = ap.parse_args()

    args.project = _sanitize_project(args.project)
    artifacts = _resolve_within_workspace(args.artifacts_dir)
    artifacts.mkdir(parents=True, exist_ok=True)

    # 读取上次报告的 PCB screenshot sha256（用于 stale 检测）
    prev_report_path = artifacts / f"visual-qa-{args.project}.json"
    prev_sha = args.prev_sha
    if not prev_sha and prev_report_path.exists():
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
                else capture_pcb_snapshot(args.project, artifacts, prev_sha,
                                          pcb_doc=args.pcb_doc))
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

    report_json = json.dumps(report, ensure_ascii=False, indent=2)
    if not args.summary:
        print(report_json)
    # 持久化报告供下次运行读 prev_sha（stale 检测闭环）
    try:
        prev_report_path.write_text(report_json, encoding="utf-8")
    except OSError as e:
        sys.stderr.write(f"[visual-qa] WARN: cannot persist report for next run: {e}\n")
    if args.out:
        out_path = _resolve_within_workspace(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report_json, encoding="utf-8")
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
