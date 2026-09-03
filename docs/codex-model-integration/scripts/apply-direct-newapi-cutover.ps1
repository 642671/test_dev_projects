param(
    [string]$BackupRoot = 'C:\Users\twm\.codex\backups'
)

$ErrorActionPreference = 'Stop'

$codexHome = 'C:\Users\twm\.codex'
$configPath = Join-Path $codexHome 'config.toml'
$catalogPath = Join-Path $codexHome 'newapi-direct-model-catalog.json'
$stateDb = Join-Path $codexHome 'state_5.sqlite'
$sqlite = 'D:\self_install\adb\platform-tools\sqlite3.exe'
$ccSettings = 'C:\Users\twm\.cc-switch\settings.json'
$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$runValueName = 'CCSwitchMulti'

if (Get-Process -Name 'cc-switch' -ErrorAction SilentlyContinue) {
    throw 'CCSwitchMulti is still running. Exit it normally before applying the cutover.'
}

$codexProcesses = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessName -in @('ChatGPT', 'codex', 'codex-code-mode-host')
})
if ($codexProcesses.Count -gt 0) {
    $names = ($codexProcesses.ProcessName | Sort-Object -Unique) -join ', '
    throw "Codex is still running ($names). Close Codex Desktop normally before applying the cutover."
}

foreach ($path in @($configPath, $catalogPath, $stateDb, $sqlite, $ccSettings)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required path not found: $path"
    }
}

$key = [Environment]::GetEnvironmentVariable('TWM_NEWAPI_API_KEY', 'User')
if ([string]::IsNullOrWhiteSpace($key)) {
    throw 'User environment variable TWM_NEWAPI_API_KEY is missing.'
}

$catalog = Get-Content -LiteralPath $catalogPath -Raw | ConvertFrom-Json
$visionModel = @($catalog.models | Where-Object { $_.id -eq 'deepseek-v4-flash-vision-exp' })
if ($visionModel.Count -ne 1 -or 'image' -notin @($visionModel[0].input_modalities)) {
    throw 'The direct model catalog does not mark deepseek-v4-flash-vision-exp as image-capable.'
}
if ([string]$visionModel[0].default_reasoning_effort -ne 'max') {
    throw 'The direct vision model catalog default reasoning effort is not max.'
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backup = Join-Path $BackupRoot "direct-newapi-cutover-$stamp"
New-Item -ItemType Directory -Path $backup | Out-Null
Copy-Item -LiteralPath $configPath -Destination (Join-Path $backup 'config.toml')
Copy-Item -LiteralPath $catalogPath -Destination (Join-Path $backup 'newapi-direct-model-catalog.json')
Copy-Item -LiteralPath $ccSettings -Destination (Join-Path $backup 'ccswitch-settings.json')

$runValue = Get-ItemPropertyValue -LiteralPath $runKey -Name $runValueName -ErrorAction SilentlyContinue
[pscustomobject]@{
    existed = $null -ne $runValue
    value = $runValue
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup 'ccswitch-run-value.json') -Encoding UTF8

$backupSql = $backup.Replace([char]92, [char]47)
& $sqlite $stateDb '.timeout 10000' ".backup '$backupSql/state_5.sqlite'"
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to back up the Codex history database.'
}

# Back up every historical rollout that belongs to the stable provider bucket.
# The migration below parses each JSON line and only changes turn_context.payload.model.
$rolloutBackupRoot = Join-Path $backup 'rollouts'
$rolloutPaths = @(& $sqlite $stateDb ".mode list" ".separator '`t'" "SELECT DISTINCT rollout_path FROM threads WHERE model_provider = 'codex_model_router_v2' AND rollout_path IS NOT NULL;")
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to enumerate historical rollout files.'
}

$rolloutPaths = @($rolloutPaths | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
foreach ($storedPath in $rolloutPaths) {
    $rolloutPath = $storedPath -replace '^\\\\\?\\', ''
    if (-not (Test-Path -LiteralPath $rolloutPath)) {
        throw "Historical rollout file not found: $rolloutPath"
    }
    $sessionsRoot = Join-Path $codexHome 'sessions'
    if (-not $rolloutPath.StartsWith($sessionsRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to migrate rollout outside the Codex sessions folder: $rolloutPath"
    }
    $relativePath = $rolloutPath.Substring($sessionsRoot.Length).TrimStart([char]92)
    $backupPath = Join-Path $rolloutBackupRoot $relativePath
    New-Item -ItemType Directory -Path (Split-Path -Parent $backupPath) -Force | Out-Null
    Copy-Item -LiteralPath $rolloutPath -Destination $backupPath
}

[pscustomobject]@{
    rollout_count = $rolloutPaths.Count
    sessions_root = (Join-Path $codexHome 'sessions')
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup 'rollout-backup-manifest.json') -Encoding UTF8

$config = [IO.File]::ReadAllText($configPath)
$config = [regex]::Replace($config, '(?m)^model\s*=.*(?:\r?\n)?', '')
$config = "model = `"deepseek-v4-flash-vision-exp`"`r`n" + $config
# Codex Desktop updates have rewritten config.toml without model_provider;
# pin the router explicitly so requests reach the NewAPI direct endpoint.
if ($config -notmatch '(?m)^model_provider\s*=') {
    $config = "model_provider = `"codex_model_router_v2`"`r`n" + $config
}
$config = [regex]::Replace($config, '(?m)^model_reasoning_effort\s*=.*$', 'model_reasoning_effort = "max"')
if ($config -notmatch '(?m)^model_reasoning_effort\s*=') {
    $config = "model_reasoning_effort = `"max`"`r`n" + $config
}
$config = [regex]::Replace(
    $config,
    '(?m)^model_catalog_json\s*=.*$',
    "model_catalog_json = 'C:\Users\twm\.codex\newapi-direct-model-catalog.json'"
)

$providerBlock = @'
[model_providers.codex_model_router_v2]
name = "Noontec NewAPI Direct"
base_url = "http://10.18.2.100/v1"
wire_api = "responses"
env_key = "TWM_NEWAPI_API_KEY"
requires_openai_auth = false
supports_websockets = false
supports_standalone_web_search = false
request_max_retries = 2
stream_max_retries = 5
'@

$providerPattern = '(?ms)^\[model_providers\.codex_model_router_v2\].*\z'
if (-not [regex]::IsMatch($config, $providerPattern)) {
    # The current config.toml has no codex_model_router_v2 block (a Codex
    # Desktop rewrite dropped the whole model_providers section). Append the
    # direct block at the end instead of failing.
    $config = $config.TrimEnd() + "`r`n`r`n" + $providerBlock.TrimEnd() + "`r`n"
} else {
    $config = [regex]::Replace($config, $providerPattern, $providerBlock.TrimEnd() + "`r`n")
}
[IO.File]::WriteAllText($configPath, $config, [Text.UTF8Encoding]::new($false))

$visionAliases = @(
    'deepseek-v4-flash-vision-exp',
    'newapi-deepseek-v4-flash-vision-exp'
)
$migratedRollouts = 0
foreach ($storedPath in $rolloutPaths) {
    $rolloutPath = $storedPath -replace '^\\\\\?\\', ''
    $changed = $false
    $outputLines = [Collections.Generic.List[string]]::new()
    foreach ($line in [IO.File]::ReadLines($rolloutPath)) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            $outputLines.Add($line)
            continue
        }
        $item = $line | ConvertFrom-Json
        if ($item.type -eq 'turn_context' -and $null -ne $item.payload -and $null -ne $item.payload.model) {
            $targetModel = if ($visionAliases -contains [string]$item.payload.model) {
                'deepseek-v4-flash-vision-exp'
            } else {
                'deepseek-v4-flash'
            }
            if ([string]$item.payload.model -ne $targetModel) {
                $item.payload.model = $targetModel
                $line = $item | ConvertTo-Json -Depth 100 -Compress
                $changed = $true
            }
        }
        $outputLines.Add($line)
    }
    if ($changed) {
        [IO.File]::WriteAllLines($rolloutPath, $outputLines, [Text.UTF8Encoding]::new($false))
        $migratedRollouts++
    }
}

$sql = @"
.timeout 10000
BEGIN IMMEDIATE;
UPDATE threads
SET model = CASE
    WHEN model IN ('deepseek-v4-flash-vision-exp', 'newapi-deepseek-v4-flash-vision-exp')
        THEN 'deepseek-v4-flash-vision-exp'
    ELSE 'deepseek-v4-flash'
END,
reasoning_effort = 'max'
WHERE model_provider = 'codex_model_router_v2';
COMMIT;
"@
$sql | & $sqlite $stateDb
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to migrate historical thread model aliases.'
}


# Keep CCSwitchMulti installed for rollback, but stop it from managing Codex or
# starting its local router automatically after this direct-connect cutover.
$settings = Get-Content -LiteralPath $ccSettings -Raw | ConvertFrom-Json
$settings.launchOnStartup = $false
$settings.enableLocalProxy = $false
if ($null -ne $settings.visibleApps) {
    $settings.visibleApps.codex = $false
}
$settings | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $ccSettings -Encoding UTF8

if ($null -ne $runValue) {
    Remove-ItemProperty -LiteralPath $runKey -Name $runValueName -ErrorAction Stop
}

[pscustomobject]@{
    applied = $true
    provider = 'codex_model_router_v2'
    base_url = 'http://10.18.2.100/v1'
    default_model = 'deepseek-v4-flash-vision-exp'
    catalog = $catalogPath
    backup = $backup
    rollout_files_scanned = $rolloutPaths.Count
    rollout_files_migrated = $migratedRollouts
    ccswitch_autostart_disabled = $true
    ccswitch_codex_management_disabled = $true
    key_value_printed = $false
}
