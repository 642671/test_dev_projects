# JMeter 目录说明

> 更新时间：2026-09-03

## 当前最终测试计划

```text
D:\test_dev_projects\Jmeter\01-测试计划\TNAS存储管理接口测试计划.jmx
```

这是包含超级管理员、管理员、普通用户三套登录流程的最终版本。

## 目录结构

```text
D:\test_dev_projects\Jmeter
├── 01-测试计划
│   ├── TNAS存储管理接口测试计划.jmx
│   └── TNAS存储管理接口测试计划_编辑前备份_20260903_150811.jmx（本地，不入库）
├── 02-学习笔记
│   ├── JMeter学习目录.md
│   ├── JMeter-JSR223-Groovy入门与内置变量.md
│   ├── JMeter-Groovy语法速查表.md
│   ├── JMeter-Groovy常用代码示例.md
│   ├── JMeter-正则表达式学习手册.md
│   ├── JMeter-正则表达式提取器实战.md
│   ├── JMeter-边界提取器完整笔记.md
│   ├── JMeter-JSON提取器完整笔记.md
│   ├── JMeter-断言完整笔记.md
│   ├── JMeter-参数化与CSV完整笔记.md
│   ├── JMeter-接口串联完整笔记.md
│   ├── JMeter-RSA登录加密前置脚本笔记.md
│   ├── JMeter-三账号登录流程笔记.md
│   └── JMeter-GUI运行监听器与报告完整笔记.md
├── 03-脚本
│   └── 前后置脚本\apifox-登录
│       ├── encoderLoginPassword.go
│       └── 前置.txt
├── 04-备份
│   ├── TNAS存储管理接口测试计划.jmx
│   ├── TNAS存储管理接口测试计划_登录加密版.jmx
│   ├── TNAS存储管理接口测试计划_旧版备份_20260902.jmx
│   ├── TNAS存储管理接口测试计划_正则版备份_20260903.jmx
│   └── TNAS存储管理接口测试计划_三账号登录版_单角色备份.jmx
└── 性能监控
    └── 性能监控文档
```

## 使用建议

1. 需要执行 JMeter 时，打开：

```text
01-测试计划\TNAS存储管理接口测试计划.jmx
```

2. 需要学习时，从：

```text
02-学习笔记\JMeter学习目录.md
```

开始。

3. Apifox 原脚本和 Go 加密脚本放在：

```text
03-脚本\前后置脚本\apifox-登录
```

4. 历史版本不要直接使用，放在：

```text
04-备份
```

## 后续维护

以后新的 JMX 放到：

```text
01-测试计划
```

新的学习笔记放到：

```text
02-学习笔记
```

旧的版本放到：

```text
04-备份
```

脚本放到：

```text
03-脚本
```
