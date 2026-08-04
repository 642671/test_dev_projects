# Apifox 变量全链路追踪文档

> 生成时间：2026-07-24 | Apifox 项目 ID：7536053 | 模块：默认模块（单接口测试）

---

## 目录

1. [认证层变量](#一认证层变量)
2. [卷模块变量](#二卷模块变量)
3. [创建卷资源变量（cv_）](#三创建卷资源变量-cv_)
4. [存储池模块变量](#四存储池模块变量)
5. [存储池编辑变量（vg_ raid/md）](#五存储池编辑变量-vg_-raidmd)
6. [创建存储池资源变量（cp_）](#六创建存储池资源变量-cp_)
7. [磁盘模块变量](#七磁盘模块变量)
8. [磁盘详情变量（反查模式）](#八磁盘详情变量反查模式)
9. [SMART 任务变量](#九smart-任务变量)
10. [接口执行顺序](#十接口执行顺序)
11. [脚本文件索引](#十一脚本文件索引)

---

## 一、认证层变量

| 变量名 | 生成接口 | 提取来源 | 作用域 | 含义 | 使用方 |
|--------|----------|----------|--------|------|--------|
| **RSA_PUBLIC_KEY** | `GET /v2/welcome` | 响应头 `X-Rsa-Token` | environment | RSA 公钥，用于密码加密脚本 | `POST /v2/login` 前置脚本（密码 RSA 加密） |
| **X-Csrf-Token** | `POST /v2/login`，登出时清除 | 登录后置脚本拼接，登出后置脚本 `unset` 清除 | environment | CSRF 防护令牌（登出后被清除，下次 /tos/ 重新生成） | 几乎所有需要认证的接口 Header |
| **Cookie** | `POST /v2/login` | 后置脚本拼接：`X-Csrf-Token` + `TMSESSNAME` + `tos_current_username` + `userName` + `loginStatus=true` | environment | 完整 Cookie 会话凭证 | 几乎所有需要认证的接口 Header |
| **X-Curpass-Token** | `POST /v2/otp/verify_pwd` | 加密脚本处理后生成 | environment | 密码验证令牌，用于敏感操作前的身份确认 | `DELETE /v2/storage/delete/pool/{uuid}`、`DELETE /v2/storage/delete/volume/{uuid}`、`DELETE /v2/disk/DelSysDisk`、`POST /v2/disk/sec_erase/start`、`POST /v2/disk/format/start` 等敏感接口 |
| **wrong_X-Curpass-Token** | `POST /v2/otp/verify_pwd` | 后置脚本：当前 `X-Curpass-Token` 改第 5/15 位 base64 字符 | environment | 用于「token 不一致」场景（有效密码验证令牌 + 不匹配值） | 「token 不一致」负向测试用例 Header |
| **expired_Cookie** | `POST /v2/logout` | 后置脚本：登出前的 `Cookie` 快照（会话已轮换，自然失效） | environment | 已失效的完整 Cookie（服务端已修复 session 轮换） | 「已失效凭证」负向测试用例 Header |
| **expired_X-Csrf-Token** | `POST /v2/logout` | 后置脚本：登出前的 `X-Csrf-Token` 快照 | environment | 已失效的 CSRF 令牌原始备份 | 「已失效凭证」负向测试用例 Header |
| **wrong_X-Csrf-Token** | `POST /v2/login` | 登录后置脚本：当前 `X-Csrf-Token` 改第 10/30/50 位 hex | environment | 用于「token 不一致」场景（有效 Cookie + 不匹配 CSRF） | 「token 不一致」负向测试用例 Header |

---

## 二、卷模块变量

**生成接口**：`GET /v2/storage/list/volume`（获取卷列表）

**后置脚本**：`02_sync_volume_uuid.js`

| 变量名 | 提取来源 | 作用域 | 含义 | 使用方 |
|--------|----------|--------|------|--------|
| **lv0_uuid** | `volume.uuid`（sort=1） | moduleVariables | 第 1 个卷的 UUID | 见下表 |
| **lv1_uuid** | `volume.uuid`（sort=2） | moduleVariables | 第 2 个卷的 UUID | 见下表 |
| **lv2_uuid** ~ **lv49_uuid** | 同上，按 sort 排列 | moduleVariables | 第 N 个卷的 UUID | 见下表 |
| **lv0_filesystem** | `volume.filesystem` | moduleVariables | 第 1 个卷的文件系统类型 | 脚本中使用 |
| **lv1_filesystem** | 同上 | moduleVariables | 第 2 个卷的文件系统类型 | 脚本中使用 |
| **lv_count** | `volumes.length` | moduleVariables | 卷总数 | 脚本中使用（循环控制） |

### 卷详情变量（GET edit/volume）

**生成接口**：`GET /v2/storage/edit/volume/{uuid}`（获取卷信息）

**后置脚本**：`04_edit_volume_mntpath.js`

| 变量名 | 提取来源 | 作用域 | 含义 | 使用方 |
|--------|----------|--------|------|--------|
| **lv{N}_mnt_path** | `data.mntpath`，按 `data.name` 动态命名 | environment | 第 N 个卷的挂载路径 | 待补充 |
| **lv{N}_sort** | `data.sort`，按 `data.name` 动态命名（如 `lv0_sort = 1`） | moduleVariables | 第 N 个卷的 sort 编号 | 待补充 |

### lv{N}_uuid 使用方明细

| 使用接口 | 引用的变量 | 用途 |
|----------|-----------|------|
| `GET /v2/storage/edit/volume/{uuid}` | `lv0_uuid` | 获取卷信息，路径参数 |
| `POST /v2/storage/edit/volume/{uuid}` | `lv6_uuid` | 编辑卷，路径参数 |
| `GET /v2/storage/volumeOccupyStatus` | `lv5_uuid` | 获取卷容量占用情况 |
| `POST /v2/storage/volumeOccupyAction` | `lv0_uuid` | 卷容量统计操作（前置） |
| `GET /v2/storage/volumeOccupyStatusAll` | `lv0_uuid` | 获取全部卷容量占用（后置） |
| `GET /v2/storage/ssd/trim/{uuid}` | `lv6_uuid` | 获取 SSD TRIM 信息 |
| `POST /v2/storage/ssd/trim/{uuid}` | `lv5_uuid` | 设置 SSD TRIM |
| `GET /v2/storage/defragment/{uuid}` | `lv6_uuid` | 碎片整理 |
| `POST /v2/storage/compression/{uuid}` | `lv1_uuid` | 设置卷压缩 |
| `POST /v2/storage/volumeFormatting` | `lv1_uuid` | 卷格式化 |
| `DELETE /v2/storage/delete/volume/{uuid}` | `lv1_uuid` | 删除卷 |

---

## 三、创建卷资源变量（cv_）

**生成接口**：`GET /v2/storage/create/volume`（获取创建卷资源信息）

**后置脚本**：`03_create_volume_resources.js`

**使用方**：全部供 `POST /v2/storage/create/volume`（创建卷）的请求体使用

### 磁盘相关

| 变量名 | 提取来源 | 含义 |
|--------|----------|------|
| `cv_disk_list` | `data.free_disk[]` → JSON | 空闲磁盘完整列表 |
| `cv_disk_0_path` | `freeDisks[0].device` | 第 1 块空闲磁盘设备路径 |
| `cv_disk_0_name` | `freeDisks[0].name` | 第 1 块空闲磁盘名称 |
| `cv_disk_1_path` | `freeDisks[1].device` | 第 2 块空闲磁盘设备路径 |
| `cv_disk_1_name` | `freeDisks[1].name` | 第 2 块空闲磁盘名称 |
| `cv_disk_2_path` | `freeDisks[2].device` | 第 3 块空闲磁盘设备路径 |
| `cv_disk_2_name` | `freeDisks[2].name` | 第 3 块空闲磁盘名称 |

### 存储池相关

| 变量名 | 提取来源 | 含义 |
|--------|----------|------|
| `cv_pool_list` | `data.free_pool[]` → JSON | 可选存储池列表 |
| `cv_vg{N}_name` | `p.name`（按实际池名动态） | 存储池名称（如 `cv_vg0_name`） |
| `cv_vg{N}_free_kb` | `p.free`（KB） | 存储池剩余空间 |
| `cv_vg{N}_free_gb` | `p.free / 1024 / 1024`（GB） | 存储池剩余空间 |
| `cv_selected_pool_name` | `freePools[0].value` | 默认选中的存储池名 |
| `cv_selected_pool_free_gb` | 默认池剩余 GB | 默认池可用容量 |

### 新建池/卷相关

| 变量名 | 提取来源 | 含义 |
|--------|----------|------|
| `cv_new_pool_name` | `data.pool_info.show_name` | 创建新池时的自动命名（mode=0） |
| `cv_new_pool_sort` | `data.pool_info.sort` | 新存储池 sort 编号 |
| `cv_new_volume_sort` | `data.volume_info1.sort` | 自动生成的卷 sort 编号 |

### 文件系统相关

| 变量名 | 提取来源 | 含义 |
|--------|----------|------|
| `cv_xfs_available` | `!!data.hype_lock`（布尔） | XFS 是否可用 |
| `cv_fs_options` | `['btrfs','ext4']` + 条件 `'xfs'`（JSON） | 可选文件系统列表 |
| `cv_filesystem` | 固定 `'btrfs'` | 默认文件系统 |

---

## 四、存储池模块变量

**生成接口**：`GET /v2/storage/list/storagePool`（获取存储池列表）

**后置脚本**：`05_sync_pool_uuid.js`（UUID 同步）+ `06_pool_health_status.js`（健康状态分类）

### UUID 同步（脚本 05）

| 变量名 | 提取来源 | 作用域 | 含义 | 使用方 |
|--------|----------|--------|------|--------|
| **vg0_uuid** | `pool.uuid`（sort=1） | moduleVariables | 第 1 个存储池的 UUID | `GET /v2/storage/edit/pool/{uuid}`（路径参数）、`GET /v2/storage/CheckAddDisk`（路径参数） |
| **vg1_uuid** | `pool.uuid`（sort=2） | moduleVariables | 第 2 个存储池的 UUID | 同上模式 |
| **vg2_uuid** ~ **vg49_uuid** | 同上 | moduleVariables | 第 N 个存储池 | 同上 |
| **vg_count** | `storagePools.length` | moduleVariables | 存储池总数 | 脚本中使用（循环控制） |

### 健康状态分类（脚本 06）

| 变量名 | 提取来源 | 作用域 | 含义 |
|--------|----------|--------|------|
| `avail_{池名}_uuid` | `pool.uuid`（`health === 999` 的可用池） | moduleVariables | 健康存储池的 UUID | `POST /v2/storage/CheckAvailablePool/{disk}` |
| `avail_{池名}_disk` | `p.decated_required_disk[0].device` 去 `/dev/` | moduleVariables | 健康存储池的磁盘设备名 | `POST /v2/storage/CheckAvailablePool/{disk}` |
| `corrupt_{池名}_uuid` | `pool.uuid`（`health === 0` 的损坏池） | moduleVariables | 损坏存储池的 UUID | `POST /v2/storage/CheckAvailablePool/{disk}` |
| `corrupt_{池名}_disk` | `p.decated_required_disk[0].device` 去 `/dev/` | moduleVariables | 损坏存储池的磁盘设备名 | `POST /v2/storage/CheckAvailablePool/{disk}` |

---

## 五、存储池编辑变量（vg_ raid/md）

**生成接口**：`GET /v2/storage/edit/pool/{uuid}`（获取存储池信息）

**后置脚本**：`07_sync_pool_raid.js`（RAID 同步）+ `08_pool_check_disk.js`（空闲磁盘检测）

### RAID 同步（脚本 07）

| 变量名 | 提取来源 | 作用域 | 含义 | 使用方 |
|--------|----------|--------|------|--------|
| **vg0_raid** | `pvs[0]`（如 `/dev/md1`） | moduleVariables | 存储池的 RAID 设备路径 | `GET /v2/storage/GetRaidSpeedOrBitmap`（路径参数） |
| **vg2_raid** | 同上 | moduleVariables | 同上 | `GET /v2/storage/GetDataScrubbingConf`（路径参数） |
| **vg{N}_raid** | 按 `data.name` 动态命名 | moduleVariables | 对应存储池的 RAID 设备路径 | RAID 相关操作 |
| **vg0_md** | 卷中 `raidname[0]`（如 `md0`） | moduleVariables | 存储池的 md 设备名 | `POST /v2/storage/CheckMdInfo/{md}`（路径参数） |
| **vg{N}_md** | 按 `data.name` 动态命名 | moduleVariables | 对应存储池的 md 设备名 | md 相关操作 |
| **vg_raid_count** | `pvs.length` | moduleVariables | RAID 设备数量 | 脚本中使用 |
| **vg_md_count** | 去重 raidname 数量 | moduleVariables | md 设备数量 | 脚本中使用 |

### 空闲磁盘检测（脚本 08）

| 变量名 | 提取来源 | 作用域 | 含义 |
|--------|----------|--------|------|
| `{池名}_check_disk` | `data.free_disk[].device` 逗号拼接 | **environment** | 存储池的空闲磁盘列表 |

> ⚠️ `{池名}_check_disk` 在 Apifox 参数中未找到直接引用，使用场景待补充。

---

## 六、创建存储池资源变量（cp_）

**生成接口**：`GET /v2/storage/create/pool`（获取创建池资源信息）

**后置脚本**：`09_create_pool_resources.js`

**使用方**：全部供 `POST /v2/storage/create/pool`（创建存储池）的请求体使用

### 磁盘资源

| 变量名 | 提取来源 | 含义 |
|--------|----------|------|
| `cp_disk_list` | `data.free_disk[]` → JSON | 空闲磁盘完整列表 |
| `cp_disk_count` | `freeDisks.length` | 空闲磁盘总数 |
| `cp_disk_{N}_path` | `d.device`（如 `/dev/sdg`） | 第 N 块空闲磁盘设备路径 |
| `cp_disk_{N}_name` | `d.name`（如 `HDD1`） | 第 N 块空闲磁盘名称 |
| `cp_disk_{N}_type` | `d.type`（ssd/normal/nvme） | 磁盘类型 |
| `cp_disk_{N}_capacity` | `d.capacity` | 容量文本 |
| `cp_disk_{N}_slot` | `d.slot` | 槽位号 |

### 新建存储池信息

| 变量名 | 提取来源 | 含义 |
|--------|----------|------|
| `cp_new_pool_show_name` | `pool_info.show_name` | 新池显示名称 |
| `cp_new_pool_sort` | `pool_info.sort` | 新池 sort 编号 |
| `cp_new_pool_uuid` | `pool_info.uuid` | 新池 UUID（创建前一般为空） |
| `cp_new_pool_description` | `pool_info.description` | 新池描述 |
| `cp_new_pool_compression` | `pool_info.compression` | 新池压缩设置 |
| `cp_new_pool_vg_name` | `vg{pool_info.sort - 1}` | 推导的 vg 名 |

### 请求体使用示例（脚本内置注释）

```json
// 单盘 basic
{ "level": "basic",  "disks": ["{{cp_disk_0_path}}"] }

// 双盘 RAID1
{ "level": "raid1",  "disks": ["{{cp_disk_0_path}}", "{{cp_disk_1_path}}"] }

// 三盘 RAID5
{ "level": "raid5",  "disks": ["{{cp_disk_0_path}}", "{{cp_disk_1_path}}", "{{cp_disk_2_path}}"] }

// 四盘 RAID6/RAID10
{ "level": "raid6",  "disks": ["{{cp_disk_0_path}}", "{{cp_disk_1_path}}", "{{cp_disk_2_path}}", "{{cp_disk_3_path}}"] }

// 大盘位 TRAID
{ "level": "traid",  "disks": ["{{cp_disk_0_path}}", ..., "{{cp_disk_11_path}}"] }
```

---

## 七、磁盘模块变量

**生成接口**：`GET /v2/disk/GetDiskOption`（获取硬盘下拉选项）

**后置脚本**：`10_sync_cap_disk.js`（CheckAvailablePool 专用）+ `11_sync_disk_list.js`（通用磁盘列表）

### CheckAvailablePool 专用（脚本 10）

| 变量名 | 提取来源 | 作用域 | 含义 | 使用方 |
|--------|----------|--------|------|--------|
| **cap_disk0** | `d.device` 去 `/dev/`（如 `sda`） | moduleVariables | 第 1 个磁盘设备名 | `/v2/storage/CheckAvailablePool/{{cap_disk0}}` |
| **cap_disk1** ~ **cap_disk49** | 同上 | moduleVariables | 第 N 个磁盘 | 同上模式 |
| **cap_disk_count** | `disks.length` | moduleVariables | 磁盘总数 | 脚本中使用 |

### 通用磁盘列表（脚本 11）

| 变量名 | 提取来源 | 作用域 | 含义 | 使用方 |
|--------|----------|--------|------|--------|
| **disk1_device** | `d.device`（如 `/dev/sda`），索引从 1 起 | moduleVariables | 第 1 个磁盘的设备路径 | 磁盘操作接口（性能测试、格式化、安全擦除等） |
| **disk1** | `d.name`（如 `HDD1`） | moduleVariables | 第 1 个磁盘的名称 | 同上 |
| **disk2_device** ~ | 同上 | moduleVariables | 第 N 个磁盘 | 同上 |
| **disk_count** | `disks.length` | moduleVariables | 磁盘总数 | 脚本中使用 |
| **disk_list** | 完整列表 JSON | moduleVariables | 磁盘完整列表 | 脚本中使用 |

---

## 八、磁盘详情变量（反查模式）

**生成接口**：`GET /v2/disk/GetDiskDetailData`（获取指定磁盘 SMART 详细信息）

**后置脚本**：`12_disk_detail_info.js`

**核心逻辑**：从请求的 `device` 参数（如 `/dev/sda`）反查 `disk{N}_device`，找到对应索引 N 后写入详情。这个脚本依赖脚本 11 先执行。

| 变量名 | 提取来源 | 作用域 | 含义 |
|--------|----------|--------|------|
| **disk1_model** | `data.model` | moduleVariables | 第 1 个磁盘的型号 |
| **disk1_serial** | `data.serial` | moduleVariables | 第 1 个磁盘的序列号 |
| **disk1_type** | `data.type` | moduleVariables | 第 1 个磁盘的类型 |
| **disk1_capacity** | `data.factory_capacity` | moduleVariables | 第 1 个磁盘的出厂容量 |
| **disk1_slot** | `data.slot` | moduleVariables | 第 1 个磁盘的槽位号 |
| **disk2_*** ~ | 同上 | moduleVariables | 第 N 个磁盘的详情 |

---

## 九、SMART 任务变量

**生成接口**：
- `GET /v2/disk/smart_test/schedule`（获取 SMART 测试任务列表）
- `POST /v2/disk/smart_test/schedule`（创建 SMART 测试任务）

**后置脚本**：`13_smart_schedule.js`（GET 列表同步）+ `14_smart_create.js`（POST 创建同步）

| 变量名 | 提取来源 | 作用域 | 含义 | 使用方 |
|--------|----------|--------|------|--------|
| **disk1_smart_id** | `item.id`（GET）/ `data.id`（POST），通过 `disks` 反查 N | moduleVariables | 第 1 个磁盘的 SMART 任务 ID | `POST /v2/disk/smart_test/schedule/{{disk1_smart_id}}/stop`、`/exec`、`/edit`；`DELETE .../{id}` |
| **disk2_smart_id** ~ | 同上 | moduleVariables | 第 N 个磁盘 | 同上 |
| **smart_task_count** | `tasks.length`（仅 GET 脚本） | moduleVariables | SMART 任务总数 | 脚本中使用 |

> 两个脚本写入同一个变量，触发时机不同：GET 是列出已有任务后批量同步，POST 是创建新任务后单条更新。

---

## 九点二、热备磁盘变量（反查模式）

**生成接口**：`GET /v2/hotsparedisk/GetAvailableDiskList`（可热备的空闲磁盘）

**后置脚本**：`16_hotspare_disk_list.js`

| 变量名 | 提取来源 | 作用域 | 含义 | 使用方 |
|--------|----------|--------|------|--------|
| **hs1_device** | `data[].device`（如 `/dev/sdzb`），按热备可用顺序编号，从 1 起 | moduleVariables | 第 1 块可热备磁盘的设备路径 | `POST /v2/hotsparedisk/CreateHotSpareDisk`（请求体 `devices` 数组） |
| **hs1_name** | `data[].name`（如 `NVMe Disk2`） | moduleVariables | 第 1 块可热备磁盘的名称 | 参考信息 |
| **hs2_device** ~ | 同上 | moduleVariables | 第 N 块 | 同上 |
| **hs_disk_count** | 匹配计数 | moduleVariables | 可热备空闲磁盘总数 | 脚本内部使用 |

### 热备存储池变量

**生成接口**：`GET /v2/hotsparedisk/GetRaidHotSpare`（获取阵列列表）

**后置脚本**：`17_hotspare_raid_list.js`

| 变量名 | 提取来源 | 作用域 | 含义 | 使用方 |
|--------|----------|--------|------|--------|
| **hs1_vg** | `data[0].vgs`（如 `vg0`） | moduleVariables | 第 1 个支持热备的存储池名称 | `POST /v2/hotsparedisk/CreateHotSpareDisk`（请求体 `raids` 数组） |
| **hs2_vg** | `data[1].vgs`（如 `vg1`） | moduleVariables | 第 2 个支持热备的存储池名称 | 同上 |
| **hs3_vg** ~ | 同上 | moduleVariables | 第 N 个 | 同上 |
| **hs_vg_count** | `vgNames.length` | moduleVariables | 支持热备的存储池总数 | 脚本内部使用 |
| **hs_vg_list** | JSON 数组 | moduleVariables | 支持热备的存储池名称列表 | 脚本内部使用 |

> CreateHotSpareDisk 请求体：`{ "devices": ["{{hs1_device}}"], "raids": ["{{hs1_vg}}"] }`

### 已有热备盘变量

**生成接口**：`GET /v2/hotsparedisk/GetHotSpareList`（获取热备盘列表）

**后置脚本**：`18_hotspare_list.js`

| 变量名 | 提取来源 | 作用域 | 含义 | 使用方 |
|--------|----------|--------|------|--------|
| **hsp1_device** | `data[0].device`（如 `/dev/sdh`） | moduleVariables | 第 1 个已有热备盘的设备路径 | `POST /v2/hotsparedisk/DelHotSpare`（删除热备盘） |
| **hsp1_blk** | `data[0].device_name`（如 `sdh`） | moduleVariables | 第 1 个已有热备盘的 blk 名 | `POST /v2/hotsparedisk/ModifyArray`（请求体 `blk` 参数） |
| **hsp2_device** ~ | 同上 | moduleVariables | 第 N 个 | 同上 |
| **hsp_count** | `items.length` | moduleVariables | 已有热备盘总数 | 脚本内部使用 |

> `hsp`（Hot SPare 已有）与 `hs`（可热备）前缀区分，避免冲突。

---

## 九点五、IHM 健康扫描磁盘变量

**生成接口**：`GET /v2/disk/IhmInfoList`（获取 IHM 信息列表）

**后置脚本**：`15_ihm_info_list.js`

| 变量名 | 提取来源 | 作用域 | 含义 | 使用方 |
|--------|----------|--------|------|--------|
| **Ihm1_device** | `d.device`（如 `/dev/sde`），索引从 1 起 | moduleVariables | 第 1 块可健康扫描磁盘的设备路径 | `POST /v2/disk/ManualTest`（手动测试 IHM，device 参数）、`GET /v2/disk/ExportIhmLog`（导出 IHM 日志，query 参数 device） |
| **Ihm1_name** | `d.name`（如 `HDD1`） | moduleVariables | 第 1 块 IHM 磁盘的名称 | 同上 |
| **Ihm1_model** | `d.model`（如 `ST2000VN004-2E4164`） | moduleVariables | 第 1 块 IHM 磁盘的型号 | 参考信息 |
| **Ihm1_health** | `d.health`（如 `Healthy`） | moduleVariables | 第 1 块 IHM 磁盘的健康状态 | 参考信息 |
| **Ihm2_*** ~ | 同上 | moduleVariables | 第 N 块 IHM 磁盘 | 同上 |
| **Ihm_count** | `disks.length` | moduleVariables | 可执行健康扫描的磁盘总数 | 脚本中使用 |
| **Ihm_disk_list** | 完整列表 JSON | moduleVariables | IHM 磁盘完整列表（含 drive_type、capacity） | 脚本中使用 |

> 说明：IHM（IronWolf Health Management）仅支持希捷酷狼等特定型号磁盘，当前环境仅 1 块可扫描盘。脚本兼容空数组场景，磁盘拔出后变量自动清空。

---

## 十、接口执行顺序

测试用例执行时的推荐依赖顺序：

| 步骤 | 接口 | 产出变量 | 说明 |
|------|------|----------|------|
| 1 | `GET /v2/welcome` | `RSA_PUBLIC_KEY` | 登录前置，获取加密公钥 |
| 2 | `POST /v2/login` | `Cookie`, `X-Csrf-Token` | 认证基础，后续所有接口依赖 |
| 3 | `POST /v2/otp/verify_pwd` | `X-Curpass-Token` | 敏感操作密码验证 |
| 4 | `GET /v2/storage/list/storagePool` | `vg{N}_uuid`, `vg_count`, `avail_*`, `corrupt_*` | 存储池同步 |
| 5 | `GET /v2/storage/list/volume` | `lv{N}_uuid`, `lv{N}_filesystem`, `lv_count` | 卷同步 |
| 6 | `GET /v2/disk/GetDiskOption` | `cap_disk{N}`, `disk{N}_device`, `disk{N}`, `disk_count` | 磁盘同步 |
| 7 | `GET /v2/storage/edit/pool/{uuid}` | `vg{N}_raid`, `vg{N}_md` | 存储池 RAID 详情 |
| 8 | `GET /v2/storage/edit/pool/{uuid}` | `vg{N}_check_disk` | 存储池空闲磁盘 |
| 9 | `GET /v2/storage/edit/volume/{uuid}` | `lv{N}_mnt_path`, `lv{N}_sort` | 卷详情 |
| 10 | `GET /v2/disk/GetDiskDetailData` | `disk{N}_model`, `disk{N}_serial` 等 | 磁盘详情 |
| 11 | `GET /v2/storage/create/volume` | `cv_*`（19 个变量） | 创建卷资源 |
| 12 | `GET /v2/storage/create/pool` | `cp_*`（~14 个变量） | 创建池资源 |
| 13 | `GET /v2/disk/smart_test/schedule` | `disk{N}_smart_id`, `smart_task_count` | SMART 任务同步 |
| 14 | `GET /v2/disk/IhmInfoList` | `Ihm{N}_device`, `Ihm{N}_name`, `Ihm{N}_model`, `Ihm{N}_health`, `Ihm_count` | IHM 健康扫描磁盘同步 |
| 15 | `GET /v2/hotsparedisk/GetAvailableDiskList` | `hs{N}_device`, `hs{N}_name`, `hs_disk_count` | 热备磁盘同步 |
| 16 | `GET /v2/hotsparedisk/GetRaidHotSpare` | `hs{N}_vg`, `hs_vg_count`, `hs_vg_list` | 热备存储池同步 |
| 17 | `GET /v2/hotsparedisk/GetHotSpareList` | `hsp{N}_device`, `hsp{N}_blk`, `hsp_count` | 已有热备盘同步 |

### 凭证失效变量（负向测试前置步骤）

| 步骤 | 接口 | 产出变量 | 说明 |
|------|------|----------|------|
| L1 | `POST /v2/login` | `Cookie`, `X-Csrf-Token` | 先登录，获得有效凭证 |
| L2 | `POST /v2/logout` | `expired_Cookie`, `expired_X-Csrf-Token`；且清除 `X-Csrf-Token` | 登出后脚本备份原始凭证（expired_*），清除环境变量 `X-Csrf-Token`（下次 /tos/ 重新生成） |

> 负向测试用例引用规则：`expired_Cookie` + `expired_X-Csrf-Token` 用于"过期凭证"场景（session 已轮换，真正失效）；有效 `Cookie` + `wrong_X-Csrf-Token` 用于"token 不一致"场景；`wrong_X-Curpass-Token` 用于"密码验证令牌不一致"场景；`{{X-Csrf-Token}}` 在登出后已被清除，下次 /tos/ 调用时会重新生成。

---

## 十一、脚本文件索引

所有脚本存放于 `apifox_scripts/` 目录。

| 编号 | 文件名 | 对应接口 | 产出的变量 | 编码模式 |
|------|--------|----------|-----------|----------|
| 01 | `01_auth_login.js` | `POST /v2/login` | `Cookie`, `X-Csrf-Token`, `wrong_X-Csrf-Token` | 拼接写入 + 改第 10/30/50 位 hex 生成不一致 token |
| 02 | `02_sync_volume_uuid.js` | `GET /v2/storage/list/volume` | `lv{N}_uuid`, `lv{N}_filesystem`, `lv_count` | 全量同步（sort-1 零基映射） |
| 03 | `03_create_volume_resources.js` | `GET /v2/storage/create/volume` | `cv_*`（19 个） | 全量同步（前缀扫描清理） |
| 04 | `04_edit_volume_mntpath.js` | `GET /v2/storage/edit/volume/{uuid}` | `lv{N}_mnt_path`, `lv{N}_sort` | 动态命名（environment + moduleVariables） |
| 05 | `05_sync_pool_uuid.js` | `GET /v2/storage/list/storagePool` | `vg{N}_uuid`, `vg_count` | 全量同步（sort-1 零基映射） |
| 06 | `06_pool_health_status.js` | `GET /v2/storage/list/storagePool` | `avail_*`, `corrupt_*` | 条件分类 + 动态清理 |
| 07 | `07_sync_pool_raid.js` | `GET /v2/storage/edit/pool/{uuid}` | `vg{N}_raid`, `vg{N}_md`, `vg_raid_count`, `vg_md_count` | 全量清理 + 增量写入 |
| 08 | `08_pool_check_disk.js` | `GET /v2/storage/edit/pool/{uuid}` | `{池名}_check_disk` | 动态命名（environment） |
| 09 | `09_create_pool_resources.js` | `GET /v2/storage/create/pool` | `cp_*`（~14 个） | 全量同步（前缀扫描清理） |
| 10 | `10_sync_cap_disk.js` | `GET /v2/disk/GetDiskOption` | `cap_disk{N}`, `cap_disk_count` | 全量同步（去掉 /dev/ 前缀） |
| 11 | `11_sync_disk_list.js` | `GET /v2/disk/GetDiskOption` | `disk{N}_device`, `disk{N}`, `disk_count`, `disk_list` | 全量同步（索引从 1 起） |
| 12 | `12_disk_detail_info.js` | `GET /v2/disk/GetDiskDetailData` | `disk{N}_model`, `disk{N}_serial`, `disk{N}_type`, `disk{N}_capacity`, `disk{N}_slot` | **反查模式**（请求 device → 匹配 diskN_device → 写入） |
| 13 | `13_smart_schedule.js` | `GET /v2/disk/smart_test/schedule` | `disk{N}_smart_id`, `smart_task_count` | 反查模式（数组/对象兼容） |
| 14 | `14_smart_create.js` | `POST /v2/disk/smart_test/schedule` | `disk{N}_smart_id` | 反查模式（请求体 device → 匹配） |
| 15 | `15_ihm_info_list.js` | `GET /v2/disk/IhmInfoList` | `Ihm{N}_device`, `Ihm{N}_name`, `Ihm{N}_model`, `Ihm{N}_health`, `Ihm_count`, `Ihm_disk_list` | 全量同步（正则前缀扫描清理，索引从 1 起，兼容空数组） |
| 16 | `16_hotspare_disk_list.js` | `GET /v2/hotsparedisk/GetAvailableDiskList` | `hs{N}_device`, `hs{N}_name`, `hs_disk_count` | 按热备顺序编号（从 1 起） |
| 17 | `17_hotspare_raid_list.js` | `GET /v2/hotsparedisk/GetRaidHotSpare` | `hs{N}_vg`, `hs_vg_count`, `hs_vg_list` | 按数组顺序编号（从 1 起） |
| 18 | `18_hotspare_list.js` | `GET /v2/hotsparedisk/GetHotSpareList` | `hsp{N}_device`, `hsp{N}_blk`, `hsp_count` | 按数组顺序编号（从 1 起），hsp 前缀区分已有热备盘 |
| 19 | `19_logout_capture_expired.js` | `POST /v2/logout` | `expired_Cookie`, `expired_X-Csrf-Token` | 快照备份 + 清除 X-Csrf-Token |
| 20 | `20_verify_pwd_wrong_curpass.js` | `POST /v2/otp/verify_pwd` | `wrong_X-Curpass-Token` | base64 改第 5/15 位生成不一致令牌 |

### 编码模式说明

| 模式 | 说明 | 代表脚本 |
|------|------|----------|
| **全量同步** | 先清空所有旧变量，再按最新响应全部重写。用于资源列表接口。 | 02, 03, 05, 09, 10, 11, 15 |
| **条件分类** | 根据响应字段（如 health）将资源分类写入不同变量组。 | 06 |
| **反查模式** | 从请求参数中提取 device/disk 等标识，匹配已有变量找索引，再写入对应的 `diskN_*` 变量。 | 12, 13, 14 |
| **动态命名** | 按响应的 name 字段动态拼接变量名（如 `{poolName}_check_disk`）。 | 04, 08 |
| **拼接写入** | 从多个来源拼凑完整值后写入。 | 01 |
| **快照清除** | 备份原始值后清除环境变量，触发服务端重新生成。 | 19 |

---

## 九点八、USB 设备模块变量（2026-07-28 新增）

**生成接口**：`GET /v2/extStorageDevice/DeviceList`（获取USB设备列表）

**后置脚本**：`20_usb_device_list.js`

| 变量名 | 提取来源 | 含义 | 使用方 |
|--------|----------|------|--------|
| `usb{N}_name` | `item.name` | 第N个USB设备名（如 sdg） | `IsFormating`（name）、`FormattingDevice`（name） |
| `usb{N}_device` | `item.device_name` | 第N个USB设备路径 | `MountedDevice`（device） |
| `usb{N}_z{M}` | `item.zone_name[]` | 第N个USB设备第M个分区名（如 sdb1） | `EditUsbLabel`（device_name）、`FormattingDevice`（分区场景） |
| `usb{N}_s{M}` | `shared_folders[].shared_name` | 第N个USB设备第M个共享文件夹名 | `UsbAclAll` / `SetUsbAclAll` |
| `usb{N}_mnt` | 挂载状态(1)分区 device_name 逗号拼接 | 已挂载分区列表 | 挂载状态相关场景 |
| `usb{N}_umnt` | 未挂载状态(2)分区 device_name 逗号拼接 | 未挂载分区列表 | 未挂载场景 |
| `usb{N}_fmt` | 格式化中状态(3)分区 device_name 逗号拼接 | 格式化中分区列表 | 格式化中场景 |
| `usb_count` | `items.length` | USB设备总数 | 脚本内部 |

> ⚠️ 分区变量命名：用例中引用 **`{{usb1_z1}}`**（第1个分区）、**`{{usb1_z2}}`**（第2个分区）——不要用 `usb1_part_name`（历史旧名已废弃）。执行前脚本会清空上一轮全部 `usb*_*` 变量（前缀扫描清理）。

**生成接口**：`POST /v2/extStorageDevice/ObtainSecretKey`（获取密钥文件路径）

**后置脚本**：`21_usb_obtain_key.js`

| 变量名 | 提取来源 | 含义 | 使用方 |
|--------|----------|------|--------|
| `usb_key_data` | `data` 兼容 string/对象多字段 | Base64密钥文件路径 | `DownloadSecretKey`（data） |

---

## 九点九、HyperCache 模块变量（2026-07-28 新增）

**生成接口**：`GET /v2/lvmCache/CacheLvsInfo`（获取SSD缓存列表）

**后置脚本**：`22_hc_cache_list.js`（前缀扫描清理 + 状态/RAID级别/盘类型条件分类）

| 变量名 | 提取来源 | 含义 | 使用方 |
|--------|----------|------|--------|
| `hc{N}_uuid` | `lv_uuid/uuid/cache_uuid` | 第N个缓存逻辑卷UUID | `DeleteCacheLv`（lv_uuid） |
| `hc_md1_uuid` | 状态=降阶 且 RAID1 | 降阶RAID1缓存阵列UUID | `FixLvmCache`（md_uuid） |
| `hc_md5_uuid` | 状态=降阶 且 RAID5 | 降阶RAID5缓存阵列UUID | 同上 |
| `hc_md_ok_uuid` | 状态=正常 且 RAID1 | 正常RAID1阵列UUID | 正常阵列修复失败场景 |
| `hc_md_ok0_uuid` | 状态=正常 且 RAID0 | 正常RAID0阵列UUID | 同上 |
| `hc_md_bad1_uuid` | 状态=损坏 且 RAID1 | 损坏RAID1阵列UUID | 损坏阵列修复失败场景 |
| `hc_md_bad0_uuid` | 状态=损坏 且 RAID0 | 损坏RAID0阵列UUID | 同上 |
| `hc_md_repair_uuid` | 状态=修复中 | 修复中阵列UUID | 修复中互斥场景 |
| `hc_md_mix_uuid` | 磁盘类型含SSD且NVMe | SSD+NVMe混合阵列UUID | 混合阵列修复场景 |
| `hc_md_ssd_uuid` | 磁盘类型仅SSD | 纯SSD阵列UUID | 纯SSD阵列修复场景 |
| `hc_md_nvme_uuid` | 磁盘类型仅NVMe | 纯NVMe阵列UUID | 纯NVMe阵列修复场景 |
| `creating_hc_uuid` | 状态=创建中 | 创建中缓存UUID | 创建中任务互斥场景 |
| `deleted_hc_uuid` | 状态=已删除（通常列表不含） | 已删除缓存UUID | 已删除缓存场景 |

**生成接口**：`GET /v2/lvmCache/GetVolumeList`（获取可加速卷列表）

**后置脚本**：`23_hc_volume_list.js`

| 变量名 | 提取来源 | 含义 | 使用方 |
|--------|----------|------|--------|
| `hc_lv_path` | 首条正常可加速卷路径 | 可加速卷路径 | `CreateCacheLv`（main_lv） |
| `hc_lv_cached` | 状态含cache | 已有缓存的卷路径 | 已有缓存卷创建失败场景 |
| `corrupt_lv_path` | 状态损坏 | 损坏卷路径 | 损坏卷创建失败场景 |
| `unmount_lv_path` | 状态未挂载 | 未挂载卷路径 | 未挂载卷创建失败场景 |
| `big_lv_path` | 容量>1TB 或标记大容量 | 大容量卷路径 | 卷容量大于阵列失败场景 |

**生成接口**：`GET /v2/lvmCache/FreeSSDs`（获取空闲SSD列表）

**后置脚本**：`24_hc_free_ssds.js`

| 变量名 | 提取来源 | 含义 | 使用方 |
|--------|----------|------|--------|
| `hc_cand_ssd` / `_ssd2` / `_ssd3` | SSD类型（含默认） | 候选SSD设备路径（按序） | `CreateCacheLv`（fast_devices）、`FixLvmCache`（disk_list） |
| `hc_cand_nvme` | NVMe类型 | 候选NVMe设备路径 | 同上 |
| `hc_cand_hdd` | HDD类型 | 候选HDD设备路径 | 类型不匹配失败场景 |

---

## 十二、环境配置变量（无后置脚本产出，需手工配置）

以下变量依赖真实硬件/网络环境，**没有接口后置脚本自动产出**，须在 Apifox 环境变量中手工配置：

| 变量名 | 说明 |
|--------|------|
| `iscsi_lan_ip` | 同网段iSCSI服务端IP（B机） |
| `wan_target_iqn` | 不同网段Target的IQN |
| `iscsi_single_target` | 不允许多重连接的Target IQN |
| `iscsi_multi_target` | 允许多重连接的Target IQN |
| `deleted_target_iqn` | 已删除虚拟磁盘的IQN |
| `other_lunid` | 另一Target下已连接虚拟磁盘的LUN编号 |
| `warn_disk` / `error_disk` | SMART状态为警告/错误的磁盘路径 |
| `locked_disk` / `removed_disk` / `4kn_disk` | 锁定/已移除/4KN磁盘路径 |
| `mounted_disk` / `pool_disk` / `sys_disk` | 已挂载/存储池用/系统盘路径 |
| `small_disk` | 容量小于阵列要求的最小容量磁盘路径 |
| `cache_disk` / `repair_disk` | 已用于缓存阵列/修复阵列的磁盘路径 |
| `usb_ssd_device` | USB设备中的SSD路径 |
| `usb_sata_*` / `usb_nvme_*` / `usb_other_*` / `sdtf_*` | USB/SD外设的 device/model/serial（GetDiskOption 手工筛选） |
| `usb1_umnt_share` | 未挂载USB的共享文件夹名（未挂载获取权限失败场景；亦可由20脚本 usb{N}_umnt 未挂载分区名配合构造） |
| `removed_usb` | 已被安全移除的USB设备分区名（已移除设备卸载失败场景） |
| `usb1_encrypted_share` | 已加密USB的共享文件夹名（未挂载加密获取权限失败场景） |
| `wrong_X-Curpass-Token` | 错误密码令牌（由 verify_pwd 后置脚本或手工配置） |
| `X-Curpass-Token` | 密码验证令牌（由 POST /v2/otp/verify_pwd 产出） |

---

## 十三、脚本文件索引（2026-07-28 更新）

| 编号 | 文件名 | 对应接口 | 产出的变量 | 编码模式 |
|------|--------|----------|-----------|----------|
| 20 | `20_usb_device_list.js` | `GET /v2/extStorageDevice/DeviceList` | `usb{N}_name`, `usb{N}_device`, `usb{N}_z{M}`, `usb{N}_s{M}`, `usb{N}_mnt/umnt/fmt`, `usb_count` | 前缀扫描清理 + 状态分类（原20号verify_pwd脚本已保留于verify_pwd_wrong_curpass.js） |
| 21 | `21_usb_obtain_key.js` | `POST /v2/extStorageDevice/ObtainSecretKey` | `usb_key_data` | 单值全量同步 + 空值清除 |
| 22 | `22_hc_cache_list.js` | `GET /v2/lvmCache/CacheLvsInfo` | `hc{N}_uuid`, `hc_md*_uuid` 系列, `creating_hc_uuid`, `deleted_hc_uuid` | 前缀扫描清理 + 状态/级别/类型条件分类 |
| 23 | `23_hc_volume_list.js` | `GET /v2/lvmCache/GetVolumeList` | `hc_lv_path`, `hc_lv_cached`, `corrupt_lv_path`, `unmount_lv_path`, `big_lv_path` | 清理 + 状态条件分类 |
| 24 | `24_hc_free_ssds.js` | `GET /v2/lvmCache/FreeSSDs` | `hc_cand_ssd`/`_ssd2`/`_ssd3`, `hc_cand_nvme`, `hc_cand_hdd` | 清理 + 类型条件分类 |


---

## 九点十、USB/SD 外设磁盘变量（2026-07-28 新增）

**生成接口**：`GET /v2/disk/GetDiskOption`（获取硬盘下拉选项）

**后置脚本**：`25_disk_usb_classify.js`（与 10/11 号脚本同挂此接口，负责外设分类）

| 变量名 | 判定依据 | 含义 | 使用方 |
|--------|----------|------|--------|
| `usb_disk_device` / `usb_disk_name` | type/interface 含 usb | 第一块USB磁盘 | 挂载/卸载/移除/启用/坏块扫描等磁盘模块接口 |
| `usb_sata_device/model/serial` | USB 且含 sata/ata | USB中的SATA盘 | GetDiskDetailData、SMART任务创建/编辑 |
| `usb_nvme_device/model/serial` | USB 且含 nvme | USB中的NVMe盘 | 同上 |
| `usb_other_device/model/serial` | USB 且非SATA/NVMe | USB其他类型设备 | 同上 |
| `sdtf_device/model/serial` | 含 sd/mmc/tf/sdtf/card | SD/TF卡 | SMART不支持场景、安全擦除、新增系统盘失败场景 |
| `usb_ssd_device` | 取 usb_sata/usb_other/usb_disk | USB中的SSD路径 | HyperCache 候选盘场景 |

> 执行前清空上一轮 `usb_(disk|sata|nvme|other|ssd)_*` 与 `sdtf_*` 变量（前缀扫描清理，保留 `usb{N}_*` 编号变量不受影响）。model/serial 字段缺省时自动 unset 不残留。

---

## 十三、脚本文件索引（2026-07-28 更新）

| 编号 | 文件名 | 对应接口 | 产出的变量 | 编码模式 |
|------|--------|----------|-----------|----------|
| 25 | `25_disk_usb_classify.js` | `GET /v2/disk/GetDiskOption` | `usb_disk_device/name`, `usb_sata/nvme/other_device/model/serial`, `sdtf_device/model/serial`, `usb_ssd_device` | 前缀扫描清理 + 类型条件分类 |
