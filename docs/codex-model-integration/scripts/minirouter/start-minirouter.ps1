# start-minirouter.ps1 — 启动 Codex 迷你路由（替代 CCSwitchMulti 的路由功能）
# 用法：双击运行，或
#   powershell -ExecutionPolicy Bypass -File 'D:\test_dev_projects\docs\codex-model-integration\scripts\minirouter\start-minirouter.ps1'
# 停止：在窗口里按 Ctrl+C，或直接关闭窗口。

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$node = 'D:\self_install\nodejs\node.exe'
$port = 15721

if (-not (Test-Path -LiteralPath $node)) {
    throw "找不到 node.exe：$node"
}
if (-not (Test-Path -LiteralPath (Join-Path $root 'minirouter.js'))) {
    throw "找不到 minirouter.js：$(Join-Path $root 'minirouter.js')"
}

# 1. 端口检查：防止与 CCSwitchMulti 或别的实例撞车
$listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    $procName = (Get-Process -Id $listener[0].OwningProcess -ErrorAction SilentlyContinue).ProcessName
    throw "端口 $port 已被占用（进程: $procName）。CCSwitchMulti 或另一个路由实例还在运行，请先退出它。"
}

# 2. 补上环境变量（从注册表读，不打印内容）
if (-not $env:TWM_NEWAPI_API_KEY) {
    $env:TWM_NEWAPI_API_KEY = [Environment]::GetEnvironmentVariable('TWM_NEWAPI_API_KEY', 'User')
}
if (-not $env:TWM_NEWAPI_API_KEY) {
    throw '未找到用户环境变量 TWM_NEWAPI_API_KEY，无法走第三方模型。'
}

# 3. 提示代理状态（官方模型必须经过 127.0.0.1:7897）
$proxyOn = [bool](Get-NetTCPConnection -LocalPort 7897 -State Listen -ErrorAction SilentlyContinue)
if ($proxyOn) {
    Write-Host '代理 127.0.0.1:7897 在线 —— 官方模型可正常出网。' -ForegroundColor Green
} else {
    Write-Warning '代理 127.0.0.1:7897 未运行 —— 第三方（deepseek）不受影响，但官方模型会出网失败。'
}

Write-Host '启动迷你路由，按 Ctrl+C 停止。' -ForegroundColor Cyan
& $node (Join-Path $root 'minirouter.js')
$exit = $LASTEXITCODE
Write-Host "路由已退出（代码 $exit）。" -ForegroundColor Gray

# 双击运行时暂停窗口；从终端/管道运行时直接结束
if (-not [Console]::IsInputRedirected) {
    Read-Host '按回车关闭窗口'
}
exit $exit
