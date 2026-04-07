# ## ⬇️ Place start-all service consoles in a 3x2 grid on the primary monitor (five tiles + one spare).
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class TileWin {
  public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc lpEnumFunc, IntPtr lParam);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassName(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr hWnd, int X, int Y, int nWidth, int nHeight, bool bRepaint);
}
"@

function Get-ConsoleWindows {
  $list = [System.Collections.Generic.List[System.Tuple[IntPtr, string]]]::new()
  $cb = {
    param([IntPtr] $hWnd, [IntPtr] $lParam)
    if (-not [TileWin]::IsWindowVisible($hWnd)) { return $true }
    $cn = [System.Text.StringBuilder]::new(256)
    [void][TileWin]::GetClassName($hWnd, $cn, $cn.Capacity)
    $class = $cn.ToString()
    # ## ⬇️ Classic conhost; Windows Terminal host (optional)
    if ($class -ne "ConsoleWindowClass" -and $class -ne "CASCADIA_HOSTING_WINDOW_CLASS") { return $true }
    $sb = [System.Text.StringBuilder]::new(1024)
    [void][TileWin]::GetWindowText($hWnd, $sb, $sb.Capacity)
    $title = $sb.ToString()
    if ([string]::IsNullOrEmpty($title)) { return $true }
    [void]$list.Add([System.Tuple[IntPtr, string]]::new($hWnd, $title))
    return $true
  }
  $del = [TileWin+EnumProc]$cb
  [void][TileWin]::EnumWindows($del, [IntPtr]::Zero)
  return $list
}

function Get-ProcessInfoCached {
  param([int] $ProcessId, [hashtable] $Cache)
  if ($Cache.ContainsKey($ProcessId)) { return $Cache[$ProcessId] }
  $info = @{ Name = $null; Path = $null; CmdLine = $null }
  try {
    $p = Get-Process -Id $ProcessId -ErrorAction Stop
    $info.Name = $p.ProcessName
    $info.Path = $p.Path
  } catch {
    $Cache[$ProcessId] = $info
    return $info
  }
  $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
  if ($null -ne $cim) { $info.CmdLine = $cim.CommandLine }
  $Cache[$ProcessId] = $info
  return $info
}

# ## ⬇️ Processes sharing this console report MainWindowHandle == console HWND (not conhost PID).
function Get-ProcessesAttachedToConsole {
  param([IntPtr] $Hwnd)
  Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $mh = $_.MainWindowHandle
    if ($mh -eq [IntPtr]::Zero) { return $false }
    return $mh -eq $Hwnd
  }
}

function Classify-FromProcess {
  param([System.Diagnostics.Process] $Proc, [hashtable] $ProcessCache)
  $info = Get-ProcessInfoCached -ProcessId $Proc.Id -Cache $ProcessCache
  $exe = $info.Path
  $cmd = $info.CmdLine
  $name = $info.Name
  if ($null -ne $exe) {
    if ($exe -match '(?i)\\ai-api\\venv\\Scripts\\python(\.exe)?$') { return "ai" }
    if ($exe -match '(?i)\\mcp-servers\\mcp-server-oa\\venv\\Scripts\\python(\.exe)?$') { return "mcp_oa" }
    if ($exe -match '(?i)\\mcp-servers\\mcp-server-bingchuan\\venv\\Scripts\\python(\.exe)?$') { return "mcp_bc" }
    if ($exe -match '(?i)\\mcp-servers\\mcp-server\\venv\\Scripts\\python(\.exe)?$') { return "mcp_aux" }
    if ($exe -match '(?i)\\mcp-servers\\mcp-server-rag\\venv\\Scripts\\python(\.exe)?$') { return "mcp_oa" }
  }
  if ($null -ne $cmd) {
    if ($name -eq 'cmd' -or $name -eq 'cmd.exe') {
      if ($cmd -match '(?i)npm\s+run\s+dev') { return "next" }
      if ($cmd -match '(?i)npm\s+start') { return "node" }
      # ## ⬇️ start-all.bat may launch frontend/backend with node.exe only (avoids npm retitling the console).
      if ($cmd -match '(?i)node(\.exe)?\s+.*server\.js') { return "node" }
      if ($cmd -match '(?i)node_modules[/\\]next[/\\]dist[/\\]bin[/\\]next') { return "next" }
      if ($cmd -match '(?i)dev-console-title\.js') { return "next" }
    }
    if ($name -eq 'node' -or $name -eq 'node.exe') {
      if ($cmd -match '(?i)next.*dev|next\.js|\\frontend\\') { return "next" }
      if ($cmd -match '(?i)\\backend\\.*server\.js|server\.js') { return "node" }
    }
    if ($cmd -match '(?i)uvicorn|main:app') { return "ai" }
    if ($cmd -match '(?i)mcp-server-oa') { if ($cmd -match '(?i)server\.py') { return "mcp_oa" } }
    if ($cmd -match '(?i)mcp-server-bingchuan') { if ($cmd -match '(?i)server\.py') { return "mcp_bc" } }
    if ($cmd -match '(?i)\\mcp-server\\') { if ($cmd -match '(?i)server\.py') { if ($cmd -notmatch '(?i)bingchuan') { return "mcp_aux" } } }
    if ($cmd -match '(?i)server\.py(\s|$|")') { return "mcp_oa" }
  }
  return $null
}

function Get-ServiceSlot {
  param(
    [IntPtr] $Hwnd,
    [string] $Title,
    [hashtable] $ProcessCache
  )
  $attached = @(Get-ProcessesAttachedToConsole -Hwnd $Hwnd)
  foreach ($proc in $attached) {
    $slot = Classify-FromProcess -Proc $proc -ProcessCache $ProcessCache
    if ($null -ne $slot) { return $slot }
  }
  # ## ⬇️ Title-only hints (Next.js replaces the cmd title with next-server)
  if ($Title -like '*Node frontend (3500)*' -or $Title -like '*next-server*' -or $Title -like '*Next.js*') { return "next" }
  if ($Title -like '*AI API (8500)*' -or $Title -like '*uvicorn*') { return "ai" }
  if ($Title -like '*MCP Bingchuan (8503)*' -or $Title -like '*MCP Bingchuan (8501)*') { return "mcp_bc" }
  if ($Title -like '*MCP OA (8501)*' -or $Title -like '*MCP server (8501)*') { return "mcp_oa" }
  if ($Title -like '*MCP aux (8502)*' -or $Title -like '*MCP OA (8502)*' -or $Title -like '*MCP server (8502)*') { return "mcp_aux" }
  if ($Title -like '*Node backend (3501)*') { return "node" }
  return $null
}

function Find-HwndByTitlePatterns {
  param(
    [System.Collections.Generic.List[System.Tuple[IntPtr, string]]] $Windows,
    [string[]] $Patterns,
    [System.Collections.Generic.HashSet[IntPtr]] $Used
  )
  foreach ($pair in $Windows) {
    if ($Used.Contains($pair.Item1)) { continue }
    foreach ($p in $Patterns) {
      if ($pair.Item2 -like "*${p}*") { return $pair.Item1 }
    }
  }
  return [IntPtr]::Zero
}

$area = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$left = $area.Left
$top = $area.Top
$wThird = [int][Math]::Floor($area.Width / 3)
$hHalf = [int][Math]::Floor($area.Height / 2)
if ($wThird -lt 280) { $wThird = [int][Math]::Floor($area.Width / 2) }
if ($hHalf -lt 240) { $hHalf = [int]$area.Height }

# ## ⬇️ Top row: AI | Node | Next — bottom row: MCP OA (8501) | MCP Bingchuan (8503) | MCP aux (8502)
$layout = @(
  @{ Id = "ai";       X = $left;                 Y = $top;           W = $wThird; H = $hHalf; TitleFallback = @("AI API (8500)", "uvicorn") }
  @{ Id = "node";     X = $left + $wThird;      Y = $top;           W = $wThird; H = $hHalf; TitleFallback = @("Node backend (3501)", "npm start", "server.js") }
  @{ Id = "next";     X = $left + 2 * $wThird;  Y = $top;           W = $wThird; H = $hHalf; TitleFallback = @("Node frontend (3500)", "next-server", "localhost:3500", "127.0.0.1:3500") }
  @{ Id = "mcp_oa";   X = $left;                 Y = $top + $hHalf; W = $wThird; H = $hHalf; TitleFallback = @("MCP OA (8501)", "MCP server (8501)") }
  @{ Id = "mcp_bc";   X = $left + $wThird;      Y = $top + $hHalf; W = $wThird; H = $hHalf; TitleFallback = @("MCP Bingchuan (8503)", "MCP Bingchuan (8501)", "MCP server (8501)") }
  @{ Id = "mcp_aux";  X = $left + 2 * $wThird;  Y = $top + $hHalf; W = $wThird; H = $hHalf; TitleFallback = @("MCP aux (8502)", "MCP server (8502)") }
)

$usedHwnd = [System.Collections.Generic.HashSet[IntPtr]]::new()
$placedId = @{}

for ($attempt = 0; $attempt -lt 30; $attempt++) {
  $windows = Get-ConsoleWindows
  $procCache = @{}

  foreach ($pair in $windows) {
    if ($usedHwnd.Contains($pair.Item1)) { continue }
    $slot = Get-ServiceSlot -Hwnd $pair.Item1 -Title $pair.Item2 -ProcessCache $procCache
    if ($null -eq $slot) { continue }
    if ($placedId.ContainsKey($slot)) { continue }
    $cell = $layout | Where-Object { $_.Id -eq $slot } | Select-Object -First 1
    if ($null -eq $cell) { continue }
    [void][TileWin]::MoveWindow($pair.Item1, $cell.X, $cell.Y, $cell.W, $cell.H, $true)
    [void]$usedHwnd.Add($pair.Item1)
    $placedId[$slot] = $true
  }

  foreach ($cell in $layout) {
    if ($placedId.ContainsKey($cell.Id)) { continue }
    $hwnd = Find-HwndByTitlePatterns -Windows $windows -Patterns $cell.TitleFallback -Used $usedHwnd
    if ($hwnd -ne [IntPtr]::Zero) {
      [void][TileWin]::MoveWindow($hwnd, $cell.X, $cell.Y, $cell.W, $cell.H, $true)
      [void]$usedHwnd.Add($hwnd)
      $placedId[$cell.Id] = $true
    }
  }

  if ($placedId.Count -ge 6) { break }
  Start-Sleep -Milliseconds 350
}
