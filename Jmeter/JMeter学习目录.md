# JMeter 学习目录

> 更新时间：2026-09-03
> 目录位置：D:\test_dev_projects\Jmeter

## 一、当前测试计划文件

| 文件 | 说明 |
|---|---|
| `TNAS存储管理接口测试计划.jmx` | 当前测试计划 |
| `TNAS存储管理接口测试计划_旧版备份_20260902.jmx` | 旧版备份 |
| `TNAS存储管理接口测试计划_正则版备份_20260903.jmx` | 正则提取版备份 |

## 二、JMeter 学习笔记列表

| 序号 | 文件 | 内容 |
|---|---|---|
| 1 | `JMeter-JSR223-Groovy入门与内置变量.md` | JSR223、Groovy、内置变量 |
| 2 | `JMeter-Groovy语法速查表.md` | Groovy 语法速查 |
| 3 | `JMeter-Groovy常用代码示例.md` | 常用代码和场景 |
| 4 | `JMeter-正则表达式学习手册.md` | 正则语法和示例 |
| 5 | `JMeter-正则表达式提取器实战.md` | 正则表达式提取器配置 |
| 6 | `JMeter-边界提取器完整笔记.md` | 边界提取器 |
| 7 | `JMeter-JSON提取器完整笔记.md` | JSON 提取器 |
| 8 | `JMeter-断言完整笔记.md` | 断言 |
| 9 | `JMeter-参数化与CSV完整笔记.md` | 参数化、CSV、函数 |
| 10 | `JMeter-接口串联完整笔记.md` | 接口串联 |
| 11 | `JMeter-GUI运行监听器与报告完整笔记.md` | GUI、命令行、监听器、报告 |

## 三、建议学习顺序

第一阶段：基础

```text
JMeter-GUI运行监听器与报告完整笔记.md
JMeter-参数化与CSV完整笔记.md
```

第二阶段：提取器

```text
JMeter-边界提取器完整笔记.md
JMeter-JSON提取器完整笔记.md
JMeter-正则表达式学习手册.md
JMeter-正则表达式提取器实战.md
```

第三阶段：接口测试

```text
JMeter-断言完整笔记.md
JMeter-接口串联完整笔记.md
```

第四阶段：脚本进阶

```text
JMeter-JSR223-Groovy入门与内置变量.md
JMeter-Groovy语法速查表.md
JMeter-Groovy常用代码示例.md
```

## 四、目前使用的核心方案

当前 JMX 中，从响应头提取变量使用的是：

```text
JSR223 后置处理程序
```

只保存：

```text
csrfToken
rsaPublicKey
```

不会生成：

```text
csrfToken_g
csrfToken_g0
csrfToken_g1
```

## 五、后续可继续补充

后续如果需要，可以继续添加：

- JMeter-WebSocket测试笔记
- JMeter-数据库测试笔记
- JMeter-分布式测试完整笔记
- JMeter-自动化与CI集成笔记
- JMeter-性能调优笔记
- JMeter-常见报错排查手册
- JMeter-接口测试报告模板

## 六、学习原则

每学一个主题，建议：

1. 看笔记
2. 在 JMeter 中实操
3. 用真实响应验证
4. 记录自己遇到的问题
5. 把问题补充到笔记中

文档会在需要时继续更新，不会只保留“开头摘要”。
