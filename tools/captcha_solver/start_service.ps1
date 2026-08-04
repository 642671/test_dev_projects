# TNAS 登录服务 - 一键启动脚本
# 功能：安装依赖并启动 Selenium 登录服务

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TNAS 登录 Cookie 服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 安装依赖
Write-Host "[1/3] 检查并安装依赖..." -ForegroundColor Yellow
python -m pip install flask selenium -q 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  安装失败，尝试使用 pip3..." -ForegroundColor Red
    pip3 install flask selenium -q
}
Write-Host "  依赖检查完成" -ForegroundColor Green

# 2. 检查 Chrome 浏览器
Write-Host "[2/3] 检查 Chrome 浏览器..." -ForegroundColor Yellow
$chromePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)
$chromeFound = $false
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        Write-Host "  找到 Chrome: $path" -ForegroundColor Green
        $chromeFound = $true
        break
    }
}
if (-not $chromeFound) {
    Write-Host "  警告：未找到 Chrome 浏览器，请确保已安装" -ForegroundColor Yellow
}

# 3. 启动服务
Write-Host "[3/3] 启动服务..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  服务地址: http://localhost:8765" -ForegroundColor Green
Write-Host "  健康检查: http://localhost:8765/health" -ForegroundColor Green
Write-Host "  登录接口: POST http://localhost:8765/login" -ForegroundColor Green
Write-Host ""
Write-Host "  Apifox 前置脚本已生成在:" -ForegroundColor White
Write-Host "  tools/captcha_solver/apifox_pre_script.js" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

Set-Location $PSScriptRoot
python tnas_login_service.py
