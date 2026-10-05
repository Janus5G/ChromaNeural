param(
  [Parameter(Mandatory=$true)][string]$Config,
  [Parameter(Mandatory=$true)][ValidateSet("Send","ReceiveOnce")][string]$Mode,
  [string]$PeerHost,
  [int]$Port = 7443,
  [string]$File,
  [string]$MessageId,
  [string]$Kind = "data",
  [string]$BindAddress = "127.0.0.1",
  [string]$Inbox
)
$ErrorActionPreference = "Stop"
function Convert-WslPath([string]$Value) {
  $full = [IO.Path]::GetFullPath($Value)
  if ($full -notmatch '^([A-Za-z]):\\(.*)$') { throw "Select a local drive path" }
  return "/mnt/" + $Matches[1].ToLowerInvariant() + "/" + $Matches[2].Replace('\','/')
}
$root = Convert-WslPath $PSScriptRoot
$configPath = Convert-WslPath $Config
$argsLinux = @("--exec","/usr/bin/python3",($root + "/scripts/peer_provider.py"),"--config",$configPath)
if ($Mode -eq "Send") {
  if (-not $PeerHost -or -not $File -or -not $MessageId) { throw "Send requires PeerHost, File and stable MessageId for retries" }
  $argsLinux += @("send","--host",$PeerHost,"--port","$Port","--file",(Convert-WslPath $File),"--id",$MessageId,"--kind",$Kind)
} else {
  if (-not $Inbox) { throw "ReceiveOnce requires a dedicated inbox database path" }
  $argsLinux += @("receive-once","--bind",$BindAddress,"--port","$Port","--inbox",(Convert-WslPath $Inbox))
}
& wsl.exe @argsLinux
if ($LASTEXITCODE -ne 0) { throw "WSL peer transport failed with exit code $LASTEXITCODE. Review stderr; no insecure fallback was attempted." }
