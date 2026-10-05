# ChromaNeural

[English](../en/ChromaNeural-Verified-Capabilities.md) · [Dansk](../da/ChromaNeural-Verified-Capabilities-DA.md) · [Deutsch](ChromaNeural-Verified-Capabilities.md) · [Français](../fr/ChromaNeural-Verified-Capabilities.md) · [日本語](../ja/ChromaNeural-Verified-Capabilities.md) · [简体中文](../zh-CN/ChromaNeural-Verified-Capabilities.md) · [हिन्दी](../hi-IN/ChromaNeural-Verified-Capabilities.md)
## Verifizierte Funktionen

ChromaNeural 0.2.21-rc.2-Dokumentation | Unveröffentlichter Kandidat | 3. Oktober 2026

**Stand der rc.2-Dokumentation:** Dieser Kandidat wurde nicht öffentlich veröffentlicht. Lokalisierung und erweiterbare i18n haben die lokale Verifikation bestanden; die native Build- und Paketabnahme für rc.2 steht noch aus. Die folgenden Installations-, Plattform-, LAN/WAN-, Inferenz- und Live-Dienstnachweise sind historische rc.1-Nachweise, sofern sie nicht ausdrücklich als rc.2 gekennzeichnet sind. rc.1-Downloads enthalten keine rc.2-Lokalisierung.

## rc.2-Lokalisierungsnachweise

Phase B und C haben lokale Verifikation bestanden: 303 Nachrichten in sieben ausgelieferten Sprachen, gespeicherte Auswahl, englischer Fallback, geschützte Eingaben/Zustände, modale Aktionen und synthetische Steuerungs-/Verbindungsprüfungen. Echte Tk-Aufnahmen und visuelle Abnahme bestanden. Der Blocker der chinesischen Verbindungsaufnahme wurde auf Störungen der Desktopaufnahme zurückgeführt und mit fensterspezifischer Aufnahme im Prüfwerkzeug gelöst. Frühere Fehler bleiben dokumentiert.

Auch die Erweiterbarkeitsprüfung bestand. Eine reine Datenregistry liefert Kennungen, Anzeigenamen und Zahlenformatierung. Ein isolierter achter Katalog plus ein Registry-Eintrag bestand Auswahl, Speicherung, Fallback, Windows-Starter und Paket-/Ressourcenerkennung; die Testsprache wurde entfernt. 476 Zahlenformat- und 2.121 Nachrichtenvergleiche bestanden; alle 331 erwarteten Quellhashes stimmten. Dies sind lokale Quell-/Verhaltensprüfungen, keine native rc.2-Paket-, Live-II- oder Produktionsabnahme. Keine öffentliche rc.2-Veröffentlichung fand statt.

## Historische rc.1-Nachweise lesen

**Tatsächlich physisch:** Datenverkehr oder Inferenz auf realen Rechnern beobachtet. **Native CI:** ein echter Betriebssystem-Runner baute und prüfte das Paket. **Lokale Software:** isolierter Code/Zustand wurde ausgeführt; synthetische Backends oder Sitzungen sind keine Produktion. **Nicht verifiziert:** ausreichende Belege fehlen. Eine Testumgebungsgrenze ist nicht automatisch ein Produktfehler.

### Windows

Saubere Installation, Payloadintegrität, gebündeltes ICP SDK, CLI, Tk, Bestandserhalt und Bereinigung sind verifiziert. Die abschließende menschliche GUI-Beobachtung zeigte die öffentliche API-Antwort und den Hinweis, dass private Anmeldung im Browser bleibt. Der Client beendete normal.

### Linux und macOS

Linux amd64 wurde auf nativem Ubuntu 24.04 gebaut und auf Entpacken, Integrität, SDK, CLI und Xvfb/Tk geprüft. macOS Intel wurde auf nativem macOS 15 gebaut und auf Paketintegrität, SDK, CLI und Tk geprüft. Dies sind native Runner-Ergebnisse, keine menschliche GUI-Abnahme sämtlicher Endbenutzersysteme.

Pro Plattform gibt es 18 Release-Prüfungen. Die Windows-CI-Payload entsprach allen 1.547 Dateien der zuvor akzeptierten lokalen Payload. Endgültige Downloads wurden per SHA-256 geprüft.

### Tatsächliche lokale Modellinferenz

Gebündelte Qwen-Hintergrundinferenz lief auf Windows. Ollama 0.34.4 mit qwen2.5-coder:0.5b lief auf einem separaten physischen Windows-Testrechner. Anbieter/Modell und Ausgabe-/Warteschlangen-/SQLite-Hashes wurden korreliert. Keine Duplikate, Anbieterwechsel, Punkte oder Veröffentlichung. Die Steuerebene war eine isolierte Fixture; die Modellinferenz war echt.

<!-- page -->
## Kommunikation und Arbeitsablauf

### Zwei physische Windows-Computer im LAN

Beide Richtungen sowie Rücklauf von Fragen/Antworten wurden geprüft. Abgedeckt: TLS-Peer-Identität, Bytegleichheit, SHA-256, dauerhafter SQLite-Posteingang, Neustart/Wiederholung, Duplikatschutz, Ablehnung unbekannter Peers, inaktiver Empfangsinhalt und kontrolliertes Herunterfahren.

### Direktes WAN über Internet und NAT

Ein Node über eine separate Mobilfunkverbindung stellte direktes TCP ins Heimnetz her. ChromaSpeechAI bestand danach mit TLS 1.3, ALPN chromaspeech-prsm-v1, genehmigter Peer-Authentifizierung und 100.000-Byte-Payload. SHA-256 und Bytes stimmten. Nach Neustart/Wiederholung wurden null neue Fragmente der bereits empfangenen Nachricht gesendet. Ein unbekannter Peer wurde vor Speicherung abgelehnt; der Posteingang blieb erhalten.

Die unabhängig initiierte Gegenrichtung konnte in der vorhandenen Umgebung nicht verifiziert werden. Kein Overlay galt als Ersatz. Die temporäre Routerregel wurde anschließend entfernt.

### Hintergrundarbeit, Ressourcen und Korrelation

Die bestehende Warteschlange ist an den Hintergrundlebenszyklus des Clients angebunden. Das Windows-Profil hat gezielte Lease-, Wiederholungs-, Pause-, Stopp-, Abbruch- und Neustartprüfungen. Ressourcensteuerung umfasst CPU-Zeitplanung, Inferenzthreads und zugesicherten Speicher, keine Garantie für gesamten physischen RAM.

Auftrags-/Peer-Korrelation wurde mit echtem lokalem Windows-TLS und SQLite getestet; KI/Backend waren in diesem Test simuliert. Lokale Node-Einrichtung und autorisierte Verbindung verwendeten das Windows SDK gegen bestehendes WASM in lokalem PocketIC. Das ist keine Live-Node-Zulassung.

### Datenschutz, Prüfung und Veröffentlichung

Private Endpunktwächter, Eigentümertrennung, Cache-/Sitzungsbereinigung und Downloadintegrität sind lokal verifiziert. Globale Audit-Endpunkte sind auf die bestehende Adminrolle beschränkt, ohne neuen Zugriff auf private Datensatzinhalte. Veröffentlichungstests bewahren Verifikation, Einwilligung, Rollen und Backend-Annahme. Nichts davon belegt ein neues Produktionsdeployment.

<!-- page -->
## Korrekturen und verbleibende Grenzen

### Tatsächlich behobene Fehler

- Das fehlende SDK in einer sauberen Windows-Distribution wurde durch Paketierung des vorhandenen festgelegten @icp-sdk/core 5.4.0 und zehn Laufzeitabhängigkeiten beim Release-Build behoben. Kein Upgrade, keine npm-Installation beim Endbenutzer.
- Fehlende Auftrags-/Peer-Nachrichtenverknüpfung wurde über vorhandene Identitäten, Warteschlange und Posteingang hergestellt.
- Private Endpunkt- und Auditmetadatenfehler wurden lokal behoben, ohne Internet Identity, Eigentümermodell, Candid oder stabiles Schema zu ändern.
- PowerShell-Modulerkennung und kurze/lange temporäre Pfade der Windows-Paketierung wurden korrigiert. Historisch fehlgeschlagene CI-Läufe bleiben erhalten.

Die BigInt-Exportkorrektur ist eine Kompatibilitätskorrektur, kein überall reproduzierter Laufzeitfehler. Frühere PASS-Nachweise werden bei unveränderten relevanten Bytes und Verträgen wiederverwendet. Diese Darstellungsaktualisierung ist keine neue funktionale Testkampagne.

### Weiter unverifiziert oder nicht geliefert

- Tatsächliches Live-Internet Identity-Ende-zu-Ende, Live-Zulassung und Live-Migration.
- Manuelle macOS-GUI-Abnahme und vollständiger Linux-DEB-Installations-/Entfernungszyklus.
- Umgekehrte WAN-Initiierung in der separaten Mobilfunk-Testumgebung.
- Nativer privater Dateizugriff mit Browser-Eigentümerberechtigung und direkter privater Ergebniszugriff vor globaler Freigabe.
- Kontrollierte Ollama-/Linux-/macOS-/GPU-Beiträge; allgemeine Ressourcenfreigabe bleibt deaktiviert.
- Pakete unsigniert, macOS nicht notarisiert; Plattform-Symbolgrenzen sind separat dokumentiert.

Offizielle Android- und iOS-Unterstützung ist auf später verschoben.

### Hardware und Reproduzierbarkeit

Dies ist Software. Tatsächliche LAN-/WAN- und Inferenztests belegen die getesteten Rechner und Verbindungen. Simulationen, lokale Backends und Hardwaremodelle belegen keine physische optische/GPU-/Spezialhardwareleistung.

Native Abläufe verwenden sauberen Checkout, festgelegte Actions/Abhängigkeiten, npm-Lock und hashgeprüfte Laufzeitartefakte. Runner und ausführbare Metadaten können Pakethashes beeinflussen; identische Binärdateien in allen Umgebungen werden nicht behauptet. VERIFICATION.md und NATIVE_BUILD_EVIDENCE.json benennen akzeptierte Builds. Downloadhashes stehen in docs/DOWNLOADS.md und SHA256SUMS.txt des Releases.

MCP bleibt eine separat freizugebende Funktion nach rc.2 und ist hier nicht implementiert. Diese Dokumentation beinhaltet keine neue Änderung an Produktion oder Internet Identity.
