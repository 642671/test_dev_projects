# Quiet watcher: ASCII only, dedupes repeated lines so only changes are reported.
$config = 'C:\Users\twm\.codex\config.toml'
$sessions = 'C:\Users\twm\.codex\sessions'
$seen = @{}
$lastCfg = -1
$lastRouter = -1
$lastProcLine = ''
$lastReqText = ''

function P($t) { Write-Output $t }

while ($true) {
    try {
        $cfg = (Select-String -Path $config -Pattern 'model_providers\.codex_model_router_v2|127\.0\.0\.1:15721' -ErrorAction SilentlyContinue | Measure-Object).Count
        if ($cfg -ne $lastCfg) {
            $lastCfg = $cfg
            if ($cfg -eq 2) { P 'CONFIG OK' }
            else { P "CONFIG COMPACTION RISK! key lines = $cfg (expected 2)" }
        }

        $routerUp = [bool](Get-NetTCPConnection -LocalPort 15721 -State Listen -ErrorAction SilentlyContinue)
        if ($routerUp -ne [bool]$lastRouter) {
            $lastRouter = $routerUp
            P ("ROUTER: " + $(if ($routerUp) { 'up' } else { 'DOWN' }))
        }

        $n = @(Get-Process -Name ChatGPT -ErrorAction SilentlyContinue).Count
        $procLine = "CODEX: $n process(es)"
        if ($procLine -ne $lastProcLine) { $lastProcLine = $procLine; P $procLine }

        $recent = Get-ChildItem -LiteralPath $sessions -Recurse -Filter '*.jsonl' -File -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -gt (Get-Date).AddSeconds(-240) }
        foreach ($f in @($recent | Sort-Object LastWriteTime -Descending)) {
            if ($seen[$f.FullName]) { continue }
            $seen[$f.FullName] = $true
            $models = Select-String -LiteralPath $f.FullName -Pattern '"model":"?([A-Za-z0-9.\-_]+)"?' -AllMatches -ErrorAction SilentlyContinue |
                ForEach-Object { $_.Matches } |
                ForEach-Object { $_.Groups[1].Value } |
                Where-Object { $_ -like 'gpt-*' -or $_ -like 'deepseek*' -or $_ -like 'newapi*' } |
                Select-Object -Unique -Last 1
            if ($models) {
                $t = "REQUEST: $($f.Name.Substring($f.Name.Length-24)) model = $models"
                if ($t -ne $lastReqText) { $lastReqText = $t; P $t }
            }
        }
    } catch {}
    Start-Sleep -Seconds 5
}
