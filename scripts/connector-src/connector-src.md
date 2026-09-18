# connector-src — easyeda-agent-connector 源码快照使用政策

> 本目录是 **eext 插件（easyeda-agent-connector）本地源码快照**的封装层（编辑期维护工具）。
> 快照正本：[`../../Sample/easyeda-agent-connector/`](../../Sample/easyeda-agent-connector/)（上游 `extension/` 目录，tag+commit+sha256 清单见 `.snapshot.json`）。
> 封装脚本：[`eext-src.py`](eext-src.py)。编辑遵守 RULE_EDIT.md：文本 ≤ 50 行、自然语言。

## 为什么存在

上游 CLI/connector 破坏接口导致 skill 断用的教训（v1.4.8→v1.5.1 连续两次）促成本快照：
把插件实现了哪些 `eda.*` API、如何注册菜单与 ws 通道，固化为**离线可查正本**。
配合「更新检查已全面禁用」（用户指令 2026-09-18）：排查接口行为差异时对照本地源码，
而不是联网比版本、查发行说明。

## 使用纪律

1. **编辑期专用**：`verify`/`report`/`apis` 纯本地零网络；`fetch` 与 `eext` 会访问 GitHub（前者取
   tag 源码、后者取官方 `easyeda-agent-connector.eext` 发行资产并按 `checksums.txt` 校验 sha256），
   属维护窗口人工动作，**设计执行期禁止运行本脚本**；`.eext` 的**导入**始终由用户在 EDA
   扩展管理器手工完成（卸载同 UUID 旧项 → 导入 → 完全重启 EDA），Agent 代下载/安装属 L3 违规
   （运行环境不可变）。产物不落 skill 仓库。
2. **快照只读**：`Sample/easyeda-agent-connector/` 内容由上游决定，本 skill 不得手改其源文件；
   更新只能经 `fetch` → 人工 diff 确认 → 同步 → 重生成 `.snapshot.json` → `verify` 全绿 → 记 `CHANGELOG.md`。
3. **真值优先级不变**：运行时参数真值仍以本机 `easyeda <cmd> --help` / `easyeda actions` 为准；
   快照用于理解**行为与 API 面**（比如某 flag 背后调用了哪些 `eda.*`），不替代自描述。
4. **排除物**：上游 `images/`（二进制图标）与 `package-lock.json`（机器工件）不入库；
   LICENSE/CHANGELOG 随附保证出处与许可合规。
5. **与漂移防线的关系**：`cli_compat`（运行时能力探测）与 `link-probe` 的 `compat` 基线负责
   「检测漂移」；本快照负责「解释漂移」——上游改了行为时，改的是 connector 的哪段源码。

## 依据来源

- 快照出处：`Sample/easyeda-agent-connector/.snapshot.json`（repo/tag/commit/清单）。
- [`../../references/约束部分/运行环境不可变/运行环境不可变.md`](../../references/约束部分/运行环境不可变/运行环境不可变.md)（更新检查禁用、skill 只读）。
- [`../net-download-policy/net-download-policy.md`](../net-download-policy/net-download-policy.md)（设计执行期下载禁令不受本工具影响）。
