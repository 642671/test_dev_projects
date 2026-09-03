# JMeter 正则表达式提取器实战

> 更新时间：2026-09-03
> 适用范围：JMeter 5.6.3

## 一、正则表达式提取器是什么

正则表达式提取器是 JMeter 的后置处理器，用于：

```text
从响应正文、响应头、请求头、URL、响应代码中提取内容
保存到 JMeter 变量
供后续请求使用
```

## 二、添加位置

在 HTTP 请求上右键：

```text
添加
→ 后置处理器
→ 正则表达式提取器
```

因为它是后置处理器，必须放在产生响应结果的请求下面：

```text
01 获取公钥与令牌
├── 正则表达式提取器
└── Debug PostProcessor
```

## 三、中文界面字段说明

## 1. 引用名称 / Name of created variable

这是保存变量的名称。

例如：

```text
csrfToken
```

后续使用：

```text
${csrfToken}
```

## 2. 要检查的响应字段 / Field to check

用于选择从哪里提取。

| 选项 | 含义 |
|---|---|
| 主体 | 响应正文 |
| Body（unescaped） | 响应正文，处理转义字符 |
| Body as a Document | 文档正文 |
| 信息头 / Response Headers | 响应头 |
| Request Headers | 请求头 |
| URL | 请求 URL |
| 响应代码 | 200、404 等 |
| 响应信息 | OK、Not Found 等 |

本项目使用：

```text
信息头 / Response Headers
```

不要选：

```text
Request Headers
```

## 3. 正则表达式 / Regular Expression

填写匹配规则。

## 4. 模板 / Template

决定取匹配结果的哪一部分。

| 模板 | 含义 |
|---|---|
| `$0$` | 整个匹配结果 |
| `$1$` | 第一个括号 |
| `$2$` | 第二个括号 |

## 5. 匹配数字 / Match No.

| 值 | 含义 |
|---|---|
| `1` | 第 1 个匹配结果 |
| `2` | 第 2 个匹配结果 |
| `0` | 随机取一个 |
| `-1` | 取所有匹配结果 |

## 6. 缺省值 / Default Value

如果匹配不到，使用这个值。

推荐填写：

```text
NOT_FOUND
```

## 7. 使用空默认值

勾选后，如果匹配不到，变量值为空字符串。

## 四、当前项目准确配置

## 提取 X-Csrf-Token

| 字段 | 值 |
|---|---|
| 引用名称 | `csrfToken` |
| 要检查的响应字段 | `信息头 / Response Headers` |
| 正则表达式 | `X-Csrf-Token=([^;]+)` |
| 模板 | `$1$` |
| 匹配数字 | `1` |
| 缺省值 | `NOT_FOUND` |

## 提取 X-Rsa-Token

| 字段 | 值 |
|---|---|
| 引用名称 | `rsaPublicKey` |
| 要检查的响应字段 | `信息头 / Response Headers` |
| 正则表达式 | `X-Rsa-Token:\s*([^\r\n]+)` |
| 模板 | `$1$` |
| 匹配数字 | `1` |
| 缺省值 | `NOT_FOUND` |

## 五、为什么会出现 _g、_g0、_g1

只要使用正则表达式提取器，JMeter 就会自动生成分组变量。

例如：

```text
csrfToken = 51945...
csrfToken_g = 1
csrfToken_g0 = X-Csrf-Token=51945...
csrfToken_g1 = 51945...
```

含义：

| 变量 | 含义 |
|---|---|
| `csrfToken` | 最终使用的变量 |
| `_g` | 括号数量 |
| `_g0` | 整个匹配结果 |
| `_g1` | 第一个括号中的内容 |
| `_g2` | 第二个括号中的内容 |

这些变量只是 JMeter 的调试辅助变量，不影响使用。

## 六、如果想避免 _g 系列变量

方法一：使用 JSR223 后置处理程序，只写入需要的变量。

方法二：使用边界提取器。

方法三：使用 JSON 提取器，但仅适用于 JSON 响应。

当前项目已改为 JSR223 后置处理程序：

```text
D:\test_dev_projects\Jmeter\TNAS存储管理接口测试计划.jmx
```

## 七、正则表达式提取器完整示例

响应头：

```text
Set-Cookie: X-Csrf-Token=c95ea213...; Path=/
X-Rsa-Token: LS0tLS1CRUdJTiBSU0EgUFVCTElDIEtFWS0tLS0t...
```

两个提取器配置完成后：

```text
01 获取公钥与令牌
├── 正则表达式提取器：csrfToken
├── 正则表达式提取器：rsaPublicKey
└── Debug PostProcessor
```

后续请求：

```text
X-Csrf-Token: ${csrfToken}
X-Rsa-Token: ${rsaPublicKey}
```

## 八、怎么确认提取成功

第一步：运行测试。

第二步：打开：

```text
查看结果树
```

第三步：选择：

```text
01 获取公钥与令牌
```

第四步：选择：

```text
Debug PostProcessor
```

第五步：查看：

```text
csrfToken = c95ea...
rsaPublicKey = LS0t...
```

## 九、常见问题

## 1. 变量显示 NOT_FOUND

原因：

- 正则写错
- Field to check 选错
- 响应头名称大小写不匹配
- 提取器没有放在正确请求下

## 2. 变量显示 ${csrfToken}

原因：

- 提取器没有执行
- 提取器没有放在该请求下

## 3. 提取结果包含 ; Path=/

原因：

- 正则没有正确限制分号

正确正则：

```text
X-Csrf-Token=([^;]+)
```

## 4. 提取结果包含 X-Csrf-Token=

原因：

- Template 填成了 `$0$`

应改为：

```text
$1$
```

## 5. 响应头匹配失败

确认：

```text
要检查的响应字段 = Response Headers
```

## 十、正则表达式提取器和 JSR223 的选择

| 方式 | 优点 | 缺点 |
|---|---|---|
| 正则表达式提取器 | 图形化，简单 | 会产生 _g 变量 |
| 边界提取器 | 不需要正则，简单 | 复杂格式不好处理 |
| JSON 提取器 | 适合 JSON | 只能处理 JSON |
| JSR223 | 灵活，只保存需要的变量 | 需要写脚本 |

## 十一、推荐学习路线

1. 先学习边界提取器
2. 再学习 JSON 提取器
3. 再学习正则表达式提取器
4. 最后学习 JSR223 后置处理程序

这样能由易到难逐步掌握。
