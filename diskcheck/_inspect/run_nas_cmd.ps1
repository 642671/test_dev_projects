param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteCommand,
    [string]$NasIp = "10.18.15.135",
    [int]$SshPort = 9222,
    [string]$User = "test",
    [string]$SecretFile = "C:\Users\twm\.codex\secrets\nas-ssh.env"
)

$ErrorActionPreference = "Stop"
$temporaryPasswordFile = $null

try {
    $line = Get-Content -LiteralPath $SecretFile |
        Where-Object { $_ -match "^NAS_SSH_PASSWORD=" } |
        Select-Object -First 1
    if (-not $line) {
        throw "Password entry missing"
    }

    $password = $line.Substring($line.IndexOf("=") + 1).Trim()
    $temporaryPasswordFile = Join-Path $env:TEMP ("nas-cmd-" + [guid]::NewGuid().ToString("N") + ".pw")
    [System.IO.File]::WriteAllText(
        $temporaryPasswordFile,
        $password,
        (New-Object System.Text.UTF8Encoding($false))
    )

    $encoded = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($RemoteCommand))
    $remote = "echo $encoded | base64 -d | sh"

    $ErrorActionPreference = "Continue"
    $output = & plink.exe -batch -ssh -P $SshPort -l $User -pwfile $temporaryPasswordFile -no-antispoof $NasIp $remote 2>&1
    $output | ForEach-Object { Write-Output $_ }
    if ($LASTEXITCODE -ne 0) {
        throw "plink exit code: $LASTEXITCODE"
    }
} finally {
    if ($temporaryPasswordFile -and (Test-Path -LiteralPath $temporaryPasswordFile)) {
        Remove-Item -LiteralPath $temporaryPasswordFile -Force -ErrorAction SilentlyContinue
    }
}
