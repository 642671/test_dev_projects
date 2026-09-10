# 存储管理 Apifox → JMeter 导入说明

## 1. 来源

Apifox CLI 版本：

```text
apifox 2.2.9
```

目标项目：

```text
项目 ID：8758195
项目名称：TANS
来源目录：07 存储管理
```

使用 CLI 导出：

```powershell
apifox export `
  --project 8758195 `
  --format apifox `
  --scope folders `
  --folder-ids 94377996 `
  --no-include-api-cases `
  --output "D:\test_dev_projects\Jmeter\06-导入源\Apifox-存储管理-最新.apifox.json"
```

## 2. 导入结果

生成文件：

```text
D:\test_dev_projects\Jmeter\01-测试计划\TNAS存储管理接口测试计划_存储管理API导入版_20260903.jmx
```

原文件保留：

```text
D:\test_dev_projects\Jmeter\01-测试计划\TNAS存储管理接口测试计划.jmx
```

### 统计

| 项目 | 数量 |
|---|---:|
| 存储管理接口 | 135 |
| 概要 | 2 |
| 卷 | 17 |
| 存储池 | 23 |
| 磁盘 | 50 |
| 虚拟磁盘 | 13 |
| USB 设备 | 15 |
| 热备盘 | 6 |
| Hyper Cache | 9 |
| GET | 60 |
| POST / PUT / DELETE | 75 |
| 默认启用的接口 | 135（读取 + 写接口全部启用） |
| 默认禁用的接口 | 0 |
| Apifox 自定义后置脚本 | 18 |
| Apifox 内置提取器 | 1 |

18 个 Apifox 自定义后置脚本的原始 JS 参考文件保留在：

```text
Jmeter\06-导入源\apifox后置脚本\
```

## 3. 使用前必须知道

### 3.1 关闭旧 JMeter 窗口再打开

如果你已经打开旧 JMX，先关闭，再打开：

```text
Jmeter\01-测试计划\TNAS存储管理接口测试计划_存储管理API导入版_20260903.jmx
```

否则手动保存可能覆盖它。

### 3.2 先确认登录变量

在测试计划根节点“用户定义的变量”里检查：

```text
server_ip
server_port
super_admin_username
super_admin_password
```

当前版本禁用管理员和普通用户线程，只保留超级管理员登录流程。

### 3.3 写接口状态

当前测试机是专门用于测试的机器，因此生成版中：

```text
所有存储管理接口默认启用
GET / POST / PUT / DELETE 均可直接运行
```

运行时仍建议先确认当前 `server_ip`、目标设备、卷、LUN、USB 名称，避免把测试数据填错到其它设备上。

### 3.4 JavaScript 后置脚本依赖

Apifox 的 18 个自定义后置脚本已经转成 JMeter `JSR223PostProcessor`，语言为 `javascript`。

JMeter 自带 Rhino 核心库，但需要一个 JSR223 引擎适配器：

```text
Jmeter\06-导入源\lib\rhino-engine-1.7.14.jar
```

对应 Maven 坐标：

```text
org.mozilla:rhino-engine:1.7.14
```

生成 JMX 已在：

```text
TestPlan.user_define_classpath
```

写入该 jar 的绝对路径。换机器后需要修改这个路径。

### 3.5 变量替换

Apifox 中的变量已替换为 JMeter 变量：

| Apifox | JMeter |
|---|---|
| `{{X-Csrf-Token}}` | `${super_admin_csrf_token}` |
| `{{Cookie}}` | `${super_admin_cookie}` |
| `{{NormalUserCookie}}` | `${super_admin_cookie}` |
| `{{NormalUserCsrfToken}}` | `${super_admin_csrf_token}` |
| `{{X-Curpass-Token}}` | `${super_admin_curpass_token}` |
| 其它 `{{xxx}}` | `${xxx}` |

`X-Curpass-Token` 在登录后由前置 RSA 加密逻辑生成：

```text
super_admin_curpass_token = super_admin_encrypted_password
```

## 4. 需要手工填写的变量

因为 Apifox 很多请求依赖前面接口返回的动态值，生成版中统一初始化为：

```text
REPLACE_ME
```

常见依赖关系：

```text
先跑 01 获取卷列表 → 生成 lv0_uuid/lv1_uuid
先跑 01 获取存储池列表 → 生成 vg0_uuid/vg1_uuid
先跑 01 获取硬盘下拉选项 → 生成 disk0_device/disk0_model
先跑 03 获取创建卷资源信息 → 生成 cv_vg0_name/cv_vg0_free_gb
先跑 03 获取创建池资源信息 → 生成 cp_disk_0_path
先跑 01 获取USB设备列表 → 生成 usb1_device/usb1_name
先跑 01 获取阵列列表 → 生成 hs1_vg
```

这些动态变量由 Apifox 后置脚本产生，JMeter 中对应接口的后置处理器已经保留。  
因此如果你按依赖顺序运行，变量会在 JMeter 内存中自动更新；如果跳过前置接口，则需要手工填值。

## 5. 重新生成

```powershell
$env:PYTHONIOENCODING='utf-8'
py -3 "D:\test_dev_projects\Jmeter\06-导入源\generate_storage_jmx.py"
```

生成器只读取当前的：

```text
Jmeter\01-测试计划\TNAS存储管理接口测试计划.jmx
```

不会覆盖这个文件，只会生成新的 `_存储管理API导入版_20260903.jmx`。

## 6. 已知限制

1. JMX 没有给每个存储管理接口添加业务断言，只有登录接口有断言。
2. Apifox 的 `moduleVariables` 已被映射为 JMeter `vars`，后置脚本在 Rhino 引擎中运行。
3. 请求体使用 Apifox 示例；部分接口的 multipart/form-data 没有完整示例，需要按实际接口补充参数。
4. 存储管理接口中涉及物理磁盘、USB、LUN、系统盘等操作，务必只对你确认过的测试设备执行。
5. `/tos/` 是否同时返回 `X-Rsa-Token` 和 `X-Csrf-Token`，以当前测试环境为准；如果缺失，应补查 `/v2/welcome` 或 `/v2/lang/tos`。
