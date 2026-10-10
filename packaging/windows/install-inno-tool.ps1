$ErrorActionPreference='Stop'
$destination=Join-Path $env:RUNNER_TEMP 'chromaneural-inno-7.1.0'
$download=Join-Path $env:RUNNER_TEMP 'innosetup-7.1.0-x64.exe'
Invoke-WebRequest -Uri 'https://github.com/jrsoftware/issrc/releases/download/is-7_1_0/innosetup-7.1.0-x64.exe' -OutFile $download
if((Get-FileHash -LiteralPath $download -Algorithm SHA256).Hash -ne '0362A383ED217D4C4239B5933866DD96D3EB2102737DA92F80F6057A4B40DF2F'){throw 'Inno compiler download hash mismatch'}
$signature=Get-AuthenticodeSignature -LiteralPath $download
if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Pyrsys'){throw 'Inno compiler publisher validation failed'}
$p=Start-Process -FilePath $download -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/CURRENTUSER','/NOICONS',('/DIR="'+$destination+'"')) -WindowStyle Hidden -Wait -PassThru
if($p.ExitCode -ne 0 -or -not(Test-Path -LiteralPath "$destination\ISCC.exe")){throw 'Inno installation failed'}
"CHROMA_ISCC=$destination\ISCC.exe" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
