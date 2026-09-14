#!/usr/bin/env python3
"""
tool-probe-simulator.py — Simulate calling built-in tools/plugins in EasyEDA Pro

功能：模拟 EasyEDA Pro 内建工具与第三方插件的常见操作，展示如何通过 CLI/API 调用它们，
并生成可用于技能文档的示例报告。

用法：
  python3 scripts/tool-probe-simulator.py [--project <name>] [--output-dir ./tmp]

输出内容：
  - .kilo/tmp/tool-call-examples.json    # 结构化示例数据
  - .kilo/tmp/tool-call-examples.md     # Markdown 示例文档
  - .kilo/tmp/tool-call-guide.md         # 实用调用指南
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
            sys.stderr.write(f"[tool-probe-sim] CLI warning {cmd}: {r.stderr.strip()}\n")
        return r.stdout
    except Exception as e:
        sys.stderr.write(f"[tool-probe-sim] CLI error {cmd}: {e}\n")
        return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default="default", help="目标工程名")
    ap.add_argument("--output-dir", default="C:\\Users\\User\\.kilocode\\skills\\EasyEDAssistant/tmp", help="输出目录")
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sys.stderr.write("[tool-probe-sim] 开始模拟调用内置工具与插件...\n")

    # 模拟的工具调用示例（按工具类别组织）
    examples = {
        "builtin_tools": [
            {
                "name": "teardrop",
                "description": "自动增强焊盘与导线连接的机械强度",
                "cli_example": "easyeda pcb teardrop --project <project> --doc <page> --type via",
                "api_example": "eda.pcb.teardrop(project='<project>', doc='<page>', type='via')",
                "purpose": "增加焊盘/通孔机械连接牢固性"
            },
            {
                "name": "copper_manager",
                "description": "管理 PCB 铜层，包括重流、清理无网络死铜、重新布线",
                "cli_example": "easyeda pcb pour-rebuild --project <project> --doc <page> --net all",
                "api_example": "eda.pcb.pour_rebuild(project='<project>', doc='<page>', net='all')",
                "purpose": "修复铜图连通性，确保无死铜"
            },
            {
                "name": "net_class_manager",
                "description": "管理网络类，定义线宽/间距阶梯，控制不同类型网络的电气性能",
                "cli_example": "easyeda pcb net-classes --project <project> --doc <page> --list",
                "api_example": "eda.pcb.net_classes.list(project='<project>', doc='<page>')",
                "purpose": "管理网类设置，控制线宽/间距策略"
            },
            {
                "name": "diff_pair_manager",
                "description": "管理差分对，自动化差分对布线与等长约束",
                "cli_example": "easyeda pcb diff-pair create --name usb --positive D+ --negative D-",
                "api_example": "eda.pcb.diff_pair.create(name='usb', positive='D+', negative='D-')",
                "purpose": "建立差分对布线约束，控制差分对匹配"
            },
            {
                "name": "circuit_calculator",
                "description": "电子电路计算器，阻抗、电容、电感、频率等计算",
                "cli_example": "easyeda tools calculator --type impedance --value 100 --freq 1000",
                "api_example": "eda.tools.calculator(type='impedance', value=100, freq=1000)",
                "purpose": "电路参数计算，支持阻抗匹配、谐振、滤波器设计等"
            },
            {
                "name": "smt_selector",
                "description": "嘉立创 SMT 选型工具，按库存、价格、封装等筛选器件",
                "cli_example": "easyeda tools smt-selector --lcsc C123456 --qty 100 --online",
                "api_example": "eda.tools.smt_selector(lcsc='C123456', qty=100, online=True)",
                "purpose": "智能选型，比价，库存控制"
            }
        ],
        "plugin_examples": [
            {
                "name": "拼板助手插件",
                "description": "高级拼板设计与连线工具，支持多板间过孔、走线、DRC 检查",
                "cli_example": "easyeda plugin拼板助手 --project <project> --mode batch",
                "api_example": "eda.plugin.spare_assistant.execute(project='<project>', mode='batch')",
                "purpose": "批量拼板设计，自动化连线与检查"
            },
            {
                "name": "高级DRC检查插件",
                "description": "强化 DRC 检查，支持自定义规则、复杂约束、3D 冲突检测",
                "cli_example": "easyeda plugin advanced-drc --project <project> --strict",
                "api_example": "eda.plugin.advanced_drc(project='<project>', strict=True)",
                "purpose": "高级 DRC 检查，发现设计规则违规"
            },
            {
                "name": "智能布线优化插件",
                "description": "自动优化的布线路由，支持多算法、多约束优化",
                "cli_example": "easyeda plugin auto-router --project <project> --constraint set='high_density'",
                "api_example": "eda.plugin.auto_router(project='<project>', constraint_set='high_density')",
                "purpose": "智能布线优化，生成最佳路由方案"
            }
        ],
        "real_call_attempts": []
    }

    # 尝试执行真实 CLI 调用（可选）
    sys.stderr.write("[tool-probe-sim] 尝试执行真实 CLI 示例调用...\n")
    try:
        health = _cli(["health", "--project", args.project, "--json"])
        if health:
            examples["real_call_attempts"].append({
                "command": "easyeda health --project <project> --json",
                "success": True,
                "output": health[:200] + "..." if len(health) > 200 else health
            })
    except Exception as e:
        examples["real_call_attempts"].append({
            "command": "easyeda health",
            "success": False,
            "error": str(e)
        })

    # 写入 JSON 示例
    json_path = out_dir / "tool-call-examples.json"
    json_path.write_text(json.dumps(examples, ensure_ascii=False, indent=2), encoding="utf-8")

    # 写入 Markdown 示例文档
    md_content = f"""# EasyEDA Pro 内建工具与插件调用示例

> 生成时间：模拟运行
> 目标工程：{args.project}

## 1. 内建工具调用示例

### 1.1 泪滴工具 (teardrop)
- **用途**：{examples["builtin_tools"][0]["purpose"]}
- **CLI 示例**：`{examples["builtin_tools"][0]["cli_example"]}`
- **API 示例**：`{examples["builtin_tools"][0]["api_example"]}`

### 1.2 铺铜管理器 (copper_manager)
- **用途**：{examples["builtin_tools"][1]["purpose"]}
- **CLI 示例**：`{examples["builtin_tools"][1]["cli_example"]}`
- **API 示例**：`{examples["builtin_tools"][1]["api_example"]}`

### 1.3 网络类管理器 (net_class_manager)
- **用途**：{examples["builtin_tools"][2]["purpose"]}
- **CLI 示例**：`{examples["builtin_tools"][2]["cli_example"]}`
- **API 示例**：`{examples["builtin_tools"][2]["api_example"]}`

### 1.4 差分对管理器 (diff_pair_manager)
- **用途**：{examples["builtin_tools"][3]["purpose"]}
- **CLI 示例**：`{examples["builtin_tools"][3]["cli_example"]}`
- **API 示例**：`{examples["builtin_tools"][3]["api_example"]}`

### 1.5 电路计算器 (circuit_calculator)
- **用途**：{examples["builtin_tools"][4]["purpose"]}
- **CLI 示例**：`{examples["builtin_tools"][4]["cli_example"]}`
- **API 示例**：`{examples["builtin_tools"][4]["api_example"]}`

### 1.6 嘉立创 SMT 选型工具 (smt_selector)
- **用途**：{examples["builtin_tools"][5]["purpose"]}
- **CLI 示例**：`{examples["builtin_tools"][5]["cli_example"]}`
- **API 示例**：`{examples["builtin_tools"][5]["api_example"]}`

## 2. 扩展插件调用示例

### 2.1 拼板助手插件
- **用途**：{examples["plugin_examples"][0]["purpose"]}
- **CLI 示例**：`{examples["plugin_examples"][0]["cli_example"]}`
- **API 示例**：`{examples["plugin_examples"][0]["api_example"]}`

### 2.2 高级 DRC 检查插件
- **用途**：{examples["plugin_examples"][1]["purpose"]}
- **CLI 示例**：`{examples["plugin_examples"][1]["cli_example"]}`
- **API 示例**：`{examples["plugin_examples"][1]["api_example"]}`

### 2.3 智能布线优化插件
- **用途**：{examples["plugin_examples"][2]["purpose"]}
- **CLI 示例**：`{examples["plugin_examples"][2]["cli_example"]}`
- **API 示例**：`{examples["plugin_examples"][2]["api_example"]}`

## 3. 真实 CLI 调用记录

"""
    md_content += "\n"
    if examples["real_call_attempts"]:
        md_content += "| 命令 | 成功 | 输出/错误 |\n"
        md_content += "|-------|--------|------------|\n"
        for attempt in examples["real_call_attempts"]:
            success = "✅" if attempt["success"] else "❌"
            output = (attempt["output"] if "output" in attempt else attempt["error"]).replace("\n", " ")
            md_content += f"| {attempt['command']} | {success} | {output} |\n"

    md_content += """
## 4. 使用指南

### 4.1 内建工具调用流程
1. 确认工程与页面的有效性
2. 调用对应 CLI 或 API，传入项目/文档参数
3. 根据工具返回结果进行后续处理
4. 可选保存结果到文件或继续执行其他操作

### 4.2 扩展插件调用流程
1. 检查插件是否已安装（如插件清单所示）
2. 调用插件的 CLI 或 API 接口
3. 传入工程参数与特定选项
4. 处理插件返回的结构化数据

### 4.3 注意事项
- 所有命令都支持 `--project` 和 `--doc` 参数
- API 调用通常遵循 `eda.<domain>.<action>(...)` 模式
- 真实调用可能因权限、环境或插件安装情况而成功或失败

## 5. 安全与授权

- 所有工具/插件调用都应遵循Skill的授权范围
- 对于破坏性操作（如清空页、重命名、删除），确保用户已明确授权
- 调用前请验证工具/插件的有效性，避免调用不存在的或未经授权的操作
"""

    md_path = out_dir / "tool-call-guide.md"
    md_path.write_text(md_content, encoding="utf-8")

    sys.stderr.write(f"[tool-probe-sim] 示例调用模拟完成！已生成:\n  - {json_path}\n  - {md_path}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
