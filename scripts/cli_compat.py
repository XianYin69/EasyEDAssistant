"""cli_compat.py — easyeda CLI 运行时能力探测（接口漂移防护层，库模块，不单独执行）。

背景：上游 easyeda-agent CLI 会跨版本破坏接口（实测 v1.4.8→v1.5.1 即两次破坏性变更：
v1.5.0 移除 `sch snapshot`、`sch export-image` 改默认 SVG；`--json`/子命令在多域增删）。
脚本若把「某 flag/子命令是否存在」写死成某一版本的真相，上游每次升级 skill 都会断。
本模块把 SKILL 既有裁决「CLI 自描述为唯一真值」落到脚本层：运行时向 `--help` 提问，
按答案自适应；探测失败一律按「不支持」处理（fail-closed，由调用方走兜底路径）。

API：
  flag_supported(["sch","gate"], "--json")          → bool   flag 是否受支持
  cmd_supported(["pcb","snapshot"])                 → bool   子命令是否存在
  pick_cmd([["pcb","list"], ["pcb","components"]])  → list|None  首个可用命令
  with_flag(base, "--json") / with_flag(base, "--format", "png")
                                                     → list   支持则追加，否则原样
  help_text(cmd)                                     → str    原始 --help（排查用）

结果按命令路径进程内缓存；`--help` 为纯本机调用，不需要 daemon/编辑器窗口。
会话入口的必备能力基线见 link-probe.py 的 REQUIRED（漂移在会话开始即告警）。
"""
from __future__ import annotations

import re
import subprocess

_HELP: dict[tuple[str, ...], str] = {}


def _cmd_path(cmd: list[str]) -> list[str]:
    """从任意「路径+flags+值」混排的命令列表中取出命令路径：跳过 easyeda，遇首个 flag 停止。"""
    out: list[str] = []
    for c in cmd:
        if c == "easyeda":
            continue
        if c.startswith("--"):
            break
        out.append(c)
    return out


def help_text(cmd: list[str]) -> str:
    cmd = [c for c in cmd if c != "easyeda"] or [""]
    key = tuple(cmd)
    if key not in _HELP:
        try:
            p = subprocess.run(["easyeda", *cmd, "--help"], capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=20)
            _HELP[key] = (p.stdout or "") + (p.stderr or "")
        except Exception:
            _HELP[key] = ""
    return _HELP[key]


def flag_supported(cmd: list[str], flag: str) -> bool:
    """`easyeda <路径> --help` 的 flag 区是否声明该 flag（--x 与 --x=v 两种出现式）。"""
    t = help_text(_cmd_path(cmd))
    return bool(t) and re.search(rf"(?:^|\s){re.escape(flag)}(?:\s|=)", t, re.M) is not None


def cmd_supported(cmd: list[str]) -> bool:
    """父命令 help 的 Available Commands 区是否列出该子命令（顶层恒真）。"""
    path = _cmd_path(cmd)
    if len(path) <= 1:
        return True
    t = help_text(path[:-1])
    return bool(t) and re.search(rf"^\s+{re.escape(path[-1])}\s", t, re.M) is not None


def pick_cmd(candidates: list[list[str]]) -> list[str] | None:
    for c in candidates:
        if cmd_supported(c):
            return list(c)
    return None


def with_flag(cmd: list[str], flag: str, *value: str) -> list[str]:
    return [*cmd, flag, *value] if flag_supported(cmd, flag) else list(cmd)
