---
name: 采集监控
description: 进程树与整机资源采集：按进程树（父+全部子孙）逐秒采集 CPU/PSS/RSS/private_Dirty/RssAnon/RssFile/swap/磁盘读写/网络，产出 CSV 并做质量检查（坏行剔除、完整率）。当用户提到：开始采集、监控这个应用、盯进程树、采数据、采集资源、资源监控、进程树监控、CSV 采集、采 CPU 内存、远程采集 时使用。
---

# 采集监控

> 采集器只有两个口径：**进程树**（默认，`--scope tree`）与**整机**（`--scope host`）。
> 两者都是**只读**的——只读 `/proc/*`、`/proc/net/dev`、`/proc/diskstats`，
> **不在被测机上装任何东西、不改任何配置**，随时可中断（逐行落盘，中断也不丢）。

---

## 一、怎么跑（可直接复制）

```bash
# 1) 在【被测机上】直接跑（脚本自包含，只用标准库，拷过去就能跑）
python3 perf_collect.py --app Emby --duration 300 --out Emby_idle.csv

# 2) 在【本机】跑，经 SSH 推到被测机执行并取回 CSV
#    凭据走 TOS_HOST / TOS_USER / TOS_PASS / TOS_PORT 或同目录 .env.local
python scripts/perf_collect.py --remote --app Emby --duration 300 --out Emby_idle.csv

# 3) 整机口径（未安装态基线、安装过程监控用这个）
python scripts/perf_collect.py --scope host --duration 300 --out host_baseline.csv

# 4) 已知 PID 时直接指定根进程（跳过进程名匹配）
python scripts/perf_collect.py --pid 12345 --duration 300 --out app_tree.csv

# 5) 调采样间隔（默认 1 秒；长稳可放 5 秒省 IO）
python scripts/perf_collect.py --app Emby --interval 5 --duration 28800 --out long.csv

# 6) 只看要跑什么，不真跑（远程命令拼装先自检）
python scripts/perf_collect.py --remote --app Emby --dry-run
```

| 参数 | 说明 |
|---|---|
| `--scope tree\|host` | `tree`（默认）= 进程树口径；`host` = 整机口径 |
| `--app <正则>` | 进程名 / 命令行正则，用于匹配**根进程**（与 `--pid` 二选一） |
| `--pid <N>` | 直接指定根进程 PID |
| `--interval <秒>` | 采样间隔，默认 `1.0` |
| `--duration <秒>` | 采集秒数，`0` = 一直采直到 `Ctrl+C` |
| `--out <路径>` | CSV 输出路径 |
| `--remote` | 经 SSH 到被测机跑，跑完取回 CSV |
| `--dry-run` | 只打印将执行的命令，不真跑 |

---

## 二、采了哪些列（进程树口径 13 列，逐列口径）

| # | 列名 | 口径 | 来源文件 |
|---|---|---|---|
| 1 | 时间 | 采样时刻 | — |
| 2 | CPU占用(%) | **单核口径**，两次采样差值 ÷ `CLK_TCK` | `/proc/<pid>/stat` 的 `utime+stime` |
| 3 | PSS占用(MB) | 私有 + 共享 ÷ 共享进程数 | **`/proc/<pid>/smaps_rollup` 的 `Pss:`** |
| 4 | RSS占用(MB) | 含共享库与页缓存 | `/proc/<pid>/status` 的 `VmRSS:` |
| 5 | private_Dirty占用(MB) | **判内存压力的第一口径** | **`smaps_rollup` 的 `Private_Dirty:`** |
| 6 | swap占用(MB) | 进程被换出的内存 | `/proc/<pid>/status` 的 `VmSwap:` |
| 7 | 磁盘读速度(MB/s) | 进程级归属 | `/proc/<pid>/io` 的 `read_bytes` 差值 |
| 8 | 磁盘写速度(MB/s) | **已扣除 `cancelled_write_bytes`** | `/proc/<pid>/io` 的 `write_bytes` 差值 |
| 9 | 网络发送速度(MB/s) | **整机口径**，不可归因单应用 | `/proc/net/dev` |
| 10 | 网络接收速度(MB/s) | **整机口径**，不可归因单应用 | `/proc/net/dev` |
| 11 | RssAnon(MB) | 匿名内存 | **`/proc/<pid>/status` 的 `RssAnon:`** |
| 12 | RssFile(MB) | 文件映射页（**页缓存，可回收**） | **`/proc/<pid>/status` 的 `RssFile:`** |
| 13 | 进程数 | 进程树规模（父 + 全部子孙） | `ps -eo pid,ppid` 递归 |

> ⚠️ **注意口径所在文件别记混**：`Pss` / `Private_Dirty` 只在 **`smaps_rollup`**；
> `RssAnon` / `RssFile` 只在 **`status`**（`smaps_rollup` 里没有这两个名字，只有 `Anonymous`）。
>
> ⚠️ 老内核若缺 `smaps_rollup`，脚本自动回退逐段读 `/proc/<pid>/smaps` 求和：
> `PSS = sum(Pss:)`、`USS = sum(Private_Clean:) + sum(Private_Dirty:)`。
>
> ⚠️ 前 10 列与既有采集器 CSV **保持一致**，便于复用既有分析产物；后 3 列是本技能新增的构成拆解。

**整机口径**（`--scope host`，16 列）：时间、CPU占用(%)、用户态(%)、系统态(%)、iowait(%)、
软中断(%)、内存使用(%)、内存可用(MB)、swap使用(MB)、load1/load5/load15、
磁盘读(MB/s)、磁盘写(MB/s)、网络发送(MB/s)、网络接收(MB/s)。

---

## 三、进程树是怎么发现的

```
--app <正则>
   ├─ 先匹配 /proc/<pid>/stat 的 comm
   │     ⚠️ comm 被内核截断到 15 字符 → 「mediaindex-serv」这类名字匹配不全
   └─ 匹配不上就【退回看 /proc/<pid>/cmdline】的完整命令行
          → 命中即认作根进程
找到根进程 → 按 ppid 建父子表 → 递归收全部子孙 → 每轮采样重新展开
```

| 行为 | 说明 |
|---|---|
| **新增子进程自动纳入** | 每轮采样重新发现，转码中途 fork 出的 `ffmpeg` 会被自动收进来 |
| **进程退出自动结档** | 目标进程消失后不再计入，进程数随之回落 |
| **进程树规模是独立指标** | 实测转码服务峰值 5 个进程 = 服务进程 + 4×`ffmpeg` |

> ⚠️ **comm 截断 15 字符是必踩的坑**：`mediaindex-server` 会被截成 `mediaindex-serv`。
> 用 `--app` 时**尽量用命令行里的独有片段**（如启动参数、脚本路径），别只用进程名前缀。

---

## 四、采集质量（三件事，报告里必须回显）

| 项 | 判据 | 怎么处理 |
|---|---|---|
| **坏行剔除** | 时间列解析失败，**或任一数值列不是数字**（采集器异常时的粘连行） | 剔除**并计数**，报告里回显「剔除坏行 N 行」 |
| **按时间去重** | 同一秒出现多行（采样相位抖动 / 重复落盘） | 先按时间去重再排序，避免重复计数 |
| **完整率** | 实际采样点 ÷ 应有采样点 | 采集器掉线或进程重启会造成缺口，缺口大了统计不可信 |

> ⚠️ **坏行剔除量大会影响统计可信度**——剔除量上千就要回去看采集器是不是被打断了。
>
> ⚠️ **多进程汇总按采样周期向下对齐，不要按精确时间戳 JOIN。** 实测：1 秒的系统监控对
> 5 秒的应用探测做精确 join，只匹配上约 10% 的点，算出「均值 1.83 路」的假值；
> 改**最近邻对齐（容差 4 秒）**后得真实值 **13 路**。

分析侧由 `scripts/perf_analyze.py` 自动完成，产出里带
`quality: {samples, bad_rows, ...}` 与 `稳态占比`，报告直接引用（见 `<报告生成>/SKILL.md`）。

---

## 五、CSV 命名约定

| 场景 | 命名 | 例 |
|---|---|---|
| 手工单次采集 | `<应用>_<类型>_<日期>.csv` | `Emby_idle_20260913.csv` |
| 空载基线 | `<应用>_idle.csv` | `Emby_idle.csv` |
| 负载态 | `<应用>_load.csv` | `Emby_load.csv` |
| 进程树口径（通用） | `<应用>_tree.csv` | `mediaindex_tree.csv` |
| 整机口径 | `host_<用途>.csv` | `host_baseline.csv` |

生命周期脚本自己有一套固定的 P 前缀命名（`P0_host.csv` / `P1_install_host.csv` /
`P2_<app>.csv` / `P3_<app>.csv` / `P4_cooldown_<app>.csv` / `P5_post_uninstall_host.csv`），
不要改名——`<生命周期>/SKILL.md` 的编排按文件名认产物。

> ⚠️ 文件名里的**日期用绝对日期**（`YYYYMMDD`），别写「今天」；同名冲突加日期前缀消歧。

---

## 六、远程采集与 SFTP 回退

```bash
# 凭据走环境变量，不写进命令（也不进报告）
TOS_HOST=<被测机IP> TOS_USER=<用户> TOS_PASS=<口令> TOS_PORT=9222 \
  python scripts/perf_collect.py --remote --app Emby --duration 300 --out Emby_idle.csv
```

远程路径做三件事：`put_file` 推脚本 → `run` 执行采集 → `get_file` 取回 CSV，最后清理被测机临时文件。

> ⚠️ **有些 TOS 机器把 sftp 子系统关了**（实测 `10.18.15.179`：`open_sftp` 直接抛异常）。
> `scripts/sshcommon.py` 的 `put_file` / `get_file` **SFTP 优先、失败自动回退 base64 over exec**，
> 调用方无需关心——日志里会打印 `[传输] sftp 不可用…改用 base64 通道`。
>
> ⚠️ 缺 `paramiko` 会自动 `pip install` 并打印 `[自举] …`；设 `SKILL_NO_AUTO_INSTALL=1` 只提示不安装。

---

## 相关文档

- `references/memory-accounting.md` —— 第 3/5/11/12 列的口径与反误读案例
- `references/methodology-pitfalls.md` —— 第 11、16、18 条与本文件的进程树/对齐口径直接相关
- `<生命周期>/SKILL.md` —— P0~P5 各阶段该用哪个 scope、采多久
- `<指标口径>/SKILL.md` —— 这些列各自的参考阈值
- `<报告生成>/SKILL.md` —— 采集质量与覆盖度写进报告哪一章
