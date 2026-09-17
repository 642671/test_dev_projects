# 性能测试交付包

> 生成日期：**2026-09-13**
> 内容：一套通用**性能测试 skill** + 用它在 **MultimediaServer 3.2.106** 上的完整实测报告与原始数据
> 用途：供测试工程师后续写**系统功能**和**应用**的性能测试时参考

---

## 目录

```
性能测试_交付包_20260913/
├── README.md                     ← 本文件（先看这里）
├── 性能测试需要考虑的点.md         ← ⭐ 一页纸实操清单，建议最先看
│
├── 性能测试skill/                 ← 技能本体（目录形态，可直接放进 .claude/skills/）
│   ├── SKILL.md                  ← 总入口：两条业务线 + 三种报告体裁 + 六阶段生命周期
│   ├── 指标口径/SKILL.md           ┐
│   ├── 场景设计/SKILL.md           │
│   ├── 采集监控/SKILL.md           │
│   ├── 生命周期/SKILL.md           ├ 8 个子技能
│   ├── 泄漏检测/SKILL.md           │
│   ├── 分析定位/SKILL.md           │
│   ├── 报告生成/SKILL.md           │
│   ├── 接口压测/SKILL.md           ┘
│   ├── scripts/                  ← 7 个脚本（纯 Python 标准库，拷走就能跑）
│   │   ├── perf_collect.py       采集（进程树 / 整机，支持 SSH 远程）
│   │   ├── perf_analyze.py       CSV → 统计 JSON
│   │   ├── perf_report.py        三体裁 → md + 自包含 html
│   │   ├── perf_lifecycle.py     六阶段编排
│   │   ├── perf_run.py           k6/JMeter 执行与自举
│   │   ├── sshcommon.py          SSH 连接（SFTP 不可用时自动回退 base64）
│   │   └── selftest.py           离线自检（38 项）
│   ├── references/               ← 11 份文档
│   │   ├── metrics.md                    指标全表 + 参考阈值
│   │   ├── memory-accounting.md          内存五件套口径详解
│   │   ├── methodology-pitfalls.md       ⭐ 二十条口径与方法学陷阱（动手前必读）
│   │   ├── analysis-playbook.md          瓶颈定位决策树
│   │   ├── app-lifecycle.md              六阶段生命周期手册
│   │   ├── report-skeletons.md           三种报告体裁的章节骨架
│   │   ├── results-schema.md             统计 JSON 字段契约
│   │   ├── tos-feature-process-map.md    ⭐ TOS 功能 ↔ 进程对照表
│   │   ├── app-ports.md                  TOS 应用端口对照
│   │   ├── tools-matrix.md               压测平台与工具选型
│   │   └── examples/                     4 份样例数据
│   └── templates/                ← 6 份报告模板（3 体裁 × md/html）
│
├── 测试报告/                      ← 本次实测报告（每份都有 .md + 自包含 .html）
│   ├── 报告3_汇总报告_全阶段横向      ⭐ 主报告：瓶颈定位、放大倍数、建议、已撤回结论
│   ├── 报告1_性能报告_空载vs推流      五场景横向对比 + 趋势图
│   ├── 报告2_监控报告_安装后空载基线   安装后默认占用详版
│   └── README.md                    产出索引与核心结论
│
└── 原始采集数据/                  ← 可复核结论的原始数据
    ├── phases.json               各阶段起止时刻与口径说明
    ├── P0_pre_install_host.csv   P0 未安装态基线
    ├── P1_install_host.csv       P1 安装过程
    ├── P2_MultimediaServer.csv   P2 安装后空载
    ├── P3c_host_continuous.csv   整机连续采集
    ├── P4_app_fixed.csv          进程树连续采集（主力数据）
    └── *_stats.json              各阶段统计（报告的数据源）
```

---

## 先看哪几份

| 顺序 | 文件 | 为什么 |
|---|---|---|
| 1 | `性能测试需要考虑的点.md` | 一页纸清单，知道要测什么、注意什么 |
| 2 | `测试报告/报告3_汇总报告_全阶段横向.md` | 看一份完整报告长什么样、结论怎么给 |
| 3 | `性能测试skill/references/methodology-pitfalls.md` | **动手前必读**，二十条实测踩过的坑 |
| 4 | `性能测试skill/SKILL.md` | 要用技能时从这里进 |

HTML 版**双击即可打开**，单文件、断网可用、图表是内联 SVG。

---

## 怎么用这套 skill

1. **放进工作区**：把 `性能测试skill/` 整个目录复制到你的 Claude 项目 `.claude/skills/` 下（**目录名不要改**）
2. **重启会话**后技能生效
3. **直接说需求**，例如：「用性能测试 skill 测一下文件管理功能的性能」「测一下 XX 应用的性能」
4. **不用它也行**：`scripts/` 里的脚本是独立的，直接 `python perf_collect.py --app <进程名>` 就能跑

### 环境要求（**先跑自检，缺的会自动补**）

```bash
python "性能测试skill/scripts/selftest.py" --check-env     # 退出码 0 = 齐备
```

| 依赖 | 必须吗 | 缺了怎么办 |
|---|---|---|
| Python ≥ 3.8 | **必须** | 手动升级（解释器没法自举） |
| paramiko | **必须**（远程采集） | **自动 pip install**；失败给三选一命令 |
| k6 / JMeter / Locust | 可选（**仅**接口压测线） | 各自自举；不做接口压测就不需要 |
| sshpass | **禁用** | Windows 下会触发 PAM 锁账号；一律走 paramiko |

被测机侧：Linux + `python3`（TOS 自带）+ SSH 可达（默认 9222）。
**报告能力零依赖** —— 分析和报告脚本纯标准库，**没有 k6/JMeter 也照样出报告**。
关掉自动安装：`SKILL_NO_AUTO_INSTALL=1`。

---

## 本次实测核心结论（供参考报告写到什么程度）

| 问题 | 答案 |
|---|---|
| 装了这个应用多占多少 | PSS 31.5 MB / **private_Dirty 8.4 MB**（RSS 48 MB 里 40 MB 是可回收页缓存） |
| 推流吃性能吗 | **几乎不吃**。打满千兆时 CPU 仅 4% |
| **瓶颈在哪** | **不是带宽** —— 是 **MiniDLNA 的并发服务上限（约 50 路）**。80 路并发时前 50 路满速、第 51 路起衰减、第 67 路起拿不到数据，而此时只占千兆 **64%** |
| 能扛多少路 | 实测上限 ~50 路，建议留 30% 余量 → **≤35 路** |
| 有内存泄漏吗 | **无**。47.9 分钟长稳 private_Dirty 未升反降，单调度 0.018 |

---

## 使用须知（重要）

- **采集是只读的**：只读 `/proc/*`、`/proc/net/dev`、`/proc/diskstats`，**不在被测机装任何东西、不改任何配置**
- **安装 / 卸载 / 触发任务一律人工做**，脚本只负责监控与打点
- **报告里的阈值是业界参考值，不是业务验收标准** —— 具体项目要用 `--thresholds` 覆盖
- **采不到的指标不会填 0**：一律标 `❌未采集` / `⚠️口径降级`，报告固定带「采集覆盖度与未测项」章节

---

## 本次测试尚未覆盖的

| 项 | 原因 |
|---|---|
| **转码功能** | 应用界面宣称有，但本设备 `/etc/media.conf` 无转码配置、全程无 `ffmpeg` 进程。**要验需先在应用「兼容性」页开启后重测** |
| 前端指标 FCP/LCP/FID/CLS | 本次为服务端资源与推流性能测试 |
| 磁盘 `%util` / `await` | 设备未装 sysstat，已用 `/proc/diskstats` + 整机 `%iowait` 代替 |

---

*数据来源：10.18.15.179（x86-70）/ TOS 7 / 内核 6.12.63+ / 4 核 / 7684 MB*
