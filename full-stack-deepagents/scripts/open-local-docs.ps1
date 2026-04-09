# ## ⬇️ Open local Swagger / app URLs in one Chromium window when possible; otherwise use the default browser per URL.
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $Urls
)

$ErrorActionPreference = "Continue"

if (-not $Urls -or $Urls.Count -eq 0) {
    Write-Host "open-local-docs.ps1: pass at least one URL after the script path." -ForegroundColor Yellow
    exit 1
}

function Get-BrowserExe {
    if ($env:DEEPAGENTS_BROWSER -and (Test-Path -LiteralPath $env:DEEPAGENTS_BROWSER)) {
        return $env:DEEPAGENTS_BROWSER
    }

    $candidates = @(
        "${env:ProgramFiles}\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
        "${env:LOCALAPPDATA}\Google\Chrome\Application\chrome.exe"
    )
    foreach ($p in $candidates) {
        if ($p -and (Test-Path -LiteralPath $p)) { return $p }
    }

    $appPathKeys = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
    )
    foreach ($k in $appPathKeys) {
        if (-not (Test-Path -LiteralPath $k)) { continue }
        try {
            $p = (Get-ItemProperty -LiteralPath $k -ErrorAction Stop)."(default)"
            if ($p -and (Test-Path -LiteralPath $p)) { return $p }
        } catch {
        }
    }

    return $null
}

$browser = Get-BrowserExe

if ($browser) {
    Write-Host "Opening $($Urls.Count) tab(s) in a new window: $browser"
    try {
        $argList = @("--new-window") + $Urls
        Start-Process -FilePath $browser -ArgumentList $argList
        exit 0
    } catch {
        Write-Host "Start-Process (Chromium) failed: $_" -ForegroundColor Yellow
    }
}

Write-Host "Chromium not found under standard paths; opening each URL with the default browser handler."
$anyOk = $false
foreach ($u in $Urls) {
    try {
        Start-Process -FilePath $u
        $anyOk = $true
        Start-Sleep -Milliseconds 400
    } catch {
        Write-Host "Could not open ${u}: $_" -ForegroundColor Yellow
    }
}

if ($anyOk) {
    exit 0
}

exit 1
