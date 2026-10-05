# ChromaNeural

[English](../en/ChromaNeural-Privacy-and-Storage.md) · [Dansk](../da/ChromaNeural-Privacy-and-Storage-DA.md) · [Deutsch](ChromaNeural-Privacy-and-Storage.md) · [Français](../fr/ChromaNeural-Privacy-and-Storage.md) · [日本語](../ja/ChromaNeural-Privacy-and-Storage.md) · [简体中文](../zh-CN/ChromaNeural-Privacy-and-Storage.md) · [हिन्दी](../hi-IN/ChromaNeural-Privacy-and-Storage.md)
## Datenschutz und Speicherung

ChromaNeural 0.2.21-rc.2-Dokumentation | Unveröffentlichter Kandidat | 3. Oktober 2026

**Stand der rc.2-Dokumentation:** Dieser Kandidat wurde nicht öffentlich veröffentlicht. Lokalisierung und erweiterbare i18n haben die lokale Verifikation bestanden; die native Build- und Paketabnahme für rc.2 steht noch aus. Die folgenden Installations-, Plattform-, LAN/WAN-, Inferenz- und Live-Dienstnachweise sind historische rc.1-Nachweise, sofern sie nicht ausdrücklich als rc.2 gekennzeichnet sind. rc.1-Downloads enthalten keine rc.2-Lokalisierung.

## Drei Datengrenzen

**Lokaler Client:** Arbeitsdateien, lokale Aufträge, Einstellungen und Protokolle liegen auf Ihrem Computer. Sie wählen Arbeitsbereich und Aktionen. Eine Ordnerauswahl lädt diesen nicht automatisch hoch.

**Browser und Internet Identity:** Privater Webzugriff nutzt die bestehende Anwendung und den tatsächlich authentifizierten Aufrufer. Ein Principal in JSON ist eine Kennung, kein Nachweis von Eigentümerberechtigung. Ein Node darf keine menschliche Browsersitzung übernehmen.

**Peers und gemeinsames Wissen:** Separat genehmigte Inhalte können an genehmigte Peers gesendet werden. Globale Veröffentlichung verlangt eigene Verifikation, Einwilligung, Rollen und Backend-Annahme. Private Daten werden nicht automatisch Shared Network Knowledge.

Diese Trennung ändert weder Internet Identity noch Speichermodell oder bestehende Eigentumsrechte der Webanwendung. Sie bedeutet weder Verschlüsselung gespeicherter Daten noch Netzwerkanonymität.

### Vergleich mit zentraler Promptverarbeitung

Verarbeitet ein zentraler KI-Dienst einen Prompt extern, verlässt die Eingabe den Computer. ChromaNeurals lokale Inferenz kann gewählte Eingaben lokal verarbeiten. Genehmigte Inhalte verlassen bei gewählter Netzwerkzusammenarbeit weiterhin den Computer. Für private Daten in der Webanwendung gilt deren bestehendes Eigentümermodell.

ChromaNeural behauptet weder, allen anderen KI-Systemen fehle Datenschutz, noch, lokale Speicherung allein genüge. Betriebssystem, Sicherungen, gewählter Anbieter und genehmigte Inhalte bleiben relevant.

### Keine stillschweigende Berechtigungsübertragung

Das API-Profil enthält öffentliche Verbindungsfelder und möglicherweise einen Principal. Es ist kein Anmeldetoken. Die separate Node-Identität liegt an einem gewählten lokalen Pfad. Registrierung gewährt keine automatische Zulassung; Ressourceneinstellungen gewähren keinen Zugriff auf private Objekte.

<!-- page -->
## Speicherorte

### Standard-Zustandsverzeichnis des Clients

Windows:
```
%LOCALAPPDATA%\ChromaNeural\client
```

Linux und macOS:
```
${XDG_STATE_HOME:-$HOME/.local/state}/chroma-neural/client
```

macOS verwendet dieselbe XDG-/Fallback-Konvention wie Linux, nicht automatisch Library/Application Support. --state-dir hat Vorrang; andernfalls kann CHROMA_STATE_DIR ein anderes Verzeichnis wählen. Verwenden Sie beim nächsten Start dieselbe Auswahl, um dasselbe lokale Profil fortzusetzen.

### Dateien im Client-Zustand

- **preferences.json:** Design, Teilnahme, CPU/Threads/Speicher, Leerlauf-/Akkuoptionen und gewählter Node-Konfigurationspfad. Keine II-Sitzung.
- **ui-language.json (rc.2):** nur Version 1 und registrierte Sprachkennung; ausdrücklich im GUI gewählte Sprache im selben Zustandsverzeichnis. Keine II-Sitzung, keine Änderung an preferences.json. Fehlende/ungültige/übergroße/nicht unterstützte Werte führen ohne zerstörendes Überschreiben zu Englisch. Späteres ausdrückliches Speichern bewahrt ein ungültiges Original; Speicherfehler behalten die aktuelle Sprache. --language wird nicht dauerhaft gespeichert.
- **api-connection-v1.json:** gespeichertes API-Profil. Ein Principal kann eine Person identifizieren; öffentliche Metadaten sind nicht anonym.
- **work-queue.db:** bestehende SQLite-Warteschlange und zugehöriger Veröffentlichungszustand. Aufträge können Quelltext, Anweisungen, Ergebnisse und Referenzen enthalten. Während der Nutzung können -wal- und -shm-Dateien entstehen.
- **balance-cache.json:** zuvor abgerufener Abrechnungsstatus; ein Cache vergibt keine maßgeblichen Punkte.
- **client.log:** rotierendes Protokoll, maximal 1 MiB je Datei und drei Sicherungen. Tracebacks können lokale Pfade enthalten.

Ungültige Einstellungs-/Profildateien bleiben beim Lesen erhalten. Späteres ausdrückliches Speichern kann eine datierte Sicherung bewahren. Löschen Sie diese bei der Fehlersuche nicht automatisch.

### Weitere ausdrücklich gewählte Orte

Arbeitsdateien liegen im gewählten Arbeitsbereich. Node-Konfiguration und Identität verwenden die bei Einrichtung gewählten Verzeichnisse; dazu können private_key.pem und public_key.json gehören. Peer-Posteingänge und erweiterte CLI-Warteschlangen nutzen ausdrücklich gewählte Datenbankpfade, nicht zwingend das Standardverzeichnis.

Veröffentlichen Sie niemals private_key.pem, Identitätsverzeichnisse, Warteschlangendatenbanken oder unbereinigte Protokolle. Dieses Handbuch fordert sie nicht an.

<!-- page -->
## Private Pfade und Dateien

Ein Arbeitsbereich ist ein ausdrücklich gewählter lokaler Ordner. Ein normaler Dateipfad dient als Betriebssystempfad, nicht zur Übertragung von Eigentumsrechten. Der aktive GUI-Arbeitsbereich ist Sitzungszustand; dieser Ablauf bietet keinen allgemeinen Synchronisierungsdienst für zuletzt verwendete Ordner.

Pfade können dennoch anderswo gespeichert bleiben: preferences.json kann auf eine Node-Konfiguration verweisen, und Zusammenarbeits-/Veröffentlichungsdaten können einen Posteingang referenzieren. Protokolle können Pfade enthalten. Das Schließen eines Arbeitsbereichsfensters entfernt daher nicht sämtliche Pfadreferenzen.

Der bestehende lokale Dateiadapter bearbeitet benannte Textdateien. Er prüft Dateinamen, Symlinks/Reparse Points und Änderungen zwischen Lesen und Schreiben. Speichern nutzt temporäre Datei und atomaren Ersatz mit vorhandenen Integritätsprüfungen. Er ist kein allgemeiner Cloud-Laufwerk-Client.

Diese Mechanismen verschlüsseln lokale Daten nicht. Schützen Sie Betriebssystemkonto und Datenträger und sichern Sie nach Bedarf. Beenden Sie den Client vor dem Kopieren von SQLite-Zustand; eine aktive WAL-Datenbank ist keine beliebige einzelne Datei. Das Verschieben von Programmdateien verschiebt Arbeitsbereich, Identität oder Zustand nicht automatisch.

### Was erreicht Anbieter oder Peer?

Lokale KI nutzt gewählte, genehmigte Eingaben. Das vorhandene Auftragsmodell kann Eingabe und Anweisungen dauerhaft speichern. Peer-Offenlegung verlangt separate Genehmigung. Ein genehmigter Transport macht private Pfade, Geheimnisse oder personenbezogene Daten im Eingabetext nicht harmlos.

TLS schützt die authentifizierte Peer-Verbindung. Es verbirgt weder Endpunkt-IP-Adressen vor deren Netzen noch garantiert es Schutz bei kompromittierten Endgeräten.

<!-- page -->
## Browsersitzungen und privater Zugriff

Anmeldung nutzt bestehende Webanwendung und Internet Identity. Der native Client übernimmt Ihre II-Sitzung nicht. **Kontrollér forbindelse** prüft die öffentliche API anonym; Erfolg sagt nichts über private Datensätze oder die Gültigkeit Ihrer Browsersitzung.

Die lokal verifizierte Browserkorrektur löscht private Cache-/Formularzustände bei Abmeldung und Benutzerwechsel, behandelt Sitzungsablauf und prüft Eigentümer sowie SHA-256 vor Downloads. Backend-Korrekturen beschränken anonymen privaten Zugriff und globale Auditmetadaten. Dies sind lokale Softwarebelege. Diese Vorabversion hat die Änderungen nicht bereitgestellt; tatsächliches Live-II-Ende-zu-Ende bleibt NICHT VERIFIZIERT.

Melden Sie sich über den vorhandenen Browserablauf ab. Desktop schließen oder API-Profil vergessen ist keine Browserabmeldung und widerruft allein keine Freigaben. Bestehende Erteilungs-/Widerrufsaktionen müssen autorisierte Schnittstellen nutzen; neue Freigabetypen werden nicht eingeführt.

### Nativer privater Dateizugriff

**Private II storage** informiert lediglich. Der fehlende autorisierte Browser-/Dateikanal ist nicht implementiert. Ein Node darf nicht als menschlicher Eigentümer schreiben; eine Lesefreigabe darf nicht als Schreibrecht gelten. Kein alternatives privates Speichersystem umgeht diese Grenze.

### Private Ergebnisse und globales Wissen

Lokale Vorschläge und Peer-Antworten sind noch kein abgeschlossenes verifiziertes Wissen. Verifikation, Freigabeeinwilligung, Rollen und Backend-Annahme regeln optionale Veröffentlichung. Gleiche Integrität ist weder Qualitätsfreigabe noch Veröffentlichungserlaubnis.

Direkter privater Download eines maßgeblich verifizierten Ergebnisses durch den Auftraggeber vor optionaler globaler Freigabe ist zurückgestellt. Ein Abruf über einen nicht implementierten Eigentümerkanal wird nicht versprochen.

### Fehler und vermutete Offenlegung

Stoppen Sie die betroffene Aktion, bewahren Sie Belege privat und folgen Sie SECURITY.md. Geben Sie bereinigte Beschreibung und Version weiter, keine Schlüssel, Sitzungsdaten oder privaten Datenbanken. Abweichendes SHA-256 bedeutet unterschiedliche Bytes; fehlende Datei oder fehlender Hash sind andere Fehler und kein bewiesener Manipulationsfall.

MCP bleibt eine separat freizugebende Funktion nach rc.2 und ist hier nicht implementiert. Diese Dokumentation beinhaltet keine neue Änderung an Produktion oder Internet Identity.
