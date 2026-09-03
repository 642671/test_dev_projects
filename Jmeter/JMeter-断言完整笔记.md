# JMeter 断言完整笔记

> 更新时间：2026-09-03
> 适用版本：Apache JMeter 5.6.3

## 一、断言是什么

断言用于验证请求结果是否符合预期。

例如：

```text
响应码是不是 200
响应正文是否包含 success
JSON 中 code 是否等于 0
响应时间是否超过 3 秒
```

如果断言失败，JMeter 会把这一个请求标记为失败。

## 二、执行顺序

JMeter 的执行顺序：

```text
HTTP 请求
↓
后置处理器（提取器）
↓
断言
↓
监听器
```

所以：

```text
提取器先执行
断言后执行
```

## 三、常用断言类型

| 断言 | 用途 |
|---|---|
| 响应断言 | 检查响应内容、响应码 |
| 持续时间断言 | 检查响应时间 |
| JSON 断言 | 检查 JSON 字段和值 |
| 大小断言 | 检查响应大小 |
| XML 断言 | 检查 XML 内容 |
| HTML 断言 | 检查 HTML 内容 |
| JSR223 断言 | 自定义断言逻辑 |

## 四、响应断言完整说明

添加位置：

```text
右键 HTTP 请求
→ 添加
→ 断言
→ 响应断言
```

## 1. 要检查的响应字段

用于选择检查哪一部分。

| 字段 | 含义 |
|---|---|
| 响应文本 / Response Body | 响应正文 |
| 响应代码 | HTTP 状态码，例如 200 |
| 响应消息 | OK、Not Found 等 |
| 响应头 | 响应头 |
| 请求头 | 请求头 |
| URL | 请求 URL |

## 2. 模式匹配规则

| 规则 | 含义 |
|---|---|
| 包含 / Contains | 内容中是否包含指定字符串 |
| 匹配 / Matches | 是否完整匹配正则表达式 |
| 等于 / Equals | 是否完全相等 |
| 子字符串 / Substring | 是否包含子字符串 |
| 否 / Not | 结果取反 |

## 3. 测试字段

选择：

```text
响应文本
```

## 4. 要测试的模式

填写期望内容。

例如：

```text
success
```

## 5. 忽略大小写

勾选后，`Success` 和 `success` 都算匹配。

## 6. 忽略状态

这个选项一般不用。

## 五、响应断言示例

### 示例 1：检查响应码是 200

配置：

```text
要检查的响应字段：响应代码
模式匹配规则：等于
要测试的模式：200
```

### 示例 2：检查响应正文包含 success

配置：

```text
要检查的响应字段：响应文本
模式匹配规则：包含
要测试的模式：success
```

### 示例 3：检查响应正文不包含 error

配置：

```text
要检查的响应字段：响应文本
模式匹配规则：否
要测试的模式：error
```

### 示例 4：使用正则匹配

配置：

```text
模式匹配规则：匹配
要测试的模式：.*success.*
```

## 六、持续时间断言

用于检查响应时间。

添加位置：

```text
添加 → 断言 → 持续时间断言
```

配置：

```text
最大响应时间（毫秒）：3000
```

含义：

```text
如果响应时间超过 3000 毫秒，断言失败
```

## 七、JSON 断言

用于检查 JSON 字段。

添加位置：

```text
添加 → 断言 → JSON Assertion
```

支持 JSONPath。

### 示例 1：检查 code 等于 0

响应：

```json
{
  "code": 0,
  "message": "success"
}
```

配置：

| 字段 | 值 |
|---|---|
| JSON Path Expression | `$.code` |
| Expected Value | `0` |

### 示例 2：检查 message 等于 success

配置：

```text
JSON Path：$.message
Expected Value：success
```

### 示例 3：检查 token 不为空

配置：

```text
JSON Path：$.data.token
Expected Value：NOT_EMPTY
```

具体是否支持 `NOT_EMPTY` 语法取决于 JMeter 版本和界面，建议以实际界面为准。

如果版本不支持，可以使用：

```text
JSR223 断言
```

## 八、JSR223 断言

适合复杂断言。

添加位置：

```text
添加 → 断言 → JSR223 断言
```

语言选择：

```text
groovy
```

示例：

```groovy
def body = prev.getResponseDataAsString()

if (!body.contains('success')) {
    AssertionResult.setFailure(true)
    AssertionResult.setFailureMessage('响应中没有 success')
}
```

## 九、断言结果在哪里看

运行后打开：

```text
查看结果树
```

选择请求：

```text
断言结果
```

如果失败：

```text
显示失败原因
显示断言结果
```

## 十、断言失败后怎么处理

在线程组中设置：

```text
On sample error
```

常见选项：

| 选项 | 含义 |
|---|---|
| Continue | 继续执行后续请求 |
| Start Next Thread Loop | 开始下一个线程循环 |
| Stop Thread | 停止当前线程 |
| Stop Test | 停止整个测试 |
| Stop Test Now | 立即停止测试 |

功能测试通常：

```text
Continue
```

性能测试可根据需要：

```text
Stop Test
```

## 十一、断言完整流程示例

登录接口：

```text
登录接口
├── JSON 提取器：token
├── 响应断言：响应码等于 200
├── JSON 断言：$.code 等于 0
└── Duration Assertion：最大 3000ms
```

运行后：

```text
200
code = 0
token = abc123
```

## 十二、常见问题

## 1. 断言总失败

检查：

- 选择的是响应文本还是响应代码
- 模式匹配规则是否正确
- 是否选择了 Not
- 大小写是否一致

## 2. 响应正文中包含但断言还是失败

检查：

```text
模式匹配规则是否选择了“包含”
```

如果选“等于”，必须是完全一致。

## 3. JSON 断言报错

检查：

- 响应是否是 JSON
- Content-Type 是否是 application/json
- JSONPath 是否正确
- 字段是否存在

## 4. 响应断言失败但实际成功

常见原因：

```text
响应正文有换行或空格
```

建议：

```text
使用包含
或者使用正则表达式
```

## 十三、练习

### 练习 1

断言响应码是 200。

答案：

```text
响应断言
响应字段：响应代码
规则：等于
值：200
```

### 练习 2

断言响应包含 `success`。

答案：

```text
响应断言
响应字段：响应文本
规则：包含
值：success
```

### 练习 3

断言 JSON `$.code == 0`。

答案：

```text
JSON 断言
JSONPath：$.code
Expected Value：0
```

### 练习 4

断言响应时间小于 5000ms。

答案：

```text
持续时间断言
最大响应时间：5000
```

## 十四、学习结论

推荐组合：

```text
响应断言：检查 HTTP 状态码
JSON 断言：检查业务返回码
持续时间断言：检查性能
```

复杂逻辑再使用：

```text
JSR223 断言
```
