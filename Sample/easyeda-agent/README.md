# 上游 easyeda-agent 存档

本目录是上游 skill **easyeda-agent**（作者 zhoushoujianwork，MIT 许可，
[zhoushoujianwork/easyeda-agent](https://github.com/zhoushoujianwork/easyeda-agent)）的**说明与许可证存档**，
**不再作为可加载 skill 注册**，以免其流程与本项目主干 `SKILL.md`（skill 名 **EasyEDAssistant**）在运行时产生分歧。

- **许可证**：见 [`LICENSE`](LICENSE)（上游 MIT 版权归属原文，依法保留）。
- **辅助脚本**：原 `scripts/` 已迁至仓库根 [`../../scripts/`](../../scripts/)，按本项目流程调用。
- **参考文档正本**：原 `references/` 中被本项目引用的门禁/PCB 规范等已并入
  [`../../references/lib/`](../../references/lib/)，其余上游文档不再随本仓库分发。
- **运行时真值**：一切流程、约束、验证以根目录 [`../../SKILL.md`](../../SKILL.md) 与 `references/` 为准。

> 保留本存档用于与上游 EDA 插件/CLI 的联动溯源与许可证合规；请勿在本目录重新放入带
> `SKILL.md` frontmatter 的文件，否则会被 skill 发现机制重新注册。
