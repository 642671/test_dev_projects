# SSH 连接配置说明

## 方案对比

### ❌ SSH Config 不能直接保存密码
SSH 标准配置文件 (~/.ssh/config) **不支持**密码字段,这是 SSH 协议的安全设计。

### ✅ 推荐方案:使用 sshpass

#### 第一步:安装 sshpass
1. 下载: https://github.com/kevinburke/sshpass/releases
2. 将 `sshpass.exe` 放到 `C:\Windows\System32\`

#### 第二步:在 Qoder 终端使用(3种方式)

**方式 1: 直接命令(最简单)**
```bash
sshpass -p 'Admin123' ssh -p 9222 test@10.18.15.170
```

**方式 2: 使用 PowerShell 脚本**
```powershell
.\ssh_connect.ps1
```

**方式 3: 使用批处理文件**
```cmd
ssh_connect.bat tnas
```

### 🔥 最便捷:创建 PowerShell 别名

在 Qoder 终端的 PowerShell 中执行:

```powershell
# 编辑配置文件
notepad $PROFILE

# 添加以下内容:
function ssh-tnas {
    sshpass -p 'Admin123' ssh -p 9222 test@10.18.15.170
}
Set-Alias -Name tnas -Value ssh-tnas

# 保存后重新加载:
. $PROFILE
```

之后在 Qoder 终端只需输入:
```
tnas
```
就能直接连接!

## 为什么 SSH Config 不能保存密码?

SSH 协议设计上就不允许在配置文件中存储密码,原因:
1. 安全考虑 - 配置文件可能被其他人读取
2. 协议限制 - SSH 标准不支持这个功能
3. 最佳实践 - 推荐使用密钥认证或 sshpass 等工具

## 总结

| 方案 | 是否能在 Qoder 使用 | 是否需要额外工具 | 密码保存位置 |
|------|-------------------|----------------|------------|
| SSH Config | ❌ 不支持密码 | 否 | - |
| sshpass + 命令 | ✅ | 是(sshpass.exe) | 命令行 |
| PowerShell 别名 | ✅ | 是(sshpass.exe) | $PROFILE 文件 |
| PowerShell 脚本 | ✅ | 是(sshpass.exe) | 脚本文件 |

**推荐: PowerShell 别名方案** - 最简洁,最接近你想要的效果!
