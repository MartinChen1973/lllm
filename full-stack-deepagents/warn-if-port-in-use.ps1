param(
    [Parameter(Mandatory = $false)]
    [int] $Port = 3501,

    [Parameter(Mandatory = $false)]
    [string] $Hint = ""
)

$listen = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if (-not $listen) {
    exit 0
}

$proc = Get-Process -Id $listen.OwningProcess -ErrorAction SilentlyContinue
$name = if ($proc) { $proc.ProcessName } else { "?" }
$path = if ($proc -and $proc.Path) { $proc.Path } else { "" }

Write-Host ""
Write-Host "WARNING: TCP port $Port is already in use (PID $($listen.OwningProcess) $name)." -ForegroundColor Yellow
if ($path) {
    Write-Host "         $path" -ForegroundColor Yellow
}
if ($Hint) {
    Write-Host "         $Hint" -ForegroundColor Yellow
}
Write-Host "         PowerShell: Get-NetTCPConnection -LocalPort $Port -State Listen" -ForegroundColor DarkYellow
Write-Host "         Stop listener:  taskkill /PID $($listen.OwningProcess) /F   (closes that process)" -ForegroundColor DarkYellow
Write-Host ""
exit 0
