# JMeter Groovy 常用代码示例

> 更新时间：2026-09-03
> 适用场景：JSR223 后置处理程序

## 一、从响应头提取 X-Csrf-Token

```groovy
def headers = prev.getResponseHeaders()
String csrfToken = ''

headers.eachLine { line ->
    def m = line =~ /X-Csrf-Token=([^;]+)/
    if (m.find()) {
        csrfToken = m.group(1).trim()
    }
}

vars.put('csrfToken', csrfToken ? csrfToken : 'NOT_FOUND')
log.info('csrfToken = ' + csrfToken)
```

## 二、从响应头提取 X-Rsa-Token

```groovy
def headers = prev.getResponseHeaders()
String rsaPublicKey = ''

headers.eachLine { line ->
    def m = line =~ /X-Rsa-Token:\s*(.+)/
    if (m.find()) {
        rsaPublicKey = m.group(1).trim()
    }
}

vars.put('rsaPublicKey', rsaPublicKey ? rsaPublicKey : 'NOT_FOUND')
log.info('rsaPublicKey = ' + rsaPublicKey)
```

## 三、从 JSON 响应中提取字段

响应：

```json
{
  "code": 0,
  "data": {
    "token": "abc123"
  }
}
```

代码：

```groovy
import groovy.json.JsonSlurper

def response = prev.getResponseDataAsString()
def json = new JsonSlurper().parseText(response)

def token = json.data.token
vars.put('token', token)

log.info('token = ' + token)
```

## 四、从 JSON 数组中提取第一个元素

响应：

```json
{
  "data": [
    {"id": 1, "name": "张三"},
    {"id": 2, "name": "李四"}
  ]
}
```

代码：

```groovy
import groovy.json.JsonSlurper

def response = prev.getResponseDataAsString()
def json = new JsonSlurper().parseText(response)

def firstId = json.data[0].id
vars.put('firstId', String.valueOf(firstId))
```

## 五、从普通文本中提取内容

响应：

```text
token=abc123
```

代码：

```groovy
def body = prev.getResponseDataAsString()
def m = body =~ /token=(\w+)/

if (m.find()) {
    vars.put('token', m.group(1))
}
```

## 六、判断响应是否成功

```groovy
def code = prev.getResponseCode()

if (code == '200') {
    vars.put('status', 'SUCCESS')
    log.info('请求成功')
} else {
    vars.put('status', 'FAIL')
    log.error('请求失败，状态码=' + code)
}
```

## 七、根据条件保存变量

```groovy
def token = vars.get('csrfToken')

if (token && token != 'NOT_FOUND') {
    vars.put('authToken', token)
} else {
    vars.put('authToken', 'EMPTY')
}
```

## 八、删除变量

```groovy
vars.remove('token')
vars.remove('token_g')
vars.remove('token_g0')
vars.remove('token_g1')
```

## 九、批量删除正则提取器辅助变量

```groovy
['token', 'token_g', 'token_g0', 'token_g1'].each { name ->
    vars.remove(name)
}
```

## 十、设置全局属性

```groovy
def token = vars.get('csrfToken')
props.put('csrfToken', token)
```

其他线程使用：

```text
${__P(csrfToken)}
```

## 十一、把变量写入文件

```groovy
def file = new File('D:/test_dev_projects/Jmeter/提取变量临时记录.txt')

file.append(
    'csrfToken=' + vars.get('csrfToken') + '\n' +
    'rsaPublicKey=' + vars.get('rsaPublicKey') + '\n'
)
```

警告：

```text
不要长期保存真实 token
不要提交到 Git
临时调试完成后建议删除
```

## 十二、打印变量

```groovy
log.info('----------------')
log.info('csrfToken = ' + vars.get('csrfToken'))
log.info('rsaPublicKey = ' + vars.get('rsaPublicKey'))
log.info('----------------')
```

## 十三、生成时间戳

```groovy
def timestamp = System.currentTimeMillis()
vars.put('timestamp', String.valueOf(timestamp))
```

也可以使用：

```groovy
import java.text.SimpleDateFormat

def now = new Date()
def format = new SimpleDateFormat('yyyy-MM-dd HH:mm:ss')
vars.put('now', format.format(now))
```

## 十四、生成 UUID

```groovy
import java.util.UUID

def uuid = UUID.randomUUID().toString()
vars.put('uuid', uuid)
```

## 十五、Base64 解码 X-Rsa-Token

```groovy
import java.util.Base64

def raw = vars.get('rsaPublicKey')
def pem = new String(Base64.getMimeDecoder().decode(raw), 'UTF-8')

vars.put('rsaPublicKeyPem', pem)
log.info(pem)
```

## 十六、Base64 加密字符串

```groovy
import java.util.Base64

def text = 'hello'
def encoded = Base64.getEncoder().encodeToString(text.getBytes('UTF-8'))

vars.put('encodedText', encoded)
log.info(encoded)
```

## 十七、字符串拼接

```groovy
def prefix = 'Bearer '
def token = vars.get('csrfToken')

vars.put('authorization', prefix + token)
```

## 十八、判断变量是否为空

```groovy
def token = vars.get('csrfToken')

if (token == null || token == '') {
    log.warn('csrfToken 为空')
    vars.put('csrfToken', 'NOT_FOUND')
} else {
    log.info('csrfToken = ' + token)
}
```

## 十九、循环处理数组

```groovy
def ids = ['1001', '1002', '1003']

ids.eachWithIndex { id, index ->
    vars.put('id_' + index, id)
    log.info('id_' + index + ' = ' + id)
}
```

## 二十、JSR223 后置处理程序完整示例

这是一个直接从响应头提取两个变量，并只保留主要变量的完整脚本：

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

log.info('rsaPublicKey = ' + rsaPublicKey)
log.info('csrfToken = ' + csrfToken)
```

## 二十一、使用 Parameters 参数

在 JSR223 的“参数”字段填写：

```text
user1 user2
```

脚本：

```groovy
def values = parameters.split(' ')

vars.put('user1', values[0])
vars.put('user2', values[1])
```

结果：

```text
user1 = user1
user2 = user2
```

## 二十二、脚本文件方式

如果代码很长，可以把脚本保存到文件：

```text
D:\test_dev_projects\Jmeter\scripts\extract.groovy
```

然后在：

```text
脚本文件
```

中填写路径。

## 二十三、建议

日常使用 JSR223 后置处理程序，优先掌握：

1. `prev` 读取响应
2. `vars.get` / `vars.put` 保存变量
3. `log.info` 调试
4. `JsonSlurper` 解析 JSON
5. `eachLine` 遍历响应头
6. 正则表达式提取
7. 字符串处理

其他功能需要时再逐步学习。
