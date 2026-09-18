#!/usr/bin/env python
"""eext-src.py — easyeda-agent-connector（.eext 插件）本地源码快照的封装脚本。【编辑期维护工具】

快照位置：Sample/easyeda-agent-connector/（上游 extension/ 目录，tag v1.5.1，
元数据与 sha256 清单在 .snapshot.json）。用途：把「插件到底实现了哪些 eda.* API、
菜单如何注册、ws 协议长什么样」变成**离线可查的正本**，配合已禁用的更新检查策略——
不联网、不查版本门禁，本机 CLI 报错时可直接对照源码定位行为差异。

用法（编辑期在 skill 仓库根运行）：
  python scripts/connector-src/eext-src.py verify             # 快照 sha256 完整性校验
  python scripts/connector-src/eext-src.py report [--out x.json]  # 聚合报告（元数据+API+菜单+本机 CLI 版本记录）
  python scripts/connector-src/eext-src.py apis [--domain sch] # 列出源码实现的 eda.* API
  python scripts/connector-src/eext-src.py fetch --tag v1.6.0 --out <目录>   # 仅维护窗口：
      # 下载新版本 tag 的 extension/ 源到指定目录并打印与现快照的文件差异；不自动覆盖仓库。

安全纪律：verify/report/apis 纯本地零网络；fetch 属维护期人工动作（设计执行期禁止运行本
脚本 fetch；下载归档 zip 不违反运行期禁令的正本见 references/约束部分/运行环境不可变/——
该禁令约束设计执行期，维护期由用户指令驱动）。细则见同目录 connector-src.md。

退出码：verify 0=一致 1=有差异；report/apis 0=成功；fetch 0=成功 2=失败。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
import zipfile
from io import BytesIO
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SNAP = REPO / "Sample" / "easyeda-agent-connector"
API_RE = re.compile(r"\b(eda\.[A-Za-z0-9_]+\.[A-Za-z0-9_]+)")


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _meta() -> dict:
    return json.loads((SNAP / ".snapshot.json").read_text(encoding="utf-8"))


def _apis() -> dict:
    """从快照 TS 源码提取插件实现的 eda.* API，按 <域>.<对象> 分组。"""
    found: dict[str, set[str]] = {}
    for p in sorted(SNAP.rglob("*")):
        if not p.is_file() or p.suffix not in (".ts", ".mjs", ".js", ".jsx"):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in API_RE.finditer(text):
            api = m.group(1)
            domain = api.split(".")[1]
            found.setdefault(domain, set()).add(api)
    return {k: sorted(v) for k, v in sorted(found.items())}


def cmd_verify() -> int:
    meta = _meta()
    expect = meta["files_sha256"]
    bad, missing = [], []
    for rel, digest in expect.items():
        f = SNAP / rel
        if not f.exists():
            missing.append(rel)
        elif _sha256_file(f) != digest:
            bad.append(rel)
    extra = [str(p.relative_to(SNAP)).replace("\\", "/")
             for p in SNAP.rglob("*") if p.is_file()
             and str(p.relative_to(SNAP)).replace("\\", "/") not in expect
             and p.name != ".snapshot.json"]
    ok = not (bad or missing or extra)
    print(json.dumps({"snapshot": f"{meta['tag']}@{meta['commit'][:8]}", "ok": ok,
                      "changed": bad, "missing": missing, "extra": extra,
                      "files": len(expect)}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def cmd_report(out: str | None) -> int:
    meta = _meta()
    ext = json.loads((SNAP / "extension.json").read_text(encoding="utf-8"))
    cli = ""
    try:
        cli = subprocess.run(["easyeda", "version"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=20
                             ).stdout.strip()
    except Exception as e:
        cli = f"UNREACHABLE: {e}"
    rep = {
        "tool": "eext-src", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "snapshot": {k: meta.get(k) for k in ("tag", "commit", "connector_name",
                                              "connector_uuid", "connector_version", "fetched_utc")},
        "manifest": {k: ext.get(k) for k in ("name", "uuid", "version", "displayName", "entry")},
        "header_menus": sorted((ext.get("headerMenus") or {}).keys()),
        "api_domains": {k: len(v) for k, v in _apis().items()},
        "local_cli": {"version_text": cli or None,
                      "note": "仅记录对照，无版本门禁（更新检查已按用户指令全面禁用，见 运行环境不可变）"},
    }
    text = json.dumps(rep, ensure_ascii=False, indent=2)
    if out:
        Path(out).write_text(text, encoding="utf-8")
        print(f"[eext-src] 报告已写 {out}")
    else:
        print(text)
    return 0


def cmd_apis(domain: str | None) -> int:
    for d, lst in _apis().items():
        if domain and not d.startswith(domain):  # 前缀匹配：sch → sch_*, pcb → pcb_*
            continue
        print(f"eda.{d}.*  ({len(lst)})")
        for a in lst:
            print(f"  {a}")
    return 0


def cmd_fetch(tag: str, out_dir: str) -> int:
    url = f"https://codeload.github.com/zhoushoujianwork/easyeda-agent/zip/refs/tags/{tag}"
    print(f"[eext-src] 维护窗口动作：下载 {url}", file=sys.stderr)
    try:
        import urllib.request
        raw = urllib.request.urlopen(url, timeout=120).read()
        zf = zipfile.ZipFile(BytesIO(raw))
    except Exception as e:
        print(f"[eext-src] fetch 失败：{e}", file=sys.stderr)
        return 2
    root_pref = next(n for n in zf.namelist() if n.endswith("/extension/extension.json"))[:-len("extension.json")]
    dest = Path(out_dir) / tag
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for info in zf.infolist():
        if info.is_dir() or not info.filename.startswith(root_pref):
            continue
        rel = info.filename[len(root_pref):]
        parts = rel.split("/")
        if "images" in parts or parts[-1] == "package-lock.json":
            continue  # 与现快照同规则：排除二进制图标与锁文件
        w = dest / rel
        w.parent.mkdir(parents=True, exist_ok=True)
        w.write_bytes(zf.read(info))
        n += 1
    cur = set(_meta()["files_sha256"])
    new = {str(p.relative_to(dest)).replace("\\", "/") for p in dest.rglob("*") if p.is_file()}
    diff = {"added": sorted(new - cur - {".snapshot.json"}),
            "removed": sorted(cur - new)}
    print(f"[eext-src] 已解出 extension/ → {dest}（{n} 文件，排除 images/package-lock）")
    print(json.dumps({"vs_current_snapshot": diff}, ensure_ascii=False, indent=2))
    print("[eext-src] 后续人工步骤：a) diff 确认后同步进 Sample/easyeda-agent-connector/；"
          "b) 重生成 .snapshot.json（tag/commit/sha256）；c) 跑 verify + check-links；d) 记 CHANGELOG。",
          file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify")
    rp = sub.add_parser("report")
    rp.add_argument("--out")
    apn = sub.add_parser("apis")
    apn.add_argument("--domain")
    ft = sub.add_parser("fetch")
    ft.add_argument("--tag", required=True)
    ft.add_argument("--out", required=True)
    args = ap.parse_args()
    if not (SNAP / ".snapshot.json").exists():
        print(f"[eext-src] 快照不存在：{SNAP}", file=sys.stderr)
        return 2
    if args.cmd == "verify":
        return cmd_verify()
    if args.cmd == "report":
        return cmd_report(args.out)
    if args.cmd == "apis":
        return cmd_apis(args.domain)
    return cmd_fetch(args.tag, args.out)


if __name__ == "__main__":
    sys.exit(main())
