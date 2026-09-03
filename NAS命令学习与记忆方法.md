# NAS 命令学习与记忆方法

> 适用对象：TerraMaster TOS NAS（以当前 `F8-32`、SSH 端口 `9222`、账号 `test`、Codex 密钥登录为例）
> 重要：本手册把命令分成两类：
> - **查看类**：只读，不修改系统，适合日常学习。
> - **变更类**：会停止服务、删除卷、删除存储池、清理 RAID，必须确认目标和授权后再执行。

---

## 一、先建立一个大框架：这些命令在问什么问题？

| 你想知道什么 | 常用命令 | 中文联想 |
|---|---|---|
| 物理卷、卷组、逻辑卷 | `pvs`、`vgs`、`lvs` | 一层一层看“物理卷 → 卷组 → 逻辑卷” |
| 磁盘和分区 | `lsblk` | List Block = 列出磁盘块设备 |
| 目录挂载在哪里 | `findmnt`、`mount` | Find Mount = 找挂载 |
| 谁占用了目录/文件 | `fuser`、`lsof` | File User / List Open Files |
| 进程详情 | `ps` | Process Status = 进程状态 |
| 后台服务 | `systemctl` | System Control = 系统控制 |
| 日志 | `journalctl` | Journal Control = 看日志 |
| RAID 状态 | `mdadm --detail` | MD Array 的管理工具 |
| 系统实际执行了什么 | `strace` | System Call Trace = 跟踪系统调用 |

记忆口诀：

> **先看“状态”，再看“占用”，再看“服务”，最后才看“日志”。**

---

## 二、逐条讲解这次用到的命令

### 1. 连接 NAS

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes 15.135 'pvs; vgs; lvs'
```

拆解：

| 部分 | 意思 |
|---|---|
| `ssh` | 远程登录 Linux 主机 |
| `-o BatchMode=yes` | 不能弹密码输入框；只能使用已配置的密钥，适合自动化 |
| `-o StrictHostKeyChecking=yes` | 严格校验主机指纹，防止连错机器 |
| `15.135` | SSH 配置里的别名，实际对应一个 IP |
| `'pvs; vgs; lvs'` | 登录后依次执行三条命令 |

### 2. 查看磁盘和存储层

```bash
pvs
vgs
lvs
lsblk
findmnt
mount
```

- `pvs`：Physical Volume Status，物理卷
- `vgs`：Volume Group Status，卷组
- `lvs`：Logical Volume Status，逻辑卷
- `lsblk`：List Block Devices，磁盘块设备
- `findmnt`：查看目录是否挂载，挂载到哪里
- `mount`：查看当前所有挂载（更原始的输出）

记忆方法：

> **P = Physical，V = Volume Group，L = Logical。**
> 三个命令都带一个 `s`，意思是“状态 Status”。

### 3. 查看“谁占用了 /Volume1”

```bash
fuser -mv /Volume1
```

- `fuser`：File User，查找正在使用某个文件的进程
- `-m`：Mount，把它当作一个挂载点来检查
- `-v`：Verbose，显示更详细的信息（用户、PID、命令名）

```bash
lsof +D /Volume1
lsof +L1 /Volume1
```

- `lsof`：List Open Files，列出被打开的文件
- `+D`：Directory，递归检查这个目录
- `+L1`：专门看“已经删除但仍被占用的文件”

```bash
find /proc/[0-9]*/fd -lname '/Volume1/*' -printf '%p -> %l\n'
```

这行是“精确定位”的核心：

- `find`：查找
- `/proc/[0-9]*/fd`：Linux 把所有进程放在 `/proc/<PID>` 下；`fd` 是它打开的文件描述符
- `[0-9]*`：匹配所有数字，也就是所有 PID
- `-lname '/Volume1/*'`：找指向 `/Volume1/...` 的链接
- `-printf '%p -> %l\n'`：打印“进程路径 -> 文件路径”

结果例如：

```text
/proc/142116/fd/10 -> /Volume1/@apps/diskcheck/depends/data/scan-units/job_xxx.bin
```

这句的意思是：**进程 142116 打开着 Volume1 下的文件，所以 Volume1 被占用。**

---

## 三、为什么有的命令是 `-v`，有的不是 `-d`？

你问得很对：`详细 detail` 按英文第一印象应该是 `-d`，为什么这里用 `-v`？

答案很简单：

> **详细对应的是英文 `verbose`，不是 `detail`。**
> `verbose` 的意思是“话很多、输出很详细”，首字母是 `v`，所以习惯用 `-v`。

记忆方法：

- `v` 可以记成 **Verbose（啰嗦、说很多话）**
- `d` 在很多命令里已经“被占用”了，代表目录、设备、调试、深度等意思

例如：

| 命令 | 选项 | 含义 |
|---|---|---|
| `fuser -v` | `-v` | 显示详细占用信息（Verbose） |
| `pvs -v` | `-v` | 显示更详细的物理卷信息 |
| `vgs -v` | `-v` | 显示更详细的卷组信息 |
| `lvs -v` | `-v` | 显示更详细的逻辑卷信息 |
| `ls -d /Volume1` | `-d` | 只看 `/Volume1` 这个目录本身，不看里面的内容 |
| `find . -depth` | `-depth` | 深度优先遍历 |

注意：**同一个字母在不同命令里含义可能不同。**
例如 `ls -v` 可能表示“按版本号排序”，不是“详细输出”。
所以学习时记住这个原则：

> **先看命令是干什么的，再看这个字母在这条命令里代表什么。**
> 不要假设所有命令的 `-v` 都一模一样。

---

## 四、进程、服务的对应关系

拿到 PID 后，还要知道它属于哪个后台服务。

```bash
ps -o pid,ppid,user,stat,comm,args -p 142116
```

选项含义：

- `-o`：Output，自定义输出列
- `pid`：进程编号
- `ppid`：父进程编号
- `user`：运行用户
- `stat`：状态
- `comm`：程序名
- `args`：完整启动命令

```bash
readlink /proc/142116/exe
cat /proc/142116/cgroup
```

- `readlink /proc/<PID>/exe`：看这个进程运行的是哪个程序文件
- `cat /proc/<PID>/cgroup`：看它属于哪个 systemd 服务

```bash
systemctl status 142116 --no-pager
```

- `systemctl`：System Control，管理服务
- `status`：查看服务状态
- `--no-pager`：不要分页，直接输出全部内容

如果看到：

```text
diskcheck-helper.service
```

就说明这个 PID 属于 `diskcheck-helper.service`。

---

## 五、日志怎么查

```bash
systemctl list-units --all --no-pager --plain | grep -i diskcheck
```

拆解：

- `systemctl list-units --all`：列出所有服务
- `--no-pager`：不分页
- `--plain`：输出成简单的纯文本
- `|`：管道，把左边输出交给右边
- `grep`：筛选文字
- `-i`：Ignore Case，忽略大小写

```bash
journalctl -u StorageManager.service --no-pager --since '2026-09-02 14:00:00' --until '2026-09-02 14:30:00'
```

- `journalctl`：看 systemd 日志
- `-u`：Unit，只看某个服务
- `--since`：从什么时间开始
- `--until`：到什么时间结束

记忆方法：

> **`-u` 是 Unit，`-n` 是 Number，`--since/--until` 是一段时间。**

---

## 六、RAID 和 LVM 的“变更类”命令

下面这些命令**会改变系统状态**，只用于学习理解，不要直接复制执行。

```bash
vgremove vg0
```

- `vgremove`：Remove Volume Group，删除卷组
- 这里 `vg` = Volume Group
- 必须确保卷组里没有正在使用的 LV

```bash
pvremove /dev/md0
```

- `pvremove`：删除物理卷的 LVM 元数据
- `pv` = Physical Volume

```bash
lvremove /dev/mapper/vg0-lv0
```

- `lvremove`：删除逻辑卷
- `lv` = Logical Volume

```bash
mdadm --stop /dev/md0
mdadm --zero-superblock /dev/sdzg4
```

- `mdadm --stop`：停止 RAID 阵列
- `mdadm --zero-superblock`：清除 RAID 超级块，相当于让设备“忘记”它是 RAID 成员
- 这两个命令非常危险，尤其是 `/dev/sdzg` 上同时还有系统分区

记忆方法：

> **`lv` 是逻辑卷，`pv` 是物理卷，`vg` 是卷组；**
> **加 `remove` 就是删除对应的层。**

---

## 七、追踪“到底执行了什么命令”

删除失败时报 `exit status 127`，这种错误一般表示：

> 程序想执行某个命令，但系统找不到它。

如果你想抓到具体命令，可以用：

```bash
strace -f -e trace=execve -p 630642 -o /tmp/storagemanager.strace
```

- `strace`：跟踪系统调用
- `-f`：Follow，同时跟踪子进程
- `-e trace=execve`：只看“启动程序”的动作
- `-p`：附加到指定 PID
- `-o`：保存到文件

`execve` 就是“执行一个程序”的系统调用。
如果看到它尝试执行某个不存在的命令，就能解释 `exit status 127`。

---

## 八、今天的实战排查顺序

这次排查存储池 `vg0`，顺序是：

```text
1. SSH 登录
2. pvs / vgs / lvs          查看 LVM 状态
3. lsblk / findmnt         查看磁盘和挂载
4. fuser / lsof / /proc    找到占用 Volume1 的进程
5. ps / readlink / cgroup  把 PID 对应到服务
6. systemctl               查看和停止相关服务
7. umount /Volume1         卸载目录
8. journalctl              查看删除失败日志
9. strace                  再抓具体执行的命令
```

记住这个顺序，你以后遇到类似问题就不会乱。

---

## 九、安全提醒

- `pvs`、`vgs`、`lvs`、`lsblk`、`findmnt`、`fuser`、`lsof`、`journalctl` 都是查看类，可以放心学习。
- `systemctl stop` 会停止服务；`umount` 会卸载目录；`lvremove`、`vgremove`、`pvremove`、`mdadm --stop`、`mdadm --zero-superblock` 都是高危变更。
- 对 NAS 做变更前，先确认三件事：
  1. 目标机器是否正确；
  2. 目标路径是否为你要操作的路径；
  3. 是否已经备份或有恢复方案。
- 本手册中的命令以当前 TOS NAS 为例，细节可能因版本不同而变化，实际执行前应以当前系统帮助和产品文档为准。
