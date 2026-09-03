# JMeter Groovy 语法速查表

> 更新时间：2026-09-03
> 适用语言：Groovy 3.x，JMeter 内置

## 一、变量定义

```groovy
def name = '张三'
def age = 20
def price = 19.9
def isOk = true
```

也可以指定类型：

```groovy
String token = 'abc123'
int count = 10
boolean success = true
```

## 二、字符串

### 单引号

```groovy
def name = '张三'
```

单引号字符串不会自动替换变量。

### 双引号

```groovy
def name = '张三'
def text = "你好，${name}"
```

输出：

```text
你好，张三
```

## 三、字符串拼接

```groovy
def a = 'Bearer '
def token = 'abc'

def result = a + token
```

或：

```groovy
def result = "Bearer ${token}"
```

## 四、数字

```groovy
def a = 10
def b = 3

def sum = a + b
def diff = a - b
def product = a * b
def quotient = a / b
```

## 五、比较

```groovy
def code = '200'

if (code == '200') {
    log.info('成功')
}
```

`==` 用于判断相等。

`!=` 用于判断不相等。

## 六、空值判断

```groovy
def value = vars.get('csrfToken')

if (value == null) {
    log.warn('变量为空')
}

if (value == null || value == '') {
    vars.put('csrfToken', 'NOT_FOUND')
}
```

## 七、三元表达式

```groovy
def result = value ? value : 'NOT_FOUND'
```

等价于：

```groovy
if (value) {
    result = value
} else {
    result = 'NOT_FOUND'
}
```

## 八、安全调用 ?

```groovy
def token = json?.data?.token
```

如果 `json` 或 `data` 为 null，不会报错，结果也是 null。

## 九、列表 List

```groovy
def list = ['a', 'b', 'c']

list.each { item ->
    log.info(item)
}
```

获取元素：

```groovy
list[0]
list[1]
```

## 十、Map

```groovy
def map = [
    name: '张三',
    age: 20
]

map.each { key, value ->
    log.info(key + '=' + value)
}
```

获取值：

```groovy
map.name
map['name']
```

## 十一、if/else

```groovy
def code = prev.getResponseCode()

if (code == '200') {
    log.info('请求成功')
} else if (code == '404') {
    log.warn('接口不存在')
} else {
    log.error('请求失败，状态码=' + code)
}
```

## 十二、switch

```groovy
def code = prev.getResponseCode()

switch (code) {
    case '200':
        log.info('成功')
        break
    case '401':
        log.warn('未登录')
        break
    default:
        log.error('未知状态')
}
```

## 十三、for 循环

```groovy
for (int i = 0; i < 5; i++) {
    log.info('i = ' + i)
}
```

## 十四、集合遍历

```groovy
def list = ['a', 'b', 'c']

list.each { item ->
    log.info(item)
}
```

获取下标：

```groovy
list.eachWithIndex { item, index ->
    log.info(index + ':' + item)
}
```

## 十五、闭包

```groovy
def printName = { name ->
    log.info(name)
}

printName('张三')
```

## 十六、方法定义

```groovy
def add(int a, int b) {
    return a + b
}

def result = add(2, 3)
```

## 十七、正则表达式

```groovy
def text = 'token=abc123'
def m = text =~ /token=(\w+)/

if (m.find()) {
    log.info(m.group(1)) // abc123
}
```

忽略大小写：

```groovy
def m = text =~ /(?i)token=(\w+)/
```

## 十八、contains

```groovy
def text = 'X-Csrf-Token=abc'

if (text.contains('X-Csrf-Token')) {
    log.info('包含')
}
```

## 十九、字符串截取

```groovy
def text = 'abc123'

text.substring(0, 3) // abc
text.substring(3)     // 123
```

## 二十、替换字符串

```groovy
def text = 'a-b-c'
text.replace('-', '_') // a_b_c
```

## 二十一、去除空白

```groovy
def text = '  abc  '
text.trim() // abc
```

## 二十二、转换大小写

```groovy
def text = 'abc'

text.toUpperCase() // ABC
text.toLowerCase() // abc
```

## 二十三、JSON 解析

```groovy
import groovy.json.JsonSlurper

def response = '{"name":"张三","age":20}'
def json = new JsonSlurper().parseText(response)

def name = json.name
def age = json.age
```

## 二十四、JSON 序列化

```groovy
import groovy.json.JsonOutput

def map = [name: '张三', age: 20]
def json = JsonOutput.toJson(map)
```

## 二十五、日期

```groovy
import java.text.SimpleDateFormat

def now = new Date()
def format = new SimpleDateFormat('yyyy-MM-dd HH:mm:ss')

vars.put('now', format.format(now))
```

## 二十六、时间戳

```groovy
def timestamp = System.currentTimeMillis()
vars.put('timestamp', String.valueOf(timestamp))
```

## 二十七、UUID

```groovy
import java.util.UUID

def uuid = UUID.randomUUID().toString()
vars.put('uuid', uuid)
```

## 二十八、Base64

编码：

```groovy
import java.util.Base64

def encoded = Base64.getEncoder().encodeToString('hello'.getBytes('UTF-8'))
```

解码：

```groovy
import java.util.Base64

def raw = 'aGVsbG8='
def text = new String(Base64.getDecoder().decode(raw), 'UTF-8')
```

## 二十九、日志

```groovy
log.info('普通信息')
log.warn('警告')
log.error('错误')
log.debug('调试信息')
```

日志文件通常位于：

```text
JMeter安装目录/bin/jmeter.log
```

## 三十、读取 JMeter 变量

```groovy
def token = vars.get('csrfToken')
```

## 三十一、保存 JMeter 变量

```groovy
vars.put('csrfToken', 'abc123')
```

## 三十二、删除 JMeter 变量

```groovy
vars.remove('csrfToken')
```

## 三十三、读取 JMeter 属性

```groovy
def token = props.get('csrfToken')
```

## 三十四、保存 JMeter 属性

```groovy
props.put('csrfToken', 'abc123')
```

## 三十五、读取响应

```groovy
def body = prev.getResponseDataAsString()
def headers = prev.getResponseHeaders()
def code = prev.getResponseCode()
```

## 三十六、常用简写

```groovy
def x = value ?: '默认值'     // 空值兜底
def y = obj?.name             // 安全访问
def z = list*.name            // 集合属性映射
```

## 三十七、注释

单行注释：

```groovy
// 这是单行注释
```

多行注释：

```groovy
/*
 * 这是多行注释
 */
```

## 三十八、建议记住的顺序

学习 Groovy 时，按以下顺序掌握：

1. 变量
2. 字符串
3. if/else
4. 循环
5. 列表和 Map
6. 正则表达式
7. JSON 解析
8. 日志
9. JMeter 内置对象
