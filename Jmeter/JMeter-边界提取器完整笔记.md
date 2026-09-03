# JMeter 边界提取器完整笔记

> 更新时间：2026-09-03
> 适用版本：Apache JMeter 5.6.3

## 一、边界提取器是什么

边界提取器是 JMeter 的后置处理器，用于：

```text
从响应中提取左右边界之间的内容
```

它不需要写正则表达式，只需要知道：

```text
左边开始位置
右边结束位置
```

例如：

```text
X-Csrf-Token=c95ea213...; Path=/
```

左边界：

```text
X-Csrf-Token=
```

右边界：

```text
;
```

提取结果：

```text
c95ea213...
```

## 二、什么时候优先使用边界提取器

适合格式固定、边界清晰的内容。

例如：

```text
Set-Cookie: X-Csrf-Token=abc; Path=/
<input id="token" value="abc">
{"token":"abc"}
```

不适合：

```text
格式经常变化
边界不固定
需要复杂条件判断
```

## 三、添加方法

在 HTTP 请求上右键：

```text
添加
→ 后置处理器
→ 边界提取器
```

必须放在对应请求下面：

```text
01 获取公钥与令牌
├── 边界提取器：csrfToken
└── Debug PostProcessor
```

## 四、中文界面字段说明

## 1. 名称

组件名称，例如：

```text
X-Csrf-Token提取为csrfToken
```

## 2. 注释

写备注，不影响执行。

## 3. 作用域 / Apply to

| 选项 | 含义 |
|---|---|
| 主取样器 only | 只处理主请求 |
| 子取样器 only | 只处理子请求 |
| 主取样器和子取样器 | 两者都处理 |
| JMeter 变量名 | 处理指定的变量 |

本项目选择：

```text
主取样器 only
```

## 4. 要检查的响应字段

用于选择从哪里提取。

| 选项 | 含义 |
|---|---|
| 主体 | 响应正文 |
| Body（unescaped） | 响应正文反义字符 |
| Body as a Document | 文档正文 |
| 信息头 | 响应头 |
| Request Headers | 请求头 |
| URL | 请求 URL |
| 响应代码 | HTTP 状态码 |
| 响应信息 | 状态消息 |

本项目选择：

```text
信息头 / Response Headers
```

不要选：

```text
Request Headers
```

## 5. 引用名称

保存变量的名称。

```text
csrfToken
```

后续使用：

```text
${csrfToken}
```

## 6. 左边界

提取内容的开始位置。

例如：

```text
X-Csrf-Token=
```

## 7. 右边界

提取内容的结束位置。

例如：

```text
;
```

如果右边界为空，JMeter 会从左边开始一直提取到最后。

所以对于：

```text
X-Csrf-Token=c95ea...; Path=/
```

必须填写：

```text
;
```

否则会提取到：

```text
c95ea...; Path=/
```

## 8. 匹配数字

| 值 | 含义 |
|---|---|
| `1` | 取第 1 个匹配 |
| `2` | 取第 2 个匹配 |
| `0` | 随机取一个 |
| `-1` | 取所有匹配，通常配合 ForEach 控制器 |

## 9. 缺省值

如果匹配不到，使用缺省值。

推荐：

```text
NOT_FOUND
```

## 10. 使用空默认值

勾选后，匹配不到时变量设置为空字符串。

## 五、当前项目准确配置

## 提取 X-Csrf-Token

| 字段 | 值 |
|---|---|
| 引用名称 | `csrfToken` |
| 作用域 | 主取样器 only |
| 要检查的响应字段 | 信息头 / Response Headers |
| 左边界 | `X-Csrf-Token=` |
| 右边界 | `;` |
| 匹配数字 | `1` |
| 缺省值 | `NOT_FOUND` |

## 提取 X-Rsa-Token

由于 X-Rsa-Token 的右边界是换行符，边界提取器填写换行比较麻烦。

如果使用边界提取器，可以尝试：

| 字段 | 值 |
|---|---|
| 引用名称 | `rsaPublicKey` |
| 要检查的响应字段 | 信息头 / Response Headers |
| 左边界 | `X-Rsa-Token: ` |
| 右边界 | `${__char(10)}` |
| 匹配数字 | `1` |
| 缺省值 | `NOT_FOUND` |

如果提取结果不稳定，建议 X-Rsa-Token 使用正则表达式提取器或 JSR223。

## 六、边界提取器工作原理

假设文本：

```text
abc|DEF|ghi
```

左边界：

```text
abc|
```

右边界：

```text
|
```

提取结果：

```text
DEF
```

过程：

```text
找到左边界 abc|
从 abc| 后面开始
找到右边界 |
取左右边界之间的内容
```

## 七、多个匹配

文本：

```text
id=1; name=a
id=2; name=b
id=3; name=c
```

左边界：

```text
id=
```

右边界：

```text
;
```

匹配结果：

```text
1
2
3
```

匹配数字：

```text
1 → 1
2 → 2
3 → 3
```

## 八、负匹配数字的使用

匹配数字 `-1` 会生成：

```text
变量名_1
变量名_2
变量名_3
变量名_matchNr
```

例如：

```text
id_1 = 1
id_2 = 2
id_3 = 3
id_matchNr = 3
```

通常配合：

```text
ForEach 控制器
```

使用：

```text
${id_1}
${id_2}
```

## 九、完整实战：登录凭证提取

响应头：

```text
Set-Cookie: X-Csrf-Token=c95ea...; Path=/
```

配置：

```text
01 获取公钥与令牌
└── 边界提取器：csrfToken
    ├── 要检查的响应字段：信息头
    ├── 左边界：X-Csrf-Token=
    ├── 右边界：;
    ├── 匹配数字：1
    └── 缺省值：NOT_FOUND
```

运行后：

```text
csrfToken = c95ea...
```

后续请求：

```text
X-Csrf-Token: ${csrfToken}
```

## 十、调试方法

1. 运行测试
2. 打开 `查看结果树`
3. 选择对应请求
4. 查看 `Response Headers`
5. 添加 `Debug PostProcessor`
6. 查看变量

预期：

```text
csrfToken = c95ea...
```

## 十一、常见问题

## 1. 变量为 NOT_FOUND

检查：

- 字段是否选择了响应头
- 左右边界是否正确
- 是否有多余空格
- 匹配数字是否正确

## 2. 结果包含 ; Path=/

检查：

```text
右边界是否填写了 ;
```

## 3. 结果包含换行或完整响应头

检查：

```text
右边界是否为空
```

## 4. 大小写问题

边界提取器按原始文本匹配。

如果响应头大小写变化，最好改用正则表达式提取器，例如：

```text
(?i)X-Csrf-Token=([^;]+)
```

## 十二、边界提取器和其他提取器对比

| 方式 | 优点 | 缺点 |
|---|---|---|
| 边界提取器 | 简单，不需要正则 | 边界不固定时不好用 |
| 正则表达式提取器 | 灵活 | 会生成 _g 变量 |
| JSON 提取器 | 适合 JSON | 只能处理 JSON |
| JSR223 | 最灵活 | 需要写脚本 |

## 十三、练习

### 练习 1

响应：

```text
token=abc123; type=user
```

提取 `abc123`。

答案：

```text
左边界：token=
右边界：;
```

### 练习 2

响应：

```html
<input name="csrf" value="xyz789">
```

提取 `xyz789`。

答案：

```text
左边界：value="
右边界："
```

### 练习 3

响应头：

```text
Set-Cookie: SESSION=abcd1234; Path=/
```

提取 `abcd1234`。

答案：

```text
左边界：SESSION=
右边界：;
```

## 十四、学习结论

边界提取器适合：

```text
格式固定
左右边界清晰
不需要复杂逻辑
```

遇到复杂场景时，可以改用：

```text
正则表达式提取器
JSON 提取器
JSR223
```
