# TOS5 到 TOS7 文件位置记录

设备：TNAS（10.18.15.177:9222）  
记录时间：2026-08-24

## 1. 当前连接与系统（更新后）

- 主机名：`TNAS`（更新前为 `TNAS-FEFE`）
- 当前系统：`TOS_ARM2.0_7.0.1114`（以 `/usr/lib/version` 为准；`/etc/tos/config/version` 残留 `6.0.587`）
- 内核：`Linux TNAS 5.10.107 #434 aarch64`
- SSH 用户：`test`
- SSH ed25519 指纹：`SHA256:iXs+CM9/ulONoK03x0EdRfazDYftJNVvN76Q94lVtWs`

## 2. TOS5 下的文件位置（当前实测）

### 2.1 卷与子卷

- 数据卷：`/dev/mapper/vg0-lv0`
- 总容量：109.36G，当前已用约 4.0G，剩余约 103.4G
- `/Volume1` 挂载 btrfs 根子卷（subvolid=5）
- `/home` 挂载 `User` 子卷（subvolid=258），所以 `/home/test` 和 `/Volume1/User/test` 指向同一批文件

| 子卷 | ID | UUID |
| --- | --- | --- |
| `public` | 257 | `b1ac4429-d8df-5e40-9259-f8183a7f6bf4` |
| `User` | 258 | `4990f4f2-ac63-5e4d-9fc0-9f31e5664cfb` |
| `@system` | 259 | `242e713d-b0ab-4a43-afdd-0eac47e08340` |
| `@apps` | 260 | `4d63f146-a498-2d4a-9cc8-0e38c47f2d60` |
| `@cache` | 261 | `50d771be-b61d-f441-a3d2-2c31b5d4f644` |
| `@desktop` | 262 | `86b38d15-a2a9-fc4a-bed6-42109e772d78` |
| `1` | 263 | `86069efb-3fef-1042-822c-7a7e73fbba3f` |
| `2` | 268 | `6cecd34e-71ab-da4e-9787-b0ca47c4ab50` |

### 2.2 用户文件

用户 `test` 的文件位于：

```text
/Volume1/User/test
等价路径：/home/test
```

当前内容：206 个文件，约 3.9G（环境创建过程中会继续变化），主要包括：

- 测试抓包：`格式化卷导致卷损坏.har`、`卷3格式化卷导致卷损坏.har`、`11.har`
- 系统/更新包：`TOS_X642.0_5.1.24_00322_2302221846.ins`、`TOS_X642.0_Update_5.1.145_00012_2407270535.bz2`、`OnlineOffice_TOS_APP_8.3.315_x86_64.tpk`、`usb_boot_120M_uefi.img`
- 存储管理组件：多个 `storagemanager_*.deb`、`tosdaemon_7.1.0004~tos7.0.0.1_amd64.deb`、`tosvue_7.1.0004~tos7.0.0.1_all.deb`
- 文件系统快照：多个 `FileSystemSnapshot_*.deb` 和日志 CSV
- 测试用例：大量 `存储管理单接口测试用例*.xlsx`、`Storage_Management_*.xlsx`、`api*.json`、Apifox 报告等
- 其他：`QoderSetup-x64.exe`、`格式化卷导致卷损坏.zip`

### 2.3 共享目录

- `public`：`/Volume1/public`，当前为空
- `1`：`/Volume1/1`
- `2`：`/Volume1/2`
- 用户家目录共享：`%H`（即 `/home/test`）

### 2.4 iSCSI 现状

目标服务二进制仍存在：

- `/usr/sbin/iscsi-scstd`
- `/etc/iscsi-scstd.conf`
- `/etc/sc.d/iscsi-scst`
- `/etc/init.d/nas/mkiscsi`

但当前没有 LUN 池、没有 `iSCSI.conf`、3260 未监听，SCST 模块未加载。

## 3. 升级后的位置（历史观察，本次实测见第 6 节）

基于这台设备此前从 TOS5 升级到 TOS7 时的实测结果：

### 3.1 挂载变化

| 项目 | TOS5 | TOS7 |
| --- | --- | --- |
| `/Volume1` | btrfs 根子卷（subvolid=5） | 新 `@` 子卷 |
| `/home` | `User` 子卷 | 新 `@/homes` 子卷（新空 home） |
| 旧数据根 | `/Volume1` | `/var/subvols/<卷标识>/` |

### 3.2 旧文件去向

升级后 TOS5 的旧数据不会删除，而是保留在原始根子卷：

```text
/var/subvols/<卷标识>/User/test     <- 原 /home/test 的文件
/var/subvols/<卷标识>/public
/var/subvols/<卷标识>/1
/var/subvols/<卷标识>/@apps
/var/subvols/<卷标识>/@cache
/var/subvols/<卷标识>/@desktop
/var/subvols/<卷标识>/@system
```

这台设备此前升级后实测的卷标识为：

```text
/var/subvols/8vEbTxkKvwa/
```

升级到 TOS7 后可用下面的方式确认：

```bash
ls /var/subvols/
btrfs subvolume list -u /var/subvols/<卷标识>/
```

通过子卷 UUID 确认旧数据：

- 原 `User`：`4990f4f2-ac63-5e4d-9fc0-9f31e5664cfb`
- 原 `public`：`b1ac4429-d8df-5e40-9259-f8183a7f6bf4`

### 3.3 升级后的注意事项

- TOS7 的 SMB 共享默认指向新的 `/Volume1/public` 和新的 `/home`，旧数据不会自动出现在共享中。
- 需要把旧子卷重新挂载，或把数据迁移到新目录后，共享里才能看到原来的文件。
- iSCSI 目标和 LUN 配置在升级后可能丢失，需要重新安装/配置 iSCSI Manager。
- 旧快照会保留在 `/var/subvols/<卷标识>/@syssnapshot/`。

## 4. 升级后核对清单

- [ ] `ls /var/subvols/` 找到卷标识
- [ ] `btrfs subvolume list -u /var/subvols/<卷标识>/` 核对 `User`、`public` 的 UUID
- [ ] 检查 `/home/test` 是否为空的 TOS7 新家目录
- [ ] 检查 `/Volume1/public` 是否为新的公共目录
- [ ] 确认旧文件还在 `/var/subvols/<卷标识>/User/test`
- [ ] 决定迁移方案后再调整 SMB 共享或挂载

## 5. 更新前（TOS5）LUN 与目录统计

### 5.1 卷状态

- `/Volume1`：110G，已用 77G，剩余约 31G，72%
- btrfs Used：76.76GiB / 109.36GiB，约 70.2%

### 5.2 四个 10G LUN

| LUN | 后端文件 | 挂载点 | 内部文件 | 使用率 |
| --- | --- | --- | --- | --- |
| LUN 1 | `/Volume1/@iSCSIStoragePool/iscsi-spare-vdisk-thin1787559777` | `/Volume1/@iscsi/26824162231-0` | `fill_7G.bin` 7.0G | 71% |
| LUN 2 | `/Volume1/@iSCSIStoragePool/iscsi-spare-vdisk-thin1787559804` | `/Volume1/@iscsi/26824162237-0` | `fill_7G.bin` 7.0G | 71% |
| LUN 3 | `/Volume1/@iSCSIStoragePool/iscsi-spare-vdisk-thin1787559813` | `/Volume1/@iscsi/26824162243-0` | `fill_7G.bin` 7.0G | 71% |
| LUN 4 | `/Volume1/@iSCSIStoragePool/iscsi-spare-vdisk-thin1787559821` | `/Volume1/@iscsi/26824162231-1` | `fill_7G.bin` 7.0G | 71% |

四个后端文件实际分配均为 14786536 blocks（约 7.57GiB）。

### 5.3 其他目录

- `/Volume1/public/volume_filler.bin`：40G 卷填充文件
- `/Volume1/@iscsi/26824162838-0`：1G LUN 5 挂载点（未填充）
- `/Volume1/User/test`：用户文件目录（等价 `/home/test`）
- `/Volume1/1`、`/Volume1/2`：共享目录
- `/Volume1/@iSCSIStoragePool/`：全部 LUN 后端文件所在目录

## 6. 更新后实测（2026-08-24）

本次更新完成后系统为 `TOS_ARM2.0_7.0.1114`（以 `/usr/lib/version` 为准），旧数据被迁移进新的 `@` 子卷树，而不是留在 `/var/subvols/<卷标识>/` 原始根子卷。

### 6.1 挂载与子卷

| 挂载点 | 当前状态 |
| --- | --- |
| `/Volume1` | btrfs `@` 子卷（subvolid=384） |
| `/home` | btrfs `@/homes` 子卷（subvolid=386） |
| `/var/subvols/8vEbTxkKvwa` | 原始根子卷（subvolid=5），仅保留 `@` 和 `@syssnapshot` |

原 `User`、`public`、`1`、`2` 等顶层子卷已并入新的 `@` 树。

### 6.2 用户目录

- 当前用户文件：`/home/test`（等价 `/Volume1/homes/test`）
- 更新后实测：298 个文件，约 7.7G
- 原 TOS5 文件仍存在，但迁移时产生了带 `(1)` 后缀的重复副本，例如 `11.har` 与 `11(1).har`
- `.ssh/authorized_keys` 已保留，Codex 免密连接有效

### 6.3 共享文件夹

| 共享 | 当前路径 | 内容 |
| --- | --- | --- |
| `public` | `/Volume1/public` | 40G 的 `volume_filler.bin` |
| `1` | `/Volume1/1` | 约 46M 文件 |
| `2` | `/Volume1/2` | 空 |
| `3` | `/Volume1/3` | 空 |
| `homes` | `/home/` | 用户目录 |

### 6.4 应用目录

- `/Volume1/@apps`：1.1G，包含 CloudSync、DupleBackup_V2、DupleBackupVault_V2、HskDDNS、Snapshot、USBCopy、docker、iSCSIManager
- `/Volume1/@desktop`：448K 应用桌面入口
- `/Volume1/@cache`：空

### 6.5 LUN 与 iSCSI

- LUN 后端文件仍完整：`/Volume1/@iSCSIStoragePool/`
  - LUN 1-4 各 7.1G（blocks=14786536）
  - LUN 5 为 1G，未填充
- `/Volume1/@iscsi/` 下保留了 5 个虚拟磁盘挂载目录，但当前为空
- 更新后 iSCSI 目标服务未运行：3260 未监听，无 `iscsi-scstd` 进程
- iSCSI Manager 应用文件在 `/Volume1/@apps/iSCSIManager`，需要重新启动/安装后 LUN 才能再次作为虚拟磁盘挂载

### 6.6 快照

- 旧快照保留在 `/var/subvols/8vEbTxkKvwa/@syssnapshot/1/`
- 包含 16:21 的三个旧快照和 17:00 的新快照

### 6.7 卷状态

- `/Volume1`：110G，已用 81G，剩余约 28G，75%
- 更新前填充的 4 个 LUN（各 7G）和 40G 卷填充文件都保留在 `/Volume1` 下
