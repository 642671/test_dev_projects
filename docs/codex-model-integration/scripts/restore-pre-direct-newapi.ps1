param(
    [Parameter(Mandatory = $true)]
    [string]$BackupDirectory
)

$ErrorActionPreference = 'Stop'

$codexProcesses = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessName -in @('ChatGPT', 'codex', 'codex-code-mode-host')
})
if ($codexProcesses.Count -gt 0) {
    $names = ($codexProcesses.ProcessName | Sort-Object -Unique) -join ', '
    throw "Close Codex Desktop before restoring the backup. Still running: $names"
}


if (Get-Process -Name 'cc-switch' -ErrorAction SilentlyContinue) {
    throw 'Exit CCSwitchMulti normally before restoring the backup.'
}

$configBackup = Join-Path $BackupDirectory 'config.toml'
$stateBackup = Join-Path $BackupDirectory 'state_5.sqlite'
$sqlite = 'D:\self_install\adb\platform-tools\sqlite3.exe'
$settingsBackup = Join-Path $BackupDirectory 'ccswitch-settings.json'
$runValueBackup = Join-Path $BackupDirectory 'ccswitch-run-value.json'
$rolloutManifest = Join-Path $BackupDirectory 'rollout-backup-manifest.json'
foreach ($path in @($configBackup, $stateBackup, $sqlite, $settingsBackup, $runValueBackup, $rolloutManifest)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required backup file not found: $path"
    }
}

Copy-Item -LiteralPath 'C:\Users\twm\.codex\config.toml' `
    -Destination "C:\Users\twm\.codex\config.toml.before-restore-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item -LiteralPath $configBackup -Destination 'C:\Users\twm\.codex\config.toml' -Force
$restoreSource = $stateBackup.Replace([char]92, [char]47)
& $sqlite 'C:\Users\twm\.codex\state_5.sqlite' '.timeout 10000' ".restore '$restoreSource'"
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to restore the Codex history database.'
}
Copy-Item -LiteralPath $settingsBackup -Destination 'C:\Users\twm\.cc-switch\settings.json' -Force

$manifest = Get-Content -LiteralPath $rolloutManifest -Raw | ConvertFrom-Json
$rolloutBackupRoot = Join-Path $BackupDirectory 'rollouts'
$restoredRollouts = 0
if (Test-Path -LiteralPath $rolloutBackupRoot) {
    foreach ($backupFile in Get-ChildItem -LiteralPath $rolloutBackupRoot -File -Recurse) {
        $relativePath = $backupFile.FullName.Substring($rolloutBackupRoot.Length).TrimStart([char]92)
        $destination = Join-Path ([string]$manifest.sessions_root) $relativePath
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $backupFile.FullName -Destination $destination -Force
        $restoredRollouts++
    }
}

$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$runValueName = 'CCSwitchMulti'
$runState = Get-Content -LiteralPath $runValueBackup -Raw | ConvertFrom-Json
if ($runState.existed) {
    Set-ItemProperty -LiteralPath $runKey -Name $runValueName -Value ([string]$runState.value)
} else {
    Remove-ItemProperty -LiteralPath $runKey -Name $runValueName -ErrorAction SilentlyContinue
}

[pscustomobject]@{
    restored = $true
    source = $BackupDirectory
    rollout_files_restored = $restoredRollouts
    ccswitch_settings_restored = $true
}
