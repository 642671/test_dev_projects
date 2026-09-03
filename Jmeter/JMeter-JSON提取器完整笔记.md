# JMeter JSON 提取器完整笔记

> 更新时间：2026-09-03
> 适用版本：Apache JMeter 5.6.3

## 一、JSON 提取器是什么

JSON 提取器是 JMeter 的后置处理器，用于：

```text
从 JSON 响应中提取某个字段的值
保存为 JMeter 变量
```

它使用 JSONPath，不需要写正则表达式。

适合：

```text
登录接口提取 token
创建接口提取 ID
查询接口提取列表中的某个值
```

不适合：

```text
从响应头中提取
从 HTML 中提取
从 XML 中提取
```

## 二、JSON 基础结构

JSON 对象：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "abc123",
    "userId": 1001
  }
}
```

JSON 数组：

```json
{
  "data": [
    {"id": 1, "name": "张三"},
    {"id": 2, "name": "李四"}
  ]
}
```

## 三、JSONPath 是什么

JSONPath 是描述 JSON 中某个位置的语法。

可以类比：

```text
JSON  = 一个文件夹
JSONPath = 文件夹中的路径
```

例如：

```text
$.data.token
```

表示：

```text
从根节点开始
进入 data
取 token
```

## 四、最常用的 JSONPath 语法

## 1. `$`

表示根节点。

```text
$
```

## 2. `.`

表示下一级。

```text
$.data.token
```

## 3. `[0]`

表示数组第 1 个元素。

```text
$.data.users[0].id
```

## 4. `[*]`

表示数组所有元素。

```text
$.data.users[*].id
```

## 5. `?()`

表示条件过滤。

```text
$.data.users[?(@.id==1002)].name
```

## 6. `..`

表示递归查找。

```text
$..token
```

## 五、JSON 提取器添加方法

在 HTTP 请求上右键：

```text
添加
→ 后置处理器
→ JSON 提取器
```

必须放在返回 JSON 的请求下面：

```text
登录接口
├── JSON 提取器：token
└── Debug PostProcessor
```

## 六、JSON 提取器中文界面字段

## 1. 名称

组件名称。

## 2. 注释

备注。

## 3. 作用域 / Apply to

| 选项 | 含义 |
|---|---|
| 主取样器 only | 只处理主请求 |
| 子取样器 only | 只处理子请求 |
| 主取样器和子取样器 | 两者都处理 |
| JMeter 变量名 | 处理指定变量 |

通常选择：

```text
主取样器 only
```

## 4. Name of created variable / 引用名称

变量名。

例如：

```text
token
```

后续使用：

```text
${token}
```

## 5. JSON Path Expressions

JSONPath 表达式。

例如：

```text
$.data.token
```

## 6. Default Values / 缺省值

如果提取不到，默认值。

推荐：

```text
NOT_FOUND
```

## 7. Match No. / 匹配数字

| 值 | 含义 |
|---|---|
| `1` | 取第 1 个匹配 |
| `2` | 取第 2 个匹配 |
| `0` | 随机取一个 |
| `-1` | 取所有匹配 |

## 8. Compute concatenation var

如果匹配到多个值，会拼接成一个变量：

```text
变量名_ALL
```

## 七、一个字段提取示例

响应：

```json
{
  "code": 0,
  "data": {
    "token": "abc123"
  }
}
```

配置：

| 字段 | 值 |
|---|---|
| Name of created variable | `token` |
| JSON Path Expressions | `$.data.token` |
| Default Values | `NOT_FOUND` |
| Match No. | `1` |

结果：

```text
token = abc123
```

## 八、多个字段同时提取

响应：

```json
{
  "code": 0,
  "data": {
    "token": "abc123",
    "userId": 1001
  }
}
```

JSON 提取器支持分号分隔：

| 字段 | 值 |
|---|---|
| Name of created variable | `token;userId` |
| JSON Path Expressions | `$.data.token;$.data.userId` |
| Default Values | `NOT_FOUND;NOT_FOUND` |
| Match No. | `1;1` |

结果：

```text
token = abc123
userId = 1001
```

## 九、数组提取

响应：

```json
{
  "data": {
    "users": [
      {"id": 1001, "name": "张三"},
      {"id": 1002, "name": "李四"},
      {"id": 1003, "name": "王五"}
    ]
  }
}
```

### 提取第一个用户 ID

```text
$.data.users[0].id
```

结果：

```text
1001
```

### 提取所有用户 ID

```text
$.data.users[*].id
```

设置：

```text
Match No. = -1
```

结果：

```text
id_1 = 1001
id_2 = 1002
id_3 = 1003
id_matchNr = 3
```

### 按条件提取

提取 id 等于 1002 的用户名：

```text
$.data.users[?(@.id==1002)].name
```

结果：

```text
李四
```

## 十、嵌套对象

响应：

```json
{
  "data": {
    "userInfo": {
      "id": 1001,
      "name": "张三"
    }
  }
}
```

提取姓名：

```text
$.data.userInfo.name
```

## 十一、多个匹配值拼接

如果选择：

```text
Compute concatenation var
```

例如：

```text
$.data.users[*].name
```

结果：

```text
name_ALL = 张三,李四,王五
```

## 十二、JSON 提取器完整实战：登录获取 token

登录接口响应：

```json
{
  "code": 0,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiJ9",
    "userId": 1001
  }
}
```

配置：

```text
登录接口
├── JSON 提取器：accessToken
│   ├── JSON Path：$.data.accessToken
│   ├── Match No.：1
│   └── Default：NOT_FOUND
└── Debug PostProcessor
```

后续查询接口使用：

```text
Authorization: Bearer ${accessToken}
```

## 十三、验证提取结果

1. 运行测试
2. 打开 `查看结果树`
3. 选择登录请求
4. 选择 `Debug PostProcessor`
5. 查看：

```text
accessToken = eyJhbGciOiJIUzI1NiJ9
```

## 十四、常见问题

## 1. 变量为 NOT_FOUND

检查：

- JSONPath 是否正确
- 响应是否为 JSON
- 响应中是否有该字段
- Match No. 是否正确

## 2. 变量为 null

如果 JSON 中的值为 null，提取结果可能是 null。

可以设置默认值：

```text
NOT_FOUND
```

## 3. JSON 有转义字符

如果响应是：

```json
{
  "data": "{\"token\":\"abc\"}"
}
```

这是字符串 JSON，不能直接用：

```text
$.data.token
```

需要先解析内部 JSON。

## 4. 数组中取不到

检查：

```text
是否使用 [索引]
是否使用 [*]
```

## 5. JSONPath 语法错误

常见错误：

```text
$.data.token  → 正确
data.token    → 很多场景也可以，但在 JMeter 中建议加 $
$.data[token] → 错误
```

## 十五、JSON 提取器和正则表达式提取器对比

| 方式 | 优点 | 缺点 |
|---|---|---|
| JSON 提取器 | 简单，适合 JSON | 只能处理 JSON |
| 正则表达式提取器 | 灵活 | 会生成 _g 变量 |
| 边界提取器 | 简单 | 不适合复杂结构 |
| JSR223 | 最灵活 | 需要写脚本 |

## 十六、练习

### 练习 1

响应：

```json
{
  "code": 0,
  "data": {
    "token": "abc123"
  }
}
```

提取 token。

答案：

```text
$.data.token
```

### 练习 2

响应：

```json
{
  "data": [
    {"id": 1},
    {"id": 2}
  ]
}
```

提取第 2 个 id。

答案：

```text
$.data[1].id
```

### 练习 3

提取所有 id。

答案：

```text
$.data[*].id
```

### 练习 4

提取 name 等于 李四 的 id。

答案：

```text
$.data[?(@.name=="李四")].id
```

## 十七、学习结论

JSON 提取器最适合：

```text
标准 JSON 响应
结构固定
需要提取字段或数组
```

以后遇到 JSON 响应，优先考虑：

```text
JSON 提取器
```

遇到复杂结构时，再用：

```text
JSR223 + JsonSlurper
```
