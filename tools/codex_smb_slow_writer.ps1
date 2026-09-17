param(
    [Parameter(Mandatory = $true)]
    [string]$Target,

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

Write-Log "START target=$Target totalMiB=$TotalMiB rateMiBps=$RateMiBPerSec"

$stream = $null
try {
    $buffer = New-Object byte[] (1MB)
    $stream = [System.IO.File]::Open(
        $Target,
        [System.IO.FileMode]::Create,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::ReadWrite
    )
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    for ($index = 0; $index -lt $TotalMiB; $index++) {
        $stream.Write($buffer, 0, $buffer.Length)

        if ((($index + 1) % 64) -eq 0) {
            $stream.Flush($false)
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

    $stream.Flush($true)
    Write-Log (
        "DONE miB={0} elapsedSec={1:N1}" -f
        $TotalMiB, $stopwatch.Elapsed.TotalSeconds
    )
}
catch {
    Write-Log "ERROR $($_.Exception.ToString())"
    exit 1
}
finally {
    if ($null -ne $stream) {
        $stream.Dispose()
    }
}
