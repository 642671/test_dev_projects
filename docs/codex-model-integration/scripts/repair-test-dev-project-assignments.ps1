[CmdletBinding()]
param(
    [switch]$ValidateOnly,
    [switch]$WaitForCodexExit,
    [switch]$Relaunch,
    [int]$WaitTimeoutSeconds = 900
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$codexRoot = 'C:\Users\twm\.codex'
$globalStatePath = Join-Path $codexRoot '.codex-global-state.json'
$stateDbPath = Join-Path $codexRoot 'state_5.sqlite'
$catalogDbPath = Join-Path $codexRoot 'sqlite\codex-dev.db'
$legacySnapshotPath = Join-Path $codexRoot '..codex-global-state.json.tmp-1789116362433-4760fd3f-7646-4649-a7d3-6959f3071321'
$sqlitePath = 'D:\self_install\adb\platform-tools\sqlite3.exe'
$projectRoot = 'D:\test_dev_projects'
$legacyProjectId = '1a19b9c7-1c23-4e90-b740-0b5b972b2481'
$hostMappingKey = 'local:C:\Users\twm\.codex'
$backupBase = 'D:\test_dev_projects\docs\codex-model-integration\backups'

function Get-CodexProcesses {
    @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -in @('ChatGPT', 'codex', 'codex-code-mode-host')
    })
}

function Invoke-SqliteScalar {
    param(
        [Parameter(Mandatory)] [string]$Database,
        [Parameter(Mandatory)] [string]$Sql,
        [switch]$ReadOnly
    )

    $arguments = @()
    if ($ReadOnly) {
        $arguments += '-readonly'
    }
    $arguments += @('-noheader', $Database, $Sql)
    $output = & $sqlitePath @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "SQLite command failed for $Database"
    }
    return ($output | Select-Object -Last 1).Trim()
}

function Copy-StateFileSet {
    param(
        [Parameter(Mandatory)] [string]$Source,
        [Parameter(Mandatory)] [string]$DestinationDirectory
    )

    foreach ($candidate in @($Source, "$Source-wal", "$Source-shm")) {
        if (Test-Path -LiteralPath $candidate) {
            Copy-Item -LiteralPath $candidate -Destination $DestinationDirectory
        }
    }
}

function Restore-StateFileSet {
    param(
        [Parameter(Mandatory)] [string]$Original,
        [Parameter(Mandatory)] [string]$BackupDirectory
    )

    foreach ($suffix in @('', '-wal', '-shm')) {
        $name = [System.IO.Path]::GetFileName("$Original$suffix")
        $backup = Join-Path $BackupDirectory $name
        $target = "$Original$suffix"
        if (Test-Path -LiteralPath $backup) {
            Copy-Item -LiteralPath $backup -Destination $target -Force
        } elseif (Test-Path -LiteralPath $target) {
            Remove-Item -LiteralPath $target -Force
        }
    }
}

if ($WaitForCodexExit -and -not $ValidateOnly) {
    $deadline = (Get-Date).AddSeconds($WaitTimeoutSeconds)
    do {
        $running = @(Get-CodexProcesses)
        if ($running.Count -eq 0) {
            break
        }
        if ((Get-Date) -ge $deadline) {
            throw "Timed out waiting for Codex to exit after $WaitTimeoutSeconds seconds."
        }
        Start-Sleep -Seconds 1
    } while ($true)
}

$stillRunning = @(Get-CodexProcesses)
if (-not $ValidateOnly -and $stillRunning.Count -gt 0) {
    $names = ($stillRunning | ForEach-Object { "$($_.ProcessName):$($_.Id)" }) -join ', '
    throw "Codex must be fully closed before repair. Running processes: $names"
}

foreach ($requiredPath in @($globalStatePath, $stateDbPath, $catalogDbPath, $legacySnapshotPath, $sqlitePath)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required file is missing: $requiredPath"
    }
}

$live = Get-Content -Raw -LiteralPath $globalStatePath | ConvertFrom-Json
$snapshot = Get-Content -Raw -LiteralPath $legacySnapshotPath | ConvertFrom-Json

$matchingProjects = @($live.'local-projects'.PSObject.Properties | Where-Object {
    @($_.Value.rootPaths) -contains $projectRoot
})
if ($matchingProjects.Count -ne 1) {
    throw "Expected exactly one current local project for $projectRoot, found $($matchingProjects.Count)."
}

$currentDesktopProjectId = $matchingProjects[0].Name
$mappingHost = $live.'app-server-project-id-by-legacy-project-id-by-host'.$hostMappingKey
$mappingProperty = $mappingHost.PSObject.Properties[$currentDesktopProjectId]
if ($null -eq $mappingProperty -or [string]::IsNullOrWhiteSpace([string]$mappingProperty.Value)) {
    throw "Current App Server project mapping is missing for $currentDesktopProjectId."
}
$currentAppServerProjectId = [string]$mappingProperty.Value

$legacyAssignments = @($snapshot.'thread-project-assignments'.PSObject.Properties | Where-Object {
    $_.Value.projectKind -eq 'local' -and $_.Value.projectId -eq $legacyProjectId
})
if ($legacyAssignments.Count -ne 133) {
    throw "Expected 133 legacy assignments, found $($legacyAssignments.Count)."
}
$threadIds = @($legacyAssignments | ForEach-Object Name)
$threadIdSet = [System.Collections.Generic.HashSet[string]]::new([string[]]$threadIds)

$conflicts = @($threadIds | Where-Object {
    $existing = $live.'thread-project-assignments'.PSObject.Properties[$_]
    $null -ne $existing -and $existing.Value.projectId -ne $currentDesktopProjectId
})
if ($conflicts.Count -gt 0) {
    throw "Found $($conflicts.Count) assignments that now point to another project. No files were changed."
}

$quotedIds = ($threadIds | ForEach-Object { "'" + $_.Replace("'", "''") + "'" }) -join ','
$quotedAppServerProjectId = "'" + $currentAppServerProjectId.Replace("'", "''") + "'"

$projectRowCount = [int](Invoke-SqliteScalar -Database $stateDbPath -ReadOnly -Sql "SELECT COUNT(*) FROM projects WHERE id=$quotedAppServerProjectId;")
if ($projectRowCount -ne 1) {
    throw "Current App Server project row is missing from state_5.sqlite."
}

$statePresent = [int](Invoke-SqliteScalar -Database $stateDbPath -ReadOnly -Sql "SELECT COUNT(*) FROM threads WHERE id IN ($quotedIds);")
$stateConflicts = [int](Invoke-SqliteScalar -Database $stateDbPath -ReadOnly -Sql "SELECT COUNT(*) FROM threads WHERE id IN ($quotedIds) AND project_id IS NOT NULL AND project_id <> $quotedAppServerProjectId;")
$catalogPresent = [int](Invoke-SqliteScalar -Database $catalogDbPath -ReadOnly -Sql "SELECT COUNT(*) FROM local_thread_catalog WHERE host_id='local' AND thread_id IN ($quotedIds);")
$catalogConflicts = [int](Invoke-SqliteScalar -Database $catalogDbPath -ReadOnly -Sql "SELECT COUNT(*) FROM local_thread_catalog WHERE host_id='local' AND thread_id IN ($quotedIds) AND project_id IS NOT NULL AND project_id <> $quotedAppServerProjectId;")

if ($statePresent -ne 131 -or $catalogPresent -ne 133) {
    throw "Unexpected task inventory: state_5.sqlite=$statePresent (expected 131), catalog=$catalogPresent (expected 133)."
}
if ($stateConflicts -gt 0 -or $catalogConflicts -gt 0) {
    throw "A database contains assignments to another project. No files were changed."
}

if ($ValidateOnly) {
    [ordered]@{
        status = 'validated-no-changes'
        projectRoot = $projectRoot
        currentDesktopProjectId = $currentDesktopProjectId
        currentAppServerProjectId = $currentAppServerProjectId
        explicitLegacyAssignments = $threadIds.Count
        stateRowsPresent = $statePresent
        catalogRowsPresent = $catalogPresent
        stateConflicts = $stateConflicts
        catalogConflicts = $catalogConflicts
    } | ConvertTo-Json -Depth 4
    return
}

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupDirectory = Join-Path $backupBase "project-assignment-$timestamp"
New-Item -ItemType Directory -Path $backupDirectory | Out-Null

Copy-StateFileSet -Source $globalStatePath -DestinationDirectory $backupDirectory
Copy-StateFileSet -Source $stateDbPath -DestinationDirectory $backupDirectory
Copy-StateFileSet -Source $catalogDbPath -DestinationDirectory $backupDirectory
Copy-Item -LiteralPath $legacySnapshotPath -Destination $backupDirectory

$manifest = [ordered]@{
    createdAt = (Get-Date).ToString('o')
    projectRoot = $projectRoot
    legacyProjectId = $legacyProjectId
    currentDesktopProjectId = $currentDesktopProjectId
    currentAppServerProjectId = $currentAppServerProjectId
    explicitLegacyAssignments = $threadIds.Count
    stateRowsPresent = $statePresent
    catalogRowsPresent = $catalogPresent
    files = @(Get-ChildItem -LiteralPath $backupDirectory | ForEach-Object {
        [ordered]@{
            name = $_.Name
            length = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        }
    })
}
$manifestPath = Join-Path $backupDirectory 'backup-manifest.json'
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8

$repairSucceeded = $false
try {
    $stateChanges = [int](Invoke-SqliteScalar -Database $stateDbPath -Sql "BEGIN IMMEDIATE; UPDATE threads SET project_id=$quotedAppServerProjectId WHERE id IN ($quotedIds) AND (project_id IS NULL OR project_id <> $quotedAppServerProjectId); SELECT changes(); COMMIT;")
    $catalogChanges = [int](Invoke-SqliteScalar -Database $catalogDbPath -Sql "BEGIN IMMEDIATE; UPDATE local_thread_catalog SET project_id=$quotedAppServerProjectId WHERE host_id='local' AND thread_id IN ($quotedIds) AND (project_id IS NULL OR project_id <> $quotedAppServerProjectId); SELECT changes(); UPDATE local_thread_catalog_metadata SET catalog_revision=catalog_revision+1 WHERE id=1; COMMIT;")

    foreach ($threadId in $threadIds) {
        $live.'thread-project-assignments' | Add-Member -MemberType NoteProperty -Name $threadId -Value ([pscustomobject]@{
            projectKind = 'local'
            projectId = $currentDesktopProjectId
        }) -Force
    }
    $live.'projectless-thread-ids' = @($live.'projectless-thread-ids' | Where-Object {
        -not $threadIdSet.Contains([string]$_)
    })
    $migration = $live.'app-server-projects-migration-by-host'.$hostMappingKey
    $migration.threadAssignmentsMigrated = $true

    $tempGlobalStatePath = "$globalStatePath.repair-$timestamp.tmp"
    $json = $live | ConvertTo-Json -Depth 100 -Compress
    [System.IO.File]::WriteAllText($tempGlobalStatePath, $json, [System.Text.UTF8Encoding]::new($false))
    $roundTrip = Get-Content -Raw -LiteralPath $tempGlobalStatePath | ConvertFrom-Json
    $restoredAssignments = @($threadIds | Where-Object {
        $assignment = $roundTrip.'thread-project-assignments'.PSObject.Properties[$_]
        $null -ne $assignment -and $assignment.Value.projectId -eq $currentDesktopProjectId
    }).Count
    $remainingProjectless = @($threadIds | Where-Object {
        $_ -in @($roundTrip.'projectless-thread-ids')
    }).Count
    if ($restoredAssignments -ne 133 -or $remainingProjectless -ne 0) {
        throw "Global state round-trip validation failed."
    }
    [System.IO.File]::Move($tempGlobalStatePath, $globalStatePath, $true)

    $verifiedState = [int](Invoke-SqliteScalar -Database $stateDbPath -ReadOnly -Sql "SELECT COUNT(*) FROM threads WHERE id IN ($quotedIds) AND project_id=$quotedAppServerProjectId;")
    $verifiedCatalog = [int](Invoke-SqliteScalar -Database $catalogDbPath -ReadOnly -Sql "SELECT COUNT(*) FROM local_thread_catalog WHERE host_id='local' AND thread_id IN ($quotedIds) AND project_id=$quotedAppServerProjectId;")
    $catalogRevision = [int](Invoke-SqliteScalar -Database $catalogDbPath -ReadOnly -Sql "SELECT catalog_revision FROM local_thread_catalog_metadata WHERE id=1;")
    if ($verifiedState -ne 131 -or $verifiedCatalog -ne 133) {
        throw "Post-repair database validation failed."
    }

    $result = [ordered]@{
        status = 'success'
        completedAt = (Get-Date).ToString('o')
        backupDirectory = $backupDirectory
        currentDesktopProjectId = $currentDesktopProjectId
        currentAppServerProjectId = $currentAppServerProjectId
        restoredGlobalAssignments = $restoredAssignments
        removedFromProjectless = 133 - $remainingProjectless
        stateRowsAssigned = $verifiedState
        catalogRowsAssigned = $verifiedCatalog
        stateRowsChanged = $stateChanges
        catalogRowsChanged = $catalogChanges
        catalogRevision = $catalogRevision
        missingSourceRowsPreserved = 2
    }
    $resultPath = Join-Path $backupDirectory 'repair-result.json'
    $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding utf8
    $result | ConvertTo-Json -Depth 6
    $repairSucceeded = $true
}
catch {
    Restore-StateFileSet -Original $globalStatePath -BackupDirectory $backupDirectory
    Restore-StateFileSet -Original $stateDbPath -BackupDirectory $backupDirectory
    Restore-StateFileSet -Original $catalogDbPath -BackupDirectory $backupDirectory
    $failure = [ordered]@{
        status = 'failed-and-rolled-back'
        completedAt = (Get-Date).ToString('o')
        backupDirectory = $backupDirectory
        error = $_.Exception.Message
    }
    $failure | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $backupDirectory 'repair-result.json') -Encoding utf8
    throw
}
finally {
    if ($Relaunch -and $repairSucceeded) {
        Start-Process -FilePath 'explorer.exe' -ArgumentList 'shell:AppsFolder\OpenAI.Codex_2p2nqsd0c76g0!App'
    }
}
