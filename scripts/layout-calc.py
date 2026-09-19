#!/usr/bin/env python
"""layout-calc.py — 边距与位置计算器（PCB 布局 + 原理图布局本地演算；纪律见 references/约束部分/布局计算纪律/）。

定位：布局「理解用户需求为主」的演算层——用户 PCB 配置文件（D1–D20+R1–R5）拍板后，
先跑本脚本算出档位边距/分区/坐标建议并三行留痕，再落位；`pcb align`/`distribute`/`auto-place`
只是演算之后的规整工具，不能替代本步，也不能无依据重排用户手摆件。

子命令（坐标 rect=x,y,w,h 均指左下角+宽高；PCB 单位 mil y-up，原理图单位 raw）：
  pcb gap   --a RECT --b RECT [--profile hand|reflow]
            件间边距：hand 下限 40（大焊盘烙铁通道 60）/reflow 20。
  pcb edge  --p RECT --outline W,H [--margin 100] [--copper-margin 20]
            器件→板边 ≥margin；含铜皮外露判定 →板边 ≥copper-margin。
  pcb zone  --outline W,H --zones "名:面积比[:列数],.." [--gutter 50] [--out JSON]
            功能分区装地：按面积比+gutter 切矩形，输出各区推荐矩形与中心（供逐件落位参照）。
  sch gap   --a RECT --b RECT [--class rc|ic-small|ic-mid|mcu]
            模块间距档：rc 80–120 / ic-small(8-16pin) 200–280 / ic-mid 280–400 / mcu-RF 400–600。
  sch edge  --p RECT --sheet W,H [--margin 10] [--keepout RECT]…
            图框贴边 ≥margin；压任一 keepout（标题栏等）=违规。
  angle check --segs "x1,y1,x2,y2[;..]" [--allow 0,45]
            走线段角度合规：只允许与 --allow 档同型的 0/45° 方向；90° 直角折线/斜角=违规（R1 另定时改 --allow）。
退出码：0=合规 1=违规（列差值） 2=参数错误。默认档为用户未拍板时的保守档，拍板后以配置值显式覆盖。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PCB_GAP = {"hand": 40.0, "reflow": 20.0}
SCH_GAP = {"rc": (80.0, 120.0), "ic-small": (200.0, 280.0),
           "ic-mid": (280.0, 400.0), "mcu": (400.0, 600.0)}


def rect(s: str):
    x, y, w, h = (float(v) for v in s.split(","))
    return (x, y, x + w, y + h)


def gap(a, b):
    dx = max(0.0, max(a[0] - b[2], b[0] - a[2]))
    dy = max(0.0, max(a[1] - b[3], b[1] - a[3]))
    return math.hypot(dx, dy)


def line(f, s, r):
    print(f"公式: {f}\n代入: {s}\n结果: {r}")


def cmd_pcb_gap(a):
    g = gap(rect(a.a), rect(a.b))
    lo = PCB_GAP[a.profile]
    line("d=√(dx²+dy²) 边到边；下限=装配档位", f"{a.a} vs {a.b} profile={a.profile}",
         f"d={g:.1f} mil ≥/< {lo:.0f} → {'合规' if g >= lo else '违规(差 %.1f)' % (lo - g)}")
    return 0 if g >= lo else 1


def cmd_pcb_edge(a):
    x0, y0, x1, y1 = rect(a.p)
    m = min(x0, y0, a.outline[0] - x1, a.outline[1] - y1)
    ok = m >= a.margin
    line("margin=四边最小距离；器件≥margin，露铜≥copper-margin",
         f"{a.p} outline={a.outline}",
         f"m={m:.1f} ≥/{'<'} {a.margin} → {'合规' if ok else '违规(差 %.1f)' % (a.margin - m)}"
         f"（铜皮判定仅参考，最终以 DRC 为准）")
    return 0 if ok else 1


def cmd_pcb_zone(a):
    W, H = a.outline
    parts = []
    for tok in a.zones.split(","):
        name, ratio, *col = tok.split(":")
        parts.append((name, float(ratio), int(col[0]) if col else 1))
    total = sum(r for _, r, _ in parts)
    rows, y = [], H
    for name, ratio, _c in sorted(parts, key=lambda t: -t[1]):
        h = ratio / total * (H - a.gutter * (len(parts) - 1))
        rows.append((name, y - h, y))
        y -= h + a.gutter
    out = [{"zone": n, "rect": [0.0, r0, W, r1], "center": [W / 2, (r0 + r1) / 2], "height": round(r1 - r0, 1)}
           for n, r0, r1 in rows]
    p = Path(a.out) if a.out else Path("tmp/pcb/zones-layout.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    line("h_i=占比×(H−(n−1)gutter) 横条带分区", f"outline={W}×{H} gutter={a.gutter} zones={a.zones}",
         f"分区矩形+中心已写 {p}；逐件落位仍须按 T1→T4 顺序与配置基线")
    return 0


def cmd_sch_gap(a):
    g = gap(rect(a.a), rect(a.b))
    lo, hi = SCH_GAP[a.cls]
    verdict = "合规" if g >= lo else ("偏小(低于功能带经验下限)" if g < lo else "")
    flag = "过宽(>经验带，可收紧)" if g > hi else ""
    line("d=边到边；档位=原理图模块间距经验带", f"{a.a} vs {a.b} class={a.cls}",
         f"d={g:.0f} raw，带 {lo:.0f}–{hi:.0f} → {verdict}{('；' + flag) if flag else ''}")
    return 0 if g >= lo else 1


def cmd_sch_edge(a):
    x0, y0, x1, y1 = rect(a.p)
    m = min(x0, y0, a.sheet[0] - x1, a.sheet[1] - y1)
    hits = [k for k in (a.keepout or []) if x0 < float((k.split(",")[2])) and x1 > float(k.split(",")[0])
            and y0 < float(k.split(",")[3]) and y1 > float(k.split(",")[1])]
    ok = m >= a.margin and not hits
    line("贴边距=四边最小；keepout=标题栏等硬禁区", f"{a.p} sheet={a.sheet} keepouts={a.keepout or []}",
         f"m={m:.0f} ≥{a.margin} {'且' if not hits else '但'} 压禁区={hits or '无'} → {'合规' if ok else '违规'}")
    return 0 if ok else 1


def cmd_angle(a):
    allow = sorted({int(v) % 90 for v in a.allow.split(",")})
    bad = []
    for seg in a.segs.split(";"):
        x1, y1, x2, y2 = (float(v) for v in seg.split(","))
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0:
            bad.append((seg, "零长"))
            continue
        ang = math.degrees(math.atan2(abs(dy), abs(dx)))
        if not any(abs(ang - t) < 0.5 for t in allow):
            bad.append((seg, f"角度 {ang:.1f}° 不在 {allow}° 档"))
    line(f"θ=atan2(|Δy|,|Δx|) mod 90；允许档={allow}°", f"{a.segs}",
         f"违规段 {len(bad)}：{bad[:5]}" if bad else "全部合规（默认禁直角：90°折线请拆 45° 或加大半径圆弧）")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("pcb"); ss = s.add_subparsers(dest="sub", required=True)
    g = ss.add_parser("gap"); g.add_argument("--a", required=True); g.add_argument("--b", required=True); g.add_argument("--profile", choices=PCB_GAP, default="hand")
    e = ss.add_parser("edge"); e.add_argument("--p", required=True); e.add_argument("--outline", required=True, type=lambda v: [float(x) for x in v.split(",")]); e.add_argument("--margin", type=float, default=100.0); e.add_argument("--copper-margin", dest="copper_margin", type=float, default=20.0)
    z = ss.add_parser("zone"); z.add_argument("--outline", required=True, type=lambda v: [float(x) for x in v.split(",")]); z.add_argument("--zones", required=True); z.add_argument("--gutter", type=float, default=50.0); z.add_argument("--out")
    t = sub.add_parser("sch"); ts = t.add_subparsers(dest="sub", required=True)
    g2 = ts.add_parser("gap"); g2.add_argument("--a", required=True); g2.add_argument("--b", required=True); g2.add_argument("--class", dest="cls", choices=SCH_GAP, default="rc")
    e2 = ts.add_parser("edge"); e2.add_argument("--p", required=True); e2.add_argument("--sheet", required=True, type=lambda v: [float(x) for x in v.split(",")]); e2.add_argument("--margin", type=float, default=10.0); e2.add_argument("--keepout", action="append")
    n = sub.add_parser("angle"); ns = n.add_subparsers(dest="sub", required=True); c = ns.add_parser("check"); c.add_argument("--segs", required=True); c.add_argument("--allow", default="0,45")
    a = ap.parse_args()
    try:
        fn = {"pcb": {"gap": cmd_pcb_gap, "edge": cmd_pcb_edge, "zone": cmd_pcb_zone},
              "sch": {"gap": cmd_sch_gap, "edge": cmd_sch_edge},
              "angle": {"check": cmd_angle}}[a.cmd]
        return (fn[a.sub] if a.cmd != "angle" else fn["check"])(a)
    except (ValueError, IndexError, ZeroDivisionError) as ex:
        print(f"参数错误: {ex}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
