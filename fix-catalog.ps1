$ErrorActionPreference = "Stop"

$logPath = "C:\Users\twm\.codex\catalog-fix.log"
$sqlite = "D:\self_install\adb\platform-tools\sqlite3.exe"
$codexHome = "$env:USERPROFILE\.codex"
$stateDb = Join-Path $codexHome "state_5.sqlite"
$catalogDb = Join-Path $codexHome "sqlite\codex-dev.db"
$codexExe = "C:\Program Files\WindowsApps\OpenAI.Codex_26.803.5235.0_x64__2p2nqsd0c76g0\app\ChatGPT.exe"

function Log([string]$m) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
    Add-Content -Path $logPath -Value $line -Encoding UTF8
    Write-Host $line
}

function Esc([AllowNull()][string]$s) {
    if ($null -eq $s) { return "NULL" }
    return "'" + ($s -replace "'", "''") + "'"
}

$ts = Get-Date -Format "yyyyMMdd-HHmmss"
Log "=== catalog fix start ($ts) ==="
Log "grace period 20s before stopping Codex Desktop..."
Start-Sleep -Seconds 20

# ---------- 1. stop Codex Desktop (ChatGPT + codex only; never touch CCSM) ----------
Get-Process -Name ChatGPT,codex -ErrorAction SilentlyContinue | ForEach-Object {
    Log "graceful close request: $($_.ProcessName) pid $($_.Id)"
    try { $null = $_.CloseMainWindow() } catch {}
}
Start-Sleep -Seconds 5
for ($i = 0; $i -lt 10; $i++) {
    $left = Get-Process -Name ChatGPT,codex -ErrorAction SilentlyContinue
    if (-not $left) { break }
    $left | ForEach-Object { Log "force stop: $($_.ProcessName) pid $($_.Id)"; Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 1
}
Start-Sleep -Seconds 3
$left = Get-Process -Name ChatGPT,codex -ErrorAction SilentlyContinue
if ($left) {
    Log "ERROR: Codex processes still running - aborting without DB changes"
    Log "remaining: $($left.ProcessName -join ',')"
    exit 2
}
Log "Codex Desktop fully exited"

# ---------- 2. checkpoint WAL so backups are consistent ----------
try {
    & $sqlite $stateDb "PRAGMA wal_checkpoint(TRUNCATE);" | Out-Null
    & $sqlite $catalogDb "PRAGMA wal_checkpoint(TRUNCATE);" | Out-Null
    Log "WAL checkpoint done"
} catch { Log "checkpoint warning: $_" }

# ---------- 3. backups (state_5.sqlite* / codex-dev.db* / .codex-global-state.json) ----------
$backupTargets = @(
    "$codexHome\state_5.sqlite", "$codexHome\state_5.sqlite-wal", "$codexHome\state_5.sqlite-shm",
    "$codexHome\sqlite\codex-dev.db", "$codexHome\sqlite\codex-dev.db-wal", "$codexHome\sqlite\codex-dev.db-shm",
    "$codexHome\.codex-global-state.json"
)
foreach ($f in $backupTargets) {
    if (Test-Path -LiteralPath $f) {
        $dest = "$f.bak-$ts"
        Copy-Item -LiteralPath $f -Destination $dest -Force
        Log "backup: $f -> $dest"
    }
}

# ---------- 4. read-only verification before changes ----------
Log "--- before: threads by provider ---"
& $sqlite $stateDb "SELECT model_provider, COUNT(*) FROM threads GROUP BY model_provider;" | ForEach-Object { Log "state: $_" }
$providers = @(& $sqlite $stateDb "SELECT DISTINCT model_provider FROM threads;") | Where-Object { $_.Trim() -ne "" -and $_ -ne "codex_model_router_v2" }
Log "providers to relabel: [$(($providers | ForEach-Object { $_ }) -join ', ')]"

# ---------- 5. provider label fix (data-driven, both DBs) ----------
if ($providers.Count -gt 0) {
    $list = ($providers | ForEach-Object { "'" + ($_ -replace "'", "''") + "'" }) -join ","
    $changedState = & $sqlite $stateDb "UPDATE threads SET model_provider='codex_model_router_v2' WHERE model_provider IN ($list); SELECT changes();"
    $changedCatalog = & $sqlite $catalogDb "UPDATE local_thread_catalog SET model_provider='codex_model_router_v2' WHERE model_provider IN ($list); SELECT changes();"
    Log "threads updated: $($changedState -join '') rows; catalog updated: $($changedCatalog -join '') rows"
} else {
    Log "no provider relabel needed"
}

# ---------- 6. seed local_thread_catalog from threads (app-compatible row format) ----------
$titleMap = @{}
if (Test-Path "$codexHome\session_index.jsonl") {
    Get-Content "$codexHome\session_index.jsonl" -Encoding UTF8 | ForEach-Object {
        try { $o = $_ | ConvertFrom-Json; if ($o.id -and $o.thread_name) { $titleMap[$o.id] = $o.thread_name } } catch {}
    }
}
$obsSeqRow = @(& $sqlite $catalogDb "SELECT observation_sequence FROM local_thread_catalog_sync_state WHERE host_id='local';")
$obsSeq = if ($obsSeqRow.Count -gt 0) { [int]$obsSeqRow[0] } else { 0 }
Log "observation_sequence to stamp: $obsSeq"

$threads = @((( (& $sqlite -json $stateDb "SELECT id, title, preview, cwd, created_at, created_at_ms, updated_at, updated_at_ms, recency_at_ms, source, git_branch, thread_source, model_provider FROM threads WHERE archived=0 AND source NOT IN ('exec');") -join "") | ConvertFrom-Json))
Log "threads to seed: $($threads.Count)"

$values = @()
foreach ($t in $threads) {
    $title = ""
    if ($titleMap.ContainsKey($t.id)) { $title = $titleMap[$t.id] }
    if ([string]::IsNullOrWhiteSpace($title)) { $title = $t.title }
    if ([string]::IsNullOrWhiteSpace($title)) { $title = $t.preview }
    if ([string]::IsNullOrWhiteSpace($title)) { $title = $t.cwd }
    if ([string]::IsNullOrWhiteSpace($title)) { $title = $t.id }
    $title = ($title -replace "\s+", " ").Trim()
    if ($title.Length -gt 80) { $title = $title.Substring(0, 79) + "…" }

    $createdMs = if ($t.created_at_ms) { [long]$t.created_at_ms } else { [long]$t.created_at * 1000 }
    $updatedMs = if ($t.updated_at_ms) { [long]$t.updated_at_ms } else { [long]$t.updated_at * 1000 }
    $recencyMs = if ($t.recency_at_ms) { [long]$t.recency_at_ms } else { $updatedMs }
    $sourceKind = if ($t.source) { $t.source } else { "unknown" }
    $threadSource = if ($t.thread_source) { $t.thread_source } else { "local" }
    $gitBranch = if ($t.git_branch) { $t.git_branch } else { $null }

    $rowParts = @("'local'", (Esc $t.id), (Esc $title), "$createdMs", "$updatedMs", "$recencyMs", (Esc $t.cwd), (Esc $sourceKind), "NULL", (Esc $threadSource), (Esc $t.model_provider), (Esc $gitBranch), "$obsSeq", "0", "0")
    $values += "(" + ($rowParts -join ", ") + ")"
}

$sql = "INSERT OR REPLACE INTO local_thread_catalog (host_id, thread_id, display_title, source_created_at, source_updated_at, source_recency_at, cwd, source_kind, source_detail, thread_source, model_provider, git_branch, observation_sequence, pending_observed_title, missing_candidate) VALUES " + ($values -join ", ") + ";"
$sqlFile = Join-Path $env:TEMP "catalog-seed-$ts.sql"
[System.IO.File]::WriteAllText($sqlFile, $sql, (New-Object System.Text.UTF8Encoding($false)))
& $sqlite $catalogDb ".read $sqlFile"
Log "seeded catalog rows: $($values.Count)"
Remove-Item -LiteralPath $sqlFile -Force -ErrorAction SilentlyContinue

# ---------- 7. mark initial build complete ----------
$nowMs = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
& $sqlite $catalogDb "UPDATE local_thread_catalog_sync_state SET initial_build_complete=1, watermark_updated_at=$nowMs, last_full_reconciled_at=$nowMs WHERE host_id='local';"
& $sqlite $catalogDb "UPDATE local_thread_catalog_metadata SET catalog_revision = catalog_revision + 1 WHERE id=1;"
Log "sync state marked complete; catalog revision bumped"

# ---------- 8. verify ----------
Log "--- after: catalog by provider ---"
& $sqlite $catalogDb "SELECT model_provider, COUNT(*) FROM local_thread_catalog GROUP BY model_provider;" | ForEach-Object { Log "catalog: $_" }
Log "--- after: sync state ---"
& $sqlite $catalogDb "SELECT host_id, initial_build_complete, observation_sequence FROM local_thread_catalog_sync_state WHERE host_id='local';" | ForEach-Object { Log "sync: $_" }
Log "--- after: state providers ---"
& $sqlite $stateDb "SELECT DISTINCT model_provider FROM threads;" | ForEach-Object { Log "state: $_" }
$total = & $sqlite $catalogDb "SELECT COUNT(*) FROM local_thread_catalog WHERE host_id='local' AND missing_candidate=0;"
Log "sidebar-visible catalog rows: $($total -join '')"

# ---------- 9. relaunch Codex Desktop with unlock args ----------
try {
    Start-Process -FilePath $codexExe -ArgumentList "--remote-debugging-port=9229", "--remote-allow-origins=http://127.0.0.1:9229"
    Log "Codex Desktop relaunched with CDP 9229"
} catch {
    Log "ERROR direct launch failed: $_"
    try {
        Start-Process -FilePath "explorer.exe" -ArgumentList "shell:AppsFolder\OpenAI.Codex_2p2nqsd0c76g0!App"
        Log "Codex Desktop relaunched via shell:AppsFolder (NOTE: without CDP unlock args)"
    } catch { Log "ERROR fallback launch failed: $_" }
}

Start-Sleep -Seconds 12
$chk = Get-NetTCPConnection -LocalPort 9229 -State Listen -ErrorAction SilentlyContinue
if ($chk) { Log "CDP 9229 listening: yes" } else { Log "CDP 9229 listening: NO (check manually)" }
$proc = Get-Process -Name ChatGPT -ErrorAction SilentlyContinue
Log "ChatGPT processes after relaunch: $(@($proc).Count)"
Log "=== catalog fix done ==="
