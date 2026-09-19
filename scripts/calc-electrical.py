#!/usr/bin/env python
"""calc-electrical.py — 电气计算器（本项目本地扩展，非上游文件；纪律见 references/约束部分/计算纪律/）。

子命令（每项输出「公式 + 代入 + 结果」，可整行复制进进度账本作计算留痕）：
  ohm        --v/--i/--r/--p 任二 欧姆定律与功率
  divider    --vin --vout [--i-div uA] 分压比并给 E24 接近对
  led        --vs --vf --i LED 限流电阻（E24 + 功率二验）
  rc         --r --c → τ/fc；或 --fc --c → r（截止频率反解）
  ipc2152    --current A [--temp-rise 10] [--copper-oz 1] [--layer external|internal]
             IPC-2152 载流线宽（I=k·ΔT^0.44·A^0.725，外层 k=0.048 内层 0.024）
  via-current --drill-mil [--plating-mil 0.8] [--temp-rise 10] 钻孔镀厚载流近似
  impedance  --mode microstrip|stripline --w-mil --h-mil [--er 4.35] [--t-mil 1.4]
             Hammerstad 经验式（±10% 近似，正式阻抗以板厂叠层工具为准）
  l4         --freq-mhz [--er-effective 4.0] λ/4 长度（mm 与 mil）
  db         --to db|np --value X [--reference] dB↔倍数换算

退出码 0=成功 2=参数不足/非法。数值均为公开标准公式；档位冲突以
references/电气检查/硬编码规则/PCB/间距与线宽.md 与板厂当季参数取严。
"""
from __future__ import annotations

import argparse
import math
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6,
       3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]


def e24(x: float) -> float:
    """就近 E24 标称值。"""
    if x <= 0:
        return x
    ex = math.floor(math.log10(x))
    best, bd = None, None
    for m in (ex - 1, ex, ex + 1):
        for b in E24:
            v = b * (10 ** m)
            d = abs(math.log(v / x))
            if bd is None or d < bd:
                best, bd = v, d
    return best


def si2(v):
    """SI 前缀数值解析：'1k'→1000、'100p'→1e-10、'3u3' 不支持（写 3.3u）。"""
    if isinstance(v, (int, float)):
        return float(v)
    s = v.strip()
    mult = 1.0
    units = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6,
             "m": 1e-3, "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9}
    if s and s[-1] in units:
        mult = units[s[-1]]
        s = s[:-1]
    return float(s) * mult


def fmt(v: float) -> str:
    a = abs(v)
    for suf, mult in (("M", 1e6), ("k", 1e3), ("", 1.0), ("m", 1e-3),
                      ("µ", 1e-6), ("n", 1e-9), ("p", 1e-12)):
        if a >= mult:
            return f"{v / mult:.4g}{suf}"
    return f"{v:g}"


def line(formula: str, sub: str, result: str) -> None:
    print(f"公式: {formula}\n代入: {sub}\n结果: {result}")


def cmd_ohm(a):
    vals = {k: v for k, v in {"v": a.v, "i": a.i, "r": a.r, "p": a.p}.items() if v is not None}
    if len(vals) != 2:
        print("需恰好提供任二项 --v --i --r --p", file=sys.stderr); return 2
    (k1, v1), (k2, v2) = list(vals.items())
    pair = {k1, k2}
    if pair == {"v", "i"}:
        v, i = vals["v"], vals["i"]; r = v / i
    elif pair == {"v", "r"}:
        v, r = vals["v"], vals["r"]; i = v / r
    elif pair == {"v", "p"}:
        v, p_ = vals["v"], vals["p"]; i = p_ / v; r = v * v / p_
    elif pair == {"i", "r"}:
        i, r = vals["i"], vals["r"]; v = i * r
    elif pair == {"i", "p"}:
        i, p_ = vals["i"], vals["p"]; v = p_ / i; r = p_ / (i * i)
    elif pair == {"r", "p"}:
        r, p_ = vals["r"], vals["p"]; i = math.sqrt(p_ / r); v = i * r
    else:
        print("提供 V/I/R/P 中任二项", file=sys.stderr); return 2
    p = v * i
    line("V=I·R, P=V·I", f"{k1}={fmt(v1)}, {k2}={fmt(v2)}",
         f"V={fmt(v)} I={fmt(i)} R={fmt(r)} P={fmt(p)}")
    return 0


def cmd_divider(a):
    ratio = a.vout / a.vin
    r2 = 10000.0
    r1 = r2 * (a.vin / a.vout - 1)
    i_div = a.vin / (r1 + r2)
    line("Vout=Vin·R2/(R1+R2)", f"Vin={fmt(a.vin)} Vout={fmt(a.vout)} (I_div≈{fmt(i_div)})",
         f"R1={fmt(r1)}→E24 {fmt(e24(r1))}, R2={fmt(r2)}→E24 {fmt(e24(r2))}; "
         f"校核 Vout={fmt(a.vin * e24(r2) / (e24(r1) + e24(r2)))}")
    return 0


def cmd_led(a):
    r = (a.vs - a.vf) / a.i
    p = (a.vs - a.vf) * a.i
    line("R=(Vs−Vf)/I, P=(Vs−Vf)·I", f"Vs={fmt(a.vs)} Vf={fmt(a.vf)} I={fmt(a.i)}",
         f"R={fmt(r)}→E24 {fmt(e24(r))}, P={fmt(p)}（选封装额定 ≥2×）")
    return 0


def cmd_rc(a):
    if a.r is not None and a.c is not None:
        tau = a.r * a.c
        line("fc=1/(2πRC), τ=RC", f"R={fmt(a.r)} C={fmt(a.c)}",
             f"τ={fmt(tau)}s fc={fmt(1 / (2 * math.pi * tau))}Hz")
    elif a.fc is not None and a.c is not None:
        r = 1 / (2 * math.pi * a.fc * a.c)
        line("R=1/(2π·fc·C)", f"fc={fmt(a.fc)}Hz C={fmt(a.c)}",
             f"R={fmt(r)}→E24 {fmt(e24(r))}")
    else:
        print("需 --r --c 或 --fc --c", file=sys.stderr); return 2
    return 0


def cmd_ipc(a):
    k = 0.048 if a.layer == "external" else 0.024
    th = 1.37 * a.copper_oz  # oz→mil 铜厚
    area = (a.current / (k * a.temp_rise ** 0.44)) ** (1 / 0.725)
    w = area / th
    line("I=k·ΔT^0.44·A^0.725 (IPC-2152)",
         f"I={a.current}A ΔT={a.temp_rise}°C {a.layer} {a.copper_oz}oz (k={k})",
         f"A={area:.3g}mil² → 线宽≈{w:.1f}mil；须与 间距与线宽.md 档位取严、板厂当季参数复核")
    return 0


def cmd_via(a):
    area = math.pi * a.drill_mil * a.plating_mil
    k = 0.048
    i = k * a.temp_rise ** 0.44 * area ** 0.725
    line("I≈k·ΔT^0.44·A^0.725, A=π·d·t（镀壁截面近似）",
         f"d={a.drill_mil}mil t={a.plating_mil}mil ΔT={a.temp_rise}°C",
         f"载流≈{i:.2f}A（保守值；≥0.5A 电流过孔优先加大或并多个）")
    return 0


def cmd_imp(a):
    t, w, h, er = a.t_mil, a.w_mil, a.h_mil, a.er
    if a.mode == "microstrip":
        z = 87.0 / math.sqrt(er + 1.41) * math.log(5.98 * h / (0.8 * w + t))
        f = "Z0=87/√(εr+1.41)·ln(5.98h/(0.8w+t))"
    else:
        z = 60.0 / math.sqrt(er) * math.log(1.9 * (2 * h + t) / (0.8 * w + t))
        f = "Z0=60/√εr·ln(1.9(2h+t)/(0.8w+t))"
    line(f + "（Hammerstad 近似 ±10%）",
         f"w={w}mil h={h}mil t={t}mil εr={er}",
         f"Z0≈{z:.1f}Ω；正式值以板厂叠层阻抗工具为准")
    return 0


def cmd_l4(a):
    lam0_mm = 299792.458 / a.freq_mhz  # λ0[mm]=c/f；c=299792458m/s → 299792.458/f_MHz mm
    lam_mm = lam0_mm / math.sqrt(a.er_effective)
    line("λg=λ0/√εre, l=λg/4", f"f={a.freq_mhz}MHz εre={a.er_effective}",
         f"λ/4≈{lam_mm / 4:.2f}mm ≈ {lam_mm / 4 / 0.0254:.0f}mil")
    return 0


def cmd_db(a):
    if a.to == "db":
        v = 20 * math.log10(a.value)
        line("dB=20·log10(X/Xref)", f"X/Xref={a.value}", f"={v:.2f}dB")
    else:
        v = 10 ** (a.value / 20)
        line("X/Xref=10^(dB/20)", f"={a.value}dB", f"={v:.4g}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("ohm"); [o.add_argument("--" + n, type=si2) for n in ("v", "i", "r", "p")]
    d = sub.add_parser("divider"); d.add_argument("--vin", type=si2, required=True); d.add_argument("--vout", type=si2, required=True); d.add_argument("--i-div", type=float, dest="i_div")
    l = sub.add_parser("led"); l.add_argument("--vs", type=si2, required=True); l.add_argument("--vf", type=si2, required=True); l.add_argument("--i", type=si2, required=True)
    r = sub.add_parser("rc"); r.add_argument("--r", type=si2); r.add_argument("--c", type=si2); r.add_argument("--fc", type=si2)
    i2 = sub.add_parser("ipc2152"); i2.add_argument("--current", type=si2, required=True); i2.add_argument("--temp-rise", type=float, dest="temp_rise", default=10.0); i2.add_argument("--copper-oz", type=float, dest="copper_oz", default=1.0); i2.add_argument("--layer", choices=["external", "internal"], default="external")
    vc = sub.add_parser("via-current"); vc.add_argument("--drill-mil", type=float, dest="drill_mil", required=True); vc.add_argument("--plating-mil", type=float, dest="plating_mil", default=0.8); vc.add_argument("--temp-rise", type=float, dest="temp_rise", default=10.0)
    im = sub.add_parser("impedance"); im.add_argument("--mode", choices=["microstrip", "stripline"], required=True); im.add_argument("--w-mil", type=float, dest="w_mil", required=True); im.add_argument("--h-mil", type=float, dest="h_mil", required=True); im.add_argument("--er", type=si2, default=4.35); im.add_argument("--t-mil", type=float, dest="t_mil", default=1.4)
    q = sub.add_parser("l4"); q.add_argument("--freq-mhz", type=float, dest="freq_mhz", required=True); q.add_argument("--er-effective", type=si2, dest="er_effective", default=4.0)
    db = sub.add_parser("db"); db.add_argument("--to", choices=["db", "np"], required=True); db.add_argument("--value", type=float, required=True)
    args = ap.parse_args()
    fn = {"ohm": cmd_ohm, "divider": cmd_divider, "led": cmd_led, "rc": cmd_rc,
          "ipc2152": cmd_ipc, "via-current": cmd_via, "impedance": cmd_imp,
          "l4": cmd_l4, "db": cmd_db}[args.cmd]
    try:
        return fn(args)
    except ZeroDivisionError:
        print("参数导致除零", file=sys.stderr); return 2


if __name__ == "__main__":
    sys.exit(main())
