# Qoder 记忆恢复提示词

## 使用方法

1. 在 Windows 公司的 Qoder 中打开 `test_dev_projects` 项目
2. 等待项目加载完成
3. 将下方"恢复提示词"部分的**完整内容**复制粘贴到 Qoder 对话框中发送
4. Qoder 会根据内容自动创建所有记忆

> **注意**: 记忆数量较多（102条），Qoder 可能需要分批处理。如果一次粘贴太多，可以按"章节"分段发送。

---

## 恢复提示词

请根据以下数据，为我创建所有记忆。每条记忆请按以下格式创建：
- 使用 UpdateMemory 工具的 create action
- 严格按照给出的 category 分类
- title、content、keywords、usage_scenario 均按下文内容填写
- 对于 usage_scenario 为空的条目，可省略该字段

数据来源文件：`qoder_memory_export/memories_export.md`，请先阅读该文件获取完整内容，然后按照文件中列出的每条记忆逐一创建。

以下是需要创建的**全部记忆清单概览**（详细内容见 memories_export.md）：

### 用户偏好（1条）
1. 用户交互节奏偏好 → user_communication

### 项目环境配置（9条）
2. TOS系统运行环境与认证要求 → project_environment_configuration
3. Python测试项目运行环境与启动流程 → project_environment_configuration
4. Kimi API Key格式规范 → project_environment_configuration
5. 代理运行环境配置 → project_environment_configuration
6. 火山引擎API基础地址 → project_environment_configuration
7. Latent Upscale节点标准配置 → project_environment_configuration
8. Image Scale节点标准配置 → project_environment_configuration
9. ComfyUI模型缺失导致标签页无法关闭 → project_environment_configuration

### 项目SCM配置（2条）
10. 项目GitHub远程仓库地址 → project_scm_configuration
11. 双分支跨平台协作策略 → project_scm_configuration

### 项目IDE配置（2条）
12. Qoder编辑器文件导航规范 → project_ide_configuration
13. VS Code pytest测试面板完整配置与故障排查 → project_ide_configuration

### 项目技术栈（1条）
14. 三方技术栈集成 → project_tech_stack

### 项目介绍（19条）
15-33: 测试自动化工作区项目概述、多模块自治目录结构规范、模块完全自治架构设计、项目配置分层设计原则、API文档模块内聚规范、工具分层治理架构、UI自动化学习路线图、Kimi流量拦截架构、系统看板设置功能说明、Kimi-for-coding模型映射规则、TOS登录判定、TOS两步式登录、TOS登录流程×2、TOS右栏空白区域、USB设备界面、右侧栏收起规则、右侧栏搜索交互、动漫风格模型 → project_introduction

### 开发实践规范（11条）
34-44: TOS显式等待规范、公共UI组件层规范、Fixture模块化分层规范、三层职责分离规范、Page层定义与窗口管理规范、跨平台路径规范、测试失败自动恢复规范、用例按业务模块组织规范、看板滚动规范、看板端到端测试流程规范、模型推理程度配置 → development_practice_specification

### 开发测试规范（2条）
45-46: 测试用例字段格式与粒度规范、系统看板设置功能测试覆盖规范 → development_test_specification

### 开发代码规范（1条）
47. 动漫风格图像生成提示工程规范 → development_practice_specification

### 经验教训（14条）
48-61: GitHub HTTP/2 RPC失败、BYOK Credits限制、Kimi sk-校验、NODE_EXTRA_CA_CERTS、火山引擎v1路径、SearchReplace参数、代理日志root权限、ComfyUI metal参数、API Key占位符、Chromium IPv6 hosts、火山引擎Bearer认证、run_in_terminal不可用×3 → common_pitfalls_experience

### 重要决策（3条）
62-64: 技术栈与用例格式决策、看板端到端验证合并决策、BYOK前端绕过决策 → important_decision_experience

### 专家经验（6条）
65-70: TOS桌面测试点、用户设置界面结构、桌面通知与图标交互、TNAS/TOS回答原则、搜索界面功能、消息通知界面功能 → expert_experience

### 学到的技能（28条）
71-95: SPA滚动检测、Vue拖动模拟、看板勾选联动、Context7 MCP检索、Vue表单验证、代码库安全清理、目录结构设计、目录重构验证、Git提交指南、Bash覆盖文件、conftest清洗、配置目录重构、SPA框架补全、工具分层治理、配置分层治理、目录结构（解耦配置版）、代理后端切换、BYOK补丁、baseUrl数据库配置、反向代理绕过、Git安全提交、右侧栏点击收起、文档结构化补全、文档精准表述、跨平台同步构建 → learned_skill_experience
99. Qoder第三方模型配置文件定位技能 → learned_skill_experience
100. 跨平台智能体记忆与知识库迁移技能 → learned_skill_experience
101. 测试用例生成协作模式与记忆策略 → learned_skill_experience

### 补充的新增记忆（7条）
96. 开发者平台模块测试点 → expert_experience
97. TOS导航栏与桌面应用右键菜单规则 → expert_experience
98. TOS导航栏应用名称映射决策-通用设置=控制面板 → important_decision_experience
99-101: 见上方学到的技能部分
102. Qoder跨平台记忆迁移打包规范 → project_environment_configuration

---

## 知识库恢复

repowiki 知识库文件已导出到 `qoder_memory_export/repowiki/` 目录。这些文件是项目的知识库文档（markdown格式），包含：
- API参考文档
- UI自动化测试框架
- 开发者指南
- 性能测试框架
- 接口测试框架
- 故障排除与FAQ
- 测试框架配置
- 测试用例生成器
- 通用工具模块
- 部署与运维
- 配置管理

Qoder 打开此项目后会自动识别 `.qoder/repowiki/` 目录中的知识库。你只需将 `repowiki/` 文件夹复制回 `.qoder/` 目录下即可：

```powershell
# 在 Windows PowerShell 中执行
Copy-Item -Recurse qoder_memory_export\repowiki .qoder\repowiki
```

---

## JSON备份说明

`json_backup/` 目录包含原始的记忆结构文件（topic_tree 和 network JSON），仅供参考。这些JSON文件记录了记忆之间的关系网络，但**无法直接恢复到 Windows 的 Qoder 中**（因为二进制搜索引擎索引不跨平台）。通过上述提示词重建记忆后，Qoder 会自动重新生成这些结构文件。

---

## 环境差异适配清单

从 Mac 迁移到 Windows 时，以下配置需要适配：

| 配置项 | Mac | Windows |
|--------|-----|---------|
| Python解释器路径 | `venv/bin/python3.12` | `venv\Scripts\python.exe` |
| 虚拟环境激活 | `source venv/bin/activate` | `venv\Scripts\activate` |
| 路径分隔符 | `/` | `\`（代码中用 `os.path.join`） |
| VS Code解释器 | `${workspaceFolder}/venv/bin/python3.12` | `${workspaceFolder}/venv/Scripts/python.exe` |
| Git分支 | `main` | `win` |
