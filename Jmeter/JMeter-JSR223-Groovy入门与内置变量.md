# JMeter JSR223 / Groovy 入门与内置变量

> 更新时间：2026-09-03
> 适用范围：Apache JMeter 5.6.3

## 一、什么是 JSR223

JSR223 是 Java 平台提供的一套“脚本语言调用规范”。

JMeter 通过 JSR223 组件，可以在测试计划中执行脚本语言编写的代码。

常见 JSR223 组件：

| 组件 | 执行时机 |
|---|---|
| JSR223 前置处理器 | 请求发送前 |
| JSR223 后置处理器 | 请求执行完成后 |
| JSR223 取样器 | 作为一个取样器执行 |
| JSR223 断言 | 用于断言 |
| JSR223 监听器 | 测试阶段监听 |

本次主要使用：

```text
JSR223 后置处理程序
```

它的执行顺序是：

```text
HTTP 请求
↓
JSR223 后置处理程序
↓
断言
↓
监听器
```

## 二、JMeter 支持的脚本语言

JMeter 5.6.3 自带以下常用脚本引擎：

| 语言 | 是否内置 | 说明 |
|---|---|---|
| Groovy | ✅ 内置 | 推荐，语法简洁，功能强 |
| BeanShell | ✅ 内置 | Java 风格，传统组件，性能相对一般 |
| JavaScript | ✅ Rhino 内置 | 可写简单脚本，但不是完整现代 JS |
| JEXL | ✅ 内置 | 表达式语言，适合简单逻辑 |
| Java | ⚠️ 不能直接作为脚本语言 | 可以通过 Groovy/BeanShell 调用 Java 类 |
| Python | ❌ 默认不支持 | 需要额外安装 Jython 等脚本引擎，且通常不支持 Python 3 |

## 三、Groovy 是什么

Groovy 不是 Java。

但它是运行在 Java 虚拟机上的语言，可以：

- 直接调用 Java 类
- 使用 Java 库
- 语法比 Java 简洁
- 和 Java 混用

例如：

```groovy
def list = [1, 2, 3]
list.each { item ->
    log.info(String.valueOf(item))
}
```

同样的逻辑用 Java 写会复杂很多。

所以 JMeter 中优先推荐：

```text
语言：groovy
```

## 四、为什么不能用 Python

JMeter 默认没有 Python 脚本引擎。

如果希望使用 Python，通常需要：

```text
安装 Jython 或其他 JSR-223 Python 引擎
把对应 jar 放入 JMeter 的 lib 目录
重启 JMeter
```

但这类方案：

- 兼容性不稳定
- 通常只支持旧版 Python
- 和 JMeter 生态配合不如 Groovy

所以 JMeter 脚本建议直接学习 Groovy。

## 五、JSR223 后置处理程序中文界面字段

添加位置：

```text
右键 HTTP 请求
→ 添加
→ 后置处理器
→ JSR223 后置处理程序
```

界面字段：

| 中文字段 | 作用 |
|---|---|
| 名称 | 组件名称 |
| 注释 | 说明 |
| 语言 | 脚本语言，选择 groovy |
| 参数 | 向脚本传递的字符串 |
| 脚本文件 | 外部脚本文件路径 |
| 脚本 | 直接编写的脚本 |
| 脚本编译缓存 | 是否缓存编译后的脚本 |

## 六、JSR223 脚本自动提供的变量

你不需要自己创建这些变量，JMeter 已经内置。

## 1. vars：当前线程变量

```groovy
vars.get('csrfToken')
vars.put('csrfToken', 'abc')
vars.remove('csrfToken')
```

对应：

```text
${csrfToken}
```

## 2. props：JMeter 属性

```groovy
props.get('token')
props.put('token', 'abc')
props.remove('token')
```

属性可以在整个测试运行期间共享。

## 3. prev：上一次取样结果

```groovy
prev.getResponseDataAsString()
prev.getResponseHeaders()
prev.getRequestHeaders()
prev.getResponseCode()
prev.getResponseMessage()
prev.isSuccessful()
prev.getURLAsString()
```

## 4. ctx：JMeter 上下文

```groovy
ctx.getThreadNum()
ctx.getVariables()
ctx.getPreviousResult()
```

## 5. sampler：当前取样器

```groovy
sampler.getName()
```

## 6. log：日志

```groovy
log.info('信息')
log.warn('警告')
log.error('错误')
```

## 7. parameters：参数值

如果在“参数”字段填写：

```text
user1 user2
```

脚本中：

```groovy
log.info(parameters)
```

输出：

```text
user1 user2
```

## 七、标准代码模板

```groovy
// 1. 获取响应
def body = prev.getResponseDataAsString()
def headers = prev.getResponseHeaders()

// 2. 提取数据
def value = ''

// 在这里写提取逻辑
// value = ...

// 3. 保存变量
vars.put('value', value)

// 4. 写日志
log.info('value = ' + value)
```

## 八、执行顺序和放置位置

JSR223 后置处理程序必须放在对应 HTTP 请求下面：

```text
01 获取公钥与令牌
├── JSR223 后置处理程序
└── Debug 查看提取结果
```

不要放在线程组下，否则会影响该范围内所有请求。

## 九、初学者常见错误

| 错误 | 原因 |
|---|---|
| 变量没有值 | 忘记调用 `vars.put` |
| 变量为 null | 使用 `vars.get` 但变量不存在 |
| `${变量}` 没有替换 | 变量没有保存到 vars |
| 日志没输出 | 没运行测试，或没有查看 jmeter.log |
| prev 报错 | 后置处理器没有放在请求下 |
| Groovy 报语法错误 | 字符串括号、引号或分号写错 |

## 十、调试建议

```groovy
log.info('csrfToken = ' + vars.get('csrfToken'))
log.info('rsaPublicKey = ' + vars.get('rsaPublicKey'))
```

然后查看 JMeter 日志：

```text
bin/jmeter.log
```

或者保留：

```text
Debug 查看提取结果
```

在“查看结果树”中查看。
