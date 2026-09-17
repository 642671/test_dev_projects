param(
    [Parameter(Mandatory = $true)]
    [string]$SshHost,

    [Parameter(Mandatory = $true)]
    [string]$RemotePath,

    [Parameter(Mandatory = $true)]
    [string]$LogPath,

    [int]$TotalMiB = 8192,

    [double]$RateMiBPerSec = 8
)

function Write-Log {
    param([string]$Message)

    Add-Content -LiteralPath $LogPath -Value (
        "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    )
}

$remoteCommand = "dd of='$RemotePath' bs=1M status=none conv=fsync"
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = 'ssh.exe'
$startInfo.Arguments = "-o BatchMode=yes -o ConnectTimeout=8 $SshHost `"$remoteCommand`""
$startInfo.UseShellExecute = $false
$startInfo.RedirectStandardInput = $true
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$startInfo.CreateNoWindow = $true

Write-Log "START host=$SshHost remotePath=$RemotePath totalMiB=$TotalMiB rateMiBps=$RateMiBPerSec"

$process = $null
try {
    $process = [System.Diagnostics.Process]::Start($startInfo)
    $buffer = New-Object byte[] (1MB)
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    for ($index = 0; $index -lt $TotalMiB; $index++) {
        $process.StandardInput.BaseStream.Write($buffer, 0, $buffer.Length)

        if ((($index + 1) % 64) -eq 0) {
            $process.StandardInput.Flush()
            Write-Log (
                "PROGRESS miB={0}/{1} elapsedSec={2:N1}" -f
                ($index + 1), $TotalMiB, $stopwatch.Elapsed.TotalSeconds
            )
        }

        $targetMilliseconds = (($index + 1) / $RateMiBPerSec) * 1000
        $delayMilliseconds = [int]($targetMilliseconds - $stopwatch.Elapsed.TotalMilliseconds)
        if ($delayMilliseconds -gt 0) {
            [System.Threading.Thread]::Sleep($delayMilliseconds)
        }
    }

    $process.StandardInput.Close()
    $process.WaitForExit()
    $stderr = $process.StandardError.ReadToEnd()
    $stdout = $process.StandardOutput.ReadToEnd()
    Write-Log (
        "DONE miB={0} elapsedSec={1:N1} exitCode={2} stderr={3} stdout={4}" -f
        $TotalMiB, $stopwatch.Elapsed.TotalSeconds, $process.ExitCode, $stderr, $stdout
    )
}
catch {
    Write-Log "ERROR $($_.Exception.ToString())"
    exit 1
}
finally {
    if ($null -ne $process -and -not $process.HasExited) {
        $process.Kill()
    }
}
