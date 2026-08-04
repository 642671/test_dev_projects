# UI自动化测试链路文档生成器

## 📋 简介

这是一个用于自动生成UI自动化测试链路文档的工具。它能够：
- 自动执行UI操作步骤
- 在每步操作后自动截图
- 生成包含操作步骤、输入数据、预期结果和实际截图的Word文档

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install python-docx
```

### 2. 创建链路配置

复制模板文件：
```bash
cd ui_automation/tools/doc_generator
copy configs\_template.yaml configs\my_chain.yaml
```

编辑配置文件，定义测试链路。

### 3. 生成文档

**基本用法：**
```bash
cd d:\test_dev_projects
python -m ui_automation.tools.doc_generator.cli -c ui_automation/tools/doc_generator/configs/my_chain.yaml
```

**无头模式（不显示浏览器窗口）：**
```bash
python -m ui_automation.tools.doc_generator.cli -c ui_automation/tools/doc_generator/configs/my_chain.yaml --headless
```

**批量生成：**
```bash
python -m ui_automation.tools.doc_generator.cli --batch ui_automation/tools/doc_generator/configs/*.yaml
```

## 📝 配置文件格式

### 基本结构

```yaml
chain_name: "测试链路名称"

environment:
  url: "http://192.168.64.7:8181"
  env_name: "测试环境"

preparation: |
  1. 确保系统可访问
  2. 准备测试账号

variables:
  username: "test"
  password: "Admin123"

steps:
  - name: "步骤名称"
    description: "操作描述"
    page: "页面对象类名"
    action: "方法名"
    args: []
    expected: "预期结果"
    wait_after: 2
```

### 字段说明

| 字段 | 说明 | 必填 |
|------|------|------|
| chain_name | 链路名称 | 是 |
| environment.url | 测试环境地址 | 是 |
| environment.env_name | 环境名称 | 否 |
| preparation | 环境准备说明 | 否 |
| variables | 变量定义，可在步骤中引用 | 否 |
| steps | 操作步骤列表 | 是 |

### 步骤字段说明

| 字段 | 说明 | 必填 |
|------|------|------|
| name | 步骤名称 | 是 |
| description | 操作描述 | 否 |
| page | 页面对象类名（如TosLoginPage） | 是 |
| action | 要执行的方法名 | 是 |
| args | 方法参数列表，支持${variable}占位符 | 否 |
| expected | 预期结果 | 否 |
| wait_after | 操作后等待秒数 | 否 |

### 变量引用

在args中可以使用 `${variable_name}` 引用变量：

```yaml
variables:
  username: "test"

steps:
  - name: "输入用户名"
    page: "TosLoginPage"
    action: "input_username"
    args: ["${username}"]  # 会被替换为 "test"
```

也支持嵌套变量：
```yaml
args: ["${environment.url}"]  # 引用 environment.url
```

## 📂 输出说明

### 截图目录

```
ui_automation/tools/doc_generator/evidence/
└── 初始化配置超级用户_20260623_143025/
    ├── step_01_打开登录页面.png
    ├── step_02_输入用户名.png
    ├── step_03_点击第一步下一步.png
    └── ...
```

### Word文档

```
ui_automation/tools/doc_generator/output/
└── 初始化配置超级用户_20260623.docx
```

文档内容包含：
- 链路基本信息（名称、环境地址、环境准备）
- 每个步骤的详细信息：
  - 操作描述
  - 输入数据
  - 预期结果
  - 实际结果
  - 执行状态
  - 对应截图

## 💡 使用示例

### 示例1：生成登录链路文档

已提供完整示例配置 `configs/login_chain.yaml`：

```bash
python -m ui_automation.tools.doc_generator.cli \
  -c ui_automation/tools/doc_generator/configs/login_chain.yaml
```

### 示例2：批量生成多个链路文档

```bash
python -m ui_automation.tools.doc_generator.cli \
  --batch \
  ui_automation/tools/doc_generator/configs/login_chain.yaml \
  ui_automation/tools/doc_generator/configs/dashboard_chain.yaml
```

或使用通配符：
```bash
python -m ui_automation.tools.doc_generator.cli \
  --batch \
  "ui_automation/tools/doc_generator/configs/*.yaml"
```

## 🔧 架构说明

### 核心模块

- **DocGenerator** (generator.py): 核心编排器，协调整个生成流程
- **Executor** (executor.py): UI操作执行器，复用现有POM页面对象
- **ScreenshotMgr** (screenshot_mgr.py): 截图管理器
- **WordTemplates** (templates.py): Word文档模板与样式
- **CLI** (cli.py): 命令行入口

### 与现有框架的关系

本工具完全复用现有的UI自动化框架：
- 使用 `pages/` 目录下的页面对象
- 使用 `config/` 目录下的配置
- 使用 `common/logger.py` 进行日志记录
- 不修改任何现有测试代码

## ⚠️ 注意事项

1. **页面对象命名**：配置文件中的page字段使用PascalCase（如TosLoginPage），会自动转换为文件名tos_login_page.py
2. **浏览器驱动**：需要确保已安装ChromeDriver
3. **依赖安装**：首次使用需要安装 `python-docx` 库
4. **路径问题**：配置文件路径可以使用相对路径或绝对路径

## 🐛 故障排查

### 问题：提示找不到模块

**解决**：确保在项目根目录（d:\test_dev_projects）下执行命令

### 问题：截图为空或黑色

**解决**：
- 确保浏览器窗口可见（不要使用--headless）
- 检查页面是否完全加载（增加wait_after时间）

### 问题：文档生成失败

**解决**：
- 检查YAML配置文件格式是否正确
- 查看日志文件了解详细错误信息
- 确认所有必需的字段都已填写

## 📞 支持

如有问题或建议，请联系开发团队。
