#!/usr/bin/env python
"""calc-scientific.py — 科学计算器（本项目本地扩展，非上游文件；计算纪律见 references/约束部分/计算纪律/）。

能力：安全表达式求值（AST 白名单，无 eval 注入）、SI 工程前缀（f p n u/m k M G T）、
复数运算（阻抗直角/极坐标）、常用数学函数、单位换算。设计/电气计算器的简单换算可直接用它。

用法（设计执行期以工作区为 cwd）：
  python <SKILL_DIR>/scripts/calc-scientific.py '50/sqrt(2)'             # → 35.355
  python <SKILL_DIR>/scripts/calc-scientific.py '2k*10u'                 # → 0.02（SI 前缀自动乘）
  python <SKILL_DIR>/scripts/calc-scientific.py 'abs(50+30j)' --format polar  # → 极坐标
  python <SKILL_DIR>/scripts/calc-scientific.py --var R=4000 --var V=3.3 'V*V/R'
  python <SKILL_DIR>/scripts/calc-scientific.py --convert '10mil mm'     # 单位换算
  python <SKILL_DIR>/scripts/calc-scientific.py --list                   # 函数与常量清单

纪律：本工具输出可整行复制进进度账本 `cmd:`/证据（计算留痕，见 计算纪律.md）；
不联网、不写文件、退出码 0=成功 2=表达式/参数错误。
"""
from __future__ import annotations

import argparse
import cmath
import json
import math
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SI = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3,
      "k": 1e3, "M": 1e6, "G": 1e9, "T": 1e12}
FUNCS = {
    "sqrt": math.sqrt, "cbrt": lambda x: x ** (1 / 3), "exp": math.exp,
    "ln": math.log, "log": math.log10, "log2": math.log2, "log10": math.log10,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan, "atan2": math.atan2,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "deg": math.degrees, "rad": math.radians, "abs": abs, "arg": cmath.phase,
    "phase": lambda z: round(math.degrees(cmath.phase(z)), 6),
    "conj": lambda z: z.conjugate() if isinstance(z, complex) else z,
    "floor": math.floor, "ceil": math.ceil, "round": round,
    "min": lambda *a: min(a), "max": lambda *a: max(a),
    "pow": lambda a, b: a ** b, "hypot": math.hypot, "factorial": math.factorial,
    "polar": lambda r, t=0.0: r * cmath.exp(1j * math.radians(t)),
    "re": lambda z: z.real, "im": lambda z: z.imag,
}
CONSTS = {"pi": math.pi, "PI": math.pi, "e": math.e, "tau": math.tau,
          "c": 299792458.0, "q_e": 1.602176634e-19, "k_B": 1.380649e-23,
          "eps0": 8.8541878128e-12, "mu0": 1.25663706212e-6}

UNIT_CONV = {
    ("mil", "mm"): lambda v: v * 0.0254, ("mm", "mil"): lambda v: v / 0.0254,
    ("inch", "mm"): lambda v: v * 25.4, ("mm", "inch"): lambda v: v / 25.4,
    ("inch", "mil"): lambda v: v * 1000, ("mil", "inch"): lambda v: v / 1000,
    ("mm2", "mil2"): lambda v: v * 1550.0, ("mil2", "mm2"): lambda v: v / 1550.0,
    ("c", "f"): lambda v: v * 9 / 5 + 32, ("f", "c"): lambda v: (v - 32) * 5 / 9,
}
PREFIX_STEP = {"": 1, "m": 1e3, "u": 1e6, "n": 1e9, "p": 1e12,
               "k": 1e-3, "M": 1e-6, "G": 1e-9}
_NUM_SI = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)([fpnumkMGT])\b")


def inject_si(expr: str) -> str:
    """给数字后的 SI 前缀乘权（2k→2*1e3；4k7→4*1e3+7 工程写法）。"""
    def rep(m):
        return f"({m.group(1)}*{SI[m.group(2)]})"
    out = _NUM_SI.sub(rep, expr)
    # 工程写法 4k7 = 4.7k
    out = re.sub(r"\((\d+(?:\.\d+)?)\*1000\.0\)\+(\d+)", r"(\1+\2/10)*1000", out)
    return out


def evaluate(expr: str, extra_vars: dict) -> object:
    import ast
    tree = ast.parse(inject_si(expr), mode="eval")

    def ev(node):
        t = type(node)
        if t is ast.Expression:
            return ev(node.body)
        if t is ast.Constant and isinstance(node.value, (int, float, complex)):
            return node.value
        if t is ast.Name:
            n = node.id
            if n in extra_vars:
                return extra_vars[n]
            if n in CONSTS:
                return CONSTS[n]
            raise ValueError(f"未知变量: {n}")
        if t is ast.BinOp:
            l, r = ev(node.left), ev(node.right)
            return {ast.Add: lambda: l + r, ast.Sub: lambda: l - r,
                    ast.Mult: lambda: l * r, ast.Div: lambda: l / r,
                    ast.Mod: lambda: l % r, ast.Pow: lambda: l ** r}[type(node.op)]()
        if t is ast.UnaryOp:
            v = ev(node.operand)
            if type(node.op) is ast.USub:
                return -v
            if type(node.op) is ast.UAdd:
                return +v
            raise ValueError("不支持的一元运算")
        if t is ast.Call:
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCS:
                raise ValueError(f"禁止的调用: {ast.dump(node.func)[:40]}")
            return FUNCS[node.func.id](*[ev(a) for a in node.args])
        raise ValueError(f"不支持的语法节点: {t.__name__}")

    return ev(tree)


def si_form(v: float) -> str:
    if v == 0 or isinstance(v, complex):
        return str(v)
    a = abs(v)
    for pre, mult in sorted(SI.items(), key=lambda kv: -kv[1]):
        if a >= mult:
            return f"{v / mult:g}{pre}"
    return f"{v:g}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("expr", nargs="?", help="表达式，如 'V*V/R'")
    ap.add_argument("--var", action="append", default=[], help="变量赋值 R=4k7，可多次")
    ap.add_argument("--format", choices=["auto", "si", "float", "polar", "json"], default="auto")
    ap.add_argument("--convert", help="单位换算，如 '10mil mm'")
    ap.add_argument("--list", action="store_true", help="列出函数与常量")
    args = ap.parse_args()

    if args.list:
        print(json.dumps({"functions": sorted(FUNCS), "constants": sorted(CONSTS),
                          "si_prefixes": "f p n u(µ) m k M G T",
                          "units": sorted({f"{a}->{b}" for a, b in UNIT_CONV})},
                         ensure_ascii=False, indent=2))
        return 0

    if args.convert:
        m = re.match(r"\s*([\d.]+(?:[eE][+-]?\d+)?)\s*([A-Za-zµ²2]+)\s*(?:to|->|→)?\s*([A-Za-zµ²2]+)\s*$",
                     args.convert)
        if not m:
            print("格式：--convert '10mil mm'（支持 mil/mm/inch/mm2/mil2/℃/°F 与 F/H 电容电感前缀）",
                  file=sys.stderr)
            return 2
        v, frm, to = float(m.group(1)), m.group(2), m.group(3)
        try:
            fn = UNIT_CONV.get((frm.lower(), to.lower()))
            if fn is None:
                fm = re.match(r"([fpnumµ]?)([FH])", frm, re.I)
                tm = re.match(r"([fpnumµ]?)([FH])", to, re.I)
                if fm and tm and fm.group(2).upper() == tm.group(2).upper():
                    sc = SI.get(fm.group(1).lower().replace("µ", "u"), 1.0) / \
                         SI.get(tm.group(1).lower().replace("µ", "u"), 1.0)
                    fn = lambda x: x * sc
            if fn is None:
                print(f"不支持的换算 {frm}->{to}", file=sys.stderr)
                return 2
            print(f"{v:g}{frm} = {fn(v):.10g}{to}")
            return 0
        except Exception as e:
            print(f"换算失败: {e}", file=sys.stderr)
            return 2

    if not args.expr:
        ap.print_help()
        return 2
    variables = {}
    for kv in args.var:
        k, _, val = kv.partition("=")
        if not val:
            print("--var 需 NAME=VALUE", file=sys.stderr)
            return 2
        try:
            variables[k] = evaluate(val, variables)
        except Exception as e:
            print(f"变量 {k} 解析失败: {e}", file=sys.stderr)
            return 2
    try:
        result = evaluate(args.expr, variables)
    except Exception as e:
        print(f"求值失败: {e}", file=sys.stderr)
        return 2

    fmt = args.format
    if fmt == "auto":
        fmt = "polar" if isinstance(result, complex) else "si"
    if fmt == "polar" and isinstance(result, complex):
        print(f"{result} → |{abs(result):g} ∠ {math.degrees(cmath.phase(result)):.2f}°")
    elif fmt == "json":
        print(json.dumps({"expr": args.expr, "vars": {k: str(v) for k, v in variables.items()},
                          "result": str(result)}, ensure_ascii=False))
    elif fmt == "si":
        r = result if isinstance(result, (complex, int)) else float(result)
        print(f"{args.expr} = {si_form(r) if not isinstance(r, complex) else r} "
              f"(float {r if isinstance(r, complex) else float(r):.10g})")
    else:
        print(f"{args.expr} = {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
