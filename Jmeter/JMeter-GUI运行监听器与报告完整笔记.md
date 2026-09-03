# JMeter GUI 运行、监听器、命令行与报告完整笔记

> 更新时间：2026-09-03
> 适用版本：Apache JMeter 5.6.3

## 一、JMeter 两种运行方式

JMeter 有两种运行方式：

```text
1. GUI 图形界面运行
2. 命令行 Non-GUI 运行
```

用途：

| 方式 | 用途 |
|---|---|
| GUI | 编写测试计划、调试请求、查看结果 |
| Non-GUI | 正式压测、自动化、CI、生成报告 |

## 二、GUI 基本操作

## 1. 启动

本机 JMeter 路径：

```text
D:\self_install\apache-jmeter-5.6.3\apache-jmeter-5.6.3\bin\jmeter.bat
```

## 2. 打开 JMX

```text
文件 → 打开
```

选择：

```text
D:\test_dev_projects\Jmeter\TNAS存储管理接口测试计划.jmx
```

## 3. 运行

点击顶部绿色启动按钮。

## 4. 停止

点击红色停止按钮。

## 5. 清空结果

点击清空按钮。

## 三、GUI 常用的监听器

监听器用于查看运行结果。

## 1. 查看结果树

添加：

```text
右键线程组
→ 添加
→ 监听器
→ 查看结果树
```

可以查看：

- 请求是否成功
- 请求头
- 请求体
- 响应头
- 响应体
- 响应时间
- 错误原因
- Debug PostProcessor 变量

建议：调试时使用，正式压测时关闭。

## 2. 汇总报告

添加：

```text
右键线程组
→ 添加
→ 监听器
→ 汇总报告
```

可以查看：

- 请求数
- 平均响应时间
- 最小时间
- 最大时间
- 90%/95%/99% 响应时间
- 错误率
- 吞吐量
- KB/sec

## 3. 聚合报告

添加：

```text
右键线程组
→ 添加
→ 监听器
→ 聚合报告
```

统计信息更详细。

## 4. 简单数据写入器

添加：

```text
右键线程组
→ 添加
→ 监听器
→ 简单数据写入器
```

用于保存结果到 `.jtl` 文件。

## 5. 后端监听器

添加：

```text
右键线程组
→ 添加
→ 监听器
→ 后端监听器
```

可以把结果发送到 InfluxDB、Graphite 等。

## 四、常用性能指标

| 指标 | 含义 |
|---|---|
| Samples | 请求总数 |
| Errors | 错误数 |
| Error % | 错误率 |
| Average | 平均响应时间 |
| Min | 最小响应时间 |
| Max | 最大响应时间 |
| Median | 中位数响应时间 |
| 90% / 95% / 99% | 百分位响应时间 |
| Throughput | 每秒请求数 |
| KB/sec | 每秒传输数据量 |

不要只看平均值，重要看：

```text
90%
95%
99%
错误率
吞吐量
```

## 五、命令行运行方式

## 1. 基本命令

```powershell
cd D:\self_install\apache-jmeter-5.6.3\apache-jmeter-5.6.3\bin

.\jmeter.bat -n `
  -t D:\test_dev_projects\Jmeter\TNAS存储管理接口测试计划.jmx `
  -l D:\test_dev_projects\Jmeter\result.jtl `
  -e `
  -o D:\test_dev_projects\Jmeter\report
```

## 2. 参数说明

| 参数 | 含义 |
|---|---|
| `-n` | Non-GUI 模式 |
| `-t` | JMX 测试计划文件 |
| `-l` | 结果文件，JTL |
| `-e` | 生成 HTML 报告 |
| `-o` | HTML 报告输出目录 |
| `-J` | 传入 JMeter 属性 |
| `-q` | 加载外部 properties 文件 |
| `-r` | 使用远程所有服务器 |
| `-R` | 指定远程服务器 |
| `-h` | 帮助 |

## 3. 传入属性

```powershell
.\jmeter.bat -n `
  -t D:\test_dev_projects\Jmeter\TNAS存储管理接口测试计划.jmx `
  -Jserver_ip=10.18.15.135 `
  -Jserver_port=8181 `
  -l result.jtl `
  -e `
  -o report
```

测试计划中使用：

```text
${__P(server_ip)}
${__P(server_port)}
```

## 4. 加载属性文件

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
.\jmeter.bat -n `
  -t D:\test_dev_projects\Jmeter\TNAS存储管理接口测试计划.jmx `
  -q D:\test_dev_projects\Jmeter\test.properties `
  -l result.jtl `
  -e `
  -o report
```

## 六、HTML 报告

如果使用：

```powershell
-e
-o D:\test_dev_projects\Jmeter\report
```

完成后打开：

```text
D:\test_dev_projects\Jmeter\report\index.html
```

报告中可以查看：

- 请求统计
- 响应时间分布
- 错误率
- 吞吐量
- 90%/95%/99% 响应时间
- 趋势图

注意：

```text
-o 目录必须不存在或为空
```

## 七、使用示例：只生成 JTL

```powershell
.\jmeter.bat -n `
  -t D:\test_dev_projects\Jmeter\TNAS存储管理接口测试计划.jmx `
  -l D:\test_dev_projects\Jmeter\result.jtl
```

## 八、使用示例：生成 HTML 报告

```powershell
.\jmeter.bat -n `
  -t D:\test_dev_projects\Jmeter\TNAS存储管理接口测试计划.jmx `
  -l D:\test_dev_projects\Jmeter\result.jtl `
  -e `
  -o D:\test_dev_projects\Jmeter\report
```

## 九、使用示例：循环 10 次

JMX 的线程组中设置：

```text
线程数：1
Ramp-Up：1
循环次数：10
```

或者命令行：

```powershell
.\jmeter.bat -n `
  -t testplan.jmx `
  -Jloops=10 `
  -l result.jtl `
  -e `
  -o report
```

然后在 JMX 线程组的循环次数中使用：

```text
${__P(loops,1)}
```

## 十、分布式测试

适合单机无法产生足够并发的情况。

结构：

```text
Master
├── Slave 1
├── Slave 2
└── Slave 3
```

Slave 启动：

```text
jmeter-server.bat
```

Master 运行：

```powershell
.\jmeter.bat -n -t testplan.jmx -r -l result.jtl -e -o report
```

或指定：

```powershell
.\jmeter.bat -n -t testplan.jmx -R 192.168.1.10,192.168.1.11 -l result.jtl -e -o report
```

## 十一、GUI 和 Non-GUI 如何选择

| 场景 | 方式 |
|---|---|
| 编写测试计划 | GUI |
| 调试单个请求 | GUI |
| 查看响应 | GUI |
| 正式压测 | Non-GUI |
| 自动化测试 | Non-GUI |
| CI/CD | Non-GUI |
| 生成报告 | Non-GUI + -e -o |

## 十二、GUI 压测的问题

GUI 运行会占用大量内存和 CPU，尤其是：

```text
查看结果树
```

所以正式压测：

```text
关闭查看结果树
使用命令行运行
使用 HTML 报告
```

## 十三、常见问题

## 1. 报告目录已存在

错误：

```text
Report directory already exists
```

解决：

```text
删除旧目录
或使用新的目录名
```

## 2. JTL 文件已存在

部分情况下 JMeter 会要求文件不存在。

解决：

```text
删除旧 JTL
或修改文件名
```

## 3. 中文乱码

在 `bin/jmeter.properties` 中设置：

```text
sampleresult.default.encoding=UTF-8
```

## 4. GUI 看不到请求结果

检查：

- 是否添加了监听器
- 是否点击了运行
- 是否选择了正确的请求

## 5. 命令行没有生成报告

检查：

- 是否加了 `-e`
- 是否加了 `-o`
- `-o` 目录是否为空

## 十四、推荐命令行模板

```powershell
.\jmeter.bat -n `
  -t D:\test_dev_projects\Jmeter\TNAS存储管理接口测试计划.jmx `
  -Jserver_ip=10.18.15.135 `
  -Jserver_port=8181 `
  -l D:\test_dev_projects\Jmeter\result.jtl `
  -e `
  -o D:\test_dev_projects\Jmeter\report
```

## 十五、学习结论

调试时用：

```text
GUI + 查看结果树 + Debug PostProcessor
```

执行时用：

```text
命令行 + JTL + HTML 报告
```

以后要自动化，只需要把命令行命令放到：

```text
Jenkins
GitLab CI
GitHub Actions
定时任务
```
