#!/usr/bin/env python
"""calc-design.py — 设计计算器（本项目本地扩展，非上游文件；纪律见 references/约束部分/计算纪律/）。

子命令（每项输出「公式 + 代入 + 结果」，整行可进进度账本作计算留痕）：
  ldo-heat   --vin --vout --i [--ta 55] [--tj-max 125]
             P=(Vin−Vout)·I；θJA 需求=(Tjmax−Ta)/P，对照封装手册 θJA，超标即换方案
  buck-l     --vin --vout --f-khz --i-out [--ripple-frac 0.3]
             L=(Vin−Vout)·Vout/(Vin·f·ΔI)，ΔI=ripple-frac·Iout，给下一标准感值
  buck-cout  --ripple-i --f-khz --c-uf [--esr-mohm 30]
             ΔV≈ΔIL·(ESR+1/(8·f·C))
  battery    --cap-mah --i-avg-ma [--duty 1] [--years 0]  续航（含占空比；可选年自放校核）
  crystal-cl --cl-pf --cstray-pf  C1=C2=2·(CL−Cstray)，就近 E24
  resistor   --inputs "10k:1,20k:5" --mode series|parallel  串并联合成 + worst/RSS 容差
  copper-heat --p-w [--dt 20] [--copper-oz 1]  自然对流铜面散热面积近似（0.05 W/cm²/°C 经验，须实测复核）

退出码 0=成功 2=参数错误。经验系数均标注出处/保守性；正式判据以数据手册与板厂参数为准。
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


def fmt(v: float) -> str:
    a = abs(v)
    for suf, mult in (("M", 1e6), ("k", 1e3), ("", 1.0), ("m", 1e-3),
                      ("µ", 1e-6), ("n", 1e-9), ("p", 1e-12)):
        if a >= mult:
            return f"{v / mult:.4g}{suf}"
    return f"{v:g}"


def line(formula, sub, result):
    print(f"公式: {formula}\n代入: {sub}\n结果: {result}")


def si2(v: float) -> float:
    """SI 前缀数值解析（'10k'→10000；'4u7' 不支持，用 4.7u）。"""
    v = v.strip()
    mult = 1.0
    units = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3,
             "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9}
    if v and v[-1] in units:
        mult = units[v[-1]]
        v = v[:-1]
    return float(v) * mult


def cmd_ldo(a):
    p = (a.vin - a.vout) * a.i
    if p <= 0:
        print("要求 Vin>Vout", file=sys.stderr); return 2
    need = (a.tj_max - a.ta) / p
    line("P=(Vin−Vout)·I; θJA_req=(Tjmax−Ta)/P",
         f"Vin={fmt(a.vin)} Vout={fmt(a.vout)} I={fmt(a.i)} Ta={a.ta}°C",
         f"P={fmt(p)}W；θJA 需 ≤{need:.0f}°C/W（对照封装手册 θJA，含结-铜路径增益后仍需富余；超标→加大压差散热铜/换开关）")
    return 0


def cmd_buck_l(a):
    di = a.ripple_frac * a.i_out
    l = (a.vin - a.vout) * a.vout / (a.vin * (a.f_khz * 1e3) * di)
    line("L=(Vin−Vout)·Vout/(Vin·f·ΔI), ΔI=k·Iout",
         f"Vin={fmt(a.vin)} Vout={fmt(a.vout)} f={a.f_khz}kHz Iout={fmt(a.i_out)} ΔI/I={a.ripple_frac}",
         f"L={fmt(l)}H → 下一标准感值 {fmt(e24(l * 1.5))}~{fmt(e24(l * 2.2))}（饱和电流≥1.3·Iout；峰谷值按手册纹流档）")
    return 0


def cmd_buck_c(a):
    dv = a.ripple_i * (a.esr_mohm * 1e-3 + 1.0 / (8 * a.f_khz * 1e3 * a.c_uf * 1e-6))
    line("ΔV≈ΔIL·(ESR+1/(8fC))",
         f"ΔIL={fmt(a.ripple_i)} f={a.f_khz}kHz C={a.c_uf}µF ESR={a.esr_mohm}mΩ",
         f"纹波≈{fmt(dv)}V（陶瓷电容按降额后 ESR 取值；目标纹波超差→加 C 或并小容）")
    return 0


def cmd_battery(a):
    h = a.cap_mah / (a.i_avg_ma * a.duty)
    result = f"≈{h:.1f}h ≈ {h / 24:.2f}天"
    if a.years:
        result += f"；{a.years} 年累计电荷需求 {a.i_avg_ma * a.duty * 8760 * a.years / 1000:.2f}Ah（自放另计，留 ≥30% 裕量）"
    line("t=C/(I·duty)", f"C={a.cap_mah}mAh I={a.i_avg_ma}mA duty={a.duty}", result)
    return 0


def cmd_cl(a):
    c = 2 * (a.cl_pf - a.cstray_pf)
    if c <= 0:
        print("需 CL>Cstray", file=sys.stderr); return 2
    line("C1=C2=2·(CL−Cstray)", f"CL={a.cl_pf}pF Cstray={a.cstray_pf}pF",
         f"C=2×{a.cl_pf - a.cstray_pf:.1f}pF → E24 {fmt(e24(c * 1e-12))}F（两端同值；Cstray 实测后回代）")
    return 0


def cmd_resistor(a):
    items = []
    for tok in a.inputs.split(","):
        val, _, tol = tok.partition(":")
        items.append((si2(val), float(tol or "1")))
    if a.mode == "series":
        r = sum(v for v, _ in items)
        contribs = [v * t / 100 for v, t in items]            # ∂R/∂R_i·δR_i = δR_i
    else:
        r = 1 / sum(1 / v for v, _ in items)
        contribs = [(r * r / v) * t / 100 for v, t in items]  # ∂R/∂R_i·δR_i = (R/R_i)²·δR_i
    worst = sum(contribs)
    rss = math.sqrt(sum(c * c for c in contribs))
    line(f"电阻{'串联合成' if a.mode=='series' else '并联合成'}；worst=Σ|δ|, RSS=√Σδ²",
         f"{a.inputs} ({a.mode})",
         f"R={fmt(r)} ±worst {fmt(worst)}({worst / r * 100:.2f}%) / ±RSS {fmt(rss)}({rss / r * 100:.2f}%)")
    return 0


def cmd_copper(a):
    area_cm2 = a.p_w / (0.05 * a.dt)
    side = math.sqrt(area_cm2)
    line("P≈0.05·A(cm²)·ΔT（外层1oz自然对流经验系数，保守）",
         f"P={a.p_w}W ΔT={a.dt}°C {a.copper_oz}oz",
         f"需裸铜面积≈{area_cm2:.1f}cm²（约{side * 10:.0f}mm 见方；2oz 与内层打折，须热像实测复核）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("ldo-heat"); o.add_argument("--vin", type=si2, required=True); o.add_argument("--vout", type=si2, required=True); o.add_argument("--i", type=si2, required=True); o.add_argument("--ta", type=float, default=55); o.add_argument("--tj-max", type=float, dest="tj_max", default=125)
    b = sub.add_parser("buck-l"); b.add_argument("--vin", type=si2, required=True); b.add_argument("--vout", type=si2, required=True); b.add_argument("--f-khz", type=float, dest="f_khz", required=True); b.add_argument("--i-out", type=si2, dest="i_out", required=True); b.add_argument("--ripple-frac", type=float, dest="ripple_frac", default=0.3)
    c = sub.add_parser("buck-cout"); c.add_argument("--ripple-i", type=si2, dest="ripple_i", required=True); c.add_argument("--f-khz", type=float, dest="f_khz", required=True); c.add_argument("--c-uf", type=float, dest="c_uf", required=True); c.add_argument("--esr-mohm", type=float, dest="esr_mohm", default=30)
    e = sub.add_parser("battery"); e.add_argument("--cap-mah", type=float, dest="cap_mah", required=True); e.add_argument("--i-avg-ma", type=float, dest="i_avg_ma", required=True); e.add_argument("--duty", type=float, default=1.0); e.add_argument("--years", type=float, default=0)
    f = sub.add_parser("crystal-cl"); f.add_argument("--cl-pf", type=float, dest="cl_pf", required=True); f.add_argument("--cstray-pf", type=float, dest="cstray_pf", required=True)
    g = sub.add_parser("resistor"); g.add_argument("--inputs", required=True, help="如 '10k:1,20k:5'"); g.add_argument("--mode", choices=["series", "parallel"], required=True)
    h = sub.add_parser("copper-heat"); h.add_argument("--p-w", type=float, dest="p_w", required=True); h.add_argument("--dt", type=float, default=20); h.add_argument("--copper-oz", type=float, dest="copper_oz", default=1)
    args = ap.parse_args()
    fn = {"ldo-heat": cmd_ldo, "buck-l": cmd_buck_l, "buck-cout": cmd_buck_c,
          "battery": cmd_battery, "crystal-cl": cmd_cl, "resistor": cmd_resistor,
          "copper-heat": cmd_copper}[args.cmd]
    try:
        return fn(args)
    except (ZeroDivisionError, ValueError) as ex:
        print(f"参数错误: {ex}", file=sys.stderr); return 2


if __name__ == "__main__":
    sys.exit(main())
