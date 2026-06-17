# JMeter 使用指南

## 脚本存放说明

将 JMeter 测试计划文件（`.jmx` 文件）放入当前 `performance/scripts/` 目录中。

建议命名规范：
```
<模块名>_<测试类型>_test.jmx
```

示例：
- `login_load_test.jmx` — 登录接口负载测试
- `order_stress_test.jmx` — 订单模块压力测试
- `api_smoke_test.jmx` — 接口冒烟测试

---

## 命令行执行 JMeter 测试

### 基本执行命令

```bash
# 在项目根目录下执行
jmeter -n -t performance/scripts/your_test.jmx -l performance/reports/results.jtl
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-n` | 以非 GUI 模式运行（命令行模式） |
| `-t` | 指定测试计划文件（.jmx）路径 |
| `-l` | 指定测试结果日志文件输出路径 |
| `-j` | 指定 JMeter 引擎日志路径 |
| `-e` | 测试完成后生成 HTML 报告 |
| `-o` | 指定 HTML 报告输出目录 |

### 完整执行示例

```bash
# 执行测试并生成 HTML 报告到 reports 目录
jmeter -n \
  -t performance/scripts/login_load_test.jmx \
  -l performance/reports/login_results.jtl \
  -j performance/reports/jmeter.log \
  -e \
  -o performance/reports/login_html_report
```

### 带参数覆盖执行

可通过 `-J` 参数在命令行中覆盖 JMeter 属性：

```bash
# 覆盖线程数和循环次数
jmeter -n \
  -t performance/scripts/login_load_test.jmx \
  -l performance/reports/results.jtl \
  -Jthreads=50 \
  -Jrampup=30 \
  -Jloops=100
```

> 注意：脚本中需使用 `${__P(threads,10)}` 函数引用这些属性。

---

## 报告输出配置

### 输出到 reports/ 目录

所有测试报告统一输出到 `performance/reports/` 目录，建议按以下结构组织：

```
performance/reports/
├── login_results_20260601.jtl        # 原始结果数据
├── login_html_report_20260601/       # HTML 可视化报告
│   ├── index.html
│   └── ...
└── jmeter_20260601.log               # 执行日志
```

### 从已有结果生成报告

如果已有 `.jtl` 结果文件，可单独生成报告：

```bash
jmeter -g performance/reports/results.jtl -o performance/reports/html_report
```

### 注意事项

1. **输出目录必须为空**：`-o` 指定的目录必须不存在或为空目录，否则会报错
2. **结果文件格式**：确保 `jmeter.properties` 中配置 `jmeter.save.saveservice.output_format=csv`
3. **时间戳命名**：建议报告文件名包含日期，避免覆盖历史数据
4. **Git 忽略**：`.jtl` 文件和 HTML 报告目录建议加入 `.gitignore`（reports/ 目录下仅保留 `.gitkeep`）
