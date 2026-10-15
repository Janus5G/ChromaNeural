# Installer-only presentation. Active locales come from the client registry.
function Initialize-InstallerText([string]$ResourceDirectory, [string]$RegistryPath, [string]$Language) {
  $script:installerEnglish = Get-Content -LiteralPath (Join-Path $ResourceDirectory 'en.json') -Raw -Encoding UTF8 | ConvertFrom-Json
  $script:installerMessages = $script:installerEnglish
  $script:installerLocale = 'en'
  try {
    if ((Get-Item -LiteralPath $RegistryPath).Length -gt 65536) { throw 'registry-size' }
    $registry = Get-Content -LiteralPath $RegistryPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $ids = @($registry.locales | ForEach-Object { $_.id })
    if ($registry.version -ne 1 -or $ids -cnotcontains 'en') { throw 'registry-schema' }
    foreach ($id in $ids) {
      if ($id -isnot [string] -or $id -cnotmatch '^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$') { throw 'registry-id' }
    }
    if (@($ids | Sort-Object -Unique).Count -ne $ids.Count) { throw 'registry-duplicate' }
    if ($Language -and $Language -cin $ids) { $script:installerLocale = $Language }
    $catalogue = Join-Path $ResourceDirectory ($script:installerLocale + '.json')
    if ((Get-Item -LiteralPath $catalogue -ErrorAction Stop).Length -gt 1048576) { throw 'catalogue-size' }
    $script:installerMessages = Get-Content -LiteralPath $catalogue -Raw -Encoding UTF8 | ConvertFrom-Json
  } catch { $script:installerMessages = $script:installerEnglish }
}
function Get-InstallerText([string]$Key, [hashtable]$Values = @{}) {
  $english = [string]$script:installerEnglish.PSObject.Properties[$Key].Value
  $value = $script:installerMessages.PSObject.Properties[$Key].Value
  $pattern = '\{([A-Za-z_][A-Za-z0-9_]*)\}'
  $expected = @([regex]::Matches($english,$pattern) | ForEach-Object { $_.Value } | Sort-Object) -join '|'
  $actual = @([regex]::Matches([string]$value,$pattern) | ForEach-Object { $_.Value } | Sort-Object) -join '|'
  if ($value -isnot [string] -or -not $value -or $actual -cne $expected) { $value = $english }
  if (-not $value) { return $Key }
  return [regex]::Replace($value,$pattern,{
    param($match)
    $name = $match.Groups[1].Value
    if ($Values.ContainsKey($name)) { return [string]$Values[$name] }
    return $match.Value
  })
}
function Show-InstallerMessage([string]$Text, [switch]$Confirm) {
  Add-Type -AssemblyName System.Windows.Forms
  if ($Confirm) {
    return ([System.Windows.Forms.MessageBox]::Show($Text,'ChromaNeural',[System.Windows.Forms.MessageBoxButtons]::YesNo,[System.Windows.Forms.MessageBoxIcon]::Question) -eq [System.Windows.Forms.DialogResult]::Yes)
  }
  [void][System.Windows.Forms.MessageBox]::Show($Text,'ChromaNeural',[System.Windows.Forms.MessageBoxButtons]::OK,[System.Windows.Forms.MessageBoxIcon]::Information)
}
