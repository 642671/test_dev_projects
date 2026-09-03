# JMeter 接口串联完整笔记

> 更新时间：2026-09-03
> 适用版本：Apache JMeter 5.6.3

## 一、什么是接口串联

接口串联是指多个接口按顺序执行，并且后面的接口使用前面接口返回的数据。

典型流程：

```text
登录接口
→ 获取 token
→ 查询订单
→ 新增订单
→ 修改订单
→ 删除订单
```

这就是最常见的接口串联。

## 二、接口串联的关键

需要完成两件事：

```text
1. 从前一个接口提取数据
2. 在后一个接口中使用数据
```

例如：

```text
登录接口返回 token
提取 token
后续接口请求头使用 token
```

## 三、接口串联完整测试树

```text
测试计划
├── 用户定义的变量
├── 全局 HTTP 请求默认值
├── 全局 HTTP 信息头
├── 全局 HTTP Cookie 管理器
└── 登录链路线程组
    ├── 01 获取公钥和令牌
    │   ├── JSR223 后置处理程序
    │   └── Debug PostProcessor
    ├── 02 登录接口
    │   ├── JSON 提取器：accessToken
    │   └── 响应断言
    ├── 03 查询用户信息
    ├── 04 新增用户
    │   ├── JSON 提取器：userId
    │   └── 响应断言
    ├── 05 修改用户
    └── 06 删除用户
```

## 四、接口 1：登录接口

假设登录接口：

```text
POST /api/login
```

响应：

```json
{
  "code": 0,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiJ9",
    "userId": 1001
  }
}
```

添加 JSON 提取器：

| 字段 | 值 |
|---|---|
| Name of created variable | `accessToken` |
| JSON Path Expressions | `$.data.accessToken` |
| Default Values | `NOT_FOUND` |
| Match No. | `1` |

结果：

```text
accessToken = eyJhbGciOiJIUzI1NiJ9
```

## 五、接口 2：后续接口使用 token

查询接口：

```text
GET /api/user/1001
```

在请求头中添加：

```text
Authorization: Bearer ${accessToken}
```

JMeter 会自动替换为：

```text
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9
```

## 六、从新增接口提取 userId

新增接口：

```text
POST /api/user
```

响应：

```json
{
  "code": 0,
  "data": {
    "id": 2001
  }
}
```

添加 JSON 提取器：

```text
Name of created variable = userId
JSON Path Expressions = $.data.id
```

后续修改删除接口：

```text
PUT /api/user/${userId}
DELETE /api/user/${userId}
```

## 七、变量作用范围

JSR223、JSON 提取器、正则提取器保存的变量默认是：

```text
JMeter 变量
```

作用范围：

```text
当前线程内
```

也就是说：

```text
线程 1 获取的 token
线程 2 看不到
```

这是正确的，因为每个用户应该有自己独立的 token。

## 八、跨线程组传递变量

如果多个线程组需要共享同一个值，可以用属性：

```groovy
props.put('accessToken', vars.get('accessToken'))
```

其他线程组使用：

```text
${__P(accessToken)}
```

注意：

```text
不要把每个用户独立的 token 放到全局属性中
```

因为多个线程会互相覆盖。

## 九、Cookie 串联

如果接口使用 Cookie 登录：

```text
登录接口返回 Set-Cookie
后续接口自动携带 Cookie
```

添加：

```text
线程组
→ 添加
→ 配置元件
→ HTTP Cookie 管理器
```

JMeter 会自动保存同一域名的 Cookie。

如果后续请求还需要把 Cookie 值放到请求头：

```text
${COOKIE_X-Csrf-Token}
```

需要先设置：

```text
CookieManager.save.cookies=true
```

## 十、事务控制器

把多个相关接口看作一个事务：

```text
事务控制器：创建订单
├── 新增订单
├── 查询订单
└── 确认订单
```

添加：

```text
右键线程组
→ 添加
→ 逻辑控制器
→ 事务控制器
```

适合统计：

```text
整个业务的总响应时间
总体吞吐量
总体错误率
```

## 十一、循环控制器

重复执行某个步骤：

```text
循环控制器
└── 查询订单接口
```

添加：

```text
右键线程组
→ 添加
→ 逻辑控制器
→ 循环控制器
```

设置循环次数：

```text
5
```

## 十二、If 控制器

根据变量条件执行：

```text
If 控制器：如果登录成功
└── 查询订单
```

条件：

```text
${accessToken} != "NOT_FOUND"
```

添加：

```text
右键线程组
→ 添加
→ 逻辑控制器
→ If 控制器
```

## 十三、Setup 和 Teardown

## Setup Thread Group

用于测试前准备：

```text
登录管理员
获取 token
准备测试数据
```

## Teardown Thread Group

用于测试后清理：

```text
删除测试数据
注销登录
清理环境
```

## 十四、接口串联示例：登录到删除

### 步骤 1：登录

```text
登录接口
执行成功
提取 accessToken
提取 userId
```

### 步骤 2：查询

```text
GET /api/user/${userId}
Authorization: Bearer ${accessToken}
```

### 步骤 3：新增

```text
POST /api/user
Authorization: Bearer ${accessToken}
Body：{"username":"newUser"}
```

### 步骤 4：修改

```text
PUT /api/user/${userId}
Authorization: Bearer ${accessToken}
```

### 步骤 5：删除

```text
DELETE /api/user/${userId}
Authorization: Bearer ${accessToken}
```

## 十五、串联接口的调试方法

1. 添加 `Debug PostProcessor`
2. 查看每一步的变量
3. 确认：

```text
accessToken 是否提取成功
userId 是否提取成功
```

4. 查看后续请求的 Request Headers
5. 确认：

```text
Authorization 是否已经替换为 token
```

## 十六、接口串联常见问题

## 1. 后续接口 401

原因：

```text
token 未提取
token 已过期
请求头没有带 token
```

## 2. 变量为 NOT_FOUND

原因：

- 提取器没有执行
- JSONPath 或正则写错
- 提取器位置错误

## 3. 变量被覆盖

原因：

```text
多个请求使用了相同的变量名
```

建议：

```text
每个接口使用不同变量名
```

例如：

```text
loginToken
userToken
orderId
```

## 4. 后续接口无法访问

检查：

- 服务器地址是否正确
- 端口是否正确
- 请求方法是否正确
- 请求路径是否正确

## 5. 多线程 token 串了

原因：

```text
使用了 props 全局属性保存每个用户独立的 token
```

建议：

```text
每个线程使用 vars 保存自己的 token
```

## 十七、接口串联推荐配置

```text
线程组：1
循环次数：1
中文变量名建议使用英文
提取器放在对应请求下面
断言放在提取器后面
后续请求使用 ${变量名}
```

## 十八、练习

### 练习 1

登录接口返回：

```json
{
  "code": 0,
  "data": {
    "accessToken": "abc123"
  }
}
```

提取 accessToken 并在查询接口请求头中使用。

答案：

```text
JSON 提取器：accessToken
查询接口请求头：Authorization: Bearer ${accessToken}
```

### 练习 2

新增接口返回：

```json
{
  "code": 0,
  "data": {
    "id": 2001
  }
}
```

提取 id 并在删除接口使用。

答案：

```text
JSON 提取器：userId
删除接口：DELETE /api/user/${userId}
```

### 练习 3

登录 token 只在一个线程内使用。

答案：

```text
使用 vars，不要使用 props
```

## 十九、学习结论

接口串联的核心：

```text
提取前一个接口的结果
后一个接口引用变量
```

推荐流程：

```text
登录 → 提取 token → 查询 → 提取 ID → 修改 → 删除
```

正式测试时：

```text
每个接口都添加断言
每个提取变量都要验证
使用 Debug 确认变量
```
