param([string]$Language = $env:CHROMANEURAL_INSTALL_LANGUAGE, [switch]$Quiet)
$ErrorActionPreference = 'Stop'
# Select the native module even when a PowerShell 7 parent supplied PSModulePath.
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1') -ErrorAction Stop
$version = '0.2.21-rc.4'
. (Join-Path $PSScriptRoot 'localization.ps1')
Initialize-InstallerText -ResourceDirectory $PSScriptRoot -RegistryPath (Join-Path $PSScriptRoot 'locale-registry.json') -Language $Language
# Localized confirmation; success finishes silently, failures remain explicit.
if (-not $Quiet -and -not (Show-InstallerMessage (Get-InstallerText 'prompt' @{version=$version}) -Confirm)) { exit 0 }
$destination = $env:CHROMANEURAL_INSTALL_DESTINATION
if (-not $destination) { $destination = Join-Path $env:LOCALAPPDATA "Programs\ChromaNeural\$version" }
$log = Join-Path $env:TEMP 'ChromaNeural-install.log'
$stage = Join-Path $env:TEMP ('ChromaNeural-extract-' + [Guid]::NewGuid().ToString('N'))
try {
  Start-Transcript -LiteralPath $log -Force | Out-Null
  try { Get-Command pyw.exe -ErrorAction Stop | Out-Null } catch { throw (Get-InstallerText 'tool_required' @{command='pyw.exe'}) }
  try { Get-Command node.exe -ErrorAction Stop | Out-Null } catch { throw (Get-InstallerText 'tool_required' @{command='node.exe'}) }
  & py.exe -3 -c "import sys,tkinter; assert sys.version_info >= (3,14)"
  if ($LASTEXITCODE -ne 0) { throw (Get-InstallerText 'python') }
  if (Test-Path -LiteralPath $destination) { throw (Get-InstallerText 'existing') }
  Expand-Archive -LiteralPath (Join-Path $PSScriptRoot 'payload.zip') -DestinationPath $stage
  & (Join-Path $stage 'Install-ChromaNeural.ps1') -Destination $destination -Language $Language
  # Publish the per-user shortcut only after the verified payload install succeeds.
  $launcher = (Get-Item -LiteralPath (Join-Path $destination 'Start-ChromaNeural.ps1') -ErrorAction Stop).FullName
  $programs = [Environment]::GetFolderPath('Programs')
  if (-not $programs) { throw (Get-InstallerText 'incomplete' @{path='Start Menu/Programs'}) }
  [IO.Directory]::CreateDirectory($programs) | Out-Null
  $shortcutPath = Join-Path $programs 'ChromaNeural.lnk'
  $shell = New-Object -ComObject WScript.Shell
  try {
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $launcher + '"'
    $shortcut.WorkingDirectory = [IO.Path]::GetDirectoryName($launcher)
    $shortcut.IconLocation = (Join-Path $destination 'client\assets\chroma.ico') + ',0'
    $shortcut.Description = 'ChromaNeural'
    $shortcut.Save()
    Write-Output $shortcutPath
  } finally {
    if ($shortcut) { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shortcut) }
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shell)
  }
} catch {
  $failure = Get-InstallerText 'failed' @{detail=$_.Exception.Message}
  Write-Error $failure -ErrorAction Continue
  if (-not $Quiet) { Show-InstallerMessage $failure }
  exit 1
} finally {
  if (Test-Path -LiteralPath $stage) {
    $resolved = (Get-Item -LiteralPath $stage -Force).FullName
    $parent = (Get-Item -LiteralPath $env:TEMP -Force).FullName.TrimEnd('\')
    if ([IO.Path]::GetDirectoryName($resolved) -ne $parent -or [IO.Path]::GetFileName($resolved) -notmatch '^ChromaNeural-extract-[a-f0-9]{32}$') { throw (Get-InstallerText 'unsafe_cleanup') }
    Remove-Item -LiteralPath $resolved -Recurse -Force
  }
  Stop-Transcript -ErrorAction SilentlyContinue | Out-Null
}
