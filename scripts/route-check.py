#!/usr/bin/env python
"""route-check.py — 单段走线落笔前的干涉演算门（向量-节点 / 网络标签-端口布线法专用）。

本项目已弃用上游迷宫自动布线（autoroute/export-dsn/import-autoroute，见指令索引·布线与过孔）。
人工逐段布 `pcb track` 之前，用本脚本对候选向量段做几何干涉演算：
  节点/端口 = `pcb list --include-pads`（焊盘中心 + 网络名标签）；
  障碍      = 异网 track/via/pad/keepout region/板框（全部运行时回读，信封剥壳、键形宽容）；
  判据      = references/电气检查/硬编码规则/PCB/间距与线宽.md（默认档内置，可 --clearance 覆盖）。

用法（以用户确认的工作区为 cwd）：
  python <SKILL_DIR>/scripts/route-check.py --project <工程> [--pcb-doc <PCB页>]
      --net GND --x1 1000 --y1 1000 --x2 1500 --y2 1000
      [--layer 1] [--width 6] [--role signal|clock|power|gnd] [--clearance 6]
      [--out ./tmp/pcb/routecheck-<ts>.json]

角色默认档（mil，源自 间距与线宽.md 走线宽度档位表·1 oz 外层；可显式覆盖）：
  signal 宽6 距6 | clock 宽6(建议8) 距8（长平行段请按 3×线宽 手工给 --clearance）
  power  宽12   距8 | gnd   宽8    距6
同网铜不计间距（允许相连）；异网按 间距 = clearance + (本段宽/2 + 障碍半宽) 判。

退出码：0 = 无干涉可落笔；1 = 有干涉（报告列出每个障碍 id/距离/差值，改向量或换层/绕距后复检）；
3 = 数据回读 blocked（形状不可解析/链路不通——**演算失败 ≠ 通过**，禁止凭感觉落笔）。
每次落 track 前跑一次；本段验证 primitive 与部分级截图硬门、`pcb-gate` 终检纪律不变（部分绘制与验收.md）。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cli_compat as cc

ROLE_DEFAULTS = {  # (width_mil, clearance_mil)
    "signal": (6, 6), "clock": (8, 8), "power": (12, 8), "gnd": (8, 6),
}
TRACK_R = 0.0   # track 半宽按各自 width/2 处理（回读缺 width 时用 6/2）
VIA_HALF = 21.5  # 常用过孔外径 ~43 mil 的半宽（保守近似）
PAD_HALF = 15.0  # 焊盘缺尺寸时的保守半宽近似
EDGE_KEEPIN = 10.0    # 走线到板边（间距与线宽.md 图形质量）
COPPER_EDGE_KEEPIN = 20.0


def guard_not_skill_repo() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        return
    cwd = Path.cwd()
    if (cwd / "SKILL.md").exists() and (cwd / "RULE_EDIT.md").exists():
        raise SystemExit(
            "[route-check] 拒绝运行：cwd 是 skill 仓库。先 cd 到用户确认的工作区根目录再执行。")


def within_cwd(raw: str) -> Path:
    p = Path(raw) if Path(raw).is_absolute() else Path.cwd() / raw
    p = p.resolve()
    try:
        p.relative_to(Path.cwd().resolve())
    except ValueError:
        raise SystemExit(f"[route-check] 拒绝写出工作区之外：{p}")
    return p


def _cli_json(args: list[str], timeout: int = 90):
    cmd = cc.with_flag(["easyeda", *args], "--json")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    except Exception as e:
        return {"__err__": str(e)[:200]}
    if p.returncode != 0:
        return {"__err__": f"rc={p.returncode}: {(p.stderr or '').strip()[:200]}"}
    out = (p.stdout or "").strip()
    try:
        return _unwrap(json.loads(out))
    except Exception:
        m = re.search(r"[\[{].*", out, re.S)
        if m:
            try:
                return _unwrap(json.loads(m.group(0)))
            except Exception:
                pass
        return {"__err__": "输出非 JSON 且无可行抽取"}


def _unwrap(d):
    if isinstance(d, dict) and isinstance(d.get("result"), (dict, list)) and ("ok" in d or "type" in d):
        return d["result"]
    return d


def _num(v):
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def _lst(d, *keys):
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for k in keys:
            if isinstance(d.get(k), list):
                return d[k]
        for v in d.values():
            got = _lst(v, *keys) if isinstance(v, (dict, list)) else None
            if got is not None:
                return got
    return None


def _pt(obj, xs, ys):
    for xk, yk in zip(xs, ys):
        if _num(obj.get(xk)) and _num(obj.get(yk)):
            return float(obj[xk]), float(obj[yk])
    return None


def seg_point_dist2(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == dy == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return ((x1 + t * dx - px) ** 2 + (y1 + t * dy - py) ** 2) ** 0.5


def seg_seg_dist2(a1, b1, a2, b2):
    d = min(seg_point_dist2(a1[0], a1[1], a2[0], a2[1], b2[0], b2[1]),
            seg_point_dist2(b1[0], b1[1], a2[0], a2[1], b2[0], b2[1]),
            seg_point_dist2(a2[0], a2[1], a1[0], a1[1], b1[0], b1[1]),
            seg_point_dist2(b2[0], b2[1], a1[0], a1[1], b1[0], b1[1]))
    if _cross(a1, b1, a2, b2):
        return 0.0
    return d


def _cross(p1, p2, p3, p4):
    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    d1, d2, d3, d4 = cr(p2, p1, p3), cr(p2, p1, p4), cr(p1, p2, p3), cr(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def collect_obstacles(sel: list[str], net: str, notes: list):
    """返回 [{'kind','id','net','seg':(p1,p2) 或 'pt':(x,y) 或 'rect':(x0,y0,x1,y1),'half':w}]。"""
    obs = []
    tl = _cli_json([*sel, "pcb", "track-list"])
    if isinstance(tl, dict) and "__err__" in tl:
        notes.append(f"track-list 回读失败：{tl['__err__']}")
    else:
        for t in _lst(tl, "tracks", "items", "result") or []:
            if not isinstance(t, dict):
                continue
            p1 = _pt(t, ("x1", "xa", "x_1"), ("y1", "ya", "y_1")) or \
                _pt(t.get("start") or t.get("a") or {}, ("x",), ("y",))
            p2 = _pt(t, ("x2", "xb", "x_2"), ("y2", "yb", "y_2")) or \
                _pt(t.get("end") or t.get("b") or {}, ("x",), ("y",))
            if p1 and p2:
                obs.append({"kind": "track", "id": t.get("primitiveId") or t.get("id"),
                            "net": str(t.get("net") or ""),
                            "seg": (p1, p2),
                            "half": (float(t["width"]) if _num(t.get("width")) else 6.0) / 2})
    vl = _cli_json([*sel, "pcb", "via-list"])
    if isinstance(vl, dict) and "__err__" in vl:
        notes.append(f"via-list 回读失败：{vl['__err__']}")
    else:
        for v in _lst(vl, "vias", "items") or []:
            if isinstance(v, dict):
                p = _pt(v, ("x",), ("y",))
                if p:
                    obs.append({"kind": "via", "id": v.get("primitiveId") or v.get("id"),
                                "net": str(v.get("net") or ""), "pt": p, "half": VIA_HALF})
    cl = _cli_json(cc.with_flag([*sel, "pcb", "list"], "--include-pads"))
    if isinstance(cl, dict) and "__err__" in cl:
        notes.append(f"pcb list 回读失败：{cl['__err__']}")
    else:
        for c in _lst(cl, "components", "devices") or []:
            for pd in (c.get("pads") or [] if isinstance(c.get("pads"), list) else []):
                if not isinstance(pd, dict):
                    continue
                p = _pt(pd, ("x", "cx"), ("y", "cy"))
                if p:
                    obs.append({"kind": "pad", "id": pd.get("primitiveId") or pd.get("padId") or c.get("name"),
                                "net": str(pd.get("net") or ""), "pt": p, "half": PAD_HALF})
    rl = _cli_json(cc.with_flag([*sel, "pcb", "region", "list"], "--json"))
    if isinstance(rl, dict) and "__err__" in rl:
        notes.append(f"region list 回读失败（keepout 未计入）：{rl['__err__']}")
    else:
        for r in _lst(rl, "regions", "items") or []:
            if not isinstance(r, dict):
                continue
            bb = r.get("bbox") or r
            p1 = _pt(bb, ("minX", "x0", "x1", "left"), ("minY", "y0", "y1", "bottom"))
            p2 = _pt(bb, ("maxX", "x1", "x2", "right"), ("maxY", "y1", "y2", "top"))
            if p1 and p2:
                obs.append({"kind": "keepout", "id": r.get("name") or r.get("primitiveId"),
                            "net": "", "rect": (p1[0], p1[1], p2[0], p2[1]), "half": 0.0})
    return obs


def main() -> int:
    guard_not_skill_repo()
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--pcb-doc")
    ap.add_argument("--net", required=True)
    for k in ("x1", "y1", "x2", "y2"):
        ap.add_argument(f"--{k}", type=float, required=True)
    ap.add_argument("--layer", type=int, default=1)
    ap.add_argument("--width", type=float)
    ap.add_argument("--role", default="signal", choices=sorted(ROLE_DEFAULTS))
    ap.add_argument("--clearance", type=float)
    ap.add_argument("--out")
    args = ap.parse_args()

    w = args.width if args.width is not None else ROLE_DEFAULTS[args.role][0]
    clr = args.clearance if args.clearance is not None else ROLE_DEFAULTS[args.role][1]
    sel = ["--project", args.project]
    if args.pcb_doc:
        sel += ["--doc", args.pcb_doc]

    notes: list[str] = []
    ol = _cli_json(cc.with_flag([*sel, "pcb", "outline-get"], "--json"))
    bbox = None
    if isinstance(ol, dict) and "__err__" not in ol:
        cand = ol.get("bbox") if isinstance(ol.get("bbox"), dict) else ol
        p1 = _pt(cand, ("minX", "x0", "left"), ("minY", "y0", "bottom"))
        p2 = _pt(cand, ("maxX", "x1", "right"), ("maxY", "y1", "top"))
        if p1 and p2:
            bbox = (p1[0], p1[1], p2[0], p2[1])
    else:
        notes.append(f"outline-get 回读失败（板边距未计入）：{(ol or {}).get('__err__')}")

    obs = collect_obstacles(sel, args.net, notes)
    a, b = (args.x1, args.y1), (args.x2, args.y2)

    hits, blocked_reads = [], [n for n in notes if "回读失败" in n]
    if bbox:
        for (x, y) in (a, b):
            if not (bbox[0] + EDGE_KEEPIN <= x <= bbox[2] - EDGE_KEEPIN
                    and bbox[1] + EDGE_KEEPIN <= y <= bbox[3] - EDGE_KEEPIN):
                hits.append({"kind": "board-edge", "id": "outline", "dist": None,
                             "msg": f"端点 ({x},{y}) 越板边 keep-in（bbox={bbox}，边距≥{EDGE_KEEPIN} mil）"})
    for o in obs:
        if o["net"] == args.net:
            continue  # 同网豁免间距（相连合法）
        need = clr + w / 2 + o.get("half", 0.0)
        if "seg" in o:
            dist = seg_seg_dist2(a, b, o["seg"][0], o["seg"][1])
        elif "pt" in o:
            dist = min(seg_point_dist2(o["pt"][0], o["pt"][1], a[0], a[1], b[0], b[1]),
                       1e9)
        elif "rect" in o:
            x0, y0, x1, y1 = o["rect"]
            inx = any(x0 <= cx <= x1 and y0 <= cy <= y1 for cx, cy in (a, b))
            inside = any(x0 <= (a[0] + t * (b[0] - a[0])) <= x1
                         and y0 <= (a[1] + t * (b[1] - a[1])) <= y1
                         for t in [i / 20 for i in range(21)])
            dist = 0.0 if (inside or inx) else min(
                seg_point_dist2(px, py, a[0], a[1], b[0], b[1])
                for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)))
        else:
            continue
        if dist < need:
            hits.append({"kind": o["kind"], "id": o["id"], "net": o["net"],
                         "dist": round(dist, 2), "need": round(need, 2),
                         "shortfall": round(need - dist, 2)})

    out = within_cwd(args.out or f"./tmp/pcb/routecheck-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    status = "blocked" if (blocked_reads and not obs) else ("interference" if hits else "clear")
    rep = {"tool": "route-check", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "project": args.project, "net": args.net,
           "segment": {"a": a, "b": b, "layer": args.layer, "width": w, "role": args.role,
                       "clearance": clr},
           "obstacles_read": len(obs), "notes": notes, "status": status,
           "interferences": hits[:20], "interference_total": len(hits),
           "verdict_hint": ("可落笔：easyeda pcb track --x1.. --net " + args.net +
                            f" --layer {args.layer} --width {int(w)}（落笔后逐笔回读 primitive + 部分级截图硬门 + 终检 pcb-gate）"
                            if status == "clear" else
                            "禁止凭感觉落笔：改向量/绕距/经批准换层(via-hop)/rip-up 让位后复检" if status == "interference"
                            else "回读失败=演算失败，先修链路/形状再判")}
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[route-check] {status.upper()}：{len(hits)} 处干涉  报告 {out}")
    for h in hits[:10]:
        print("  -", json.dumps(h, ensure_ascii=False))
    for n in notes:
        print("  note:", n)
    if status == "blocked":
        print("[route-check] 数据回读失败，演算未成立（≠通过）", file=sys.stderr)
        return 3
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
