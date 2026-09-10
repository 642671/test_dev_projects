param(
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
    $temporaryPasswordFile = Join-Path $env:TEMP ("nas-tools-" + [guid]::NewGuid().ToString("N") + ".pw")
    [System.IO.File]::WriteAllText(
        $temporaryPasswordFile,
        $password,
        (New-Object System.Text.UTF8Encoding($false))
    )

    $remoteScript = @'
hostname
uname -a
id
echo '=== TOOL PATHS ==='
for t in nvme skdump sg_inq sg_sat_read_gplog openSeaChest_SMART tos smartctl smartd; do
    printf '%-22s' "$t"
    command -v "$t" || echo 'MISSING'
done
echo '=== PACKAGES ==='
dpkg -l 2>/dev/null | grep -Ei 'smartmontools|^ii  nvme|sg3|libatasmart|openseachest' || true
echo '=== VERSIONS ==='
smartctl --version 2>/dev/null | head -n 1 || true
nvme version 2>/dev/null || true
tos --version 2>/dev/null || true
'@

    $encoded = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($remoteScript))
    $remoteCommand = "echo $encoded | base64 -d | sh"

    $ErrorActionPreference = "Continue"
    $output = & plink.exe -batch -ssh -P $SshPort -l $User -pwfile $temporaryPasswordFile -no-antispoof $NasIp $remoteCommand 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "plink exit code: $LASTEXITCODE"
    }
    $output | ForEach-Object { Write-Output $_ }
} finally {
    if ($temporaryPasswordFile -and (Test-Path -LiteralPath $temporaryPasswordFile)) {
        Remove-Item -LiteralPath $temporaryPasswordFile -Force -ErrorAction SilentlyContinue
    }
}
