param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
$ErrorActionPreference = 'Stop'
$path = [IO.Path]::GetFullPath($PSScriptRoot)
if ($path -notmatch '^([A-Za-z]):\\(.*)$') { throw 'Select a local drive path' }
$root = '/mnt/' + $Matches[1].ToLowerInvariant() + '/' + $Matches[2].Replace('\','/')
# All explicit command/config paths passed to the Python CLI are WSL paths.
& wsl.exe --exec /usr/bin/python3 ($root + '/scripts/network_client.py') @Arguments
if ($LASTEXITCODE -ne 0) { throw "Network command failed (exit $LASTEXITCODE); no fallback." }
