# 内存口径专章

> **为什么单独一章**：内存是性能测试里**最容易误读**的指标。实测报告里最大的两次误判都出在内存上
> （qBittorrent「吃掉 5.9 GB」、Jellyfin「155 MB swap = 内存压力」），两次都被推翻并留了纠错记录。
> 判内存压力**先看构成，再看大小**。

---

## 一、五个口径，各是什么

```
                  ┌─────────────────────────────────────────┐
                  │              RSS（常被误读）              │
                  │  ┌───────────────┬───────────────────┐  │
                  │  │   RssAnon     │     RssFile        │  │
                  │  │  （匿名内存）  │  （文件映射页缓存） │  │
                  │  │               │   ← 内核可随时回收   │  │
                  │  └───────────────┴───────────────────┘  │
                  └─────────────────────────────────────────┘
                        PSS = 私有 + 共享 ÷ 共享进程数
                        USS = Private_Clean + Private_Dirty
                        private_Dirty ≈ RssAnon  ← 判压力的第一口径
```

| 口径 | 定义 | 读取位置 | 什么时候用 |
|---|---|---|---|
| **RSS** | 进程占用的物理内存（含共享库与页缓存） | `/proc/<pid>/status` → `VmRSS:` | **仅作对照**。多进程共享库会重复计算，mmap 大文件会被页缓存撑大 |
| **PSS** | 私有 + 共享 ÷ 共享进程数 | `/proc/<pid>/smaps_rollup` → `Pss:` | **推荐首选**。多进程/多线程应用求和才不虚高 |
| **private_Dirty** | 进程私有且不可回收的脏页 | `/proc/<pid>/smaps_rollup` → `Private_Dirty:` | **判内存压力的第一口径**。与 `RssAnon` 基本相等 |
| **USS** | 只算进程独占，不含任何共享 | `Private_Clean + Private_Dirty` | 判「这个进程退出能释放多少」 |
| **RssAnon / RssFile** | 匿名内存 / 文件映射页 | `/proc/<pid>/status` | 拆构成。`RssFile` 是**页缓存，可回收** |

> **本技能采集器实际用的是 `/proc/<pid>/smaps_rollup`**（已实测可用，一次读取拿到 Pss / Private_Dirty /
> Private_Clean / Rss_Anon / Rss_File / Swap，比逐段读 `smaps` 快一个数量级）。
> 老内核若缺 `smaps_rollup`，回退读 `/proc/<pid>/smaps` 逐段求和：
> `PSS = sum(Pss:)`、`USS = sum(Private_Clean:) + sum(Private_Dirty:)`。

### cgroup v2（第六个口径，按需）

应用有 systemd unit 时，另采：

```
/sys/fs/cgroup/system.slice/<unit>/memory.current     # 总占用
/sys/fs/cgroup/system.slice/<unit>/memory.stat        # anon / slab / sock 分解
```

**为什么**：cgroup 口径**含记在该 cgroup 上的内核内存**（socket 缓冲区、slab），
逐进程 RSS 看不到这部分。**fork-per-connection 架构的应用**（如 pptpd）应优先用 cgroup。

实测佐证：PPT 服务端 30 会话时 cgroup 为 **80.7 MB**，而 4 个常驻进程 RSS 合计只有 29~35 MB
——差的那部分是 fork 出来的 `pppd`/`pptpctrl` 子进程 + 内核 slab。

---

## 二、四条判读规则

### 规则 1：判压力用 `private_Dirty`，不要用 RSS

> **实测案例（qBittorrent 做种）**：RSS 均值 **5918 MB**，看着吃掉整机 37%。
> 拆开看：`RssFile` 占 **5778 MB（97.6%）**——来自 libtorrent 对被做种文件的 `mmap` 映射；
> 真实匿名（`RssAnon` / `private_Dirty`）**仅 140 MB**，且全程恒定、无增长。
>
> **结论**：不构成 OOM 风险。报告里「限制写缓存 512MB~1GB」的建议**据此撤回**。

### 规则 2：页缓存会放大 RSS，且**不会进入 swap**

`RssFile` 是内核可随时丢弃后重读的文件页。推论：

- 不能用 RSS 判 OOM 风险；
- **页缓存不参与 swap**，所以「某应用的残留写缓存污染了另一应用的 swap 统计」这种因果**不成立**
  （实测报告初版就栽在这里，已撤回）。

### 规则 3：swap 换出 ≠ 内存压力

> **实测案例（Jellyfin 深度空闲）**：swap 155 MB 看着像内存不足。
> 但同一窗口 PSS 仅 **30 MB**、CPU 均值 **0.01%**、磁盘读写近乎为零。
> 说明这些页**已长时间未被访问**，是「深度空闲」的结果，不是压力。
>
> **代价**：长期空闲后突然接到请求会有一次**换入延迟**（首次响应略慢）——正常现象，
> 报告里要写出来，别让读者误判为故障。

### 规则 4：空闲期内存不归零属正常设计

> **实测案例（Duple Backup）**：任务停止后仍保留 62~335 MB 常驻缓冲。
> 判据不是「是否归零」，而是「**是否有单调爬升**」。无爬升即判无泄漏。

---

## 三、反误读清单（写报告时必须做的事）

- [ ] 内存表格里**同时给出** PSS / RSS / private_Dirty / RssAnon / RssFile，不要只给 RSS
- [ ] 给出 **页缓存占 RSS 比例**（`RssFile ÷ RSS`）——这是读者理解 RSS 虚高的钥匙
- [ ] 出现「内存很大」的结论前，先问一句：**这是匿名内存还是页缓存？**
- [ ] 换出（swap）单独成行，并注明「换出 ≠ 压力」
- [ ] 用 cgroup 口径时注明「含内核 slab/socket，与逐进程 RSS 不可直接相加」
- [ ] 跨应用对比内存时，**统一到同一个口径**（建议 private_Dirty），不要一个用 RSS 一个用 PSS

---

## 四、采集时的注意事项

| 事项 | 做法 | 原因 |
|---|---|---|
| 采样前禁 swap | `swapoff -a`（瞬时，服务重启即复位） | 避免换出污染内存读数 |
| 采样前加内存上限 | 给目标 cgroup 设 `memory.max` | 让超限行为暴露出来 |
| 冷启动 vs 稳态 | 明确标注是**首次启动**还是**稳态** | Emby 首次启动含媒体库初始化扫描，CPU 峰值与磁盘读峰值都是一次性动作，数值偏保守 |
| 重复测试前清缓存 | 清应用自己的缓存目录 + 保证请求参数唯一 | 否则命中缓存，测出「CPU 接近 0」的假象（Jellyfin 转码产物就是典型） |
| 时间对齐 | 多进程汇总**按采样周期向下对齐**，不按精确时间戳 JOIN | 不同采集器相位不同，精确 JOIN 会产生幻影行 |

---

## 相关文档

- `metrics.md` —— 指标全表
- `methodology-pitfalls.md` —— 十八条口径与方法学陷阱
- `app-lifecycle.md` —— P2 空载基线 / P4 泄漏检测怎么采
