#!/usr/bin/env python
"""net-probe.py — 网络环境检测：判用户是否在大陆（能否访问谷歌），择优平台清单。
正本：references/浏览器检索/网络环境检测/网络环境检测.md。
判据：探测 URL 可达性——google 可达→global；google 不可达且大陆平台可达→cn；否则 unknown。
      结果落工作区 ./tmp/init/net-env.json；一次会话缓存复用。region 仅平台择优启发式，非硬门禁。
只读可达性探测（短超时，不下载文件体、不装任何物）。退出码：0=已分类，3=unknown。cwd 在 skill 仓库拒跑。
"""
from __future__ import annotations
import json, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

GOOGLE = "https://www.google.com/generate_204"
CN_PROBES = ["https://item.szlcsc.com/", "https://www.hqchip.com/"]
UA = {"User-Agent": "Mozilla/5.0 (EasyEDAssistant net-probe)"}
PLAT = {"cn": ["https://item.szlcsc.com/", "https://www.hqchip.com/", "https://www.jlcpcb.com/"],
        "global": ["https://www.mouser.com/", "https://www.digikey.com/", "https://www.lcsc.com/", "厂商官网"],
        "unknown": []}


def probe(url, timeout=6):
    t0 = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA, method="GET"), timeout=timeout) as r:
            return {"url": url, "ok": 200 <= r.status < 400, "status": r.status, "ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        return {"url": url, "ok": False, "status": None, "err": type(e).__name__, "ms": int((time.time() - t0) * 1000)}


def main() -> int:
    cwd = Path.cwd()
    if "--help" not in sys.argv and (cwd / "SKILL.md").exists() and (cwd / "RULE_EDIT.md").exists():
        raise SystemExit(f"[net-probe] 拒绝运行：cwd 是 skill 仓库 {cwd}；先 cd 到工作区根。")
    g = probe(GOOGLE)
    cn = [probe(u) for u in CN_PROBES]
    region = "global" if g["ok"] else ("cn" if any(c["ok"] for c in cn) else "unknown")
    out = {"tool": "net-probe", "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "google_reachable": g["ok"], "cn_platforms_reachable": sum(c["ok"] for c in cn), "region": region,
           "note": "region 仅平台择优启发式，非硬门禁；unknown 时由用户指定",
           "preferred_platforms": PLAT[region], "probes": [g] + cn}
    p = Path("tmp") / "init" / "net-env.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[net-probe] region={region} google={g['ok']} cn_ok={out['cn_platforms_reachable']} → {p.as_posix()}")
    return 0 if region != "unknown" else 3


if __name__ == "__main__":
    sys.exit(main())
