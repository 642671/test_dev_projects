# TOS 功能 → 进程 / 服务映射表

> **用途**：做 TOS 功能 / 应用的性能测试时，用它查出**该盯哪几个进程**。
> 即：先在这里找到「被测功能」那一行，拿到 `comm` 和「要不要连子进程」，再去跑 `perf_collect.py --app <comm>`。
>
> **采集来源**：2026-09-13 对实机 `x86-70`（`10.18.15.179`，SSH 9222）的**只读**探查——`ps` / `systemctl` / `/proc` / `ss` / nginx 配置。
> 机器：Ubuntu 22.04 底座 + TOS 7，内核 6.12.63+，4 核 / 7.6 GB；`/`=md9，`/Volume1`=vg0-lv0(15T, btrfs)。
> 规模：**248 个进程**（内核线程 154 + 用户态 95），**51 个 systemd 服务在跑**，用户态进程名 69 个。
>
> ⚠️ 本文是**该机器的快照**。换机器 / 换版本请重采一遍 `ps` 核对，别照抄。

---

## 一、系统管理类（TOS 自身）

| TOS 功能 | 进程名（comm） | 可执行路径 | systemd 服务 | 端口 | 监控要连子进程吗 | 备注 |
|---|---|---|---|---|---|---|
| TOS 主控 | `TOSDaemon` | `/usr/sbin/TOSDaemon` | `TOSDaemon.service` | 5050（仅 127.0.0.1） | 否 | Web 与 CLI 的 `/v2/`、`/tos`、`/ws`、`/static` 全部打到它。**改配置会自我重启**（见「注意」） |
| 资源监控采集端 | `ResourceCollect` | `/usr/sbin/ResourceCollection` | `ResourceCollection.service` | 5051（仅 127.0.0.1） | **要**：`mpstat`、`smartctl` | `comm` 被截断，真名 ResourceCollection。每 ~9 s fork 一次 `mpstat` |
| 登录鉴权 | `twm_authenticat` | `/usr/sbin/twm_authentication` | `twm_authentication.service` | 5057（全网卡） | 否 | nginx 的 `/auth-docker/` 反代到它；`comm` 截断 |
| 消息中心 | `msgcenter` | `/usr/bin/msgcenter` | `msg.service` | 5052（全网卡） | 否 | nginx `/msgcenter/` |
| 消息总线 | `msgbus` | `/usr/sbin/msgbus` | `msgbus.service` | 40011（TCP）、50051（gRPC） | 否 | nginx `/msg_bus`（WebSocket） |
| 定时任务调度 | `ScheduledTask` | `/usr/sbin/ScheduledTask` | `ScheduledTask.service` | 无 | **要**：备份 / 同步 / 快照都由它拉起 | 所有计划任务的**唯一触发源** |
| 存储管理 | `storagemanager` | `/usr/sbin/storagemanager` | `StorageManager.service` | unix `/var/run/socks/storage.sock` | **要**：`datascrubbing`、`ter_hotspare`、`btrfs`/`mdadm`/`lvm` | nginx 的 `/storage` `/disk` `/lvmCache` `/virtualdisk` `/extStorageDevice` `/hotsparedisk` 全是它 |
| 配置数据库 | `postgres` | `/usr/lib/postgresql/13/bin/postgres` | `postgresql@13-main.service` | 5032（仅 127.0.0.1） | **要**：**每条连接一个后端子进程** | 常驻 10+ 个 `comm=postgres`；按单 PID 采会严重低估 |
| 缓存 | `redis-server` | `/usr/bin/redis-server` | `redis-server.service` | 6379（仅 127.0.0.1） | 否 | |
| 磁盘 / IP 状态 | `nasips` | `/sbin/nasips` | `nasips.service` | 未见监听口 | 否 | 重启计数器增长较快 |
| 风扇调速 | `ter_smartfan` | `/usr/sbin/ter_smartfan` | `tnas-smartfan.service` | 无 | 否 | 启动时用 `vmtouch` 预载 `ipmitool`/`smartctl` |
| 缩略图 | `thumbnaild` | `/usr/sbin/thumbnaild` | `thumbnailDaemon.service` | 无 | **要**：`heifThumbnail`、`rawThumbnail`、`thumbnailTool` | 单元里写死 `CPUQuota=100%`，会吃满一个核 |
| 磁盘事件 | `disk-monitor.sh` | `/etc/tos/scripts/disk-monitor.sh`（bash） | `tnas-disk-monitor.service` | 无 | 否：fork `udevadm` | 热插拔监控 |

---

## 二、文件与共享

| TOS 功能 | 进程名（comm） | 可执行路径 | systemd 服务 | 端口 | 监控要连子进程吗 | 备注 |
|---|---|---|---|---|---|---|
| 文件管理 | `filemanager` | `/usr/sbin/filemanager` | `filemanage.service` | unix `/var/api/file-manage.sock`、`/var/api/file-manage-rpc.sock` | **要**：`rclone`、`rsyncClient` | 内含 1 个 janitor + 3 个 worker；nginx `/fileManage` `/remotefolder` |
| 全局搜索 | `globalsearch` | `/usr/sbin/globalsearch` | `globalsearch.service` | unix `/var/api/File_Search.sock` | 否 | nginx `/fileSearch` |
| SMB 共享 | `smbd` | `/usr/sbin/smbd` | `samba.service` | 445 | **要**：`smbd-notifyd`、`cleanupd`、`samba-bgqd` | 另有 `winbindd` 做账号映射 |
| NetBIOS 名称 | `nmbd` | `/usr/sbin/nmbd` | `nmbd.service` | 137 / 138（UDP） | 否 | |
| 域账号映射 | `winbindd` | `/usr/sbin/winbindd` | `winbind.service` | 无 | **要**：`domain child`、`idmap child` | 两个子进程也叫 `winbindd` |
| 网络发现 | `wsdd` | `/usr/sbin/wsdd`（python3） | `wsdd.service` | 5357（TCP）、3702（UDP） | 否 | ⚠️ `comm` 显示为 **`python3`**——按 comm 匹配会误伤，用 `--app wsdd` |
| RPC 端口映射 | `rpcbind` | `/sbin/rpcbind` | `rpcbind.service` | 111 | 否 | NFS 依赖 |
| Web 终端 | `ttyd` | `/usr/bin/ttyd` | `ttyd.service` | 7681（仅 127.0.0.1） | 否 | nginx `/v2/ttyd` |

---

## 三、存储与备份（多数无常驻进程，按需拉起）

| TOS 功能 | 进程名（comm） | 可执行路径 | systemd 服务 | 端口 | 监控要连子进程吗 | 备注 |
|---|---|---|---|---|---|---|
| 快照 / 卷快照 | 无独立进程 | `/etc/tos/scripts/snapshot` → `btrfs subvolume snapshot` | 无（由 ScheduledTask 拉起） | 无 | **要**：`btrfs-cleaner`、`btrfs-transaction` 等内核线程 | 同步操作，秒级返回 |
| 数据清洗（scrub） | `datascrubbing` | `/etc/tos/scripts/datascrubbing` | 无（按需） | 无 | **要**：btrfs 内核线程 | 长跑重活，**必须连子进程看** |
| 热备盘 | `ter_hotspare` | `/sbin/ter_hotspare` | 无（按需） | 无 | 否 | 29 MB 二进制 |
| RAID 告警 | `ter_raid_warning` | `/usr/sbin/ter_raid_warning` | `tnas-warnning.service`（static） | 无 | 否 | |
| RAID 监控 | `mdadm` | `/sbin/mdadm` | `mdmonitor.service` | 无 | 否 | 内核侧 `md0_raid1`/`md8_raid1`/`md9_raid1` |
| iSCSI Target | **无用户态守护** | — | — | **3260 本机未监听** | — | 走内核 SCST：模块已加载（`/sys/kernel/scst_tgt` 在），内核线程 `scstd0..3`、`iscsird0_*`、`iscsiwr0_*` 在跑，但**没有配置 target，3260 没起来**。测前先确认端口在听 |
| iSCSI 发起端 | `iscsid` | `/sbin/iscsid` | `iscsid.service` | 未见监听 | 否 | 两个同名进程 |
| CloudSync | 无（按需） | `/usr/sbin/cloud_disk_tool` | 无 | 无 | 否 | 75 MB 二进制，用时才起 |
| TerraSync / rsync | 无（按需） | `/usr/sbin/rsyncClient`、`/usr/bin/rsync` | `rsync.service`（disabled） | 无 | 否 | 定时同步由 ScheduledTask 拉起 |
| Duple Backup / 时光机 | 无（按需） | `/etc/tos/modules/Backup/`（`FsSnapShot`/`SnapShoot`/`TfmBackup`/`TimeMachine`） | 无 | 无 | — | 只有模块定义，无守护进程 |

> **要点**：这一类的共同特征是 **`ps` 里平时看不到**。测「备份 / 快照 / 同步」性能时，先触发任务，
> 再立刻用 `perf_collect.py --scope host`（整机口径）采，否则 `--app` 找不到根进程会直接报错退出。

---

## 四、应用平台

| TOS 功能 | 进程名（comm） | 可执行路径 | systemd 服务 | 端口 | 监控要连子进程吗 | 备注 |
|---|---|---|---|---|---|---|
| 应用中心 | `application` | `/usr/sbin/application` | `application.service` | unix `/var/api/Application.sock` | 否 | nginx `/app`、`/v2/app`；应用安装 / 启停走它 |
| Docker 引擎 | `dockerd` | `/Volume1/@apps/DockerEngine/dockerd/bin/dockerd` | `DockerEngine.service` | 无（unix socket） | **要**：`containerd` | 第三方应用，装在 `/Volume1/@apps/` |
| 容器运行时 | `containerd` | `/Volume1/@apps/DockerEngine/dockerd/bin/containerd` | dockerd 的子进程 | 无 | **要**：**每个容器一个 shim** | 跑容器时 shim 进程数 = 容器数 |
| Docker 应用后端 | `dockermgr-api` | `/Volume1/@apps/docker/sbin/dockermgr-api` | `docker.service` | 无 | **要**：`docker events` | nginx `/docker`、`/auth-docker` |
| 应用目录 | — | `/Volume1/@apps/`（本机只有 `docker`、`DockerEngine`） | — | — | — | `/var/apps` 与 `/usr/local/*/sbin` **不存在** |

---

## 五、网络服务

| TOS 功能 | 进程名（comm） | 可执行路径 | systemd 服务 | 端口 | 监控要连子进程吗 | 备注 |
|---|---|---|---|---|---|---|
| Web 入口（全部） | `nginx` | `/usr/sbin/nginx` | `nginx.service` | 80、443、5443、8181 | **要**：**4 个 worker** | 所有 Web 功能共用；配置在 `/etc/nginx/`（不是 `/usr/local/nginx/`） |
| SSH | `sshd` | `/usr/sbin/sshd` | `ssh.service` | 9222 | **要**：每连接一个 `sshd` | 采集脚本自己也会被算进去 |
| L2TP VPN | `xl2tpd` | `/usr/sbin/xl2tpd` | `xl2tpd.service` | 1701（UDP） | 否 | |
| 动态 DNS | `inadyn` | `/usr/bin/inadyn` | `inadyn.service` | 无 | 否 | |
| 4G/5G 模块 | `ModemManager` | `/usr/sbin/ModemManager` | `ModemManager.service` | 无 | 否 | |
| mDNS | `avahi-daemon` | `/usr/sbin/avahi-daemon` | `avahi-daemon.service` | 5353、43665 | 否 | 两进程：主 + chroot helper |
| 时间同步 | `ntpd` | `/usr/sbin/ntpd` | `ntp.service` | 123 | 否 | |
| 路由监听 | `ip_monitor` | `/etc/tos/scripts/ip_monitor`（bash） | 无（独立常驻） | 无 | 否：fork `ip monitor route` | |
| 网口插拔 | `netplugd` | `/sbin/netplugd` | `netplug.service` | 无 | 否 | |
| 在线服务 | `onlined` | `/usr/sbin/onlined` | `onlined.service` | 无 | 否 | |
| 虚拟交换 | `ovs-vswitchd`、`ovsdb-server` | `/usr/lib/openvswitch-switch/ovs-vswitchd` | `ovs-vswitchd.service`/`ovsdb-server.service` | 无 | 否 | |

---

## 六、本机**没有**的功能（抓不到映射，如实记录）

| 功能 | 状态 | 原因 |
|---|---|---|
| 媒体转码（Emby / Jellyfin / Plex） | ❌ 无映射 | **未安装**。`/Volume1/@apps/` 下只有 Docker；无任何媒体应用进程。`/usr/bin/ffmpeg` 二进制**存在**（300 KB）但无常驻进程，用时才被 fork |
| qBittorrent / 下载 | ❌ 无映射 | 未安装 |
| Surveillance 监控 | ❌ 无映射 | 未安装 |
| 虚拟机 / VMs | ❌ 无映射 | 未安装（无 libvirt / qemu 进程） |
| 媒体库索引 | ❌ 无映射 | `mediaindex.service` = **disabled**、`mediadb.service` = static 未运行。二进制 `/usr/sbin/mediaindex` 在，但没跑 |
| FTP / SFTP | ⚠️ 未启用 | `ftp.service`、`sftp.service` 均 disabled；`/usr/sbin/sftpd` 在但未运行 |
| WebDAV | ⚠️ 未启用 | `webdav.service` disabled；`/usr/sbin/webdav` 在但未运行 |
| NFS 服务端 | ⚠️ 未启用 | `nfs-server.service` disabled；只有 `rpcbind` 在跑 |
| TerraSearch / Terai / OnlyOffice 等 | ❌ 无映射 | 未安装（这些在 `app-ports.md` 里有端口，但**本机没有**） |

> **读不到的**：**没有**。nginx 配置成功读到（`/etc/nginx/` 可读，`nginx -T` 正常输出）；
> `/proc/<pid>/smaps_rollup` 与 `/proc/<pid>/status` 对 TOS 服务**均可读**——因为本机 SSH 账号 `yxw` 就是 **uid=0**。
> 换到普通账号时可能只能读 `status`（脚本会自动退化）。

---

## 七、怎么用它做性能测试

**通用流程**：① 在本文找到被测功能 → ② 记下 `comm` 和「要不要连子进程」→ ③ **先采 60 s 空载基线** →
④ 触发功能，**再采 300 s** → ⑤ 两份对比，差值才是功能的开销。

```bash
# ① 基线：功能还没触发，先采 60 s 空载
python ".claude/skills/性能测试/scripts/perf_collect.py" \
    --remote --app "filemanager" --duration 60 --out filemanager_idle.csv

# ② 触发功能（此时去 Web UI 上传/复制/删除文件）,同时采 300 s
python ".claude/skills/性能测试/scripts/perf_collect.py" \
    --remote --app "filemanager" --duration 300 --out filemanager_load.csv

# ③ 对比两份
python ".claude/skills/性能测试/scripts/perf_analyze.py" \
    --in filemanager_idle.csv filemanager_load.csv --app filemanager
```

**四个具体例子**

```bash
# 例 1 —— 测「文件管理」:盯 filemanager 整棵进程树(含 3 个 worker + 可能 fork 的 rclone)
python ".claude/skills/性能测试/scripts/perf_collect.py" \
    --remote --app "filemanager" --duration 300 --out filemanager.csv

# 例 2 —— 测「缩略图/相册」:thumbnaild 会 fork heifThumbnail / rawThumbnail,必须连子进程
python ".claude/skills/性能测试/scripts/perf_collect.py" \
    --remote --app "thumbnaild" --duration 300 --out thumbnaild.csv

# 例 3 —— 测「Web 页面 / 登录」:观察者是 nginx + TOSDaemon + twm_authentication 三个
#           注意 TOSDaemon(5050) 是 127.0.0.1,外部压不到,只能压 nginx 的 80/443
python ".claude/skills/性能测试/scripts/perf_collect.py" \
    --remote --app "nginx"    --duration 300 --out nginx.csv
python ".claude/skills/性能测试/scripts/perf_collect.py" \
    --remote --app "TOSDaemon" --duration 300 --out tosdaemon.csv

# 例 4 —— 测「备份 / 快照 / 同步 / 清洗」:平时无进程,先触发任务,用整机口径采
python ".claude/skills/性能测试/scripts/perf_collect.py" \
    --remote --scope host --duration 300 --out backup_host.csv

# 附 —— 只想知道整机水位时,永远用 host 口径(不含单功能归因)
python ".claude/skills/性能测试/scripts/perf_collect.py" \
    --remote --scope host --duration 300 --out host_baseline.csv
```

---

## 八、注意（踩过的坑）

| 现象 | 原因 | 怎么办 |
|---|---|---|
| `--app "ResourceCollect"` 匹配不上 / 匹配到别的 | **`comm` 被内核截断到 15 字符**。真名是 `ResourceCollection`、`twm_authentication`、`systemd-journald`、`networkd-dispatcher`、`systemd-resolved`、`systemd-networkd`、`btrfs-transaction` | 用 `--app` 传**正则前缀**（如 `"ResourceColl"`），或干脆 `--pid`；也可读 `/proc/<pid>/exe` 拿全路径对账 |
| `--app "wsdd"` 匹配不到 | 它是 python 脚本，**`comm` 显示为 `python3`** | 用 `--app "wsdd"`（按 cmdline 匹配）；别用 `--app "python3"`——会误抓到别的 python |
| 采到的内存明显偏小 | 只抓了主进程，漏了 worker / 子进程：nginx **4 worker**、postgres **每连接一后端**、smbd **3 个辅助**、winbindd **2 个子**、containerd **每容器一 shim** | 一律用 `--app`（脚本会递归收子孙），别用 `--pid` 只指主进程 |
| 压着压着被测进程 PID 变了，曲线断成两截 | **TOSDaemon 改配置会自我重启**——实机日志：`proxy config persisted, process restart scheduled` → `restarting process for proxy config to take effect`，随后 `nasips`、`filemanager`、nginx worker 被连带重启（TOSDaemon 重启计数 4、nasips 6） | **性能测试期间绝对不要通过 Web UI 改任何设置**（含代理、网络、共享）。基线里记下 PID，采样中发现 PID 变化就作废重采 |
| 自己采的数据把自己干扰了 | `ResourceCollection` **每 ~9 s fork 一次 `mpstat`** 采 CPU（90 s 实测 11 次），`smartctl` 偶发；`ps` 本身也耗 CPU | 采 60 s 基线时把这段也算进去，两份数据同等对待；不要用极短采样窗口 |
| 网络指标说不清是哪个功能占的 | `/proc/net/dev`、`ss` 只有**整机口径**，没有 per-process 网络 | 网络单独说明为「整机流量」，不要归因到单个功能；要归因就上 `nethogs`/`iptables` 计数（需装包，本工作区不允许装） |
| 测 iSCSI 时找不到目标端进程 | iSCSI Target 在**内核 SCST**里，用户态没有守护进程；且本机**未配置 target**，3260 根本没监听 | 只能监控内核线程 `scstd0..3`、`iscsird0_*`、`iscsiwr0_*`；**先确认 3260 在听**再压。压块存储用 `fio` 不用 HTTP 压测器 |
| 备份 / 快照 / 同步类 `--app` 直接报错退出 | 这类功能**平时没有常驻进程**，用时才 fork | 先触发任务再用 `--scope host`；或先 `ps` 找到刚起来的 PID 再 `--pid` |
| 换台机器 / 升个版本，进程名对不上 | TOS 内部改名频繁（如 `testhub`→`test-center` 这类整体改名），且本文只是**一台机器的快照** | 每次测前重跑一遍 `ps -eo pid,ppid,comm,args --sort=comm` + `systemctl list-units --type=service --state=running` 核对，把差异补回本文件 |

---

## 相关文档

- `app-ports.md` —— TOS **应用**端口对照表（TerraSync / Terai / OnlyOffice / iSCSI 等）；注意那些应用在**本机未安装**，端口清单仅供参考，用前先在目标机 `ss -lntp` 复核
- `metrics.md` —— 指标口径与阈值总表
- `methodology-pitfalls.md` —— 口径与方法学陷阱（**做测试前必读**）
- `memory-accounting.md` —— 内存口径（PSS / RSS / smaps_rollup）
- `tools-matrix.md` —— 压测工具选型
