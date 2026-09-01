# NAS 更新前后数据存放对比

检查时间：2026-08-12  
设备：TNAS-FEFE（10.18.15.177）  
系统：TerraMaster TOS，更新后已重启

## 1. 卷总览

| 项目 | 值 |
| --- | --- |
| 数据卷 | `/dev/mapper/vg0-lv0` |
| 文件系统 | btrfs |
| 总容量 | 109.3G |
| 已用 | 65.02G |
| 剩余 | 约 42.5G |
| 使用率 | 61% |
| 系统根分区 | `/dev/md9` ext4，7.5G，已用 3.3G（更新前约 1.4G） |

## 2. 挂载与子卷变化

| 挂载点 | 更新前 | 更新后 |
| --- | --- | --- |
| `/Volume1` | subvolid=5 根子卷 | subvolid=256 `@` 子卷 |
| `/home` | 旧 `User` 子卷 | subvolid=259 `@/homes` 子卷 |
| 旧根子卷 | 直接暴露在 `/Volume1` | `/var/subvols/8vEbTxkKvwa`（subvolid=5） |

新 `/Volume1` 下当前目录：`@apps`、`@cache`、`@desktop`、`@system`、`@systemd`、`@videoframe`、`@zlog`、`homes`、`public`。

## 3. 数据目录对比

| 数据        | 更新前路径                                | 更新后用户可见位置                   | 旧数据保留位置                                              | 大小                 |
| --------- | ------------------------------------ | --------------------------- | ---------------------------------------------------- | ------------------ |
| 用户目录      | `/Volume1/User`                      | `/home/test`，几乎为空           | `/var/subvols/8vEbTxkKvwa/User`                      | 约 6.5G             |
| 公共共享      | `/Volume1/public`                    | `/Volume1/public`，新内容约 749M | `/var/subvols/8vEbTxkKvwa/public`                    | 约 44.1G            |
| iSCSI LUN | `/Volume1/@iSCSIStoragePool`         | 不可见                         | `/var/subvols/8vEbTxkKvwa/@iSCSIStoragePool`         | 8.9G               |
| 快照        | `/Volume1/@sysSnapShoot`             | 不可见                         | `/var/subvols/8vEbTxkKvwa/@syssnapshot`              | 76G（2 个）           |
| 应用数据      | `/Volume1/@apps`、`@cache`、`@desktop` | 新目录为空                       | `/var/subvols/8vEbTxkKvwa/@apps`、`@cache`、`@desktop` | 352M / 142M / 168K |
| Docker 数据 | `/Volume1/@DockerData`               | 不可见                         | `/var/subvols/8vEbTxkKvwa/@DockerData`               | 156K               |

原始根子卷下还保留了更新产生的临时目录：`.update_*`、`.deCompressDir_*`。

## 4. iSCSI LUN 状态

| LUN | 容量 | 当前分配 | 占比 |
| --- | --- | --- | --- |
| LUN 1 | 1G | 725M | 70.7% |
| LUN 2 | 10G | 6.8G | 67.1% |
| LUN 3 | 1G | 725M | 70.7% |
| LUN 4 | 1G | 733M | 71.6% |
| LUN 5 | 50G | 0 | 0% |

后端文件保留在 `/var/subvols/8vEbTxkKvwa/@iSCSIStoragePool/`，文件名沿用更新前的 `iscsi-spare-vdisk-thin*`。

更新后 iSCSI 目标服务未随新系统启动：

- 不存在 `/etc/init.d/iSCSIManager`
- 无 SCST / `iscsi-scstd`
- 端口 3260 未监听
- 旧配置 `/etc/iscsi/iSCSI.conf` 已丢失

iSCSI Manager 应用包仍保留在 `/var/subvols/8vEbTxkKvwa/@apps/iSCSIManager` 和 `/var/subvols/8vEbTxkKvwa/@cache/iSCSIManager.tpk`。

## 5. SMB 共享变化

| 共享 | 配置路径 | 当前实际指向 |
| --- | --- | --- |
| `public` | `/Volume1/public` | 新的 749M 公共目录 |
| `homes` | `/home/` | 新的空用户目录 |

旧的 44.1G `public` 和 6.5G `User` 数据不再通过 SMB 暴露。

## 6. 快照

旧快照仍保留两个：

- `GMT+08-2026.08.12-10.46.16`
- `GMT+08-2026.08.12-11.00.00`

位置：`/var/subvols/8vEbTxkKvwa/@syssnapshot/1/`。新系统目前还没有生成新的快照。

## 7. 结论

- 旧数据没有丢失，仍保留在原始根子卷 `/var/subvols/8vEbTxkKvwa/`。
- 新系统把 `/Volume1` 和 `/home` 切换到了新的 `@` 子卷树，用户可见目录和 SMB 共享目前指向新位置。
- 需要恢复旧数据时，可以把旧子卷重新挂载或迁移，也可以将 SMB 共享路径指回旧数据目录。
