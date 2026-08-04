# API 响应体 `msg` 字段语义化改进建议

---

## 一、当前响应结构

接口统一返回以下字段（引自现有规范文档）：

| 字段 | 类型 | 必须 | 规范定义 |
|------|------|------|---------|
| `is_login` | boolean | 是 | 用户登录状态，true=已登录 false=未登录 |
| `code` | boolean | 是 | 响应状态，true=操作成功 false=操作失败 |
| `msg` | string | 是 | **code 为 false 时的错误描述** |
| `data` | boolean | 是 | 操作结果，true=成功 false=失败 |
| `time` | number | 是 | 响应时间，单位：秒 |
| `code_num` | number | 是 | 返回状态码 0=成功 非0=失败 |
| `code_msg` | string | 是 | **code_num 非0时的错误描述信息** |

当前设计中，`msg` 仅在 `code=false` 时有语义，`code_msg` 仅在 `code_num≠0` 时有语义。**按现有规范，成功场景下 msg 为空是正确的。**

---

## 二、行业标准参考

以下按权威性从高到低列出 API 响应设计中关于消息/描述字段的业界规范：

### 2.1 Google AIP-193：错误处理（权威标准）

> 来源：https://google.aip.dev/193

Google API Improvement Proposals 中明确规定了 `Status.message` 字段的要求：

- "The **message** field is a **developer-facing, human-readable 'debug message'** which should be in English."
- "Error messages should **help a reasonably technical user understand and resolve the issue**, and should not assume that the user is an expert in your particular API."
- "Messages should use **simple descriptive language** that is easy to understand to clearly state the problem, and offer an **actionable resolution** to it."
- "For pre-existing APIs, the value of message **must remain the same** for any given error."

Google AIP-193 是 Google 全系云 API（Gmail、Drive、Cloud Storage 等）的强制性设计规范。

---

### 2.2 RFC 9457：Problem Details for HTTP APIs（IETF 国际标准）

> 来源：https://www.rfc-editor.org/info/rfc9457

RFC 9457 是 RFC 7807 的升级版，定义了 API 错误响应的标准格式：

- **`detail`** 字段："A **human-readable explanation specific to this occurrence** of the problem."
- 核心要求：每个具体问题的发生，都必须有对应的、人类可读的解释。

该标准被 Google、Microsoft、Zalando 等主要厂商广泛采用。

---

### 2.3 Google AIP-151：异步长时操作（Long-running Operations）

> 来源：https://google.aip.dev/151

Google 为异步 API 定义了标准模型：

```
message Operation {
  string name = 1;          // 操作唯一标识
  google.protobuf.Any metadata = 2;  // 进度/状态等元数据
  bool done = 3;            // false=进行中，true=已完成
  oneof result {
    google.rpc.Status error = 4;    // 失败时
    google.protobuf.Any response = 5; // 成功时
  }
}
```

**关键设计：用 `done` 字段彻底区分"进行中"和"已完成"，避免状态混淆。**

来源：https://github.com/googleapis/googleapis/blob/master/google/longrunning/operations.proto

---

### 2.4 GraphQL 规范（October 2021）：错误 message 字段为强制项

> 来源：https://spec.graphql.org/October2021/

GraphQL 规范明确要求：

> "**Every error must contain** an entry with the key `message` with a **string description** of the error intended for the developer as a guide to **understand and correct** the error."

message 字段是必填项（MUST contain），不可省略或留空。

---

### 2.5 JSON:API 规范 v1.1：错误对象必须包含人类可读信息

> 来源：https://jsonapi.org/format/1.1/

JSON:API 定义了 Error Objects：

- **`title`**：a short, **human-readable summary** of the problem that SHOULD NOT change from occurrence to occurrence
- **`detail`**：a **human-readable explanation specific to this occurrence** of the problem
- Error objects **MUST contain at least one** of: id, links, status, code, title, detail, source, meta

**核心原则：每个错误对象必须至少提供一个人类可读的信息维度。**

---

### 2.6 Postman 官方：API 错误处理最佳实践

> 来源：https://blog.postman.com/best-practices-for-api-error-handling/

Postman（全球最大的 API 平台）明确建议：

- "**Use descriptive error messages**: Error messages should be clear and descriptive. The consumer of your API should be able to understand the problem and how to fix it from reading the error messages."
- "**Use a standardized error response format**: Maintain a consistent standard for error messages. For example, most REST APIs include fields like `error`, `message`, `code`, and sometimes `details` for additional information."

Postman 推荐的错误响应格式示例：

```json
{
  "status": "error",
  "statusCode": 404,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found.",
    "details": "The user with the ID '12345' does not exist in our records.",
    "timestamp": "2023-12-08T12:30:45Z",
    "path": "/api/v1/users/12345",
    "suggestion": "Please check if the user ID is correct or refer to our documentation."
  }
}
```

---

### 2.7 Stripe API：错误分类 + 精确消息 + 文档链接

> 来源：https://docs.stripe.com/api/errors

Stripe（全球最大支付 API）的错误响应设计：

| 属性 | 说明 |
|------|------|
| `error.type` | 枚举：`api_error`、`card_error`、`idempotency_error`、`invalid_request_error` |
| `error.message` | **Human-readable message** providing more details about the error |
| `error.code` | **Programmatically handleable** error code string |
| `error.doc_url` | URL to documentation about the error code |

Stripe 的错误模型实现了三个层次的可辨识性：**类型分类 → 机器码 → 人类信息**。

---

### 2.8 Twilio API：异常响应必须包含 message + code + more_info

> 来源：https://www.twilio.com/docs/usage/twilios-response

Twilio（全球最大通信 API）的异常响应结构：

| 属性 | 说明 |
|------|------|
| `status` | HTTP 状态码 |
| `message` | **Detailed description** of the exception |
| `code` | Twilio-specific error code |
| `more_info` | URL to Twilio documentation for the error code |

示例：
```json
{
  "status": 400,
  "message": "No to number is specified",
  "code": 21201,
  "more_info": "http://www.twilio.com/docs/errors/21201"
}
```

---

### 2.9 阿里云 OpenAPI：错误返回必须含 code + message

> 来源：https://help.aliyun.com/zh/open-search/high-performance-searchedition/response-structure-1

阿里云 OpenAPI 错误返回结构：

| 字段 | 类型 | 描述 |
|------|------|------|
| `requestId` | String | 请求 ID |
| `httpCode` | Integer | HTTP 响应码 |
| `code` | String | **错误代码** |
| `message` | String | **错误信息** |

示例：
```json
{
  "requestId": "BD1EA715-DF6F-06C2-004C-C1FA0D3A9820",
  "httpCode": 404,
  "code": "App.NotFound",
  "message": "App not found"
}
```

---

### 2.10 腾讯云 API：Error 字段失败时必定返回，含 Code + Message

> 来源：https://cloud.tencent.com/document/product/213/15694

腾讯云 API 规范：

> "Error 字段连同其内部的 **Code 和 Message 字段在调用失败时是必定返回的**。Code 表示具体出错的错误码，Message 表示该错误的具体信息。"

**关键表述：失败时必定返回（非空）。**

---

### 2.11 阮一峰《异步 API 的设计》

> 来源：https://www.ruanyifeng.com/blog/2018/12/async-api-design.html

异步 API 标准模式：

```
POST 请求 → 202 Accepted + Location: /queue/12345
           + 响应体可包含状态描述、预计时间等
GET 查询  → 200 OK + <status>PENDING</status> + <eta>2 mins.</eta>
完成时    → 303 See Other → 新资源地址
```

核心观点：**异步中间状态通过状态字段显式表达，而非通过消息为空来暗示。**

---

### 2.12 Zalando RESTful API Guidelines

> 来源：https://github.com/zalando/restful-api-guidelines

Zalando（欧洲最大电商平台）的 API 规范明确要求：

- 使用 `application/problem+json`（RFC 9457）格式报告错误
- 必须提供 `type`、`title`、`status`、`detail` 等标准字段

---

### 2.13 gRPC 错误处理指南

> 来源：https://grpc.io/docs/guides/error/

gRPC 的 `google.rpc.Status` 模型定义了错误的三元组：

- **`code`**：标准状态码（如 `NOT_FOUND`、`INVALID_ARGUMENT`）
- **`message`**：人类可读的描述信息
- **`details`**：机器可读的附加错误详情

所有 gRPC 服务必须遵循此模型，message 为结构体必含字段。

---

### 2.14 Stack Overflow 社区共识：JSON API 响应格式

> 来源：https://stackoverflow.com/questions/12806386/is-there-any-standard-for-json-api-response-format

社区高票回答：

> "Define a **uniform structure** for errors (ex: `code`, `message`). For success it's a similar format, `code`, `message` and any data in the `data` property."

---

## 三、规范汇总对照

| 来源 | message/detail 字段要求 | 异步状态区分 |
|------|------------------------|------------|
| Google AIP-193 | **必须**有，human-readable，actionable | — |
| RFC 9457 | detail **必须**是"specific to this occurrence" | — |
| Google AIP-151 | — | `done` 字段区分 |
| GraphQL Spec | **MUST contain** message | — |
| JSON:API Spec | **MUST contain** at least one of title/detail | — |
| Postman | **Use descriptive error messages** | — |
| Stripe | error.message **必填**，human-readable | — |
| Twilio | message: **Detailed description** | — |
| 阿里云 | message: **错误信息（必填）** | — |
| 腾讯云 | Code + Message **调用失败时必定返回** | — |
| 阮一峰 | — | 202 + 状态枚举 |
| gRPC | message 为 Status 结构体**必含字段** | — |
| Zalando | 遵循 RFC 9457 format | — |

**共识结论：所有主流标准均要求 API 的错误/状态描述不可为空，且每个可区分的状态都应有对应的可辨识信息。**

---

## 四、当前存在的问题

### 问题 1：异常场景下 msg 为空，无法区分具体错误

部分已知异常场景（`code=false`）返回的 `msg` 为空字符串 `""`。此时测试只能断言 `code=false`，但无法区分是哪种错误，也无法判断是否出现了未知异常。

### 问题 2：即使所有已知场景补上 msg，仍有断言盲区

假设所有已知正常/异常场景的 msg 都填上了值，但实际运行中仍会碰到：

- **未知异常**：`code=false` 但 `msg=""`（未被覆盖的新错误），无法断言
- **异步跳过**：接口因前置条件不满足而跳过执行，同样 `msg=""`（正常现象）

这两个"空"在测试结果中完全无法区分——一个是"不该发生的未知错误"，一个是"应该发生的预期跳过"。

### 问题 3：异步跳过与异常返回的不可分辨性

这是最尴尬的场景：当一个用例预期返回某种异常（`code=false` + 特定 msg），但因为环境状态导致接口被异步跳过（`code=false` + `msg=""`），测试既不能判断"出现了预期异常"，也不能判断"是正常跳过"，直接陷入困境。

---

## 五、期望的改进方向

在不破坏现有字段语义的前提下，利用已有的 `code_num` + `code_msg` 扩展状态定义。

### 5.1 方案：扩展 code_num 为状态标识

`code_num` 当前定义"0=成功，非0=失败"，建议扩展为"0=标准成功，非0=需关注的特定状态"。

| 场景 | code | code_num | msg | code_msg |
|------|------|----------|-----|----------|
| 同步成功（不变） | true | 0 | `""` | `""` |
| 异步已提交 | true | 1 | `""` | `"任务已提交，处理中"` |
| 异步跳过（前置条件不满足） | true | 2 | `""` | `"前置条件未满足，已跳过"` |
| 同步失败：磁盘被占用 | false | 1001 | `"磁盘已被占用"` | `""` |
| 同步失败：参数缺失 | false | 1002 | `"缺少必填参数：raid_level"` | `""` |
| 同步失败：名称重复 | false | 1003 | `"存储池名称已存在"` | `""` |
| 同步失败：磁盘数量不足 | false | 1004 | `"RAID5 至少需要 3 块可用磁盘"` | `""` |

### 5.2 方案优势

1. **不破坏现有规范**：`msg` 仍然是"code=false 时的描述"，`code_msg` 仍然是"code_num≠0 时的描述"
2. **异步跳过可识别**：测试断言 `code_num=2` → 确认为"预期内的跳过"
3. **已知异常可精确断言**：通过 `code_num` 值精确定位具体错误类型
4. **未知异常自动暴露**：`code=false` + `msg=""` + `code_num` 不在预期列表中 → 直接 FAIL

### 5.3 测试侧断言策略

| code_num | 断言内容 |
|----------|---------|
| 0 | `code=true` + `code_msg=""` |
| 1 | `code=true` + `code_msg` 包含"已提交" |
| 2 | `code=true` + `code_msg` 包含"已跳过" |
| ≥1001 | `code=false` + `msg` 精确匹配 + `code_num` 精确匹配 |
| 其他 | `code=false` + `msg=""` → **直接 FAIL，标记为未覆盖异常** |

---

## 六、总结

| 维度 | 现状 | 行业标准 | 建议 |
|------|------|---------|------|
| 正常场景 msg | `""` | — | 保持不变 |
| 异常场景 msg | 部分 `""` | **必须有**（全员） | 补全所有已知异常 |
| 异步中间状态 | 无区分 | `done` 字段 / 状态枚举 | 用 `code_num` 标识 |
| 断言粒度 | 只能断言 `code` | code + message + details | `code_num` + `msg`/`code_msg` |
| 未知异常感知 | 无法感知 | 应可识别 | 对未匹配状态直接告警 |

**最终目标：任何一个 API 返回结果，测试侧都能明确知道它属于哪种状态，而非对着空字符串猜测。**
