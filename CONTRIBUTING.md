# 项目贡献指南 (CONTRIBUTING.md)

> 本文件为 EasyEDAssistant 项目的贡献指南，旨在为开发者提供清晰的贡献流程、代码规范和项目结构指南。

## 1. 概述

EasyEDAssistant 是一个基于 JLCEDA MCP VS Code 插件的移植版电路设计技能包，旨在通过程序化方式操作嘉立创 EDA 专业版（EasyEDA Pro）。本项目遵循开放源代码协作模式，欢迎所有形式的贡献。

### 1.1 贡献类型

- **代码贡献**：提交新功能、修复问题、优化性能等
- **文档贡献**：编写文档、更新 README、贡献指南等
- **测试贡献**：编写测试用例、进行质量验证
- **其他贡献**：提出问题、提供反馈、协助文档翻译等

### 1.2 贡献流程

1. **Fork** 项目到个人账户
2. **Clone** 到本地工作目录
3. **创建** 开发分支（基于 `dev` 分支）
4. **进行开发**，按照项目规范进行
5. **提交** 修改，遵守提交信息规范
6. **发起 Pull Request** 到主分支
7. **响应反馈**，并根据审查意见进行修改

## 2. 开发环境与工具

### 2.1 系统要求

- **操作系统**：Windows 10/11, macOS, Linux
- **Python**：3.7+
- **Git**：2.0+
- **VS Code**：带 Python 扩展
- **EasyEDA Pro**：最新版本

### 2.2 开发工具

- **IDE**：Visual Studio Code
- **代码管理**：Git
- **版本控制**：GitHub
- **测试框架**：pytest
- **格式检查**：black、isort、flake8

### 2.3 安装与设置

```bash
# 克隆项目
cd ~/.kilocode/skills
git clone https://github.com/EasyEDAssistant/EasyEDAssistant.git

# 进入项目目录
cd EasyEDAssistant

# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行测试
python -m pytest scripts/
```

## 3. 代码规范

### 3.1 命名约定

| 文件类型 | 命名规范 |
|---|---|
| Python 脚本 | `snake_case.py`（如 `tool-probe.py`） |
| Markdown 文档 | `README.md`、`CONTRIBUTING.md` 等 |
| 配置文件 | `*.jsonc`、`*.yaml` 等 |
| 测试文件 | `test_*.py` 或 `*_test.py` |

### 3.2 代码风格

- **代码长度**：函数应保持简短，行长不超过 80 字符
- **空格**：使用 4 个空格缩进，禁止使用 tab
- **导入顺序**：标准库、第三方库、本项目库
- **文档**：使用 Google 或 Sphinx 风格文档注释

### 3.3 提交规范

```bash
# 提交信息示例
git commit -m "feat: 添加工具探针脚本支持插件自动发现

- 新增 scripts/tool-probe.py，实现内建工具与已安装插件清单的动态生成
- 支持在 P1/P6/P8/P10 等阶段自动触发插件状态检测
- 优化 scripts/visual-qa.py 的截图管理和状态识别逻辑"
```

## 4. 贡献流程

### 4.1 新功能开发

1. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **开发实现**
   - 根据需求分析，实施所需功能
   - 编写单元测试
   - 进行代码审查

3. **提交修改**
   ```bash
   git add .
   git commit -m "feat: 您的功能描述"
   ```

4. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **发起 Pull Request**
   - 在 GitHub 上创建 Pull Request
   - 描述您的变更、原因和影响
   - 指派 reviewers

### 4.2 问题修复

1. **分支创建**
   ```bash
   git checkout -b bugfix/issue-number
   ```

2. **修复实现**
   - 修复目标 bug
   - 编写或更新测试用例
   - 进行代码审查

3. **提交修改**
   ```bash
   git add .
   git commit -m "fix: 修复 issue #number 的 bug"
   ```

4. **推送分支与发起 PR**
   - 遵循流程相同

### 4.3 文档更新

1. **更新文档**
   - 修改 README.md、CONTRIBUTING.md 等文件
   - 确保文档与代码同步

2. **提交修改**
   ```bash
   git add README.md
   git commit -m "docs: 更新文档"
   ```

3. **推送与发起 PR**
   - 遵循流程相同

## 5. 测试与验证

### 5.1 测试策略

- **单元测试**：测试单个函数或方法
- **集成测试**：测试模块间交互
- **端到端测试**：测试整个系统功能

### 5.2 测试命令

```bash
# 运行所有测试
python -m pytest

# 运行指定测试文件
python -m pytest scripts/test_tool_probe.py

# 运行特定测试
python -m pytest scripts/test_tool_probe.py -k test_example
```

### 5.3 测试覆盖

- 代码覆盖率应达到 80% 以上
- 每增加新功能，应增加相应测试
- 修复 bug 时，应更新相关测试

## 6. 代码审查

### 6.1 审查流程

1. **自查**
   - 检查代码风格是否符合规范
   - 验证功能实现是否完整
   - 确保文档是否更新

2. **他人审查**
   - 提请 team member 进行代码审查
   - 根据审查意见进行修改
   - 确保代码质量符合项目标准

3. **合并审查**
   - 通过 Pull Request 进行代码合并审查
   - 确保分支变更符合项目要求
   - 进行最终测试

### 6.2 审查标准

- **代码质量**：可读性、可维护性、健壮性
- **功能完整性**：功能实现是否完整
- **测试覆盖**：测试覆盖率是否符合要求
- **文档完整性**：文档是否更新
- **性能优化**：性能是否符合预期

## 7. 版本管理

### 7.1 版本号管理

- 遵循 **语义化版本号** 规范
- **MAJOR** 版本号表示不兼容的 API 修改
- **MINOR** 版本号表示添加新功能，但保持向后兼容
- **PATCH** 版本号表示兼容性 bug 修复

### 7.2 版本发布流程

1. **发布分支**
   ```bash
   git checkout main
   git merge dev
   ```

2. **版本标记**
   ```bash
   git tag v1.2.3
   ```

3. **发布**
   - 准备发布说明
   - 发布到 GitHub releases

## 8. 许可与归属

### 8.1 许可协议

本项目采用 **MIT 许可协议**。您可以自由地使用、复制、修改、合并、发布和分发本软件，但必须在软件副本上注明原始版权声明和许可声明。

### 8.2 归属要求

- 所有贡献者需在代码或文档中注明自己的贡献
- 贡献代码需遵守项目代码规范
- 贡献文档需遵循项目文档风格

## 9. 项目路线图

### 9.1 短期目标（0-3 个月）

- 完成工具探针功能
- 实现动态截图管理
- 优化插件自动发现
- 完善代码测试框架

### 9.2 中期目标（3-6 个月）

- 扩展至更多EDA工具支持
- 实现自动化设计流程
- 优化用户体验

### 9.3 长期目标（6-12 个月）

- 实现跨平台EDA设计自动化
- 构建综合EDA分析平台
- 扩展插件生态系统

## 10. 社区参与

### 10.1 参与方式

- **参与讨论**：GitHub Issues、Pull Request、Discussions
- **贡献代码**：提交 Pull Request
- **编写文档**：贡献项目文档
- **提供反馈**：报告 bug、提出建议

### 10.2 行为准则

- **礼貌**：尊重他人，不使用 offensive language
- **专业**：保持专业态度，提供建设性反馈
- **包容**：欢迎多样化的贡献

## 11. 附录

### 11.1 常见问题

#### Q1: 如何安装项目依赖？
A: 请参考第 2 节 **开发环境与工具** 的相关内容。

#### Q2: 如何运行测试？
A: 请参考第 5 节 **测试与验证** 的相关内容。

#### Q3: 如何提交修改？
A: 请参考第 4 节 **贡献流程** 的相关内容。

### 11.2 参考文献

- [GitHub License](https://github.com/EasyEDAssistant/EasyEDAssistant/blob/main/LICENSE)

---

*(本文件最终版本号: 1.0.0)*
*(更新时间: 2026-09-14)*
*(作者: EasyEDAssistant Team)*
