#!/usr/bin/env python3
"""
tool-probe.py — 探针脚本：获取嘉立创 EDA 专业版内建工具与已安装插件清单，并生成说明文档。

功能：
  1. 连接本地 EDA 引擎（MCP / daemon 60832）
  2. 查询编辑器注册的内建工具（Tools）与扩展插件（Extensions / Plugins）
  3. 在**工作区**临时目录生成 `./tmp/eda-tools-manifest.json` 与 `./tmp/eda-tools-guide.md`
     （禁止写入 skill 目录；输出根基于 cwd，并校验不逃逸工作区）
  4. 供 Agent 在特定设计步骤时查阅并按需调用

用法：
  python scripts/tool-probe.py [--project <name>] [--output-dir ./tmp]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _cli(args: list[str], timeout: int = 30) -> str:
    cmd = ["easyeda", *args]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            sys.stderr.write(f"[tool-probe] CLI warning {cmd}: {r.stderr.strip()}\n")
        return r.stdout
    except Exception as e:
        sys.stderr.write(f"[tool-probe] CLI error {cmd}: {e}\n")
        return ""


def _sanitize_project(name: str) -> str:
    """剥离任何路径分隔符与 .. 序列，防止注入到路径/文件名（见 FILE_CREATION_POLICY §3）。"""
    return Path(name).name or "default"


def _resolve_within_workspace(raw: str) -> Path:
    """把 raw 解析为绝对路径并强制其落在工作区(cwd)内；逃逸则拒绝。"""
    workspace = Path.cwd().resolve()
    p = Path(raw)
    candidate = (p if p.is_absolute() else workspace / p).resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError:
        raise SystemExit(
            f"[tool-probe] 安全拒绝：输出目录 {candidate} 逃逸出工作区 {workspace}"
        )
    return candidate


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default="default", help="目标工程名")
    ap.add_argument(
        "--output-dir", default="tmp",
        help="输出目录（相对工作区 cwd，禁止逃逸；默认 ./tmp）",
    )
    args = ap.parse_args()

    args.project = _sanitize_project(args.project)
    out_dir = _resolve_within_workspace(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sys.stderr.write("[tool-probe] 正在探针嘉立创 EDA 内建工具与已安装插件...\n")

    # 尝试通过 easyeda CLI 获取系统/健康状态与扩展信息
    health_raw = _cli(["health", "--project", args.project, "--json"])
    plugins_raw = _cli(["api", "search", "plugin", "--json"])
    probe_ok = bool(health_raw)

    # 内建工具清单为静态参考（官方能力描述），非运行时探针结果；
    # 运行时事实只有 health 与插件目录两项，CLI 不可达时如实标注。
    manifest = {
        "probe_status": "cli_ok" if probe_ok else "cli_unavailable",
        "note": "builtin_tools 为静态参考清单；installed_extensions 仅在 daemon 可达时来自实时回读。",
        "builtin_tools": [
            {"id": "teardrop", "name": "泪滴工具", "category": "pcb", "status": "available_via_ui_or_api"},
            {"id": "copper_manager", "name": "铺铜管理器", "category": "pcb", "status": "available"},
            {"id": "net_class_mgr", "name": "网络类管理器", "category": "pcb", "status": "available"},
            {"id": "differential_pair", "name": "差分对管理器", "category": "pcb", "status": "available"},
            {"id": "circuit_calc", "name": "电路计算器", "category": "tools", "status": "available"},
            {"id": "smt_selector", "name": "嘉立创 SMT 选型工具", "category": "tools", "status": "available"}
        ],
        "installed_extensions": [],
        "health": {}
    }

    if health_raw:
        try:
            manifest["health"] = json.loads(health_raw)
        except Exception:
            manifest["health"] = {"raw": health_raw}

    # 写入 JSON 清单
    json_path = out_dir / "eda-tools-manifest.json"
    json_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 写入 Markdown 说明文档（供 Agent 步骤查阅）
    md_content = f"""# 嘉立创 EDA 工具与插件探针报告

> 生成时间：自动探针
> 探针状态：{'cli_ok（health 来自实时回读）' if probe_ok else 'cli_unavailable —— 以下内建工具清单仅为静态参考，未经运行时验证；不可当作已探得事实使用'}
> 目标工程：{args.project}

## 1. 内建工具清单（Built-in Tools）
以下工具可在设计各阶段通过 API 或原生菜单调用：
- **泪滴工具 (teardrop)**：布线后增强焊盘与导线连接机械强度。
- **铺铜管理器 (copper_manager)**：重流、清理无网络死铜。
- **网络类管理器 (net_class_mgr)**：线宽阶梯、间距规则分级。
- **差分对管理器 (differential_pair)**：USB/高速差分对约束。
- **嘉立创 SMT 选型工具 (smt_selector)**：库存与基本库过滤。

## 2. 已安装扩展插件 (Installed Extensions)
- 详见 `eda-tools-manifest.json`。若检测到第三方扩展（如拼板助手、高阶 DRC），将在此列出。

## 3. 使用规则
当进入特定设计步骤（如铺铜、布线收尾、导出制造文件）时：
1. Agent 优先查阅本文档确认工具可用性。
2. 若涉及非标高级工具（如特殊拼板/泪滴），触发 **§11.5 条件中断点** 询问用户是否启用对应插件或工具。
"""
    md_path = out_dir / "eda-tools-guide.md"
    md_path.write_text(md_content, encoding="utf-8")

    sys.stderr.write(f"[tool-probe] 探针完成！已生成:\n  - {json_path}\n  - {md_path}\n")
    if not probe_ok:
        sys.stderr.write("[tool-probe] 警告：easyeda CLI 不可达，清单未经运行时验证（exit 2），先起 daemon 再重跑。\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
