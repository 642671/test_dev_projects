# JMeter 正则提取与登录凭证笔记

> 更新时间：2026-09-02
> 用途：TNAS 存储管理接口测试计划中，从 `/tos/` 响应头提取 RSA 公钥和 CSRF Token，供后续接口自动使用。

## 一、相关文件

- 测试计划：`D:\test_dev_projects\Jmeter\TNAS存储管理接口测试计划.jmx`
- 旧版备份：`D:\test_dev_projects\Jmeter\TNAS存储管理接口测试计划_旧版备份_20260902.jmx`

## 二、目标

从下面的响应头中提取两个值：

```text
X-Rsa-Token: <Base64 编码的 RSA 公钥>
Set-Cookie: X-Csrf-Token=<CSRF Token>; Path=/
```

提取结果：

```text
rsaPublicKey = <X-Rsa-Token 的值>
csrfToken = <X-Csrf-Token 的值>
```

## 三、为什么不能用 JSON 提取器

这两个值不在 JSON 响应正文中，而是在 HTTP 响应头中。

因此必须使用：

```text
正则表达式提取器
或
边界提取器
```

本次采用**正则表达式提取器**。

## 四、第一个正则表达式提取器：X-Rsa-Token

位置：

```text
01 获取公钥与令牌
└── 正则表达式提取器：X-Rsa-Token提取为rsaPublicKey
```

配置：

| 字段 | 值 |
|---|---|
| Name of created variable | `rsaPublicKey` |
| Field to check | `Response Headers` |
| Regular Expression | `X-Rsa-Token:\s*([^\r\n]+)` |
| Template | `$1$` |
| Match No. | `1` |
| Default Value | `NOT_FOUND` |

正则解释：

```text
X-Rsa-Token:        找响应头名称
\s*                 冒号后面允许有空格
([^\r\n]+)          取到换行之前的所有内容作为第 1 组
```

`$1$` 表示只保存第 1 组括号中的内容。

## 五、第二个正则表达式提取器：X-Csrf-Token

位置：

```text
01 获取公钥与令牌
└── 正则表达式提取器：X-Csrf-Token提取为csrfToken
```

配置：

| 字段 | 值 |
|---|---|
| Name of created variable | `csrfToken` |
| Field to check | `Response Headers` |
| Regular Expression | `X-Csrf-Token=([^;]+)` |
| Template | `$1$` |
| Match No. | `1` |
| Default Value | `NOT_FOUND` |

正则解释：

```text
X-Csrf-Token=    找 Set-Cookie 中的变量名
([^;]+)          提取分号之前的所有内容
```

实际响应：

```text
Set-Cookie: X-Csrf-Token=c95ea...; Path=/
```

提取结果：

```text
csrfToken = c95ea...
```

## 六、Field to check 注意事项

必须选择：

```text
Response Headers
```

中文界面一般显示为：

```text
信息头
```

不要选择：

```text
Request Headers
```

## 七、后续请求使用方式

在后续业务请求下添加：

```text
HTTP 信息头管理器
```

填写：

```text
X-Rsa-Token: ${rsaPublicKey}
X-Csrf-Token: ${csrfToken}
```

## 八、验证方式

1. 在“01 获取公钥与令牌”请求下添加 `Debug PostProcessor`
2. 运行测试
3. 打开“查看结果树”
4. 查看 Debug 输出

预期结果：

```text
rsaPublicKey = LS0tLS1CRUdJTiBSU0EgUFVCTElDIEtFWS0tLS0t...
csrfToken = c95ea213...
```

## 九、常见问题

| 现象 | 原因 |
|---|---|
| 变量为 `NOT_FOUND` | 正则没匹配到 |
| 变量仍为 `${rsaPublicKey}` | 提取器没执行或位置错误 |
| 提取结果包含 `; Path=/` | 正则没有正确限制分号 |
| 一直失败但响应中确实有值 | Field to check 选成了 Body 或 Request Headers |
| 提取器没执行 | 提取器没有放在对应 HTTP 请求下 |

注意：粘贴响应时，每行末尾的 `\` 是文本换行标记，不是真实响应内容，不要写进正则。

## 十、X-Rsa-Token 是 Base64 编码的公钥

`X-Rsa-Token` 的值是 Base64 编码后的 RSA 公钥。

如果只是原样传给后续请求，直接使用：

```text
${rsaPublicKey}
```

如果需要得到 PEM 格式公钥，需要 Base64 解码。

## 十一、以后如何追加新正则提取器

基本步骤：

1. 在需要提取的 HTTP 请求下添加“正则表达式提取器”
2. 填写 Reference Name
3. 选择 Field to check
4. 填写正则表达式
5. Template 填写 `$1$`
6. Match No. 填写 `1`
7. 填写 Default Value 为 `NOT_FOUND`
8. 添加 Debug PostProcessor 验证
9. 在后续请求中使用 `${变量名}`

## 十二、只保留需要变量的方案（当前 JMX 已采用）

正则表达式提取器会自动额外生成：

```text
变量名_g
变量名_g0
变量名_g1
```

这些属于 JMeter 的调试辅助变量，不影响使用，但会出现在 Debug 中。

如果希望 Debug 中不出现 `_g` 系列变量，可以把两个正则表达式提取器替换成一个 `JSR223 后置处理程序`，只写入需要的两个变量：

```groovy
def headers = prev.getResponseHeaders()
String rsaPublicKey = ''
String csrfToken = ''

headers.eachLine { line ->
    def mRsa = line =~ /(?i)^X-Rsa-Token:\s*(.+)$/
    if (mRsa.find()) {
        rsaPublicKey = mRsa.group(1).trim()
    }
    def mCsrf = line =~ /(?i)X-Csrf-Token=([^;]+)/
    if (mCsrf.find()) {
        csrfToken = mCsrf.group(1).trim()
    }
}

vars.put('rsaPublicKey', rsaPublicKey ? rsaPublicKey : 'NOT_FOUND')
vars.put('csrfToken', csrfToken ? csrfToken : 'NOT_FOUND')
```

说明：

- `prev.getResponseHeaders()` 获取响应头
- 脚本内部仍会匹配响应头，但不会生成 `_g`、`_g0`、`_g1`
- 只写入 `rsaPublicKey` 和 `csrfToken`
- Debug PostProcessor 仍会显示 JMeter 自带的系统变量，这是 Debug 组件的默认行为

当前文件：

```text
D:\test_dev_projects\Jmeter\TNAS存储管理接口测试计划.jmx
```

已经采用该方案。
