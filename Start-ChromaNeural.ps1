param([string]$Workspace, [string]$SmokeReport, [string]$StateDirectory, [string]$Language)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'client\Start-ChromaNeural.ps1') @PSBoundParameters
