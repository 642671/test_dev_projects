[CmdletBinding()]
param(
  [string]$SetupPath = 'D:\test_dev_projects\downloads\Codex-Dream-Skin-v1.5.14\CodexDreamSkin-Setup-v1.5.14.exe',
  [string]$ThemeUri = 'dreamskin://apply?version=ver_34a73ec14a33630c2578',
  [int]$CloseWaitSeconds = 1200
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$workRoot = Split-Path -Parent $PSCommandPath
$statusPath = Join-Path $workRoot 'install-apply-status.json'
$installerLog = Join-Path $workRoot 'setup-v1.5.14.log'
$applyLog = Join-Path $workRoot 'community-apply.log'
$verifyLog = Join-Path $workRoot 'verify.log'
$screenshotPath = Join-Path $workRoot 'codex-dream-skin-verification.png'
$expectedSetupHash = 'e40dd6f024d4ec3ea84014105569001716ab9372cdbc28aec7cdb1a02bbccad9'
$expectedThemeId = 'cecilylove002'
$expectedVersion = '1.5.14'
$stateRoot = Join-Path $env:LOCALAPPDATA 'CodexDreamSkin'
$engineRoot = Join-Path $stateRoot 'engine'
$powershellPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'

function Write-InstallApplyStatus {
  param(
    [Parameter(Mandatory = $true)][string]$Stage,
    [Parameter(Mandatory = $true)][string]$Result,
    [string]$Message = ''
  )
  $payload = [ordered]@{
    stage = $Stage
    result = $Result
    message = $Message
    updatedAt = [DateTime]::UtcNow.ToString('o')
    themeUri = $ThemeUri
    expectedThemeId = $expectedThemeId
    screenshot = $screenshotPath
  } | ConvertTo-Json -Depth 4
  $temporaryPath = "$statusPath.tmp"
  [System.IO.File]::WriteAllText($temporaryPath, $payload, [System.Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $statusPath -Force
}

function Get-RunningStoreCodexProcesses {
  $matches = @()
  foreach ($process in @(Get-Process -Name 'ChatGPT', 'codex' -ErrorAction SilentlyContinue)) {
    $processPath = ''
    try { $processPath = $process.Path } catch { $processPath = '' }
    if ($processPath -like 'C:\Program Files\WindowsApps\OpenAI.Codex_*') {
      $matches += $process
    }
  }
  return @($matches)
}

function Get-Sha256Hex {
  param([Parameter(Mandatory = $true)][string]$LiteralPath)
  $stream = [System.IO.File]::OpenRead($LiteralPath)
  $sha256 = [System.Security.Cryptography.SHA256]::Create()
  try {
    return -join ($sha256.ComputeHash($stream) | ForEach-Object { $_.ToString('x2') })
  } finally {
    $sha256.Dispose()
    $stream.Dispose()
  }
}

try {
  Write-InstallApplyStatus -Stage 'preflight' -Result 'running' -Message 'Rechecking downloaded installer.'
  if (-not (Test-Path -LiteralPath $SetupPath -PathType Leaf)) {
    throw "Setup.exe was not found at $SetupPath"
  }
  $setupHash = Get-Sha256Hex -LiteralPath $SetupPath
  if ($setupHash -cne $expectedSetupHash) {
    throw "Setup.exe SHA-256 mismatch. Expected $expectedSetupHash, got $setupHash"
  }

  Write-InstallApplyStatus -Stage 'waiting-for-codex-close' -Result 'waiting' `
    -Message 'Close the current Codex window to continue. No process will be force-stopped.'
  $deadline = [DateTime]::UtcNow.AddSeconds($CloseWaitSeconds)
  while (@(Get-RunningStoreCodexProcesses).Count -gt 0) {
    if ([DateTime]::UtcNow -ge $deadline) {
      throw "Timed out after $CloseWaitSeconds seconds waiting for Codex to close."
    }
    Start-Sleep -Seconds 2
  }

  Write-InstallApplyStatus -Stage 'installing' -Result 'running' -Message 'Installing verified v1.5.14 release.'
  $setupArguments = @(
    '/VERYSILENT',
    '/SUPPRESSMSGBOXES',
    '/NORESTART',
    '/SP-',
    "/LOG=$installerLog"
  )
  & $SetupPath @setupArguments
  if ($LASTEXITCODE -ne 0) {
    throw "Setup.exe exited with code $LASTEXITCODE. See $installerLog"
  }

  $versionPath = Join-Path $engineRoot 'VERSION'
  if (-not (Test-Path -LiteralPath $versionPath -PathType Leaf)) {
    throw 'The installer exited successfully but the managed engine VERSION file is missing.'
  }
  $installedVersion = ([System.IO.File]::ReadAllText($versionPath)).Trim()
  if ($installedVersion -cne $expectedVersion) {
    throw "Installed engine version mismatch. Expected $expectedVersion, got $installedVersion"
  }

  $protocolCommand = (Get-ItemProperty `
      -LiteralPath 'Registry::HKEY_CURRENT_USER\Software\Classes\dreamskin\shell\open\command' `
      -ErrorAction Stop).'(default)'
  if ([string]::IsNullOrWhiteSpace("$protocolCommand") -or
      "$protocolCommand" -notmatch 'apply-community-theme\.ps1') {
    throw 'The canonical dreamskin:// protocol handler was not registered.'
  }

  $applyScript = Join-Path $engineRoot 'scripts\apply-community-theme.ps1'
  if (-not (Test-Path -LiteralPath $applyScript -PathType Leaf)) {
    throw 'The installed community theme handler is missing.'
  }

  Write-InstallApplyStatus -Stage 'awaiting-theme-confirmation' -Result 'waiting' `
    -Message 'Confirm the already verified community theme in the native dialog.'
  & $powershellPath -NoProfile -STA -WindowStyle Hidden -ExecutionPolicy RemoteSigned `
    -File $applyScript $ThemeUri *> $applyLog
  if ($LASTEXITCODE -ne 0) {
    throw "Community theme apply exited with code $LASTEXITCODE. See $applyLog"
  }

  $activeThemePath = Join-Path $stateRoot 'active-theme\theme.json'
  if (-not (Test-Path -LiteralPath $activeThemePath -PathType Leaf)) {
    throw 'The community apply returned without an active theme file.'
  }
  $activeTheme = [System.IO.File]::ReadAllText($activeThemePath) | ConvertFrom-Json
  if ("$($activeTheme.id)" -cne $expectedThemeId) {
    throw "The requested theme is not active. Expected $expectedThemeId, got $($activeTheme.id)"
  }

  $verifyScript = Join-Path $engineRoot 'scripts\verify-dream-skin.ps1'
  Write-InstallApplyStatus -Stage 'verifying' -Result 'running' -Message 'Running installed renderer verification.'
  & $powershellPath -NoProfile -ExecutionPolicy RemoteSigned -File $verifyScript `
    -ScreenshotPath $screenshotPath *> $verifyLog
  if ($LASTEXITCODE -ne 0) {
    throw "Renderer verification exited with code $LASTEXITCODE. See $verifyLog"
  }
  if (-not (Test-Path -LiteralPath $screenshotPath -PathType Leaf)) {
    throw 'Renderer verification succeeded without producing the expected screenshot.'
  }

  Write-InstallApplyStatus -Stage 'complete' -Result 'success' `
    -Message 'Dream Skin v1.5.14 is installed, the requested theme is active, and renderer verification passed.'
  exit 0
} catch {
  Write-InstallApplyStatus -Stage 'failed' -Result 'error' -Message $_.Exception.Message
  exit 1
}
