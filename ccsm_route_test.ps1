$ErrorActionPreference = "Stop"
$auth = Get-Content "$env:USERPROFILE\.codex\auth.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$token = $auth.tokens.access_token
$acc = $auth.tokens.account_id
$bodyFile = Join-Path $env:TEMP "ccsm_body.json"

function Test-Route([string]$model) {
    Set-Content -Path $bodyFile -Value ('{"model":"' + $model + '","input":"say hi","stream":false}') -Encoding ascii
    Write-Host "=== Route test: $model ==="
    $out = curl.exe -s -m 120 -w "`nHTTP_CODE:%{http_code} TIME:%{time_total}s" `
        -X POST http://127.0.0.1:15721/v1/responses `
        -H "Authorization: Bearer $token" `
        -H "x-cc-switch-proxy-mode: router" `
        -H "ChatGPT-Account-Id: $acc" `
        -H "User-Agent: codex_cli_rs/26.730.61639" `
        -H "Content-Type: application/json" `
        --data-binary "@$bodyFile"
    $out | Select-Object -Last 60
    Write-Host ""
}

Test-Route "gpt-5.6-terra"

Remove-Item $bodyFile -Force -ErrorAction SilentlyContinue
