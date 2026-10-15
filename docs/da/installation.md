# Installer RC5-kandidaten

[English](../en/installation.md) · [Brugervejledning](guide.md)

RC5 er ikke offentliggjort. Brug kun den præcise kandidat til manuel accept og dens SHA256SUMS. Brug ikke en tilbagetrukket RC4-pakke som erstatning. Offentlig release kræver separat ejergodkendelse og vurdering af produktionssigneringen.

## Windows x64

Installer Python 3.14 eller nyere med Tk og py/pyw-launcherne samt Node.js 24 eller nyere. Installeren henter ikke forudsætninger, modeller eller brugertilstand.

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\ChromaNeural-0.2.21-rc.5-windows-x64.exe'
Get-AuthenticodeSignature -LiteralPath '.\ChromaNeural-0.2.21-rc.5-windows-x64.exe'
```

Sammenlign hele hashen. Usignerede lokale builds og selvsignerede testbuilds er ikke betroet produktionssignering. Deaktiver ikke Windows' sikkerhedsbeskyttelse.

Kør den grafiske Inno Setup-installer. Standardmappen pr. bruger er `%LOCALAPPDATA%\Programs\ChromaNeural\App`. Den tilføjer **ChromaNeural** i Startmenuen og Installerede apps. Den opretter ingen skrivebordsgenvej, starter ikke klienten automatisk og importerer ingen konto. Start selv klienten fra Startmenuen.

Geninstallation af samme Inno-administrerede version erstatter programfilerne. En senere Inno-administreret version bruger samme installationsidentitet/mappe; nedgradering afvises. Den tidligere versionsopdelte RC4-installation fjernes eller migreres ikke tavst. Luk klienten før installation, opdatering eller fjernelse. Brugertilstand ligger separat og bevares ved afinstallation; eksisterende brugertilstand beviser ikke forurening af pakken. Brug en isoleret, tom `--state-dir` til første-start-accept.

Afinstaller via **Installerede apps** i Windows. Registrerede programfiler og Startmenu-genvejen fjernes; brugerdata og arbejdsmapper bevares. Egne filer i programmappen er ikke installerens filer. Inno Setup logger installationen; en eksplicit log kan vælges med `/LOG="<valgt-logfil>"`.

## Linux amd64

Brug den native acceptprofil Ubuntu 24.04 amd64. Afhængigheder: Python 3.11+ inklusive Python 3.12-kompatibilitet, Tk, distributionens cryptography, Node.js 20+ og libgomp1.

```sh
sha256sum chromaneural_0.2.21.rc.5_amd64.deb
sudo apt install ./chromaneural_0.2.21.rc.5_amd64.deb
chromaneural
```

Pakkeplaceringerne er fortsat `/opt/chromaneural`, `/usr/bin/chromaneural` og desktopmetadata under `/usr/share/applications`. Fjernelse sker gennem distributionens pakkehåndtering og er ikke det samme som at slette separate brugerdata.

## Ren første start

Åbn Ressourcer, lad bidrag være slået fra, gem og åbn Login & forbindelse. Feltet skal være tomt, og ingen profil eller kontoidentitet må være indlæst. Brug ikke personlige forbindelsesdata under releaseaccept. Gennemgå engelsk og dansk GUI separat med sprogvælgeren. Faktiske RC5-resultater for installation, opstart, afinstallation og signering står i [releasestatus](../../RELEASE_NOTES.md); tidligere RC4-accept certificerer ikke den nye installer.
