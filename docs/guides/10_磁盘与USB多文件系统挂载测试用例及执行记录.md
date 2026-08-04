# 磁盘与USB多文件系统挂载测试用例及执行记录

> 关联文档：[09_多文件系统磁盘挂载测试指南](./09_多文件系统磁盘挂载测试指南.md)（操作命令详解）

## 一、用例总览

| 用例 | 用例标题 | 被测对象 | 前置条件 | 执行状态 |
|------|----------|----------|----------|----------|
| 用例一 | 挂载文件系统为 ext2、ext3、ext4、exFAT、vfat、btrfs、NTFS、hfsplus 的磁盘成功 | 内置盘分区挂载（`POST /v2/disk/MountDisk/{name}`） | 系统有卷；磁盘已划分多分区并格式化 | 已执行 |
| 用例二 | 首次插入有卷且文件系统为上述类型的外接存储设备，可自动挂载和上传文件 | USB 设备首次插入自动挂载（TOS 文件管理） | 系统有卷（Volume1）；USB 设备文件系统为 8 种之一 | 大部分轮次已执行，hfsplus/exFAT 待执行 |

> 说明：用例标题中 btrfs 出现两次，实际为 8 种文件系统：ext2、ext3、ext4、exFAT、vfat（FAT32）、btrfs、NTFS、hfsplus。

## 二、用例一：内置盘多文件系统分区挂载

### 用例信息

- 对应接口：`POST /v2/disk/MountDisk/{name}`，参数 name 为**分区名**（如 sdd1），请求头需携带 Cookie 和 X-Csrf-Token，Content-Type 为 `application/x-www-form-urlencoded`；
- 预期结果：挂载该硬盘**所有能挂载**的分区，文件管理能看到挂载分区中的文件；
- 测试磁盘：`/dev/sdd`（119.2GiB 空闲盘）。

### 磁盘准备（已验证）

```bash
# 1. 划分 8 个分区（GPT，每个 14GiB，分区名即 PARTLABEL）
parted -s /dev/sdd mklabel gpt
parted -s /dev/sdd mkpart ext2fs 1MiB 15GiB
parted -s /dev/sdd mkpart ext3fs 15GiB 29GiB
parted -s /dev/sdd mkpart ext4fs 29GiB 43GiB
parted -s /dev/sdd mkpart exfatfs 43GiB 57GiB
parted -s /dev/sdd mkpart vfatfs 57GiB 71GiB
parted -s /dev/sdd mkpart btrfsfs 71GiB 85GiB
parted -s /dev/sdd mkpart ntfsfs 85GiB 99GiB
parted -s /dev/sdd mkpart hfsplusfs 99GiB 113GiB

# 2. 格式化（-L/-n/-v 一步设置文件系统标签 LABEL）
mkfs.ext2 -L ext2fs   /dev/sdd1
mkfs.ext3 -L ext3fs   /dev/sdd2
mkfs.ext4 -L ext4fs   /dev/sdd3
mkfs.exfat -n exfatfs /dev/sdd4
mkfs.vfat -F 32 -n vfatfs /dev/sdd5
mkfs.btrfs -f -L btrfsfs /dev/sdd6
mkfs.ntfs -f -L ntfsfs /dev/sdd7
mkfs.hfsplus -v hfsplusfs /dev/sdd8

# 3. 每个分区写入测试文件（供挂载后文件管理验证可见性）
mkdir -p /mnt/tmp
for p in 1 2 3 4 5 6 7 8; do
  mount /dev/sdd$p /mnt/tmp
  echo "tos mount test fs_$p" > /mnt/tmp/test_file_$p.txt
  umount /mnt/tmp
done
```

### 实际执行记录（已验证部分）

`lsblk -f /dev/sdd` 实测结果：

| 分区 | 文件系统 | 标签 | 状态 |
|------|----------|------|------|
| sdd1 | ext2 | ext2fs | 格式化成功 |
| sdd2 | ext3 | ext3fs | 格式化成功 |
| sdd3 | ext4 | ext4fs | 格式化成功 |
| sdd4 | exfat | exfatfs | 格式化成功 |
| sdd5 | vfat (FAT32) | vfatfs | 格式化成功 |
| sdd6 | btrfs | btrfsfs | 格式化成功 |
| sdd7 | ntfs | ntfsfs | 格式化成功 |
| sdd8 | hfsplus | hfsplusfs | 格式化成功 |

挂载验证已执行，各分区挂载结果按实际回填用例。

### 判定标准

- 挂载接口返回 `code_num=0`、`code=true` → 挂载成功；
- 文件管理可见挂载分区内的测试文件 → 符合预期；
- hfsplus 分区若挂载失败（系统不支持），如实记录报错信息，**不算用例失败**（预期措辞为"所有**能**挂载的分区"）；
- 前置约束：系统必须存在卷；同一分区重复挂载会失败；只读模式下读写挂载失败、只读挂载成功。

## 三、用例二：USB 设备首次插入自动挂载

### 用例信息

- 场景：首次将外接存储设备（USB）插入 NAS，系统自动挂载；
- 前置条件：系统有卷（实测 Volume1 存在）；USB 设备文件系统为 8 种之一；
- 预期结果：**自动挂载**（无需手动操作）+ **可上传文件**（文件管理可见）；
- 测试设备：`/dev/sdg`（7.3T USB，初始为 ext4 单分区，后重分区为 100GiB）。

### 磁盘准备（已验证）

```bash
# 重分区：GPT + 单个 100GiB 分区
#（原因：vfat/FAT32 上限 2TB，7.3T 分区无法格式化；小分区格式化快）
parted -s /dev/sdg mklabel gpt
parted -s /dev/sdg mkpart primary 1MiB 100GiB
```

### 每轮测试循环代码

```bash
# 0. 格式化前确认未挂载（TOS 会自动挂载 USB，必须先卸载）
lsblk -f /dev/sdg
umount /dev/sdg1          # 若 MOUNTPOINTS 非空则执行

# 1. 格式化（每轮执行对应文件系统的一条）
mkfs.ext2 -L ext2fs   /dev/sdg1
mkfs.ext3 -L ext3fs   /dev/sdg1
mkfs.vfat -F 32 -n vfatfs /dev/sdg1
mkfs.btrfs -f -L btrfsfs /dev/sdg1
mkfs.ntfs -f -L ntfsfs /dev/sdg1
mkfs.hfsplus -v hfsplusfs /dev/sdg1
mkfs.exfat -n exfatfs /dev/sdg1

# 2. 确认格式化成功（-p 强制探测，绕过 blkid 缓存）
blkid -p /dev/sdg1

# 3. 物理拔下 USB → 停 2~3 秒 → 插回（无需任何手动挂载操作）

# 4. 观察自动挂载
lsblk -f /dev/sdg

# 5. 上传文件验证
echo "usb <fs> test" > /Volume1/@usb/usb_<fs>fs/test_upload.txt
cat /Volume1/@usb/usb_<fs>fs/test_upload.txt
```

### 实际执行记录（真实结果）

| 轮次 | 文件系统 | 格式化 | 自动挂载 | 挂载路径 | 上传 | 备注 |
|------|----------|--------|----------|----------|------|------|
| 初始 | ext4 | 原有 | 成功 | `/Volume1/@usb/usb_generic` | - | 无标签时挂载点用通用名 usb_generic |
| 1 | ext2 | 成功 | 成功 | `/Volume1/@usb/usb_ext2fs` | 成功 | 带标签后挂载点随标签命名 |
| 2 | ext3 | 成功 | 成功 | - | 成功 | - |
| 3 | vfat | 成功 | 成功 | - | 成功 | - |
| 4 | btrfs | 成功 | 成功 | - | 成功 | 需 `-f` 覆盖旧签名 |
| 5 | ntfs | 成功 | 成功 | `/Volume1/@usb/usb_ntfsfs` | 成功 | 拔插后文件管理正确显示 NTFS |
| 6 | hfsplus | 待执行 | 待验证 | - | - | 预期可能不支持（不算缺陷，如实记录） |
| 7 | exfat | 待执行 | 待验证 | - | - | 用例清单包含，尚未覆盖 |

### 判定标准

1. 拔插后系统**自动**出现挂载点、文件管理自动识别，全程无手动挂载操作 → 自动挂载符合预期；
2. 文件能写入挂载分区并在文件管理可见 → 上传符合预期；
3. 某文件系统插入后未自动挂载：如实记录现象（文件管理显示什么、有无报错），按"能挂载的分区"措辞判定，不作为失败；若系统显示识别错误（如文件系统类型显示错乱）则记录为缺陷。

## 四、执行过程中发现的注意事项（经验沉淀）

1. **TOS 会自动挂载 USB**：拔插后设备自动挂载到 `/Volume1/@usb/`，因此 mkfs 前必须先 `umount /dev/sdg1`，否则报 `is mounted; will not make a filesystem here!`；
2. **USB 挂载点命名规则**：有文件系统标签时挂载点为 `/Volume1/@usb/usb_<标签>`（如 usb_ext2fs），无标签时为 `/Volume1/@usb/usb_generic`；
3. **blkid 缓存问题**：设备内容被外部工具改写后，`blkid` 默认读缓存可能返回空或旧值，**不是产品缺陷**；用 `blkid -p` 强制探测即可，TOS 拔插后经内核事件重新探测，显示正常；
4. **vfat 2TB 上限**：`mkfs.vfat -F 32` 无法格式化超过 2TB 的分区，需先缩小分区；
5. **fdisk heredoc 批量输入易丢行**：多行粘贴时个别行丢失导致分区创建失败且 fdisk 直接退出不写盘，应改用 `parted -s` 单行命令；
6. **LABEL 与 PARTLABEL 缺一不可**：内置盘挂载测试中 TOS 识别依赖两者同时存在；USB 自动挂载不强制要求标签，但带标签时挂载点命名更清晰；
7. **btrfs/ntfs 格式化参数**：btrfs 必须 `-f` 覆盖旧签名；ntfs 建议 `-f` 快速格式化（秒级完成）。

## 五、测试数据汇总（回填用例用）

```
用例一（内置盘挂载）：
  挂载 ext2 分区 sdd1：实际结果按执行回填（code_num / code / 文件可见性）
  挂载 ext3 分区 sdd2：实际结果按执行回填
  ...（8 个分区逐条回填）
  挂载 hfsplus 分区 sdd8：实际结果按执行回填（预期为不支持，记录报错信息）

用例二（USB 自动挂载）：
  ext4（初始）：自动挂载 usb_generic 成功
  ext2：自动挂载 usb_ext2fs 成功，上传成功
  ext3：自动挂载成功，上传成功
  vfat：自动挂载成功，上传成功
  btrfs：自动挂载成功，上传成功
  ntfs：自动挂载 usb_ntfsfs 成功，上传成功
  hfsplus：待执行（预期可能不自动挂载，如实记录）
  exfat：待执行
```
