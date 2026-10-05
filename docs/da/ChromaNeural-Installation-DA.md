# ChromaNeural

[English](../en/ChromaNeural-Installation.md) · [Dansk](ChromaNeural-Installation-DA.md) · [Deutsch](../de/ChromaNeural-Installation.md) · [Français](../fr/ChromaNeural-Installation.md) · [日本語](../ja/ChromaNeural-Installation.md) · [简体中文](../zh-CN/ChromaNeural-Installation.md) · [हिन्दी](../hi-IN/ChromaNeural-Installation.md)
## Installation

ChromaNeural 0.2.21-rc.2-dokumentation | Ikke offentliggjort kandidat | 3. oktober 2026

**Status for rc.2-dokumentationen:** Denne kandidat er ikke offentliggjort. Lokalisering og udvidelig i18n har bestået lokal verifikation; native build- og pakkeaccept for rc.2 afventer stadig. Installations-, platforms-, LAN/WAN-, inference- og live-tjenesteevidens nedenfor er historisk rc.1-evidens, medmindre den udtrykkeligt er mærket rc.2. Links til rc.1-downloads giver ikke rc.2-lokalisering.

## Historisk rc.1-installationsreference

Der findes endnu ingen offentlig rc.2-pakke at installere. Filnavne og kommandoer nedenfor er bevidst rc.1-eksempler. De installerer ikke sprogvælgeren eller registeret. For en allerede klargjort lokal rc.2-kandidat vælger --language sproget for én start; Windows accepterer -Language. GUI-valget gemmer sproget. Omdøb ikke en rc.1-pakke, og indsæt ikke en uverificeret rc.2-downloadadresse.

## Før du installerer

Hent pakker fra den officielle release:

../../RELEASE_NOTES.md

Vælg den præcise platform og arkitektur. Pakkerne er usignerede, og macOS er ikke notariseret. Operativsystemet kan advare eller forhindre åbning. Slå ikke sikkerhedsbeskyttelsen generelt fra. Kontrollér oprindelse og checksum, før du beslutter at åbne en pakke.

- Windows x64: ChromaNeural-0.2.21-rc.1-windows-x64.exe
- Linux amd64: chromaneural_0.2.21.rc.1_amd64.deb
- macOS Intel x86_64: ChromaNeural-0.2.21-rc.1-macos-x86_64.zip
- Kildesnapshot: ChromaNeural-0.2.21-rc.1-source.zip
- Checksums: SHA256SUMS.txt

GitHub normaliserede DEB-downloadnavnet fra ~rc.1 til .rc.1. Indholdet og SHA-256 er uændret; pakkens interne Debian-version bruger fortsat ~rc.1.

### Sammenlign SHA-256

Kør kommandoen i den mappe, hvor den pågældende download ligger:

Windows PowerShell:
```
Get-FileHash -Algorithm SHA256 -LiteralPath '.\ChromaNeural-0.2.21-rc.1-windows-x64.exe'
```

Linux:
```
sha256sum chromaneural_0.2.21.rc.1_amd64.deb
```

macOS:
```
shasum -a 256 ChromaNeural-0.2.21-rc.1-macos-x86_64.zip
```

Sammenlign alle 64 tegn med linjen for samme fil i SHA256SUMS.txt. Stop ved afvigelse. En checksum beviser byteintegritet, ikke alene udgiverens identitet. Den fulde offentlige hashoversigt findes også i docs/DOWNLOADS.md.

<!-- page -->
## Windows x64

### Forudsætninger

Python 3.14 med Tk og py/pyw-launchere samt Node.js 24 skal være installeret. EXE-filen er en offline installationspakke pr. bruger; den indeholder ikke en komplet frosset Python-/Node-runtime. Hav cirka 2 GB ledig plads til midlertidig udpakning og installation.

### Trin

1. Kontrollér den downloadede EXE-fil som beskrevet på forrige side.
2. Åbn EXE-filen, og bekræft installationen efter kontrol af OS-advarsler.
3. Programmet installeres i denne versionsmappe:
```
%LOCALAPPDATA%\Programs\ChromaNeural\0.2.21-rc.1
```
4. Start Start-ChromaNeural.ps1 i den mappe. Eksempel i PowerShell:
```
& "$env:LOCALAPPDATA\Programs\ChromaNeural\0.2.21-rc.1\Start-ChromaNeural.ps1"
```
5. Gem ressourcepræferencer ved første start. Brug siden Login & forbindelse til offentlig API-kontrol, hvis det ønskes.

Installationsloggen findes i %TEMP%\ChromaNeural-install.log. En eksisterende destinationsmappe afvises; dette er ikke en automatisk in-place-upgrader. Ingen automatisk deltagelse eller Windows-autostart registreres. Der oprettes ikke automatisk en skrivebordsgenvej i denne RC.

ICP SDK og de låste runtimeafhængigheder er allerede pakket. Kør ikke npm ci som installationskrav, og angiv ikke et NODE_PATH til et gammelt udviklingsmiljø.

### Afinstallation og state

Luk klienten helt. Fjern kun den pågældende versions installationsmappe, hvis programfilerne skal væk. Klientstate i %LOCALAPPDATA%\ChromaNeural\client, valgte workspaces og separate identitetsmapper skal bevares eller håndteres særskilt efter dit eget valg. Der medfølger ikke en automatisk afinstalleringsfunktion.

<!-- page -->
## Linux amd64

Den native verifikationsprofil er Ubuntu 24.04 amd64. Det er ikke dokumentation for alle distributioner eller alle versioner. Ingen WSL-test bruges som erstatning for native Linux-pakkeverifikation.

Pakken kræver Python 3.11 eller nyere, Tk, distributionens cryptography, Node.js 20 eller nyere og libgomp1. Brug distributionens pakkehåndtering til disse afhængigheder. Fra downloadmappen:
```
sudo apt install ./chromaneural_0.2.21.rc.1_amd64.deb
```

Start via programmenuen eller:
```
chromaneural
```

Programfiler installeres under /opt/chromaneural, launcher under /usr/bin/chromaneural og desktopmetadata under /usr/share/applications/chromaneural.desktop. Ingen post-install netværksinstallation af npm og ingen automatisk brugerstatemigration indgår.

Native build, pakkeudpakning, payloadintegritet, SDK, CLI og Xvfb/Tk er verificeret. En fuld dpkg install-/fjern-livscyklus er endnu ikke verificeret. Det offentliggjorte RC-desktopentry mangler en produktspecifik ikonreference; programstarten er stadig tilgængelig.

## macOS Intel x86_64

Kræver macOS 15+, Python 3.14 med fungerende Tk samt Node.js 24. Brug samme Python-installation til de låste cryptoafhængigheder. Fra det accepterede source-snapshots rod:
```
python3 -m pip install --require-hashes -r packaging/requirements-runtime.txt
```

Det fastlåste sæt er cryptography 46.0.5, cffi 2.1.1 og pycparser 3.0. Det er forudsætninger for denne klient, ikke et krav om II-credentials.

Udpak ZIP-filen, flyt ChromaNeural.app til Applications, og åbn den efter kontrol af oprindelse og OS-advarsler. Pakken er Intel-only; Universal 2, Apple Silicon og Rosetta er ikke accepterede platformprofiler i denne release.

Native build, pakkeintegritet, SDK, CLI og Tk er verificeret. Manuel macOS-GUI er ikke verificeret. Pakken er ikke signeret eller notariseret og mangler et produktspecifikt bundleikon. Der er ingen bundled Qwen/llama.cpp-runtime på macOS. Den eksplicitte lokale Ollama-adapter kræver egen installeret model; kontrolleret baggrundsbidrag er unsupported.

<!-- page -->
## Første start og sikker opfølgning

![Ressourcer i den faktiske Windows-klient. Platformenes vinduesdekorationer kan variere.](../images/chroma-neural-resources.png)

Vælg ressourcer og gem. Oversigt viser kun bekræftede tal; en streg er ikke et løfte om optjening. Generel ressourcedeling er fortsat deaktiveret. Brug **Afslut ChromaNeural** til at lukke helt.

Hvis programmet ikke starter, kontrollér først de dokumenterede runtimeforudsætninger og den rigtige pakke/arkitektur. Bevar eksisterende state. Undgå at nulstille identiteter eller kopiere private data ind i fejlrapporter. Se også brugervejledningen og privatlivsvejledningen.

Installation ændrer ikke Internet Identity, production-backend eller browserens session. Offentlig API-rækkevidde er verificeret på Windows. Faktisk live II end-to-end, live admission og live migration er fortsat ikke verificeret.

Officiel understøttelse af Android og iOS er udsat til senere.

Den aktuelle online dokumentation kan være nyere end teksterne i de uændrede RC-binaries og source-ZIP. Releasefilerne erstattes ikke blot for at ændre dokumentation eller ikoner. Se docs/BRANDING.md for pakkeikonernes status.

MCP er fortsat en særskilt gated funktion efter rc.2 og er ikke implementeret her. Denne dokumentation indebærer ingen ny produktions- eller Internet Identity-ændring.
