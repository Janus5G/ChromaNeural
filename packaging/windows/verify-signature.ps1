param([Parameter(Mandatory=$true)][string]$Artifact,[switch]$TestCertificate)
$ErrorActionPreference='Stop'
$expected=$env:SIGNPATH_TEST_CERT_SHA256
if(-not $TestCertificate){throw 'Production certificate policy is not approved'}
if($expected -notmatch '^[A-Fa-f0-9]{64}$'){throw 'Expected test certificate SHA-256 is missing'}
$s=Get-AuthenticodeSignature -LiteralPath $Artifact
if(-not $s.SignerCertificate){throw 'Authenticode signature missing'}
$algorithm=[Security.Cryptography.SHA256]::Create()
try{$actual=([BitConverter]::ToString($algorithm.ComputeHash($s.SignerCertificate.RawData))).Replace('-','')}finally{$algorithm.Dispose()}
if($actual -ne $expected){throw 'Unexpected signing certificate'}
if($s.Status -notin @('Valid','NotTrusted')){throw ('Signature validation failed: '+$s.Status)}
if($s.SignerCertificate.Subject -ne $s.SignerCertificate.Issuer){throw 'Expected self-signed test certificate'}
if($s.SignerCertificate.PublicKey.Key.KeySize -ne 4096){throw 'Unexpected test key size'}
$eku=@($s.SignerCertificate.EnhancedKeyUsageList | ForEach-Object {$_.ObjectId.Value})
if('1.3.6.1.5.5.7.3.3' -notin $eku){throw 'Code Signing EKU missing'}
$hash=(Get-FileHash -LiteralPath $Artifact -Algorithm SHA256).Hash.ToLowerInvariant()
$dir=Split-Path -Parent $Artifact
@{status='PASS';scope='TEST SIGNATURE ONLY';authenticode=$s.Status.ToString();certificateSHA256=$actual;artifactSHA256=$hash;trustedPublicSigning=$false} | ConvertTo-Json | Set-Content -Encoding utf8 -LiteralPath (Join-Path $dir 'TEST_SIGNATURE.json')
($hash+'  '+(Split-Path -Leaf $Artifact)) | Set-Content -Encoding ascii -LiteralPath (Join-Path $dir 'SHA256SUMS.txt')
