# 新增 code\_num 与 code\_msg

| code\_num | code\_msg | 描述 |
| --- | --- | --- |
| 用整数，0 固定为成功，非 0 为各类异常，取值唯一 | 错误码所携带的信息，简短英文描述 | 用自然语言解释"什么情况下会返回这个错误码"，方便后续查阅和测试断言 |
|  |  |  |
|  |  |  |

# 现有code\_num与code\_msg

| code\_num | code\_msg | 描述 |
| --- | --- | --- |
| 用整数，0 固定为成功，非 0 为各类异常，取值唯一 | 错误码所携带的信息，简短英文描述 | 用自然语言解释"什么情况下会返回这个错误码"，方便后续查阅和测试断言 |
| 1 | `"failed to get cron from db"` | 从数据库查询 cron 任务失败 |
| 2 | `"failed to delete from db"` | 从数据库删除记录失败 |
| 3 | `"failed to create"` | 创建操作失败 |
| 4 | `"invalid cron format"` | cron 表达式格式不合法 |
| 5 | `"invalid cron id"` | cron 任务 ID 不合法 |
| 6 | `"invalid command argument"` | 命令参数不合法 |
| 7 | `"failed to create item from db"` | 从数据库创建条目失败 |
| 8 | `"invalid id"` | ID 不合法 |
| 9 | `"id not found"` | 指定 ID 的记录不存在 |
| 10 | `"failed to get task"` | 获取任务失败 |
| 11 | `"failed to update task"` | 更新任务失败 |
| 12 | `"duplicated task name"` | 任务名称重复 |
| 13 | `"invalid task name"` | 任务名称不合法 |
| 14 | `"client ip blocked by system"` | 客户端 IP 已被系统封禁 |
| 15 | `"client ip blocked by system, but release after few days"` | 客户端 IP 已被封禁，将在几天后自动解封 |
| 16 | `"verification code error"` | 验证码错误 |
| 17 | `"invalid rsa code"` | RSA 加密验证码不合法 |
| 19 | `"missing request header"` | 缺少必需的请求头 |
| 20 | `"authentication expired"` | 认证已过期 |
| 21 | `"invalid argument"` | 参数不合法 |
| 22 | `"invalid password format"` | 密码格式不合法 |
| 23 | `"target disk is not free"` | 目标磁盘已被占用 |
| 24 | `"missing session"` | 缺少会话凭证 |
| 25 | `"local IP cannot be blocked"` | 本机 IP 不可被封禁 |
| 26 | `"can not delete hyper-lock volume"` | 无法删除处于锁定状态的卷 |
| 27 | `"account has been disabled"` | 账号已被禁用 |
| 28 | `"account has been expired"` | 账号已过期 |
| 29 | `"account authentication failed"` | 账号认证失败 |
| 30 | `"Invalid JSON Format"` | JSON 格式不合法 |
| 31 | `"Incorrect Firewall Rules"` | 防火墙规则不正确 |
| 32 | `"config already exist"` | 配置已存在 |
| 33 | `"not empty"` | 资源非空，无法执行操作 |
| 34 | `"source path can not be used"` | 源路径不可用 |
| 35 | `"source path already exist"` | 源路径已存在 |
| 36 | `"Bad Password"` | 密码错误 |
| 37 | `"Mount Device Failed"` | 挂载设备失败 |
| 38 | `"Email exceed sent out limit"` | 邮件发送次数超出限制 |
| 39 | `"insufficient free memory"` | 可用内存不足 |
| 40 | `"insufficient hard disk capacity"` | 硬盘容量不足 |
| 41 | `"otp enabled and need to authentication"` | 已启用 OTP，需要完成二次认证 |
| 42 | `"otp code number error"` | OTP 验证码错误 |
| 43 | `"name contains illegal characters"` | 名称包含非法字符 |
| 90 | `"permission denied"` | 权限不足 |
| 91 | `"app not installed"` | 应用未安装 |
| 94 | `"invalid app id"` | 应用 ID 不合法 |
| 95 | `"invalid app package"` | 应用安装包不合法 |
| 96 | `"update failed"` | 更新失败 |
| 97 | `"the user is forbid"` | 用户已被禁止访问 |
| 98 | `"invalid user"` | 用户不合法 |
| 99 | `"invalid api socket"` | API socket 连接不合法 |
| 100 | `"internal error"` | 内部错误 |
| 101 | `"occupied by snapshots"` | 被快照占用 |
| 102 | `"error authentication parameter"` | 认证参数错误 |
| 103 | `"smb auth error"` | SMB 认证错误 |
| 104 | `"path does not exist"` | 路径不存在 |
| 105 | `"invalid request parameter"` | 请求参数不合法 |
| 106 | `"Failed to save config data"` | 保存配置数据失败 |
| 107 | `"Failed to get config data"` | 获取配置数据失败 |
| 108 | `"please select a file"` | 请选择一个文件 |
| 109 | `"invalid file"` | 文件不合法 |
| 110 | `"storage hard drive mixed use"` | 存储硬盘混用（不同规格硬盘混合使用） |
| 111 | `"not enough storage space"` | 存储空间不足 |
| 112 | `"the coffer path cannot be manipulated"` | 保险箱路径不可操作 |
| 113 | `"file failed to delete"` | 文件删除失败 |
| 114 | `"Failed to conn the cloud disk"` | 云盘连接失败 |
| 115 | `"Unsupported file system format"` | 不支持的文件系统格式 |
| 116 | `"Directory is occupied"` | 目录被占用 |
| 117 | `"please login"` | 请先登录 |
| 118 | `"name already exists"` | 名称已存在 |
| 119 | `"Insufficient disk space"` | 磁盘空间不足 |
| 120 | `"Service Not Be Found"` | 服务未找到 |
| 121 | `"File error, cannot install"` | 文件错误，无法安装 |
| 122 | `"failed to delete volume"` | 删除卷失败 |
| 125 | `"The destination folder or virtual device has been mounted"` | 目标文件夹或虚拟设备已被挂载 |
| 126 | `"Read-only file system"` | 文件系统为只读 |

| code\_num | code\_msg | 描述 |
| --- | --- | --- |
| -1 | `""` | 未指定错误码 |
| 0 | `"OK"` | 成功 |
| 50 | `"Internal Error"` | 内部错误 |
| 51 | `"Validation Failed"` | 数据校验失败 |
| 52 | `"Database Operation Error"` | 数据库操作错误 |
| 53 | `"Invalid Parameter"` | 参数不合法 |
| 54 | `"Missing Parameter"` | 缺少必需参数 |
| 55 | `"Invalid Operation"` | 操作不合法（函数使用方式错误） |
| 56 | `"Invalid Configuration"` | 配置不合法 |
| 57 | `"Missing Configuration"` | 缺少必需配置 |
| 58 | `"Not Implemented"` | 功能尚未实现 |
| 59 | `"Not Supported"` | 功能不支持 |
| 60 | `"Operation Failed"` | 操作执行失败 |
| 61 | `"Not Authorized"` | 未授权 |
| 62 | `"Security Reason"` | 安全原因拒绝访问 |
| 63 | `"Server Is Busy"` | 服务繁忙，请稍后重试 |
| 64 | `"Unknown Error"` | 未知错误 |
| 65 | `"Not Found"` | 资源不存在 |
| 66 | `"Invalid Request"` | 请求不合法 |
| 300 | `"Business Validation Failed"` | 业务校验失败 |

```sql
gcode.New(1, "failed to get cron from db", nil)
gcode.New(2, "failed to delete from db", nil)
gcode.New(3, "failed to create", nil)
gcode.New(4, "invalid cron format", nil)
gcode.New(5, "invalid cron id", nil)
gcode.New(6, "invalid command argument", nil)
gcode.New(7, "failed to create item from db", nil)
gcode.New(8, "invalid id", nil)
gcode.New(9, "id not found", nil)
gcode.New(10, "failed to get task", nil)
gcode.New(11, "failed to update task", nil)
gcode.New(12, "duplicated task name", nil)
gcode.New(13, "invalid task name", nil)
gcode.New(14, "client ip blocked by system", nil)
gcode.New(15, "client ip blocked by system, but release after few days", nil)
gcode.New(16, "verification code error", nil)
gcode.New(17, "invalid rsa code", nil)
gcode.New(19, "missing request header", nil)
gcode.New(20, "authentication expired", nil)
gcode.New(21, "invalid argument", nil)
gcode.New(22, "invalid password format", nil)
gcode.New(23, "target disk is not free", nil)
gcode.New(24, "missing session", nil)
gcode.New(25, "local IP cannot be blocked", nil)
gcode.New(26, "can not delete hyper-lock volume", nil)
gcode.New(27, "account has been disabled", nil)
gcode.New(28, "account has been expired", nil)
gcode.New(29, "account authentication failed", nil)
gcode.New(30, "Invalid JSON Format", nil)
gcode.New(31, "Incorrect Firewall Rules ", nil)
gcode.New(32, "config already exist", nil)
gcode.New(33, "not empty", nil)
gcode.New(34, "source path can not be used", nil)
gcode.New(35, "source path already exist", nil)
gcode.New(36, "Bad Password", nil)
gcode.New(37, "Mount Device Failed", nil)
gcode.New(38, "Email exceed sent out limit", nil)
gcode.New(39, "insufficient free memory", nil)
gcode.New(40, "insufficient hard disk capacity", nil)
gcode.New(41, "otp enabled and need to authentication", nil)
gcode.New(42, "otp code number error", nil)
gcode.New(43, "name contains illegal characters", nil)
gcode.New(90, "permission denied", nil)
gcode.New(91, "app not installed", nil)
gcode.New(94, "invalid app id", nil)
gcode.New(95, "invalid app package", nil)
gcode.New(96, "update failed", nil)
gcode.New(97, "the user is forbid", nil)
gcode.New(98, "invalid user", nil)
gcode.New(99, "invalid api socket", nil)
gcode.New(100, "internal error", nil)
gcode.New(101, "occupied by snapshots", nil)
gcode.New(102, "error authentication parameter", nil)
gcode.New(103, "smb auth error", nil)
gcode.New(104, "path does not exist", nil)
gcode.New(105, "invalid request parameter", nil)
gcode.New(106, "Failed to save config data", nil)
gcode.New(107, "Failed to get config data", nil)
gcode.New(108, "please select a file", nil)
gcode.New(109, "invalid file", nil)
gcode.New(110, "storage hard drive mixed use", nil)
gcode.New(111, "not enough storage space", nil)
gcode.New(112, "the coffer path cannot be manipulated", nil)
gcode.New(113, "file failed to delete", nil)
gcode.New(114, "Failed to conn the cloud disk", nil)
gcode.New(115, "Unsupported file system format", nil)
gcode.New(116, "Directory is occupied", nil)
gcode.New(117, "please login", nil)
gcode.New(118, "name already exists", nil)
gcode.New(119, "Insufficient disk space", nil)
gcode.New(120, "Service Not Be Found", nil)
gcode.New(121, "File error,cannot install", nil)
gcode.New(122, "failed to delete volume", nil)
gcode.New(125, "The destination folder or virtual device has been mounted", nil)
gcode.New(126, "Read-only file system", nil)



-----

localCode{-1, "", nil}                            // No error code specified.
localCode{0, "OK", nil}                           // It is OK.
localCode{50, "Internal Error", nil}              // An error occurred internally.
localCode{51, "Validation Failed", nil}           // Data validation failed.
localCode{52, "Database Operation Error", nil}    // Database operation error.
localCode{53, "Invalid Parameter", nil}           // The given parameter for current operation is invalid.
localCode{54, "Missing Parameter", nil}           // Parameter for current operation is missing.
localCode{55, "Invalid Operation", nil}           // The function cannot be used like this.
localCode{56, "Invalid Configuration", nil}       // The configuration is invalid for current operation.
localCode{57, "Missing Configuration", nil}       // The configuration is missing for current operation.
localCode{58, "Not Implemented", nil}             // The operation is not implemented yet.
localCode{59, "Not Supported", nil}               // The operation is not supported yet.
localCode{60, "Operation Failed", nil}            // I tried, but I cannot give you what you want.
localCode{61, "Not Authorized", nil}              // Not Authorized.
localCode{62, "Security Reason", nil}             // Security Reason.
localCode{63, "Server Is Busy", nil}              // Server is busy, please try again later.
localCode{64, "Unknown Error", nil}               // Unknown error.
localCode{65, "Not Found", nil}                   // Resource does not exist.
localCode{66, "Invalid Request", nil}             // Invalid request.
localCode{300, "Business Validation Failed", nil} // Business validation failed.
```