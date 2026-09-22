#!/usr/bin/env python
"""pdf-read.py — 数据手册 PDF 可用性检查与稳健读取（stdlib，只读不落盘）。
check-url URL  下载前探测真实 PDF（%PDF- 或 application/pdf），不落盘
validate FILE  校验魔数 / %%EOF 尾 / 加密 / 页数
extract FILE   尽力提取文本；扫描件/图片型如实回报，绝不返乱码或假成功（改用多模态 read）
退出码 0=可用有文本 / 3=可用但扫描件 / 1=不可用（非 PDF/损坏/取不到）。cwd 在 skill 仓库拒跑。
正本 references/元件检查/PDF可用性检查/。"""
import argparse, json, re, sys, urllib.request, zlib
from pathlib import Path


def _get(url, limit=None):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (pdf-read)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return (r.headers.get("Content-Type") or "").lower(), (r.read(limit) if limit else r.read())


def _cls(d):
    ip = d[:5] == b"%PDF-"
    return {"is_pdf": ip, "usable": ip and b"%%EOF" in d[-2048:], "encrypted": b"/Encrypt" in d,
            "pages": len(re.findall(rb"/Type\s*/Page[^s]", d)), "bytes": len(d)}


def _txt(d):
    o = []
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", d, re.S):
        raw = m.group(1)
        try:
            raw = zlib.decompress(raw)
        except Exception:
            pass
        o += re.findall(rb"\((?:[^()\\]|\\.)*\)", raw)
    return re.sub(r"\s+", " ", re.sub(rb"\\([()\\])", rb"\1", b"".join(o)).decode("latin-1", "replace")).strip()


def main():
    c = Path.cwd()
    if "--help" not in sys.argv and (c / "SKILL.md").exists() and (c / "RULE_EDIT.md").exists():
        raise SystemExit("[pdf-read] 拒绝：cwd 是 skill 仓库，先 cd 到工作区根")
    ap = argparse.ArgumentParser(); g = ap.add_subparsers(dest="cmd", required=True)
    for n in ("check-url", "validate", "extract"):
        g.add_parser(n).add_argument("target")
    z = ap.parse_args()
    if z.cmd == "check-url":
        try:
            ct, d = _get(z.target, 4096)
        except Exception as e:
            print(json.dumps({"tool": "pdf-read", "mode": z.cmd, "usable": False, "err": type(e).__name__}, ensure_ascii=False)); return 1
        s = _cls(d); s["usable"] = s["is_pdf"] or "pdf" in ct
    else:
        s = _cls(Path(z.target).read_bytes())
    if not s["usable"]:
        print(json.dumps({"tool": "pdf-read", "cmd": z.cmd, **s, "text_extractable": False}, ensure_ascii=False)); return 1
    if z.cmd == "extract":
        t = _txt(Path(z.target).read_bytes()); ok = len(t) >= 40
        print(json.dumps({"tool": "pdf-read", "mode": z.cmd, **s, "text_extractable": ok, "chars": len(t)}, ensure_ascii=False))
        print(t[:2000] if ok else ""); return 0 if ok else 3
    print(json.dumps({"tool": "pdf-read", "mode": z.cmd, **s}, ensure_ascii=False)); return 0


if __name__ == "__main__":
    sys.exit(main())
