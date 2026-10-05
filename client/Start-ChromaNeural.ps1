param([string]$Workspace, [string]$SmokeReport, [string]$StateDirectory, [string]$Language)
$ErrorActionPreference = 'Stop'
$uiRegistryPath = Join-Path $PSScriptRoot 'locale-registry.json'
if ((Get-Item -LiteralPath $uiRegistryPath).Length -gt 65536) { throw 'Locale registry exceeds limit' }
$uiRegistry = Get-Content -LiteralPath $uiRegistryPath -Raw -Encoding UTF8 | ConvertFrom-Json
$uiLocales = @($uiRegistry.locales | ForEach-Object { $_.id })
if ($uiRegistry.version -ne 1 -or $uiLocales.Count -eq 0 -or $uiLocales -cnotcontains 'en') { throw 'Invalid locale registry' }
foreach ($uiId in $uiLocales) {
  if ($uiId -isnot [string] -or $uiId -cnotmatch '^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$') { throw 'Invalid locale identifier' }
}
if (@($uiLocales | Sort-Object -Unique).Count -ne $uiLocales.Count) { throw 'Duplicate locale identifier' }
if ($PSBoundParameters.ContainsKey('Language') -and $Language -notin $uiLocales) { throw 'Unsupported locale' }
$uiLocale = if ($Language) { $Language } else { 'en' }
if (-not $Language) {
  $uiDirectory = if ($StateDirectory) { $StateDirectory } elseif ($env:CHROMA_STATE_DIR) { $env:CHROMA_STATE_DIR } else { Join-Path $env:LOCALAPPDATA 'ChromaNeural\client' }
  $uiPreference = Join-Path $uiDirectory 'ui-language.json'
  try {
    if ((Test-Path -LiteralPath $uiPreference) -and (Get-Item -LiteralPath $uiPreference).Length -le 1024) {
      $uiSaved = Get-Content -LiteralPath $uiPreference -Raw -Encoding UTF8 | ConvertFrom-Json
      $uiKeys = @($uiSaved.PSObject.Properties.Name)
      if ($uiKeys.Count -eq 2 -and $uiKeys -contains 'version' -and $uiKeys -contains 'locale' -and $uiSaved.version -is [int] -and $uiSaved.version -eq 1 -and $uiSaved.locale -cin $uiLocales) { $uiLocale = $uiSaved.locale }
    }
  } catch { $uiLocale = 'en' }
}
$uiEnglish = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'locales\en.json') -Raw -Encoding UTF8 | ConvertFrom-Json
try { $uiMessages = Get-Content -LiteralPath (Join-Path $PSScriptRoot ("locales\" + $uiLocale + ".json")) -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $uiMessages = $uiEnglish }
function Get-LaunchText([string]$Key) {
  $value = $uiMessages.PSObject.Properties[$Key].Value
  if (-not $value) { $value = $uiEnglish.PSObject.Properties[$Key].Value }
  return [string]$value
}
$launcher = Join-Path $PSScriptRoot 'launch.py'
try { $pyw = Get-Command pyw.exe -ErrorAction Stop } catch { throw ((Get-LaunchText 'launch.failed').Replace('{code}', '?')) }
function Quote-NativeArgument([string]$Value) {
  return '"' + [regex]::Replace([regex]::Replace($Value, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1') + '"'
}
$argsList = @($launcher)
if ($Language) { $argsList += @('--language', $Language) }
if ($Workspace) { $argsList += @('--workspace', $Workspace) }
if ($StateDirectory) { $argsList += @('--state-dir', $StateDirectory) }
if ($SmokeReport) { $argsList += @('--smoke-report', $SmokeReport) }
# The legacy Python launcher parses its selector before Windows argv unquoting.
$quoted = '-3 ' + (($argsList | ForEach-Object { Quote-NativeArgument $_ }) -join ' ')
$process = Start-Process -FilePath $pyw.Source -ArgumentList $quoted -WindowStyle Hidden -PassThru
if ($process.WaitForExit(1000) -and $process.ExitCode -ne 0) {
  throw ((Get-LaunchText 'launch.failed').Replace('{code}', [string]$process.ExitCode))
}
Write-Output ((Get-LaunchText 'launch.started').Replace('{pid}', [string]$process.Id))
