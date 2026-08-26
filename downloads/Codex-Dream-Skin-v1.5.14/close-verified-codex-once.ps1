[CmdletBinding()]
param([int]$DelaySeconds = 20)

$ErrorActionPreference = 'Stop'
$verifiedPrefix = 'C:\Program Files\WindowsApps\OpenAI.Codex_26.810.7004.0_x64__2p2nqsd0c76g0\'
$logPath = 'D:\test_dev_projects\downloads\Codex-Dream-Skin-v1.5.14\close-codex.log'

Start-Sleep -Seconds $DelaySeconds
$targets = foreach ($process in @(Get-Process -Name 'ChatGPT', 'codex' -ErrorAction SilentlyContinue)) {
  $processPath = ''
  try { $processPath = $process.Path } catch { $processPath = '' }
  if ($null -ne $processPath -and
      $processPath.StartsWith($verifiedPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    [pscustomobject]@{ Id = $process.Id; Name = $process.ProcessName; Path = $processPath }
  }
}

$lines = @(
  "timestamp=$([DateTime]::UtcNow.ToString('o'))",
  "verifiedPrefix=$verifiedPrefix",
  "targetCount=$(@($targets).Count)"
)
$lines += @($targets | ForEach-Object { "target=$($_.Name):$($_.Id):$($_.Path)" })
[System.IO.File]::WriteAllLines($logPath, $lines, [System.Text.UTF8Encoding]::new($false))

foreach ($target in @($targets)) {
  Stop-Process -Id $target.Id -Force -ErrorAction SilentlyContinue
}
