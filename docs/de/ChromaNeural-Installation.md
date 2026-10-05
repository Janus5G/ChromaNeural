# ChromaNeural

[English](../en/ChromaNeural-Installation.md) · [Dansk](../da/ChromaNeural-Installation-DA.md) · [Deutsch](ChromaNeural-Installation.md) · [Français](../fr/ChromaNeural-Installation.md) · [日本語](../ja/ChromaNeural-Installation.md) · [简体中文](../zh-CN/ChromaNeural-Installation.md) · [हिन्दी](../hi-IN/ChromaNeural-Installation.md)
## Installation

ChromaNeural 0.2.21-rc.2-Dokumentation | Unveröffentlichter Kandidat | 3. Oktober 2026

**Stand der rc.2-Dokumentation:** Dieser Kandidat wurde nicht öffentlich veröffentlicht. Lokalisierung und erweiterbare i18n haben die lokale Verifikation bestanden; die native Build- und Paketabnahme für rc.2 steht noch aus. Die folgenden Installations-, Plattform-, LAN/WAN-, Inferenz- und Live-Dienstnachweise sind historische rc.1-Nachweise, sofern sie nicht ausdrücklich als rc.2 gekennzeichnet sind. rc.1-Downloads enthalten keine rc.2-Lokalisierung.

## Historische rc.1-Installationsreferenz

Es gibt noch kein öffentliches rc.2-Paket. Die folgenden Dateinamen und Befehle bleiben absichtlich rc.1-Beispiele; sie installieren weder Sprachwähler noch Registry. Bei einem bereits vorbereiteten lokalen rc.2-Kandidaten wählt --language nur die Startsprache; Windows akzeptiert -Language. Die GUI-Auswahl speichert die Sprache. Benennen Sie rc.1-Pakete nicht um und ersetzen Sie keine URL durch einen unverifizierten rc.2-Download.

## Vor der Installation

Pakete der offiziellen Veröffentlichung:

../../RELEASE_NOTES.md

Wählen Sie genau Plattform und Architektur. Pakete sind unsigniert, macOS ist nicht notarisiert. Das Betriebssystem kann warnen oder blockieren. Deaktivieren Sie den Schutz nicht global; prüfen Sie Herkunft und Prüfsumme vor dem Öffnen.

- Windows x64: ChromaNeural-0.2.21-rc.1-windows-x64.exe
- Linux amd64: chromaneural_0.2.21.rc.1_amd64.deb
- macOS Intel x86_64: ChromaNeural-0.2.21-rc.1-macos-x86_64.zip
- Quellcode-Snapshot: ChromaNeural-0.2.21-rc.1-source.zip
- Prüfsummen: SHA256SUMS.txt

GitHub normalisierte den DEB-Downloadnamen von ~rc.1 zu .rc.1. Bytes und SHA-256 sind unverändert; intern verwendet Debian weiterhin ~rc.1.

### SHA-256 prüfen

Führen Sie im Downloadverzeichnis den passenden Befehl aus.

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

Vergleichen Sie alle 64 Zeichen mit genau dieser Datei in SHA256SUMS.txt. Bei Abweichung stoppen. Die Prüfsumme belegt Byteintegrität, nicht unabhängig die Herausgeberidentität. Alle fünf veröffentlichten Hashes stehen auch in docs/DOWNLOADS.md.

<!-- page -->
## Windows x64

### Voraussetzungen

Installieren Sie Python 3.14 mit Tk und py/pyw sowie Node.js 24. Die EXE ist ein benutzerbezogener Offline-Installer, keine vollständig eingefrorene Python-/Node-Laufzeit. Planen Sie etwa 2 GB freien Platz für Entpacken und Installation ein.

### Schritte

1. Prüfen Sie die EXE wie oben beschrieben.
2. Öffnen Sie sie und bestätigen Sie nach Prüfung der Betriebssystemwarnungen.
3. Programmdateien werden hier installiert:
```
%LOCALAPPDATA%\Programs\ChromaNeural\0.2.21-rc.1
```
4. Starten Sie dort Start-ChromaNeural.ps1, zum Beispiel:
```
& "$env:LOCALAPPDATA\Programs\ChromaNeural\0.2.21-rc.1\Start-ChromaNeural.ps1"
```
5. Speichern Sie beim ersten Start Ressourcenpräferenzen. Anmeldung und Verbindung ermöglicht eine optionale öffentliche API-Prüfung.

Das Installationsprotokoll liegt unter %TEMP%\ChromaNeural-install.log. Bestehende Ziele werden abgelehnt; es gibt kein automatisches Upgrade am selben Ort. Weder automatische Teilnahme noch Autostartregistrierung erfolgen. Diese RC legt keine Desktopverknüpfung automatisch an.

ICP SDK und gesperrte Laufzeitabhängigkeiten sind enthalten. npm ci ist keine Installationsvoraussetzung; verweisen Sie NODE_PATH nicht auf eine alte Entwicklungsumgebung.

### Entfernen und Benutzerzustand

Beenden Sie vollständig. Nur das versionierte Installationsverzeichnis zu entfernen löscht Programmdateien. Zustand unter %LOCALAPPDATA%\ChromaNeural\client, Arbeitsbereiche und separate Identitätsverzeichnisse bleiben erhalten oder werden ausschließlich nach Ihrer Entscheidung separat behandelt. Ein automatisches Deinstallationsprogramm ist nicht enthalten.

<!-- page -->
## Linux amd64

Nativ verifiziert ist Ubuntu 24.04 amd64, nicht jede Distribution oder Version. WSL ersetzt keine native Linux-Paketverifikation.

Erforderlich: Python 3.11+, Tk, Distributions-cryptography, Node.js 20+ und libgomp1. Installieren Sie Abhängigkeiten mit der Paketverwaltung. Im Downloadverzeichnis:
```
sudo apt install ./chromaneural_0.2.21.rc.1_amd64.deb
```

Start über Anwendungsmenü oder:
```
chromaneural
```

Programmdateien: /opt/chromaneural; Starter: /usr/bin/chromaneural; Desktop-Metadaten: /usr/share/applications/chromaneural.desktop. Es gibt keinen npm-Netzdownload nach Installation und keine automatische Benutzerzustandsmigration.

Native Build-, Entpack-, Integritäts-, SDK-, CLI- und Xvfb/Tk-Prüfungen sind verifiziert. Der vollständige dpkg-Installations-/Entfernungszyklus ist noch unverifiziert. Der veröffentlichte Desktop-Eintrag hat keine produktspezifische Symbolreferenz; Starten bleibt möglich.

## macOS Intel x86_64

Benötigt macOS 15+, Python 3.14 mit funktionierendem Tk und Node.js 24. Nutzen Sie dieselbe Python-Installation für festgelegte Kryptografieabhängigkeiten. Im Stamm des akzeptierten Quellcode-Snapshots:
```
python3 -m pip install --require-hashes -r packaging/requirements-runtime.txt
```

Festgelegt sind cryptography 46.0.5, cffi 2.1.1 und pycparser 3.0. Dies sind Laufzeitvoraussetzungen, keine Aufforderung zu II-Zugangsdaten.

Entpacken Sie die ZIP, verschieben Sie ChromaNeural.app nach Applications und öffnen Sie nach Herkunfts- und Warnungsprüfung. Das Paket ist nur für Intel; Universal 2, Apple Silicon und Rosetta sind keine akzeptierten Profile dieser Version.

Native Build-, Integritäts-, SDK-, CLI- und Tk-Prüfungen sind verifiziert, manuelle macOS-GUI-Abnahme nicht. Das Paket ist unsigniert, nicht notarisiert und ohne produktspezifisches Bundle-Symbol. macOS enthält keine Qwen-/llama.cpp-Laufzeit. Der ausdrücklich gewählte lokale Ollama-Adapter benötigt ein separat installiertes Modell; kontrollierter Hintergrundbeitrag wird nicht unterstützt.

<!-- page -->
## Erster Start und weitere Schritte

![Ressourceneinstellungen im tatsächlichen Windows-Client; Fensterrahmen unterscheiden sich je Plattform.](../images/chroma-neural-resources.png)

Wählen und speichern Sie Präferenzen. Der Überblick zeigt nur bestätigte Werte; ein Strich ist kein Verdienstversprechen. Allgemeine Ressourcenfreigabe bleibt deaktiviert. **Afslut ChromaNeural** beendet vollständig.

Bei Startfehlern prüfen Sie zuerst Voraussetzungen, Paket und Architektur. Bewahren Sie Zustand; setzen Sie Identitäten nicht zurück und veröffentlichen Sie keine privaten Daten. Siehe Benutzerhandbuch und Datenschutz und Speicherung.

Installation ändert weder Internet Identity noch Produktionsbackend oder Browsersitzung. Öffentliche API-Erreichbarkeit wurde unter Windows verifiziert. Tatsächliches Live-II-Ende-zu-Ende, Live-Zulassung und Live-Migration bleiben unverifiziert.

Offizielle Android- und iOS-Unterstützung ist auf später verschoben.

Online-Dokumentation kann neuer sein als unveränderliche RC-Binärdateien und Quellcode-ZIP. Release-Dateien werden nicht allein wegen Dokumentation oder Symbolen ersetzt. Den Symbolstatus beschreibt docs/BRANDING.md.

MCP bleibt eine separat freizugebende Funktion nach rc.2 und ist hier nicht implementiert. Diese Dokumentation beinhaltet keine neue Änderung an Produktion oder Internet Identity.
