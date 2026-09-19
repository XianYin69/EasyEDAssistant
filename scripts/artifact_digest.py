"""artifact_digest.py — 中间工件 digest 抽象层（库模块，不单独执行）。

正本判据：references/约束部分/上下文存储压缩机制/上下文存储压缩机制.md 第 9–10 条
（无人审阅的中间工件落盘前先抽象；抽象不得丢 AI 可读语义）。

规则：判定字段（cmd/rc/ok/blocked）永不压缩；证据类 json/text 换成
「键名固定 snake_case + 计数如实（total/truncated 分列）+ 失败项样本 ≤20 条截断 ≤200 字
+ schema 版本字段」的 digest；全文仅 --raw 时另存 raw-*.json（仍在 tmp，gitignored）。
"""
from __future__ import annotations

import json
from pathlib import Path

ITEM_CAP = 200
ITEM_MAX = 20
FINDING_KEYS = ("violations", "errors", "findings", "issues", "interferences")


def _cap(v):
    if isinstance(v, (int, float, bool)) or v is None:
        return v
    if isinstance(v, list):
        return {"n": len(v)}
    if isinstance(v, dict):
        # 一层展平标量值（失败项的 rule/net 等实际值不得丢），非标量退化为键名表
        flat = {}
        for k, x in v.items():
            if isinstance(x, (int, float, bool)) or x is None:
                flat[str(k)] = x
            elif isinstance(x, str) and len(x) <= ITEM_CAP:
                flat[str(k)] = x
            elif isinstance(x, str):
                flat[str(k)] = x[:ITEM_CAP] + "…"
        return flat or {"keys": sorted(str(k) for k in v)[:12]}
    s = str(v)
    return s if len(s) <= ITEM_CAP else s[:ITEM_CAP] + "…"


def digest_json(j) -> dict:
    d = {"schema": "1", "form": "digest"}
    if isinstance(j, dict):
        d["keys"] = {k: _cap(v) for k, v in sorted(j.items())}
        for fk in FINDING_KEYS:
            items = j.get(fk)
            if isinstance(items, list) and items:
                d[fk] = [_cap(i) for i in items[:ITEM_MAX]]
                d[fk + "_total"] = len(items)
                if len(items) > ITEM_MAX:
                    d[fk + "_truncated"] = len(items) - ITEM_MAX
    elif isinstance(j, list):
        d["list_len"] = len(j)
        d["head"] = [_cap(i) for i in j[:ITEM_MAX]]
        if len(j) > ITEM_MAX:
            d["truncated"] = len(j) - ITEM_MAX
    return d


def digest_text(t: str) -> dict:
    return {"schema": "1", "form": "digest", "text_len": len(t),
            "text_head": t[:200], "text_tail": t[-500:]}


def summarize(r: dict) -> dict:
    """把一条 {cmd,rc,ok,json|text,blocked,stderr} 压成 digest 形（判定字段原样保留）。"""
    out = {k: r[k] for k in ("cmd", "rc", "ok") if k in r}
    if r.get("blocked"):
        out["blocked"] = r["blocked"]
    if isinstance(r.get("json"), (dict, list)):
        out["digest"] = digest_json(r["json"])
    elif r.get("text"):
        out["digest"] = digest_text(r["text"])
    if r.get("stderr"):
        out["stderr_head"] = r["stderr"][:300]
    return out


def stash_raw(results: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
