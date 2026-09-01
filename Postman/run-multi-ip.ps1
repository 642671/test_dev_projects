param(
    [string]$CollectionJson = "postman/collections/TEST-TNAS.collection.json",
    [string]$Csv = "nas_ips.csv",
    [string]$Filter,
    [switch]$DryRun
)

# 每个 IP 单独启动一次 postman collection run，环境互不污染，导出的 Cookie/公钥等
# 派生变量只存在于本次运行（集合变量），做到多 IP 天然隔离。
# 警告：TEST-TNAS 集合含“删除卷 / 删除存储池 / 卸载磁盘”等破坏性操作，
# 批量执行前请确认目标 NAS 状态与授权范围。

if (-not (Test-Path $CollectionJson)) { Write-Error "找不到集合 JSON: $CollectionJson"; exit 1 }
if (-not (Test-Path $Csv)) { Write-Error "找不到 CSV: $Csv"; exit 1 }

New-Item -ItemType Directory -Path "reports" -Force | Out-Null

$rows = Import-Csv $Csv
if ($rows.Count -eq 0) { Write-Error "CSV 为空"; exit 1 }

foreach ($row in $rows) {
    $baseUrl = ($row.baseUrl).Trim()
    if (-not $baseUrl) { continue }
    $slug = ($baseUrl -replace '[^A-Za-z0-9.]','_')
    $out = Join-Path "reports" ("{0}.txt" -f $slug)

    Write-Host ""
    Write-Host "==================== $baseUrl ====================" -ForegroundColor Cyan
    $argsList = @("collection","run",$CollectionJson,"-k","--env-var","baseUrl=$baseUrl","-r","cli","--suppress-exit-code")
    if ($Filter) { $argsList += @("-i",$Filter) }
    if ($DryRun) {
        Write-Host ("[DRY-RUN] postman " + ($argsList -join ' '))
        continue
    }
    & postman @argsList *> $out
    $rc = $LASTEXITCODE
    Write-Host ("完成 (exit=$rc)，报告: " + $out)
}
