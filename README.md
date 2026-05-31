# 测试自动化工作区

## 项目简介

综合测试自动化框架，涵盖 Web UI 自动化、接口测试、性能测试、测试用例生成等多个模块，支持家↔公司多地协同开发工作流。

## 目录结构

```
test_dev_projects/
├── README.md                    # 项目说明文档
├── .gitignore                   # Git 忽略规则
├── requirements.txt             # Python 依赖
├── pytest.ini                   # pytest 配置
├── conftest.py                  # pytest 全局 fixture
├── config/                      # 配置模块
│   ├── settings.py              # 全局配置管理
│   └── environments/            # 多环境配置
│       ├── dev.yaml
│       ├── test.yaml
│       └── prod.yaml
├── ui_automation/               # Web UI 自动化测试
│   ├── pages/                   # Page Object 页面对象
│   ├── testcases/               # UI 测试用例
│   ├── testdata/                # UI 测试数据
│   └── evidence/                # 截图/录屏证据
├── api_testing/                 # 接口测试
│   ├── api_client/              # API 客户端封装
│   ├── testcases/               # 接口测试用例
│   └── testdata/                # 接口测试数据
├── performance/                 # 性能测试
│   ├── scripts/                 # 性能测试脚本
│   └── reports/                 # 性能测试报告
├── testcase_generator/          # 测试用例生成器
│   ├── generator.py             # 生成器核心逻辑
│   └── templates/               # 用例模板
├── common/                      # 公共工具模块
│   ├── logger.py                # 日志工具
│   ├── file_handler.py          # 文件处理工具
│   └── report_utils.py          # 报告生成工具
└── docs/                        # 文档目录
    └── getting_started.md       # 快速入门指南
```

## 快速开始

### 1. 克隆仓库

```bash
git clone <仓库地址>
cd test_dev_projects
```

### 2. 创建虚拟环境并安装依赖

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 3. 运行测试

```bash
# 运行所有测试
pytest

# 运行冒烟测试
pytest -m smoke

# 运行接口测试
pytest -m api

# 运行 UI 自动化测试
pytest -m ui

# 并行运行测试
pytest -n auto
```

## 模块说明

| 模块 | 说明 |
|------|------|
| `config/` | 全局配置管理，支持多环境切换（dev/test/prod） |
| `ui_automation/` | 基于 Selenium 的 Web UI 自动化测试，采用 Page Object 模式 |
| `api_testing/` | 基于 Requests 的接口自动化测试 |
| `performance/` | 性能测试脚本与报告 |
| `testcase_generator/` | 自动化测试用例生成工具 |
| `common/` | 公共工具：日志、文件处理、报告生成等 |
| `docs/` | 项目文档 |

## 同步工作流（家↔公司）

本项目通过 Git 远程仓库实现多地协同：

```bash
# 开始工作前 - 拉取最新代码
git pull origin main

# 完成工作后 - 提交并推送
git add .
git commit -m "feat: 描述你的修改"
git push origin main
```

**工作流建议：**
- 每次开始工作前先 `git pull` 同步最新代码
- 工作结束后及时 `commit` 和 `push`
- 使用有意义的 commit message，便于追踪变更
- 遇到冲突时优先保留最新的改动

## 技术栈

- **测试框架**: pytest
- **UI 自动化**: Selenium WebDriver
- **接口测试**: Requests
- **数据处理**: PyYAML, openpyxl
- **日志**: Loguru
- **报告**: pytest-html, Allure
