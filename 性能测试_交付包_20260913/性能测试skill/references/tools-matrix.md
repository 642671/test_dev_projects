# 压测平台与工具选型表

> **用途**：要开压之前,用它决定**用哪个工具/平台压**,以及**本机还缺什么、怎么装**。
> 数据源:`999-临时文件存放/性能测试skill/【性能测试】带你从头开始了解性能测试.pdf` 第 8 页选型表。
> 原表**右侧被裁**,缺的内容按各工具公开信息补齐(收费模式、许可证、补充说明为补齐项),已知信息保留原文口径。

---

## 一、选型主表

| 平台 | 类型 | 收费模式 | 核心特点 | 何时选它 |
|---|---|---|---|---|
| **阿里云 PTS** | 云平台 | 新用户 30 天内 5000 VUM 免费额度,超出后收费(按量计费 / VUM 预付费资源包) | 阿里巴巴双 11 压测核心工具;SaaS 化;JMeter 脚本;分布式压测;百万级并发;压力量真实度高 | 需要**大规模并发**又不想自己搭压测集群;已在用阿里云 |
| **腾讯云 PTS** | 云平台 | 基础版有免费试用,正式使用需收费 | 分布式压力测试服务;多协议;实时与采样日志;无缝对接 APM 监控 | 同上,但团队在腾讯云生态 |
| **Apache JMeter** | 开源工具 | 完全免费(Apache-2.0) | 纯 Java;HTTP/FTP/JDBC 等协议;图形化界面;插件生态丰富;可本地部署,也可结合云平台 | **默认首选**。需要图形化、协议多、脚本可复用;本机已有 JDK 17,装完即用 |
| **Micro Focus LoadRunner** | 商业软件 | 收费(按模块 / 用户订阅) | 功能全面;几乎支持所有协议;详细性能报告;企业级支持 | 复杂企业系统、协议冷门、且**有预算与厂商支持**时 |
| **k6** | 开源工具 | 开源版免费,企业版(k6 Cloud)收费 | 现代化负载测试;JavaScript 脚本;轻量高效;专注 API / 微服务;原生支持 CI/CD | 脚本要进 **CI/CD**、团队写 JS、压 API。**本工作区推荐轻量首选** |
| **Locust** | 开源工具 | 完全免费(MIT) | 基于 Python;脚本简单;支持高并发;分布式;易扩展 | 团队是 **Python 技术栈**;要把压测逻辑和已有 Python 代码打通 |
| **Gatling** | 开源工具 | 开源版免费,企业版(Gatling FrontLine)收费 | 基于 Scala;高性能;内置 DSL;HTML 报告详细;支持 HTTP/WebSocket | Web 应用压测且**看重开箱即用的报告**;团队能接受 Scala DSL |
| **loader.io** | 云平台 | 基础版免费(每次最多 10,000 连接,测试 1 分钟),高级版收费 | 无需安装,在线使用;专注 HTTP(S);支持分布式;报告简洁直观 | 快速试一下线上站点扛不扛得住;**免费额度限制很紧,做不了正式测试** |
| **Load Impact** | 云平台 | 免费版 100 用户并发、最长 5 分钟;付费版支持更高并发与更长时长 | 全球分布式节点;真实用户模拟;复杂场景;性能趋势分析 | 面向**全球化**用户的站点,需要多地真实节点 |
| **Postman** | API 工具 | 基础版免费,专业版 / 企业版收费 | 主要用于 API 调试;内置简单性能测试;集合运行 | **顺手的轻量冒烟**;已有 Postman 集合时零成本复用。不做正式压测 |
| **Artillery** | 开源工具 | 完全免费(MPL-2.0) | 现代化可扩展;支持 HTTP/WebSocket/Socket.io;插件丰富;配置简单 | 需要压 **WebSocket / Socket.io**;配置想尽量简单 |
| **WebLOAD** | 商业软件 | 收费(按许可证 / 订阅) | 企业级;多协议;可脚本开发;集成监控与分析 | 大型企业应用,需要厂商级支持与集成监控 |

---

## 二、按场景选型

**原文三条建议:**

1. **个人 / 小团队快速验证** → 优先 **JMeter**(完全免费)或 **k6**(轻量高效);或用**阿里云 PTS 免费额度**做云压测。
2. **企业级大规模压测** → **阿里云 PTS / 腾讯云 PTS**(SaaS 化、免运维、高并发),或 **LoadRunner**(复杂场景 + 全协议支持)。
3. **开发者友好 + CI/CD 集成** → 优先 **k6** 或 **Locust**,脚本语言与现代开发栈契合度高。

**叠加本工作区的实际约束(重要,会推翻上面的默认选择):**

- 被测对象是 **TOS NAS 上的应用**,而多数应用端口**仅绑 `127.0.0.1`**(见 `app-ports.md` 1.2 节)——**云端 PTS 类平台在这种场景下基本用不上**,它们需要一个外部可达的 URL。仅少数全网卡端口(8023、8991、18580、18790)能从外部压。
- 因此本工作区的主路线是「**本机开源工具 + 目标机上采监控 + 事后分析**」,而不是「云平台灌压力」。已有的实测报告全部是这条路线产出的(监控数据采自目标机 `10.18.15.103` 上的 `perf-monitor-analysis`)。
- 需要压仅本机端口的应用时:要么**上机压**(NAS 上直接跑压测器),要么走 SSH 隧道做小流量验证。**不要在 NAS 这类资源受限设备上跑重量级图形化工具**。
- 选型建议落到本工作区:**k6 做 API 压测首选**(单二进制、Linux/ARM 上也能跑,适合上机压),**Locust** 次之(Python 栈),**JMeter** 用于需要图形化编排或复用现成 `.jmx` 时。

---

## 三、本机现状(2026-09-13 实测)

| 工具 | 状态 | 实测结果 |
|---|---|---|
| `k6` | ❌ **未安装** | `k6 version` → `command not found` |
| `jmeter` | ❌ **未安装** | `jmeter --version` → `command not found` |
| `locust` | ❌ **未安装** | `python -c "import locust"` → `ModuleNotFoundError: No module named 'locust'` |
| `java` | ✅ **有** | `openjdk version "17.0.19" 2026-04-21` (Temurin),位于 `C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot` |
| `C:\perf-tools` | ❌ **不存在** | `ls C:\perf-tools` → `No such file or directory`(约定俗成的工具落地目录尚未创建) |

**结论:现在本机一个压测器都没有,想压必须先装(见第四节)。好消息是 JDK 17 已就位,JMeter 装完即可跑。**

---

## 四、安装指引(Windows,可直接复制)

**k6**(单二进制,推荐):

```powershell
winget install k6.k6                  # 推荐;或 choco install k6
# 无包管理器:到 github.com/grafana/k6/releases 下 win 版 zip,解压后把目录加进 PATH
k6 version                            # 验证
```

**Apache JMeter**(本机已有 JDK 17,满足前置):

```powershell
winget install Apache.JMeter          # 或 choco install jmeter
# 手动方式:下 apache-jmeter-5.6.3.zip → 解压到 C:\perf-tools\jmeter → 把 bin 加进 PATH
jmeter --version                      # 验证
```

**Locust**(Python 栈):

```powershell
python -m venv .venv                  # 建议先建虚拟环境,避开 PEP 668 受管环境
.venv\Scripts\Activate.ps1
pip install locust
locust --version                      # 验证
```

> **可借力**:工作区里 `测试技能包_V3.1/install_perf_tools.ps1` 是一份现成的压测工具自举脚本(同目录还有 `run_perf_from_har.ps1`、`codegen/run_jmeter_perf.py`)。
> 想省事可以直接读它、或按它的做法装。**本技能不 import 它**——不依赖、不耦合,只在需要装环境时作为参考指引。

---

## 五、本技能的报告能力不依赖任何压测工具

**明确一句:本技能的报告产出**与上面这些工具的安装与否**无关**。
只要手上有下列**任意一种**输入,就能出报告:

- JMeter 的 `.jtl`(CSV 结果文件)
- k6 的 **summary JSON**(`k6 run --summary-export`)
- 监控侧采下来的 **CSV / 文本**(`iostat`、`vmstat`、`/proc/meminfo`、`pidstat` 等)

即:**压测器负责产生数据,本技能负责把数据变成结论**。装不上工具不影响出报告,只影响能否现场灌压力。

---

## 相关文档

- `app-ports.md` —— TOS 应用端口对照表(压哪个口、监控哪个口;**选型前先看它**)
- `metrics.md` —— 指标口径与阈值总表
- `results-schema.md` —— `.jtl` / summary JSON / 监控 CSV 长什么样、怎么解析
- `report-skeletons.md` —— 报告骨架与章节模板
- `methodology-pitfalls.md` —— 口径与方法学陷阱(**做测试前必读**)
