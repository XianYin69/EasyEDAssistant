---
name: EasyEDAssistant
description: "基于 JLCEDA MCP/CLI 双链路操作嘉立创 EDA 的电路设计 skill：原理图/PCB/射频/模拟/数字/滤波器/电源设计与检查。"
license: MIT
metadata:
  author: EasyEDAssistant
  version: "0.11.0"
---

# EasyEDAssistant 设计 Skill（主干）

## 1. 流程入口（固定）

1. **识别用户请求**：判断用户意图与目标。
2. **判断是否为第一次设计**：
   - **是** → 执行「电路板设计标准设计流程」（见 §2）。
   - **否** → 询问用户需要执行哪一个步骤；先读取 `/tmp` 下的上下文文件，再执行对应步骤（见 §3）。

## 2. 电路板设计标准设计流程

> 详见 [`references/电路设计标准设计流程/电路设计标准设计流程.md`](references/电路设计标准设计流程/电路设计标准设计流程.md)。
> 步骤：初始化部分 → 处理用户需求 → 检查方案及敲定 → 原理图制作 → PCB制作（对应连接 markdown 留空，约束部分留空）。

## 3. 询问步骤 + 读取 /tmp + 执行对应步骤（待补）

> 详细流程 markdown 后续写入。

## 4. 待补文档占位

| 文档 | 状态 |
|---|---|
| 电路板设计标准设计流程 markdown | 已写（references/电路设计标准设计流程/） |
| 询问步骤 / 读取 tmp / 执行对应步骤 markdown | 待写 |

## 5. 约束部分（预留）

> 约束规则详见后续写入的文档。