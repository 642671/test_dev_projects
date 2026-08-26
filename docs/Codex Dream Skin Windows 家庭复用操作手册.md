# Codex Dream Skin Windows 家庭复用操作手册

> 适用场景：在家中的 Windows 电脑上，为 Microsoft Store 安装的 Codex 桌面端安装 Codex Dream Skin，并应用本文记录的“休闲室内居家”主题。
>
> 最后验证日期：2026-08-18。

## 1. 本次已验证基线

当前电脑上的真实运行结果：

| 项目 | 已验证值 |
| --- | --- |
| Dream Skin 客户端 | `1.5.14` |
| 上游仓库 | <https://github.com/Fei-Away/Codex-Dream-Skin> |
| 上游提交 | `95423d849f74b9824db2ba0c1121cc7a13b56d10` |
| 主题名称 | 休闲室内居家 |
| 主题作者 | `cecilylove` |
| 活动主题 ID | `cecilylove002` |
| 主题版本 ID | `ver_34a73ec14a33630c2578` |
| 主题版本 | `0.1.0` |
| 主题页面 | <https://dreamskin.cc/themes/ver_34a73ec14a33630c2578> |
| 主题包 SHA-256 | `3ade08bd0066142f1e97f684f28071dd3fa3a356fe65cf1f397e87f779c633e7` |
| 外观模式 | `dark` |

真实渲染验证已经确认：活动主题 ID 和磁盘主题一致；皮肤版本、样式、首页结构、侧栏、输入区、可见性和页面无溢出检查通过。当前验证截图位于：

`D:\test_dev_projects\artifacts\codex-dream-skin-manual\current-theme-verification.png`

## 2. 先理解官方主题与 Dream Skin 的区别

OpenAI 官方文档中的 Codex 自定义主题针对 **Codex CLI 终端界面**：通过 `/theme` 选择主题，或把 `.tmTheme` 文件放入 `$CODEX_HOME/themes`。它不是桌面端全窗口背景换肤。

Codex Dream Skin 是第三方、非 OpenAI 官方工具。它通过本机回环 CDP 注入样式，为 Codex 桌面端增加背景和装饰层，不修改 `WindowsApps`、`app.asar` 或官方包签名。

参考：

- OpenAI Docs：<https://learn.chatgpt.com/docs/cli-customization>
- Dream Skin Windows 说明：<https://github.com/Fei-Away/Codex-Dream-Skin/blob/main/windows/README.md>

## 3. 家中电脑前置条件

1. Windows 10 或更新版本，x64。
2. 已从 Microsoft Store 安装官方 Codex，并至少正常启动、登录一次。
3. 当前 Windows 用户可以写入自己的 `%LOCALAPPDATA%`。
4. 能访问 GitHub Releases 和 `dreamskin.cc`。
5. 使用 **开始菜单单独打开的 Windows PowerShell** 执行需要重启 Codex 的命令。

重要：不要从 Codex 自己的集成终端运行“安装并重启 Codex”的长流程。Codex 退出时，其子进程可能被同一个 Windows 作业对象回收，后续安装步骤就无法继续。

使用 Release 安装器时不需要另装 Node.js；安装包包含固定版本的 Node.js。只有从源码运行时才要求 Node.js 22 或更新版本。

## 4. 安全边界

1. 只从以下来源下载：
   - <https://github.com/Fei-Away/Codex-Dream-Skin/releases/latest>
   - <https://dreamskin.cc/>
2. Release 安装器目前未购买代码签名证书。运行前应核对 GitHub Release 的 `SHA256SUMS.txt`。
3. 不要为了安装而关闭 Defender、SmartScreen 或 Smart App Control。
4. 安装器按当前用户安装，正常情况下不要求管理员权限；若意外出现管理员密码提示，应取消并重新核对来源。
5. 不接管、不改 ACL、不替换 `C:\Program Files\WindowsApps` 中的任何文件。
6. Dream Skin 的 CDP 只绑定 `127.0.0.1`，但同一 Windows 用户下的其他本机进程仍可能访问调试端口。主题运行期间不要启动不可信本机程序。
7. “暂停主题”不等于关闭 CDP。要结束调试会话，应执行完整恢复并重启，或退出所有 Codex 进程后从官方入口普通启动。

## 5. 推荐安装流程

### 5.1 先正常运行一次官方 Codex

1. 从 Microsoft Store 安装 Codex。
2. 正常打开并完成登录。
3. 确认首页可用后，完全退出 Codex。

### 5.2 下载 Release 安装器

打开：

<https://github.com/Fei-Away/Codex-Dream-Skin/releases/latest>

下载同一 Release 下的：

- `CodexDreamSkin-Setup-vX.Y.Z.exe`
- `SHA256SUMS.txt`

不要固定照抄本文的 `1.5.14`；家中安装时优先使用当时最新公开 Release，并以该 Release 自带的校验文件为准。

### 5.3 校验安装器 SHA-256

在安装器和 `SHA256SUMS.txt` 所在目录打开独立 Windows PowerShell，执行：

```powershell
$Setup = Get-ChildItem -LiteralPath . -Filter 'CodexDreamSkin-Setup-v*.exe' |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

$ExpectedLine = Get-Content -LiteralPath '.\SHA256SUMS.txt' |
  Where-Object { $_ -match [regex]::Escape($Setup.Name) } |
  Select-Object -First 1

if (-not $Setup -or -not $ExpectedLine) {
  throw '未找到安装器或对应的 SHA256SUMS 条目。'
}

$Expected = (($ExpectedLine -split '\s+')[0]).ToLowerInvariant()
$Actual = (Get-FileHash -LiteralPath $Setup.FullName -Algorithm SHA256).Hash.ToLowerInvariant()

[pscustomobject]@{
  File = $Setup.FullName
  Expected = $Expected
  Actual = $Actual
  Match = ($Actual -ceq $Expected)
} | Format-List

if ($Actual -cne $Expected) {
  throw '安装器 SHA-256 不匹配，停止安装。'
}
```

只有 `Match : True` 才继续。

### 5.4 安装

1. 确认 Codex 已完全退出。
2. 双击已校验的 `CodexDreamSkin-Setup-vX.Y.Z.exe`。
3. 如果 SmartScreen 提示“Windows 已保护你的电脑”，点击“更多信息”，再次核对文件名和来源后选择“仍要运行”。
4. 不要关闭 Defender，也不要使用管理员身份运行。
5. 按向导完成安装。

安装完成后应存在：

- 开始菜单中的 `Codex Dream Skin`；
- `%LOCALAPPDATA%\CodexDreamSkin\engine\VERSION`；
- 当前用户的 `dreamskin://` 协议处理器。

可在 PowerShell 中检查：

```powershell
Get-Content "$env:LOCALAPPDATA\CodexDreamSkin\engine\VERSION"

Get-ItemProperty `
  -LiteralPath 'Registry::HKEY_CURRENT_USER\Software\Classes\dreamskin\shell\open\command'
```

## 6. 应用“休闲室内居家”主题

### 方法 A：网页一键换肤

1. 打开 <https://dreamskin.cc/themes/ver_34a73ec14a33630c2578>。
2. 点击“一键换肤”。
3. Windows 唤起 Dream Skin 后，核对主题名称和作者。
4. 选择“是”。

### 方法 B：独立 PowerShell 直接应用，最稳定

从开始菜单单独打开 Windows PowerShell，执行：

```powershell
$ThemeUri = 'dreamskin://apply?version=ver_34a73ec14a33630c2578'
$ApplyScript = "$env:LOCALAPPDATA\CodexDreamSkin\engine\scripts\apply-community-theme.ps1"

& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
  -NoProfile -STA -ExecutionPolicy RemoteSigned `
  -File $ApplyScript $ThemeUri
```

确认框中应看到：

- 主题：休闲室内居家；
- 作者：`cecilylove`；
- 当前记录的主题包 SHA-256：`3ade08bd0066142f1e97f684f28071dd3fa3a356fe65cf1f397e87f779c633e7`。

选择“是”后，工具会下载经过审核的主题包、校验大小和 SHA-256、导入主题、启动或重启 Codex，并验证真实渲染。成功提示出现后点击“确定”。

## 7. 日常启动方式

安装后优先使用开始菜单中的 `Codex Dream Skin` 启动，而不是官方普通入口。普通入口不会自动打开 Dream Skin 所需的 CDP 会话。

系统托盘菜单可用于：

- 切换已保存主题；
- 导入主题 ZIP；
- 暂停或继续主题；
- 重新应用；
- 完整恢复官方外观。

## 8. 验证活动主题

### 8.1 检查版本、主题和会话

```powershell
$DreamRoot = "$env:LOCALAPPDATA\CodexDreamSkin"

$ClientVersion = (Get-Content "$DreamRoot\engine\VERSION" -Raw).Trim()
$Theme = Get-Content "$DreamRoot\active-theme\theme.json" -Raw -Encoding UTF8 |
  ConvertFrom-Json
$State = Get-Content "$DreamRoot\state.json" -Raw -Encoding UTF8 |
  ConvertFrom-Json

[pscustomobject]@{
  ClientVersion = $ClientVersion
  ThemeId = $Theme.id
  ThemeName = $Theme.name
  Appearance = $Theme.appearance
  Port = $State.port
  InjectorPid = $State.injectorPid
  CodexVersion = $State.codexVersion
} | Format-List
```

本主题的预期值：

```text
ThemeId   : cecilylove002
ThemeName : 休闲室内居家
Appearance: dark
```

### 8.2 运行上游真实渲染验证

```powershell
$VerifyScript = "$env:LOCALAPPDATA\CodexDreamSkin\engine\scripts\verify-dream-skin.ps1"
$Screenshot = Join-Path $env:USERPROFILE 'Desktop\codex-dream-skin-verification.png'

& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
  -NoProfile -ExecutionPolicy RemoteSigned `
  -File $VerifyScript -ScreenshotPath $Screenshot
```

验证脚本检查：

- CDP 端点仅绑定本机回环地址，并属于当前官方 Codex 包；
- 渲染页已加载预期版本和活动主题；
- 原生侧栏、主内容和输入区仍存在；
- 主题装饰层不拦截交互；
- 页面没有横向或纵向溢出。

日志位置：

```text
%LOCALAPPDATA%\CodexDreamSkin\verify.log
```

日志最后一个目标的 `"pass": true`，且截图可见、文字可读，才算验证通过。首页和普通任务页最好各检查一次。

## 9. 更新

1. 退出 Dream Skin 托盘。
2. 完全退出 Codex。
3. 从 GitHub Releases 下载最新 Setup.exe 和 `SHA256SUMS.txt`。
4. 重新校验 SHA-256。
5. 运行新安装器覆盖安装。
6. 使用 `Codex Dream Skin` 快捷方式启动并重新验证。

已保存主题、图片和配置备份会保留。Codex 自身更新后若主题失效，也先按此流程覆盖安装最新 Dream Skin。

## 10. 恢复官方外观

### 10.1 完整恢复，推荐

```powershell
$RestoreScript = "$env:LOCALAPPDATA\CodexDreamSkin\engine\scripts\restore-dream-skin.ps1"

& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
  -NoProfile -ExecutionPolicy RemoteSigned `
  -File $RestoreScript -RestoreBaseTheme -PromptRestart
```

该操作会恢复安装前保存的外观设置、关闭 Dream Skin 会话，并正常重启 Codex。

### 10.2 卸载

进入“设置 → 应用 → 已安装的应用”，卸载 `Codex Dream Skin`。卸载器会先尝试恢复官方外观并关闭 CDP。默认保留 `%LOCALAPPDATA%\CodexDreamSkin` 中的已保存主题和图片，方便以后重装。

不要直接删除运行目录来代替恢复或卸载。

## 11. 常见问题

### 安装器一直要求关闭 Codex

- 使用系统托盘菜单完全退出 Codex；
- 不要从 Codex 集成终端启动安装流程；
- 从开始菜单单独打开 Windows PowerShell，再运行安装或应用命令。

### 点击主题链接没有反应

先检查协议是否已注册：

```powershell
Get-ItemProperty `
  -LiteralPath 'Registry::HKEY_CURRENT_USER\Software\Classes\dreamskin\shell\open\command'
```

若不存在，重新运行最新 Release 安装器。也可以使用第 6 节的方法 B，直接调用已安装的主题应用脚本。

### 找不到 CDP 端点

1. 从 `Codex Dream Skin` 快捷方式启动 Codex；
2. 重新运行验证；
3. 若 Codex 刚更新，覆盖安装最新 Dream Skin；
4. 不要修改 WindowsApps 权限或接管所有权。

某些 Codex Store 版本可能无法在项目安全边界内开放可验证的 CDP 端点。此时应保存日志并关注上游 Issue，不要通过修改官方包或 ACL 强行绕过。

### PowerShell 显示中文乱码

读取 JSON 或日志时显式指定 UTF-8：

```powershell
Get-Content '<文件路径>' -Raw -Encoding UTF8
```

### 需要提交问题

上游 Issue：<https://github.com/Fei-Away/Codex-Dream-Skin/issues/new/choose>

常用日志和状态位置：

```text
%LOCALAPPDATA%\CodexDreamSkin\state.json
%LOCALAPPDATA%\CodexDreamSkin\injector.log
%LOCALAPPDATA%\CodexDreamSkin\injector-error.log
%LOCALAPPDATA%\CodexDreamSkin\verify.log
%LOCALAPPDATA%\CodexDreamSkin\active-theme\theme.json
```

提交前删除或遮蔽个人路径、私人对话、`auth.json`、API Key、Base URL、中转 token 等敏感内容。

## 12. 快速命令卡

```powershell
$DreamRoot = "$env:LOCALAPPDATA\CodexDreamSkin"
$ThemeUri = 'dreamskin://apply?version=ver_34a73ec14a33630c2578'

# 应用主题
& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
  -NoProfile -STA -ExecutionPolicy RemoteSigned `
  -File "$DreamRoot\engine\scripts\apply-community-theme.ps1" $ThemeUri

# 检查活动主题
Get-Content "$DreamRoot\active-theme\theme.json" -Raw -Encoding UTF8 |
  ConvertFrom-Json |
  Select-Object id, name, appearance

# 验证并截图
& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
  -NoProfile -ExecutionPolicy RemoteSigned `
  -File "$DreamRoot\engine\scripts\verify-dream-skin.ps1" `
  -ScreenshotPath (Join-Path $env:USERPROFILE 'Desktop\codex-dream-skin-verification.png')

# 完整恢复官方外观
& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
  -NoProfile -ExecutionPolicy RemoteSigned `
  -File "$DreamRoot\engine\scripts\restore-dream-skin.ps1" `
  -RestoreBaseTheme -PromptRestart
```

## 13. 可选：保留上游源码副本

普通用户安装不要求 clone 仓库。如果希望在家中保留源码用于审计或排错：

```powershell
Set-Location "$env:USERPROFILE\Documents"
git clone https://github.com/Fei-Away/Codex-Dream-Skin.git
git -C '.\Codex-Dream-Skin' log -1 --oneline
```

源码副本和已安装运行时是两套位置：

- 源码：你选择的 clone 目录；
- 安装运行时：`%LOCALAPPDATA%\CodexDreamSkin\engine`；
- 图形安装程序：`%LOCALAPPDATA%\Programs\CodexDreamSkin`。

日常启动和主题应用使用已安装运行时，不依赖源码目录。
