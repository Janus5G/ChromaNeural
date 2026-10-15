# Installer RC5 på Linux

[English](../en/installation.md) · [Brugervejledning](guide.md)

**Officiel release: Linux amd64.** Kildekoden er fortsat tilgængelig til community-ports og tilpasning til andre platforme. Windows, macOS og mobile platforme er ikke aktuelt officielt supporteret eller verificeret.

[RC5 prerelease / SHA256SUMS](https://github.com/Janus5G/ChromaNeural/releases/tag/v0.2.21-rc.5)

## Linux amd64

Brug den native acceptprofil Ubuntu 24.04 amd64. Afhængigheder: Python 3.11+ inklusive Python 3.12-kompatibilitet, Tk, distributionens cryptography, Node.js 20+ og libgomp1.

```sh
sha256sum chromaneural_0.2.21.rc.5_amd64.deb
sudo apt install ./chromaneural_0.2.21.rc.5_amd64.deb
chromaneural
```

Pakkeplaceringerne er fortsat `/opt/chromaneural`, `/usr/bin/chromaneural` og desktopmetadata under `/usr/share/applications`. Fjernelse sker gennem distributionens pakkehåndtering og er ikke det samme som at slette separate brugerdata.

## Ren første start

Åbn Ressourcer, lad bidrag være slået fra, gem og åbn Login & forbindelse. Feltet skal være tomt, og ingen profil eller kontoidentitet må være indlæst. Brug ikke personlige forbindelsesdata under releaseaccept. Gennemgå engelsk og dansk GUI separat med sprogvælgeren. Linux-pakkens verificering og hashes står i [releasestatus](../../RELEASE_NOTES.md).
