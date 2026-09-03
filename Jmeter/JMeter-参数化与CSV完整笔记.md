# JMeter 参数化与 CSV 完整笔记

> 更新时间：2026-09-03
> 适用版本：Apache JMeter 5.6.3

## 一、什么是参数化

参数化就是：

```text
把固定的值变成变量
让同一份测试计划可以使用不同数据
```

例如：

```text
不参数化：
http://10.18.15.135:8181/api/login

参数化：
http://${server_ip}:${server_port}/api/login
```

## 二、JMeter 中常见的参数化方式

| 方式 | 适合场景 |
|---|---|
| 用户定义的变量 | 固定配置 |
| CSV 数据文件 | 多组测试数据 |
| 函数 | 随机数、时间、UUID |
| 属性 | 多线程共享、命令行传入 |
| JSR223 | 动态计算 |

## 三、用户定义的变量

添加位置：

```text
右键测试计划或线程组
→ 添加
→ 配置元件
→ 用户定义的变量
```

例如：

```text
protocol = http
server_ip = 10.18.15.135
server_port = 8181
username = admin
password = 123456
```

使用：

```text
${server_ip}
${server_port}
${username}
```

特点：

- 会保存到 JMX 文件中
- 适合固定配置
- 不适合动态提取结果

## 四、CSV 数据文件

适合：

```text
多个用户
多组账号
多组订单编号
大数据量测试
```

## 1. CSV 文件格式

创建文件：

```text
D:\test_dev_projects\Jmeter\testdata.csv
```

内容：

```csv
username,password,userId
user1,123456,1001
user2,654321,1002
user3,999999,1003
```

第一行是变量名。

## 2. 添加 CSV 数据文件设置

```text
右键线程组
→ 添加
→ 配置元件
→ CSV 数据文件设置
```

## 3. 中文字段说明

| 字段 | 含义 |
|---|---|
| 文件名 | CSV 文件绝对路径 |
| 文件编码 | UTF-8 |
| 变量名称 | 逗号分隔的变量名，例如 username,password |
| 分隔符 | 默认逗号 |
| 是否循环 | 文件结束后是否重新开始 |
| 遇到文件结束 | Recycle、Stop Thread 等 |
| 共享模式 | 所有线程、当前线程、当前线程组 |

## 4. 变量名称对应

CSV：

```csv
username,password,userId
user1,123456,1001
```

变量名：

```text
username,password,userId
```

请求中：

```text
${username}
${password}
${userId}
```

## 5. 分隔符

如果 CSV 使用分号：

```csv
username;password
user1;123456
```

配置：

```text
分隔符 = ;
```

## 6. 文件结束处理

如果 CSV 只有 3 行，但线程循环 10 次：

- 选择 `Recycle on EOF`：继续从第 1 行开始
- 选择 `Stop thread on EOF`：线程结束

## 7. 共享模式

| 模式 | 含义 |
|---|---|
| All threads | 所有线程共享同一份文件 |
| Current thread group | 当前线程组共享 |
| Current thread | 每个线程独立读取 |

如果需要每个用户使用不同账号，通常：

```text
Current thread
```

## 五、JMeter 常用函数

在需要使用函数的地方，可以点击：

```text
函数助手对话框
```

然后选择函数。

## 1. __Random

生成随机数：

```text
${__Random(1000,9999)}
```

生成 1000 到 9999 之间的随机数。

## 2. __time

生成时间：

```text
${__time(/yyyy-MM-dd HH:mm:ss)}
```

## 3. __UUID

生成 UUID：

```text
${__UUID}
```

## 4. __counter

计数器：

```text
${__counter(TRUE)}
```

## 5. __P

读取 JMeter 属性：

```text
${__P(server_ip,10.18.15.135)}
```

第一个参数是属性名。

第二个参数是默认值。

## 6. __property

读取属性：

```text
${__property(server_ip)}
```

## 7. __V

动态变量名：

```text
${__V(userId_${index})}
```

如果：

```text
index = 1
userId_1 = 1001
```

结果：

```text
1001
```

## 8. __eval

计算表达式：

```text
${__eval(${username})}
```

## 六、命令行传入参数

测试计划中使用：

```text
${__P(server_ip)}
${__P(server_port)}
${__P(username)}
```

命令行运行：

```powershell
.\jmeter.bat -n `
  -t D:\test_dev_projects\Jmeter\TNAS存储管理接口测试计划.jmx `
  -Jserver_ip=10.18.15.135 `
  -Jserver_port=8181 `
  -Jusername=admin `
  -l result.jtl `
  -e `
  -o report
```

## 七、属性文件

创建：

```text
D:\test_dev_projects\Jmeter\test.properties
```

内容：

```text
server_ip=10.18.15.135
server_port=8181
username=admin
```

运行：

```powershell
.\jmeter.bat -n -t testplan.jmx -q D:\test_dev_projects\Jmeter\test.properties
```

`-q` 表示加载外部属性文件。

## 八、JMeter 变量和属性区别

| 类型 | 作用范围 | 是否保存在 JMX | 是否跨线程 |
|---|---|---|---|
| JMeter 变量 | 当前线程 | 不保存 | 否 |
| 用户定义的变量 | 测试计划 | 保存 | 线程内使用 |
| JMeter 属性 | 整个 JVM | 不自动保存 | 是 |
| CSV 变量 | 当前线程当前行 | 不保存 | 每行独立 |

## 九、完整参数化流程

### 1. 定义固定变量

```text
用户定义的变量：
protocol = http
server_ip = 10.18.15.135
server_port = 8181
```

### 2. 添加 CSV

```text
文件名：D:\test_dev_projects\Jmeter\testdata.csv
变量名称：username,password,userId
```

### 3. HTTP 请求中使用

URL：

```text
/api/user/${userId}
```

请求体：

```json
{
  "username": "${username}",
  "password": "${password}"
}
```

### 4. 运行

每次执行读取 CSV 的一行数据。

## 十、参数化时常见问题

## 1. 变量没有被替换

检查：

- 变量名是否拼写正确
- 是否使用 `${变量名}`
- CSV 变量名和列名是否一致

## 2. 中文乱码

CSV 编码改为：

```text
UTF-8
```

## 3. 数据只用了第一行

检查：

- CSV 文件是否有多行
- 线程循环次数是否足够
- 共享模式是否正确

## 4. 变量为空

检查：

- CSV 文件路径是否正确
- CSV 是否为空
- 变量名是否包含空格

## 5. 分隔符不正确

如果 CSV 使用：

```text
;
```

但 JMeter 配置为：

```text
,
```

就会失败。

## 十一、练习

### 练习 1

创建 CSV：

```csv
username,password
user1,123456
user2,654321
```

在请求体中使用变量。

答案：

```json
{
  "username": "${username}",
  "password": "${password}"
}
```

### 练习 2

生成 1000 到 9999 的随机数。

答案：

```text
${__Random(1000,9999)}
```

### 练习 3

生成当前时间。

答案：

```text
${__time(/yyyy-MM-dd HH:mm:ss)}
```

### 练习 4

从命令行传入 server_ip。

答案：

```powershell
.\jmeter.bat -n -t plan.jmx -Jserver_ip=10.18.15.135
```

测试计划中使用：

```text
${__P(server_ip)}
```

## 十二、学习结论

参数化推荐组合：

```text
固定配置 → 用户定义的变量
多组数据 → CSV 数据文件
动态数据 → 函数
环境切换 → 命令行参数 / 属性文件
复杂逻辑 → JSR223
```
