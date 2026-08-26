# StorageManager：异常 USB I/O 错误修复验证环境搭建

## 1. 目的与边界

验证研发对“`Statfs` 在文件系统 I/O 错误时无限挂起”的修复：异常 USB 挂载点被识别后跳过，StorageManager 仍可用，且其他存储模块不受影响。

本环境必须使用专用 NAS 和可牺牲 USB。不得在系统盘、生产卷或唯一数据副本上执行格式化、断电、拔盘、`dmsetup remove` 或文件系统修复。动态 NAS IP、TOS 版本、StorageManager 包版本均以本轮现场采集值为准。

## 2. 需要准备的变量

| 变量 | 要求 |
|---|---|
| NAS | TOS 7.x，SSH 账号 `test`、端口 `9222`，已配置 Codex 公钥或可授权一次性密钥 |
| 修复包 | 研发提供的 StorageManager `.deb`、版本号、SHA256 |
| 数据卷 | 至少一个正常可写卷（建议 50 GB 以上可用空间），用于应用安装和测试数据 |
| USB-A（控制） | 健康 USB，验证正常基线 |
| USB-B（故障） | 可牺牲 USB；优先使用已出现大量 I/O 错误的设备，或专用故障注入镜像 |
| 测试数据 | 非稀疏、连续读写时间不少于 5 分钟的真实视频文件；建议 4–20 GB |

若暂时没有真实故障 USB，可先执行第 5 节的 `dm-flakey` 确定性替身。替身能验证“异常挂载点不阻塞服务”，但不能替代真实 USB 设备枚举、SMART/链路状态和物理拔插验证。

## 3. 现场只读基线采集

在 NAS 上先保存以下输出，确认目标设备身份后再做任何写操作：

```bash
OUT=/tmp/sm_usb_io_baseline_$(date +%Y%m%d_%H%M%S)
mkdir -p "$OUT"
hostname > "$OUT/hostname.txt"
uname -a > "$OUT/uname.txt"
cat /etc/os-release > "$OUT/os-release.txt"
dpkg -s storagemanager > "$OUT/storagemanager-package.txt" 2>&1
systemctl status StorageManager.service --no-pager > "$OUT/storage-manager-status.txt" 2>&1
lsblk -o NAME,PATH,TRAN,MODEL,SERIAL,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS > "$OUT/lsblk.txt"
findmnt -rno TARGET,SOURCE,FSTYPE,OPTIONS > "$OUT/findmnt.txt"
cat /proc/mounts > "$OUT/proc-mounts.txt"
journalctl -k -b --no-pager | grep -Ei 'usb|I/O error|Buffer I/O|blk_update|reset .*USB|abort' > "$OUT/kernel-usb-errors.txt" || true
```

记录以下基线结论：

1. `StorageManager.service` 为 `active (running)`；
2. `USB-A` 的传输类型、序列号、设备路径和挂载路径；
3. 健康 USB 下，至少调用一次 `GET /v2/storage/list/volume`、`GET /v2/storage/list/storagePool`，并从浏览器 Network 记录首页其余请求；
4. 每个接口设置 10 秒客户端超时，记录 HTTP 状态、响应体中的 `code/code_num`、响应耗时。

## 4. 推荐的真实 USB 故障场景

1. 将 USB-B 接入 NAS，确认它不是系统盘、RAID 成员或唯一数据盘；确认挂载路径属于 `/Volume*/@usb/`。
2. 在文件管理中向 USB-B 连续复制视频，同时在 NAS 上观察：

   ```bash
   dmesg -wT
   # 另一个会话
   iostat -xm 1
   ```

3. 仅对 USB-B 制造可控故障：优先使用已知坏块/不稳定桥接器；若必须模拟物理故障，只允许在持续复制期间短暂断开 USB-B，再重新插入。不得拔动其他磁盘、不得断 NAS 电源。
4. 以 `dmesg` 中出现 `I/O error`、`Buffer I/O error`、USB reset/读写失败，且 USB-B 仍在系统挂载列表中作为“异常 USB”成立条件。若设备直接消失，不算本缺陷的目标场景，应另记为拔盘场景。
5. 在异常状态保持期间打开 StorageManager 首页，并依次刷新卷、存储池、磁盘/USB、容量等页面；同时执行第 7 节接口探针。

## 5. 无真实故障 USB 时的确定性替身（仅测试镜像）

该方案在正常卷上创建一个文件镜像，经 loop + `dm-flakey` 挂载到 USB 风格路径。它不会让真实 USB 出错，也不会覆盖系统盘；但仍需要 root 权限及 `dm-flakey` 内核模块。

```bash
# 先确认 /Volume1 不是生产数据卷；以下文件名必须使用本轮唯一值
IMG=/Volume1/sm_usb_fault_test.img
MNT=/Volume1/@usb/usb_statfs_fault
SIZE_MIB=8192

mkdir -p /Volume1/@usb
fallocate -l ${SIZE_MIB}M "$IMG"
LOOP=$(losetup --find --show "$IMG")
mkfs.ext4 -F "$LOOP"
SECTORS=$((SIZE_MIB*2048))
modprobe dm-flakey
# 10 秒正常、60 秒错误；错误窗口内读写返回 I/O error
dmsetup create sm-usb-flakey --table "0 $SECTORS flakey $LOOP 0 10 60 error_reads error_writes"
mkdir -p "$MNT"
mount -t ext4 /dev/mapper/sm-usb-flakey "$MNT"
dd if=/dev/zero of="$MNT/video_source.mp4" bs=8M count=512 status=progress
sync
```

在错误窗口内确认：

```bash
findmnt "$MNT"
timeout 10 stat -f "$MNT"; echo "statfs_rc=$?"
dmesg -T | tail -n 100
```

然后保持挂载不变，执行 StorageManager 页面和接口验证。若 `dm-flakey` 在目标 TOS 内不可用，不要改动内核参数；直接转真实 USB 场景或在隔离 Linux 测试机上完成替身验证。

## 6. 研发修复包安装与场景编排

1. 记录当前版本和配置备份；只在测试 NAS 安装研发包，并记录 SHA256、安装前后 `dpkg -s storagemanager`。
2. 重启/恢复 StorageManager 后先执行健康 USB 基线。
3. 在应用中心安装一个无业务副作用的应用到正常卷，确认安装完成；这一步用于保持原始缺陷的前置状态。
4. 将视频持续传输到异常 USB-B（或第 5 节替身），在 I/O 错误持续期间打开 StorageManager。
5. 先验证修复包，再用同一设备/同一复制任务回退到旧包复测一次，形成“旧包可复现、新包不可复现”的 A/B 证据。回退必须使用研发提供的可回退包，不得自行降级系统组件。

## 7. 验证矩阵与通过标准

| 场景 | 关键动作 | 通过标准 |
|---|---|---|
| 健康基线 | USB-A 挂载、传视频、打开首页 | 页面和接口正常，无 502 |
| 单个异常 USB | USB-B 出现大量 I/O 错误但挂载仍存在 | StorageManager 服务不被拖死；首页及卷/池/磁盘/USB接口均无 502；每请求 ≤10 秒 |
| 异常 USB + 应用安装 | 应用中心安装到正常卷，同时向 USB-B 传视频 | 应用安装状态正确；StorageManager 可用；正常卷读写不受影响 |
| 多个异常挂载点 | 同时保留 2 个异常 USB/替身挂载 | 所有异常点均被跳过，正常卷和 USB-A 仍可展示 |
| 故障恢复 | 移除异常 USB 或恢复链路，再刷新页面/重启服务 | 服务可继续使用；健康设备重新出现；无残留 502/永久 loading |
| 多模块联调 | 文件管理、应用中心、磁盘/USB、卷、存储池、容量统计各执行一次 | 无新增接口错误、数据错乱、挂载丢失或任务状态卡死 |

重点证据：旧包能在相同异常状态下复现 502/超时；修复包在同一状态下请求返回非 502，且日志能看到异常挂载点被探测/跳过（具体日志文案以研发实现为准）。不要仅以 `systemctl status` 正常作为通过条件。

## 8. 证据采集与清理

```bash
OUT=/tmp/sm_usb_io_result_$(date +%Y%m%d_%H%M%S)
mkdir -p "$OUT"
systemctl status StorageManager.service --no-pager > "$OUT/service.txt" 2>&1
journalctl -u StorageManager.service -b --no-pager > "$OUT/storage-manager.log" 2>&1
journalctl -k -b --no-pager | grep -Ei 'usb|I/O error|Buffer I/O|blk_update|reset .*USB|statx|statfs|skip|mount' > "$OUT/kernel-and-skip.log" || true
lsblk -o NAME,PATH,TRAN,MODEL,SERIAL,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS > "$OUT/lsblk.txt"
findmnt -rno TARGET,SOURCE,FSTYPE,OPTIONS > "$OUT/findmnt.txt"
```

替身清理（仅确认没有进程使用挂载点后执行）：

```bash
umount /Volume1/@usb/usb_statfs_fault
dmsetup remove sm-usb-flakey
losetup -d "$LOOP"
rm -f /Volume1/sm_usb_fault_test.img
rmdir /Volume1/@usb/usb_statfs_fault 2>/dev/null || true
```

真实 USB 清理只做正常卸载/安全拔出；不要运行 `fsck -y`、重新分区或格式化作为“清理”动作，除非已明确授权并确认设备中无须保留的数据。

## 9. 当前执行所缺信息

要由我直接在 NAS 上搭建并采集证据，还需要：

- 本轮 NAS 当前 IP（仅作为本次连接目标）；
- SSH 是否已能用 `test@<IP>:9222` + `C:\Users\twm\.ssh\id_ed25519_codex` 非交互登录；
- 研发修复包路径、版本和校验值；
- 可牺牲 USB-B 的设备序列号/当前挂载点；
- 是否授权在该测试 NAS 上创建测试镜像、挂载 `dm-flakey`，以及短暂拔插 USB-B。
