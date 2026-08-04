# SSH 一键连接配置指南

## 目标
在 Qoder 终端中实现类似 Xshell 的"保存密码"功能,一键连接 NAS 服务器。

## 前置条件:安装 sshpass

### Windows 安装 sshpass

1. **下载 sshpass.exe**
   - 访问: https://github.com/kevinburke/sshpass/releases
   - 下载 Windows 版本(通常是 `sshpass.exe`)

2. **安装到系统 PATH**
   
   方式 A: 放到 System32 目录(推荐)
   ```
   将 sshpass.exe 复制到 C:\Windows\System32\
   ```
   
   方式 B: 放到项目目录
   ```
   将 sshpass.exe 放到 d:\test_dev_projects\
   然后在脚本中使用相对路径
   ```

3. **验证安装**
   ```powershell
   sshpass -V
   ```
   应该显示版本信息

## 使用方法

### 方式 1: 使用连接脚本(推荐)

```powershell
# 连接默认服务器(tnas = 10.18.15.170)
.\ssh_connect.ps1

# 或指定服务器
.\ssh_connect.ps1 -Server tnas
.\ssh_connect.ps1 -Server 15.161
```

### 方式 2: 直接命令

```powershell
# 连接到 10.18.15.170
sshpass -p 'Admin123' ssh -p 9222 test@10.18.15.170

# 连接到 10.18.15.161
sshpass -p 'Admin123' ssh -p 9222 test@10.18.15.161
```

### 方式 3: 创建 PowerShell 别名(最便捷)

在 PowerShell 配置文件中添加函数:

1. 编辑配置文件:
```powershell
notepad $PROFILE
```

2. 添加以下函数:
```powershell
function Connect-TNAS {
    sshpass -p 'Admin123' ssh -p 9222 test@10.18.15.170
}

function Connect-15161 {
    sshpass -p 'Admin123' ssh -p 9222 test@10.18.15.161
}

# 设置别名
Set-Alias -Name tnas -Value Connect-TNAS
Set-Alias -Name nas1 -Value Connect-15161
```

3. 重新加载配置:
```powershell
. $PROFILE
```

4. 使用:
```powershell
tnas    # 直接输入别名即可连接
nas1
```

## 优势

✅ **NAS 重装后无需重新配置** - 只要密码不变就能用
✅ **在 Qoder 终端中生效** - 不依赖 Windows 本地配置
✅ **支持多个服务器** - 轻松管理多台 NAS
✅ **密码集中管理** - 修改密码只需改一处
✅ **类似 Xshell 体验** - 一键连接,无需输入密码

## 安全性说明

⚠️ **密码以明文存储在脚本中**

如果你的环境对安全性要求较高,可以考虑:

1. **使用环境变量存储密码**
```powershell
# 设置环境变量(只需设置一次)
$env:NAS_PASSWORD = "Admin123"

# 在脚本中使用
sshpass -p $env:NAS_PASSWORD ssh -p 9222 test@10.18.15.170
```

2. **使用 Windows 凭据管理器**
```powershell
# 保存凭据
cmdkey /add:10.18.15.170 /user:test /pass:Admin123

# 使用凭据(需要配合其他工具)
```

## 常见问题

### Q: 提示 "sshpass: command not found"
A: sshpass 未正确安装或未添加到 PATH。检查:
- sshpass.exe 是否存在于 C:\Windows\System32\
- 执行 `where sshpass` 看是否能找到

### Q: 连接时被拒绝
A: 检查:
- NAS 是否开机
- SSH 服务是否运行
- 端口 9222 是否正确
- 用户名密码是否正确

### Q: 每次都要输入 yes 确认主机密钥
A: 首次连接会提示,输入 yes 后会保存到 known_hosts,以后不会再提示。

### Q: NAS 重装后需要重新配置吗?
A: **不需要!** 只要用户名和密码不变,直接就能用。
   唯一可能需要做的是:如果 NAS IP 变了,更新脚本中的 IP 地址。
   首次连接新系统时会提示确认主机密钥,输入 yes 即可。

## 文件说明

- `ssh_connect.ps1` - 一键连接脚本
- `SSH连接指南.md` - 本说明文档
- `C:\Users\twm\.ssh\config` - SSH 配置文件(可选,用于 Host 别名)
