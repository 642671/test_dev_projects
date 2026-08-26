# monitor_nas_141.ps1 - watch 10.18.15.141 for an SSH port opening (read-only)
param(
    [string]$TargetHost = '10.18.15.141',
    [int[]]$CandidatePorts = @(22, 2222, 9222, 2022, 9022, 9522, 1022, 22022, 22222),
    [int]$LoopSeconds = 15,
    [int]$MaxProbes = 200
)
function Test-TcpPort([string]$h, [int]$p) {
    $c = [System.Net.Sockets.TcpClient]::new()
    try {
        $ar = $c.BeginConnect($h, $p, $null, $null)
        if ($ar.AsyncWaitHandle.WaitOne(2000)) {
            $c.EndConnect($ar)
            return $true
        }
    } catch { }
    finally { $c.Dispose() }
    return $false
}
$found = @()
for ($i = 0; $i -lt $MaxProbes; $i++) {
    $now = Get-Date -Format 'HH:mm:ss'
    foreach ($p in $CandidatePorts) {
        if (Test-TcpPort $TargetHost $p) {
            Write-Output ("[{0}] OPEN port {1} on {2}" -f $now, $p, $TargetHost)
            $found += $p
        }
    }
    if ($found.Count -gt 0) { break }
    Start-Sleep -Seconds $LoopSeconds
}
Write-Output ("WATCH_END found=" + ($found -join ','))
