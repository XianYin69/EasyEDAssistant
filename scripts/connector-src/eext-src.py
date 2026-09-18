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
  python scripts/connector-src/eext-src.py eext [--tag v1.5.1] [--out <目录>]  # 仅维护窗口：
      # 下载官方 easyeda-agent-connector.eext 发行资产（默认取快照同 tag），按 release
      # checksums.txt 校验 sha256 后输出 EDA 扩展管理器导入步骤——安装动作始终由用户手工完成。

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


def cmd_eext(tag: str | None, out_dir: str) -> int:
    """维护窗口：取与源码快照配套 tag 的官方 .eext 发行资产，sha256 校验后交用户手工导入。"""
    meta = _meta()
    tag = tag or meta["tag"]
    asset = "easyeda-agent-connector.eext"
    base = f"https://github.com/zhoushoujianwork/easyeda-agent/releases/download/{tag}"
    print(f"[eext-src] 维护窗口动作：下载 {base}/{asset}（设计执行期禁止运行本命令）", file=sys.stderr)
    try:
        import urllib.request
        sums = urllib.request.urlopen(base + "/checksums.txt", timeout=60).read().decode()
        want = next((ln.split()[0] for ln in sums.splitlines() if asset in ln), None)
        if not want:
            print(f"[eext-src] checksums.txt 中无 {asset}（tag 不存在或资产更名），放弃", file=sys.stderr)
            return 2
        raw = urllib.request.urlopen(f"{base}/{asset}", timeout=300).read()
    except Exception as e:
        print(f"[eext-src] 下载失败：{e}", file=sys.stderr)
        return 2
    got = hashlib.sha256(raw).hexdigest()
    if got != want:
        print(f"[eext-src] sha256 不匹配！期望 {want} 实得 {got}——文件已丢弃，勿导入", file=sys.stderr)
        return 2
    dest = Path(out_dir) / f"easyeda-agent-connector-{tag}.eext"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    print(json.dumps({"eext": str(dest.resolve()), "tag": tag, "pinned": tag == meta.get("tag"),
                      "sha256": got, "size_bytes": len(raw),
                      "import_steps": [
                          "1) EasyEDA Pro 扩展管理器卸载现装 connector（**含更高版本——本项目版本钉定，发现新版只回退不升级**；平台按 UUID 去重）",
                          f"2) 导入本文件：{dest.resolve()}",
                          "3) 完全退出并重开 EasyEDA（仅重导不保证已打开页面执行新代码），并关闭一切自动更新通道（市场原地更新/daemon --auto-update-skill）",
                          "4) 新会话跑 link-probe 确认链路且 version_gate.pin.mismatch 为 false"],
                      "alt_channel": "立创插件市场（支持原地自动更新）与版本钉定冲突：不推荐；若经市场安装须立即关闭自动更新并确认版本＝钉定"},
                     ensure_ascii=False, indent=2))
    print("[eext-src] 注意：Agent 不得在设计执行期代装（.eext 属运行期禁下载项，正本见 约束/运行环境不可变）；"
          "本产物是工具输出物，不要放回 skill 仓库。", file=sys.stderr)
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
    ee = sub.add_parser("eext")
    ee.add_argument("--tag", help="默认取快照 .snapshot.json 的 tag（与源码配套）")
    ee.add_argument("--out", default=".", help="保存目录（工作区/下载目录，勿放 skill 仓库）")
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
    if args.cmd == "eext":
        return cmd_eext(args.tag, args.out)
    return cmd_fetch(args.tag, args.out)


if __name__ == "__main__":
    sys.exit(main())
