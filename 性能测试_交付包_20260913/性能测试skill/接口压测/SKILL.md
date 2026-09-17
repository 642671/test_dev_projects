---
name: 接口压测
description: 接口/服务压测执行：k6 与 JMeter 脚本生成、执行、结果转换（k6 summary JSON / JMeter .jtl）与工具自举安装。当用户提到：接口压测、压这个接口、压测脚本、k6、JMeter、Locust、并发压测、接口性能、压测执行、jtl、k6 summary、压测工具怎么装 时使用。
---

# 接口压测

> **先说最重要的一句：本技能的报告链路不依赖任何压测工具。**
> `perf_report.py` / `perf_collect.py` / `perf_analyze.py` **全是纯标准库**——
> 手上有 k6 summary JSON、JMeter `.jtl`、或监控 CSV 里的**任意一种**，就能出双格式报告。
> 压测器只负责**产生数据**，本技能负责**把数据变成结论**。
> 选型表见 `references/tools-matrix.md`。

---

## 一、什么时候才真需要压测器

| 要做什么 | 需要压测器吗 |
|---|---|
| 出监控报告（应用使用 vs 空闲） | ❌ 不需要，`采集监控` 那条线就够了 |
| 出性能报告（空闲 vs 负载，负载由人工任务产生） | ❌ 不需要 |
| **压某个 HTTP / TCP 接口，测 TPS / P95** | ✅ 需要 |
| 阶梯压测找拐点 | ✅ 需要 |

> ⚠️ **没有必要为了「跑通报告」去装 k6 / JMeter。** 装不上只影响能不能**现场灌压力**，
> 不影响已经拿到的数据能不能出报告。

---

## 二、装（Windows，可直接复制）

**本机现状（2026-09-13 实测）**：`k6` ❌ 未装、`jmeter` ❌ 未装、`locust` ❌ 未装，
`java` ✅ 有（Temurin `17.0.19`，位于 `C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot`）。

```powershell
# k6（单二进制，推荐）
winget install k6.k6                  # 或 choco install k6
# 无包管理器：github.com/grafana/k6/releases 下 win 版 zip，解压后把目录加进 PATH
k6 version                            # 验证

# Apache JMeter（本机 JDK 17 已就位，满足前置）
winget install Apache.JMeter          # 或 choco install jmeter
# 手动方式：下 apache-jmeter-5.6.3.zip → 解压到 C:\perf-tools\jmeter → bin 加进 PATH
jmeter --version                      # 验证

# Locust（Python 栈）
python -m venv .venv                  # 先建虚拟环境，避开 PEP 668 受管环境
.venv\Scripts\Activate.ps1
pip install locust
locust --version                      # 验证
```

> ⚠️ **不要在 NAS 这类资源受限设备上跑重量级图形化工具**（JMeter GUI 尤其）。
> 要压仅绑 `127.0.0.1` 的端口时，**k6 是上机压的首选**（单二进制，Linux / ARM 上也能跑）。

---

## 三、`perf_run.py` 用法

```bash
# 0) 环境自检 + 自举：缺什么打印什么，能自动装的自己装
python scripts/perf_run.py --check-env

# 1) 由场景描述生成压测脚本（k6 / JMeter 两种目标）
python scripts/perf_run.py --gen --tool k6 --url http://<目标>:8023/api/x \
  --vus 50 --duration 5m --out k6_script.js

# 2) 执行（生成 + 跑 + 出结果，一条龙）
python scripts/perf_run.py --tool k6 --url http://<目标>:8023/api/x \
  --vus 50 --duration 5m --out-dir ./perf-out

# 3) 阶梯压测：多个并发档位各跑一轮，为找拐点准备数据
python scripts/perf_run.py --tool k6 --url http://<目标>:8023/api/x \
  --stages 10,50,100,200 --duration 5m --out-dir ./perf-out

# 4) 上机压（在 NAS 本机跑压测器，绕开 127.0.0.1 不可达的问题）
python scripts/perf_run.py --tool k6 --remote --url http://127.0.0.1:18581/api \
  --vus 50 --duration 5m --out-dir ./perf-out
```

| 参数 | 说明 |
|---|---|
| `--check-env` | 自检 + 自举：**只查不跑**，先看缺什么 |
| `--gen` | 只生成脚本不执行（想手工改脚本时用） |
| `--tool k6\|jmeter\|locust` | 目标工具 |
| `--url` / `--vus` / `--duration` | 压测目标与负载模型 |
| `--stages a,b,c` | 阶梯档位（逗号分隔） |
| `--out-dir` | 结果与脚本落点 |
| `--remote` | 经 SSH 到被测机执行（压仅本机端口用） |

> ⚠️ 压测**前**先 `ss -lntp` 确认端口与绑定范围（见 `references/app-ports.md`）：
> **仅绑 `127.0.0.1` 的端口外部压不到**，要么 `--remote` 上机压，要么走 SSH 隧道做小流量验证。

---

## 四、结果转换（报告链路怎么接上）

**不需要中间格式**——报告脚本直接吃压测工具的产物：

```bash
# k6 --summary-export 的 JSON
python scripts/perf_report.py --kind perf --from-k6 k6_summary.json --md r.md --html r.html

# JMeter .jtl / .csv
python scripts/perf_report.py --kind perf --from-jmeter result.jtl --md r.md --html r.html
```

| 坑 | 现象 | 怎么处理 |
|---|---|---|
| **k6 的 `p(95)` 有两种形态** | 有时在 `metrics.http_req_duration["p(95)"]` 直取，有时只在 `metrics.http_req_duration.thresholds` 里出现 | 脚本**先直取、取不到再下钻 thresholds**；自己写解析时两条都要试 |
| **JMeter `.jtl` 带 BOM** | 首列名变成 `\ufefftimeStamp`，按 `timeStamp` 取列**取不到** | **必须 `encoding="utf-8-sig"`** 打开，普通 `utf-8` 会留 BOM |
| k6 字段名与统计口径不同 | k6 给的是 `avg` / `p(95)` / `p(99)` / `max`，不是本技能的 `p95_rt` | 交给 `--from-k6` 转换，**别手工对字段** |

> ⚠️ **`.jtl` 的 BOM 坑**：`open(path, encoding="utf-8")` 读出来的第一列名是
> `\ufefftimeStamp`，看起来一模一样但 `==` 不相等。**一律用 `utf-8-sig`。**
>
> ⚠️ k6 的 `--summary-export` 至少要 `--summary-export out.json` 才有文件；
> 只在终端打印 summary 是拿不到 JSON 的。

---

## 五、接口压测该关注什么

| 指标 | 口径 | 参考阈值 |
|---|---|---|
| **TPS / QPS** | 每秒成功处理的完整事务 / 请求数 | 无固定值；期望**目标并发下曲线平稳** |
| **P95 / P99 响应时间** | 95% / 99% 请求在此时间内完成 | **核心操作 ≤200ms**；页面加载 ≤3s；只读查询 ≤10ms（**业务口径优先**） |
| **错误率** | 失败请求 ÷ 总请求 | **≤0.2%**（成功率 ≥99.5%） |
| **并发用户数** | 同一时刻与系统交互的用户数 | 在线用户数的 **8%~12%** 可作估算 |

**与服务端资源指标的关联分析**（压测数据只有配上资源监控才能定位瓶颈）：

| 压测侧看到的 | 同时看服务端 | 结论方向 |
|---|---|---|
| TPS 上不去 + 响应时间变长 | CPU >80%、`%iowait` 低 | **CPU 计算瓶颈** |
| TPS 上不去 + 响应时间变长 | `%iowait` / `%util` / `await` 高 | **磁盘 I/O 瓶颈** |
| TPS 上不去 + 响应时间变长 | 网络贴近 119 MB/s（千兆线速） | **网卡瓶颈** |
| 响应时间变长但 TPS 平稳、资源均不高 | 资源都正常 | **应用逻辑 / 慢 SQL / 外部依赖**（时间花在「等」上） |
| 错误率非零 | — | 先分三类：**超时 / 连接拒绝 / 5xx**，根因完全不同 |

```bash
# 压测结果 + 服务端监控一起出报告：分别转 stats.json，再用 summary 体裁合并
python scripts/perf_analyze.py --in "perf-out/host_load.csv" --app Server --tag 负载 --out load.json
python scripts/perf_report.py --kind summary -i k6_stats.json -i load.json \
  --labels 接口侧,服务端资源 --md r.md --html r.html
```

> ⚠️ **服务端资源指标是整机口径**（CPU / 内存 / 磁盘 / 网络）或**进程树口径**，
> 与压测侧的 TPS 是**两条独立数据流**，必须按**同一时间线对齐**才能做关联分析——
> 不要按精确时间戳 JOIN（见 `references/methodology-pitfalls.md` 第 11 条）。

---

## 六、选型

| 场景 | 选谁 |
|---|---|
| 脚本要进 CI/CD、团队写 JS、压 API | **k6**（本工作区推荐轻量首选） |
| 需要图形化编排、协议多、复用现成 `.jmx` | **JMeter**（本机 JDK 17 已就位） |
| 团队是 Python 栈、要与已有 Python 代码打通 | **Locust** |
| 需要大规模并发又不想自建集群 | 云 PTS（**但压不到仅绑 127.0.0.1 的应用端口**） |

完整选型表与本机现状见 `references/tools-matrix.md`。

## 相关文档

- `references/tools-matrix.md` —— 压测平台选型、本机现状、安装指引
- `references/app-ports.md` —— 压哪个口、能不能从外部压（**选型前先看它**）
- `references/metrics.md` —— TPS / QPS / P95 / 错误率的口径与阈值
- `references/methodology-pitfalls.md` —— 负载真实性验证、时间对齐等坑
- `<场景设计>/SKILL.md` —— 并发档位、窗口长度、防陷阱前置清单
- `<报告生成>/SKILL.md` —— `--from-k6` / `--from-jmeter` 与三种体裁
- `<分析定位>/SKILL.md` —— 拿到 TPS 曲线后怎么定位瓶颈
