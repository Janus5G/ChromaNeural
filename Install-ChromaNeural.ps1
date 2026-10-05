param([Parameter(Mandatory=$true)][string]$Destination, [string]$Language = $env:CHROMANEURAL_INSTALL_LANGUAGE)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'installer\localization.ps1')
Initialize-InstallerText -ResourceDirectory (Join-Path $PSScriptRoot 'installer') -RegistryPath (Join-Path $PSScriptRoot 'client\locale-registry.json') -Language $Language
$source = [IO.Path]::GetFullPath($PSScriptRoot)
$target = [IO.Path]::GetFullPath($Destination)
if (Test-Path -LiteralPath $target) { throw (Get-InstallerText 'new_destination') }
if ($target.StartsWith($source + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw (Get-InstallerText 'outside') }

function Assert-NoReparse([string]$Path) {
  $current = [IO.Path]::GetFullPath($Path)
  while ($current) {
    if (Test-Path -LiteralPath $current) {
      $item = Get-Item -LiteralPath $current -Force
      if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw (Get-InstallerText 'linked_install' @{path=$current}) }
    }
    $current = [IO.Path]::GetDirectoryName($current)
  }
}
Assert-NoReparse $source
Assert-NoReparse $target
$manifestPath = Join-Path $source 'SHA256SUMS.txt'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw (Get-InstallerText 'missing_manifest') }
Assert-NoReparse $manifestPath
if ((Get-Item -LiteralPath $manifestPath).Length -gt 4194304) { throw (Get-InstallerText 'manifest_size') }
$hashes = @{}
foreach ($line in [IO.File]::ReadAllLines($manifestPath)) {
  if ($line -notmatch '^([a-fA-F0-9]{64})  (.+)$') { throw (Get-InstallerText 'invalid_manifest') }
  $hash = $Matches[1].ToLowerInvariant(); $relative = $Matches[2]
  if ($relative.Contains('\') -or $relative.Contains(':') -or $relative.StartsWith('/') -or
      ($relative.Split('/') | Where-Object { $_ -eq '' -or $_ -eq '.' -or $_ -eq '..' -or $_.EndsWith('.') -or $_.EndsWith(' ') }) -or
      $hashes.ContainsKey($relative)) { throw (Get-InstallerText 'unsafe_manifest' @{path=$relative}) }
  $hashes[$relative] = $hash
}
$selfName = 'Install-ChromaNeural.ps1'
if (-not $hashes.ContainsKey($selfName) -or (Get-FileHash -LiteralPath (Join-Path $source $selfName) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hashes[$selfName]) { throw (Get-InstallerText 'installer_mismatch') }

# Preserve the established portable payload and launcher/state contracts.
$required = @('client', 'models', 'runtime', 'scripts', 'Start-ChromaNeural.ps1', 'ChromaSpeech-WSL.ps1')
foreach ($item in $required) { if (-not (Test-Path -LiteralPath (Join-Path $source $item))) { throw (Get-InstallerText 'incomplete' @{path=$item}) } }
$roots = @('client', 'models', 'runtime/linux-x64', 'runtime/windows-x64', 'scripts', 'Start-ChromaNeural.ps1', 'ChromaSpeech-WSL.ps1')
foreach ($provider in @('runtime/linux-x64','runtime/windows-x64')) {
  if (-not (Test-Path -LiteralPath (Join-Path $source $provider) -PathType Container)) { throw (Get-InstallerText 'incomplete' @{path=$provider}) }
}
foreach ($item in @('README.md','VALIDATION.md','docs','installer','ChromaNetwork-WSL.ps1','LICENSE','NOTICE','THIRD_PARTY_LICENSES.md','THIRD_PARTY_NOTICES.md','INSTALLATION.md','VERIFICATION.md','KNOWN_LIMITATIONS.md','RELEASE_NOTES.md','CHANGELOG.md','SECURITY.md','CONTRIBUTING.md','VERSION')) {
  if (Test-Path -LiteralPath (Join-Path $source $item)) { $roots += $item }
}
# Discover translated root READMEs; the same manifest/path checks apply.
Get-ChildItem -LiteralPath $source -Filter 'README-*.md' -File | ForEach-Object { $roots += $_.Name }
$files = @{}
$pending = New-Object 'System.Collections.Generic.Stack[string]'
foreach ($relative in $roots) { $pending.Push((Join-Path $source $relative)) }
while ($pending.Count) {
  $path = $pending.Pop(); $item = Get-Item -LiteralPath $path -Force
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw (Get-InstallerText 'linked_payload' @{path=$path}) }
  if ($item.PSIsContainer) {
    foreach ($child in Get-ChildItem -LiteralPath $path -Force) { $pending.Push($child.FullName) }
  } else {
    $relative = $item.FullName.Substring($source.Length + 1).Replace('\','/')
    if (-not $hashes.ContainsKey($relative)) { throw (Get-InstallerText 'unmanifested' @{path=$relative}) }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hashes[$relative]) { throw (Get-InstallerText 'payload_mismatch' @{path=$relative}) }
    $files[$relative] = $path
  }
}
foreach ($relative in $hashes.Keys) {
  foreach ($root in $roots) {
    if (($relative -eq $root -or $relative.StartsWith($root + '/', [StringComparison]::OrdinalIgnoreCase)) -and -not $files.ContainsKey($relative)) { throw (Get-InstallerText 'missing_payload' @{path=$relative}) }
  }
}
if ($files.Count -eq 0) { throw (Get-InstallerText 'empty') }

$parent = [IO.Path]::GetDirectoryName($target)
$stage = Join-Path $parent ('.chromaneural-install-' + [Guid]::NewGuid().ToString('N'))
$created = $false
try {
  # No user state, credentials, dependencies or network operations are involved.
  if (Test-Path -LiteralPath $stage) { throw (Get-InstallerText 'stage_exists') }
  New-Item -ItemType Directory -Path $stage | Out-Null; $created = $true
  foreach ($relative in ($files.Keys | Sort-Object)) {
    $output = Join-Path $stage $relative
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($output)) | Out-Null
    [IO.File]::Copy($files[$relative], $output, $false)
    if ((Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hashes[$relative]) { throw (Get-InstallerText 'copied_mismatch' @{path=$relative}) }
  }
  $lines = @($files.Keys | Sort-Object | ForEach-Object { $hashes[$_] + '  ' + $_ })
  [IO.File]::WriteAllLines((Join-Path $stage 'SHA256SUMS.txt'), $lines, (New-Object System.Text.UTF8Encoding($false)))
  Assert-NoReparse $target
  if (Test-Path -LiteralPath $target) { throw (Get-InstallerText 'destination_appeared') }
  [IO.Directory]::Move($stage, $target)
  $created = $false
} finally {
  if ($created -and (Test-Path -LiteralPath $stage)) {
    # Delete only this invocation's random staging directory, never Destination.
    $resolved = (Resolve-Path -LiteralPath $stage).Path
    if ([IO.Path]::GetDirectoryName($resolved) -ne $parent -or [IO.Path]::GetFileName($resolved) -notmatch '^\.chromaneural-install-[a-f0-9]{32}$') { throw (Get-InstallerText 'unsafe_stage') }
    Assert-NoReparse $stage
    Remove-Item -LiteralPath $resolved -Recurse -Force
  }
}
Write-Output (Get-InstallerText 'installed' @{path=$target})
Write-Output (Get-InstallerText 'verified')
Write-Output (Get-InstallerText 'boundaries')
