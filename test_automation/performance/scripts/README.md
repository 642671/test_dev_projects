# 性能测试使用指南

本目录包含项目的性能测试脚本和相关配置。支持 JMeter 和 k6 两种主流性能测试工具。

---

## 目录结构说明

```
performance/
├── scripts/          # 存放性能测试脚本（k6 脚本、JMeter .jmx 文件等）
│   ├── example_load_test.js    # k6 示例负载测试脚本
│   └── jmeter_guide.md        # JMeter 使用说明
└── reports/          # 存放测试执行报告（HTML 报告、CSV 结果等）
```

---

## JMeter

### 安装

使用 Homebrew 安装 JMeter：

```bash
brew install jmeter
```

安装完成后验证：

```bash
jmeter --version
```

### 基本使用流程

1. **创建测试计划**：打开 JMeter GUI，创建新的测试计划
2. **添加线程组**：定义并发用户数、循环次数、启动时间
3. **添加取样器**：配置 HTTP 请求（URL、方法、参数、请求头）
4. **添加断言**：设置响应验证规则
5. **添加监听器**：配置结果收集方式（聚合报告、查看结果树等）
6. **执行测试**：使用命令行模式执行以获得更准确的结果

### 配置线程组

线程组是 JMeter 测试的核心，主要参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| 线程数（Number of Threads） | 模拟的并发用户数 | 100 |
| Ramp-Up 时间 | 所有线程启动完成所需时间（秒） | 60 |
| 循环次数 | 每个线程执行测试的次数 | 10 |

### 配置 HTTP 请求

在线程组下添加 HTTP 请求取样器：

- **协议**：http 或 https
- **服务器名称或 IP**：目标服务器地址
- **端口号**：服务端口
- **方法**：GET、POST、PUT、DELETE 等
- **路径**：接口路径
- **参数/请求体**：请求参数或 JSON Body

### 配置断言

常用断言类型：

- **响应断言**：验证响应内容包含/不包含指定字符串
- **JSON 断言**：验证 JSON 响应中特定字段的值
- **持续时间断言**：验证响应时间不超过指定阈值

### 命令行执行（非 GUI 模式）

生产环境压测必须使用非 GUI 模式执行，以减少资源消耗：

```bash
# 基本执行
jmeter -n -t scripts/test_plan.jmx -l reports/results.jtl

# 参数说明：
# -n : 非 GUI 模式
# -t : 指定测试计划文件路径
# -l : 指定结果日志文件路径
# -j : 指定 JMeter 运行日志路径
```

### 报告生成

执行完成后生成 HTML 报告：

```bash
# 方式一：测试执行时同时生成报告
jmeter -n -t scripts/test_plan.jmx -l reports/results.jtl -e -o reports/html_report

# 方式二：从已有结果文件生成报告
jmeter -g reports/results.jtl -o reports/html_report

# 参数说明：
# -e : 测试结束后生成报告
# -o : 指定 HTML 报告输出目录
# -g : 从指定的 jtl 文件生成报告
```

---

## k6

### 安装

使用 Homebrew 安装 k6：

```bash
brew install k6
```

安装完成后验证：

```bash
k6 version
```

### 基本概念

| 概念 | 说明 |
|------|------|
| **VUs（Virtual Users）** | 虚拟用户数，模拟并发访问的用户数量 |
| **Duration** | 测试持续时间，如 `30s`、`1m`、`5m` |
| **Stages** | 阶梯式负载配置，可定义多个阶段逐步增加/减少用户数 |
| **Thresholds** | 性能阈值，定义测试通过/失败的标准 |
| **Checks** | 功能验证点，类似断言 |

### 脚本编写基础

k6 脚本使用 JavaScript（ES6）编写，基本结构：

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

// 测试配置
export const options = {
  vus: 10,              // 10 个虚拟用户
  duration: '30s',      // 持续 30 秒
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% 请求在 500ms 内完成
  },
};

// 测试主函数 - 每个 VU 循环执行
export default function () {
  const res = http.get('https://your-api.com/endpoint');
  
  check(res, {
    '状态码为 200': (r) => r.status === 200,
  });
  
  sleep(1);  // 模拟用户思考时间
}
```

阶梯式负载配置（推荐用于压力测试）：

```javascript
export const options = {
  stages: [
    { duration: '1m', target: 50 },    // 1分钟内增加到 50 用户
    { duration: '3m', target: 50 },    // 保持 50 用户 3 分钟
    { duration: '1m', target: 100 },   // 1分钟内增加到 100 用户
    { duration: '3m', target: 100 },   // 保持 100 用户 3 分钟
    { duration: '1m', target: 0 },     // 1分钟内降到 0
  ],
};
```

### 执行命令

```bash
# 执行测试脚本
k6 run scripts/example_load_test.js

# 指定虚拟用户数和持续时间（覆盖脚本中的配置）
k6 run --vus 50 --duration 2m scripts/example_load_test.js

# 输出 JSON 结果
k6 run --out json=reports/result.json scripts/example_load_test.js

# 输出 CSV 结果
k6 run --out csv=reports/result.csv scripts/example_load_test.js
```

### 结果分析

k6 执行完成后会输出汇总指标，重点关注：

| 指标 | 说明 | 关注点 |
|------|------|--------|
| `http_req_duration` | 请求响应时间 | avg、p(90)、p(95)、max |
| `http_req_failed` | 请求失败率 | 应接近 0% |
| `http_reqs` | 总请求数 / 每秒请求数 | 吞吐量指标 |
| `vus` | 当前活跃虚拟用户数 | 负载水平 |
| `iterations` | 完成的迭代总数 | 实际执行次数 |

**性能基线建议**：

- P95 响应时间 < 500ms
- 错误率 < 1%
- 平均响应时间 < 200ms

---

## 最佳实践

1. **环境隔离**：性能测试应在独立的测试环境中执行，避免影响生产
2. **基线建立**：首次测试建立性能基线，后续测试与基线对比
3. **逐步加压**：使用阶梯式负载，逐步增加压力，观察系统表现
4. **监控配合**：测试时同步监控服务器资源（CPU、内存、网络、磁盘）
5. **报告归档**：每次测试报告保存至 `reports/` 目录，标注日期和版本
