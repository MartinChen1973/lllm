param(
    [Parameter(Mandatory = $false)]
    [string] $Url = "http://127.0.0.1:8500/openapi.json",

    [Parameter(Mandatory = $false)]
    [int] $RequestTimeoutSec = 3,

    [Parameter(Mandatory = $false)]
    [int] $MaxWaitSec = 120,

    [Parameter(Mandatory = $false)]
    [string] $Label = "service"
)

$deadline = [datetime]::UtcNow.AddSeconds($MaxWaitSec)
$n = 0
while ([datetime]::UtcNow -lt $deadline) {
    $n++
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $RequestTimeoutSec
        if ($r.StatusCode -eq 200) {
            if ($n -gt 1) {
                Write-Host "[$Label] Ready after ~$n s ($Url)"
            } else {
                Write-Host "[$Label] Ready ($Url)"
            }
            exit 0
        }
    } catch {
        # still starting — MCP handshake, model init, etc.
    }
    if (($n -eq 1) -or (($n % 5) -eq 0)) {
        Write-Host "[$Label] Waiting for HTTP 200 ($Url) ... (${n}s)"
    }
    Start-Sleep -Seconds 1
}

Write-Host "[$Label] TIMEOUT after ${MaxWaitSec}s ($Url)"
exit 1
