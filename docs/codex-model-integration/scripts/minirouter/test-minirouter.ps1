# test-minirouter.ps1 — 冒烟测试：路由是否在 15721 应答，模型列表是否完整。
#   用法：先启动 start-minirouter.ps1，再运行本脚本。
#   加 -DeepTest 会真实请求一次 newapi-deepseek-v4-flash（消耗少量令牌）。

param(
    [switch]$DeepTest
)

$ErrorActionPreference = 'Stop'
$base = 'http://127.0.0.1:15721'

# 1) GET /v1/models
try {
    $models = Invoke-RestMethod -Uri "$base/v1/models" -TimeoutSec 10
    $ids = @($models.data | ForEach-Object { $_.id })
    Write-Host ("模型列表: {0} 个" -f $ids.Count) -ForegroundColor Green
    $ids | ForEach-Object { Write-Host "  - $_" }
} catch {
    Write-Host "GET /v1/models 失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host '  → 路由没在跑？先运行 start-minirouter.ps1'
    exit 1
}

if (-not $DeepTest) { exit 0 }

# 2) DeepTest：真实发一次 small 请求（走 NewAPI，消耗非常少的令牌）
try {
    $body = @{
        model = 'newapi-deepseek-v4-flash'
        input = '回复 OK 两个字'
        max_output_tokens = 8
        stream = $false
    } | ConvertTo-Json -Depth 5
    $resp = Invoke-RestMethod -Uri "$base/v1/responses" -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 60
    $text = if ($resp.output_text) { $resp.output_text } else { ($resp | ConvertTo-Json -Depth 5) }
    Write-Host ("DeepTest 成功: model={0}" -f $resp.model) -ForegroundColor Green
    Write-Host ("  输出片段: {0}" -f ([string]$text).Substring(0, [Math]::Min(60, ([string]$text).Length)))
    Write-Host '路线：newapi-deepseek-v4-flash -> NewAPI 10.18.2.100 ✓'
} catch {
    Write-Host "DeepTest 失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
