# 快速上手指南

## 环境准备

### 1. 克隆仓库
```bash
git clone <你的仓库地址>
cd test_dev_projects
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境
修改 `config/environments/` 下对应环境的 yaml 配置文件。

设置环境变量切换环境：
```bash
export TEST_ENV=test
```

## 运行测试

### UI 自动化测试
```bash
pytest ui_automation/testcases/ -m ui -v
```

### 接口测试
```bash
pytest api_testing/testcases/ -m api -v
```

### 所有测试
```bash
pytest -v
```

### 生成 HTML 报告
```bash
pytest --html=reports/report.html --self-contained-html
```

## 生成测试用例
```bash
cd testcase_generator
python example_usage.py
```

## 性能测试
```bash
# 安装 k6
brew install k6

# 运行示例脚本
k6 run performance/scripts/example_load_test.js
```

## 家↔公司 同步工作流

### 日常同步流程

1. **开始工作前先拉取最新代码**
   ```bash
   git pull origin main
   ```

2. **进行开发和测试工作**

3. **工作完成后提交并推送**
   ```bash
   git add .
   git commit -m "描述你的修改内容"
   git push origin main
   ```

### 注意事项
- 每次开始工作前务必 `git pull`
- 提交前检查是否有冲突
- 建议使用有意义的 commit message
- `evidence/` 和 `logs/` 目录下的文件不会被提交（已配置 .gitignore）
