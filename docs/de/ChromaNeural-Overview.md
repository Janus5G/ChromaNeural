# ChromaNeural

[English](../en/ChromaNeural-Overview.md) · [Dansk](../da/ChromaNeural-Overview-DA.md) · [Deutsch](ChromaNeural-Overview.md) · [Français](../fr/ChromaNeural-Overview.md) · [日本語](../ja/ChromaNeural-Overview.md) · [简体中文](../zh-CN/ChromaNeural-Overview.md) · [हिन्दी](../hi-IN/ChromaNeural-Overview.md)
## Überblick

ChromaNeural 0.2.21-rc.2-Dokumentation | Unveröffentlichter Kandidat | 3. Oktober 2026

**Stand der rc.2-Dokumentation:** Dieser Kandidat wurde nicht öffentlich veröffentlicht. Lokalisierung und erweiterbare i18n haben die lokale Verifikation bestanden; die native Build- und Paketabnahme für rc.2 steht noch aus. Die folgenden Installations-, Plattform-, LAN/WAN-, Inferenz- und Live-Dienstnachweise sind historische rc.1-Nachweise, sofern sie nicht ausdrücklich als rc.2 gekennzeichnet sind. rc.1-Downloads enthalten keine rc.2-Lokalisierung.

### Lokale Intelligenz. Ausdrücklich genehmigte Zusammenarbeit.

ChromaNeural verbindet lokale KI-Arbeit, eine dauerhafte Arbeitswarteschlange und Kommunikation zwischen genehmigten Peers. Sie wählen die zu verarbeitenden Eingaben und die teilbaren Beiträge. Eine Modellantwort ist dadurch allein weder richtig noch verifiziert.

Das unterstützte Zusammenarbeitsprofil dieser Version sind Codevorschläge. Es gibt keinen allgemeinen Marktplatz, der beliebige entfernte Aufträge automatisch annimmt und ausführt. Der Desktop bietet noch keine allgemeine Schaltfläche zum Einreichen beliebiger Probleme oder Studien.

![Tatsächlicher Windows-Client bei gestoppter Teilnahme, ohne privates Konto oder Daten.](../images/chroma-neural-overview.png)

### Sprachunterstützung in rc.2

Ein Client enthält en, da, de, fr, ja, zh-CN und hi-IN. Englisch ist Standard und Rückfallsprache. Die Seitenleistenauswahl ändert anwendungseigene Texte und speichert die Wahl für den nächsten Start. Die erweiterbare Registry ermöglicht künftige Kataloge ohne separate Clients oder GUI-Logik. Einstellungen und Startüberschreibungen erläutert das Benutzerhandbuch.

### Was heute möglich ist

- Teilnahmestatus ansehen und Ressourceneinstellungen speichern.
- Die Erreichbarkeit der öffentlichen Backend-API prüfen.
- Mit der vorhandenen lokalen KI Änderungen an einer ausgewählten Datei vorschlagen.
- Bereits genehmigte lokale Aufträge im Hintergrund des unterstützten Windows-Profils bearbeiten.
- Über die bestehende erweiterte CLI ausdrücklich genehmigte, korrelierte Peer-Zusammenarbeit nutzen.

<!-- page -->
## Von der Eingabe zum Ergebnis

Allgemeine Ressourcenfreigabe bleibt deaktiviert. Installation und erfolgreiche Verbindungsprüfung gewähren weder Netzwerkzulassung noch Aufträge oder ChromaPoints.

### 1. Eingabe und Erlaubnis

Ein vorhandener Auftrag benennt Quelleingabe, Anweisung und Anbieter/Modell. Lokale KI-Verarbeitung und Netzwerknutzung benötigen jeweils ihre Genehmigungen. Einen Ordner zu öffnen erlaubt keine Weitergabe.

### 2. Warteschlange und Verarbeitung

Die vorhandene SQLite-Warteschlange bewahrt Auftragsidentität und Status. Eine Lease reserviert Arbeit für einen Worker. Kontrollierte Pause, Abbruch, Stopp und Neustart sind im dokumentierten Windows-Profil verifiziert. Es wird keine zweite Auftragsdatenbank eingeführt.

### 3. Optionale Peer-Zusammenarbeit

Fragen und Antworten bleiben mit dem ursprünglichen Auftrag verbunden. ChromaSpeechAI verwendet genehmigte Peer-Identitäten und TLS. Empfangener Inhalt wird im Posteingang gespeichert und bleibt inaktiv: Daten sind keine Erlaubnis zur Codeausführung. Quelltextfreigabe erfordert ausdrückliche Einwilligung.

### 4. Integrität und Prüfung

Ein Ergebnis enthält Identität, Hashes und Herkunft, soweit der bestehende Ablauf sie liefert. Lokale und von Peers erzeugte Beiträge sind unterscheidbar. Übereinstimmende SHA-256-Werte belegen gleiche Bytes, keine technische Qualität. Ergebnisse bleiben unverifiziert, bis die bestehende maßgebliche Verifikation sie akzeptiert.

### 5. Optionale Veröffentlichung

Globale Freigabe nutzt den bestehenden Veröffentlichungsablauf mit Verifikation, Einwilligung, Rollen und Backend-Annahme. Private Dateien werden nicht automatisch zu Shared Network Knowledge. Die Veröffentlichungssoftware ist lokal verifiziert; diese Version belegt keinen funktionierenden Produktionsdienst dafür.

Direkter privater Zugriff des Auftraggebers auf ein maßgeblich verifiziertes Ergebnis vor einer optionalen globalen Freigabe ist zurückgestellt. Er ist nicht mit dem Lesen eines lokalen, noch unverifizierten Auftragsergebnisses gleichzusetzen.

<!-- page -->
## Datenschutz und Vertrauen

### Drei getrennte Bereiche

**Ihr Computer:** Arbeitsdateien, Einstellungen, Warteschlange, Ergebnisse und Protokolle. Ein lokaler KI-Anbieter verarbeitet ausdrücklich gewählte Eingaben lokal. Die Anwendung verschlüsselt diese Daten nicht automatisch im Ruhezustand.

**Ihr Browser:** Die bestehende Webanwendung nutzt Ihre Internet Identity. Der tatsächlich authentifizierte Aufrufer bestimmt den Eigentümerzugriff. Kopierte Verbindungsmetadaten sind keine Anmeldesitzung.

**Genehmigte Peers und geteilte Ergebnisse:** Die jeweilige Genehmigung begrenzt versendete Inhalte. Verbindungen können IP-Adressen und Peer-Identität offenlegen; ChromaNeural verspricht keine Anonymität.

Verarbeitet ein Dienst Prompts auf einem externen Server, müssen Eingaben den Computer verlassen. ChromaNeurals lokaler Anbieter kann gewählte Eingaben auf dem Computer verarbeiten. Peer-Zusammenarbeit und Browserspeicher überschreiten weiterhin Datengrenzen. Entscheidend sind ausdrückliche Kontrolle und Trennung, kein Versprechen, dass Netzwerknutzung niemals Informationen weitergibt.

### Was ist verifiziert?

Windows-Client und saubere Installation haben automatisierte Prüfungen und menschliche GUI-Abnahme bestanden. Windows, Linux amd64 und macOS Intel haben native Build-/Paketprüfungen. Echte Zwei-Computer-LAN-, direkte Mobilfunk-zu-Heimnetz-WAN-Tests und lokale Modellinferenz sind dokumentiert. Tests mit synthetischem Backend-Zustand oder Identität sind keine Live-Internet Identity-Tests.

### Was bleibt unverifiziert?

Tatsächliches Live-Internet Identity-Ende-zu-Ende, Live-Zulassung und Live-Migration. Manuelle macOS-GUI-Abnahme und vollständiger Linux-DEB-Installations-/Entfernungszyklus fehlen ebenfalls. Nativer privater Datei-Upload/-Download mit Browser-Eigentümerberechtigung ist nicht implementiert. Spezialisierte Hardwareleistung ist nicht physisch verifiziert.

Pakete sind unsigniert; macOS ist nicht notarisiert. Windows, Linux und macOS sind innerhalb dieser Vorabversionsgrenzen offizielle Plattformen.

Offizielle Android- und iOS-Unterstützung ist auf später verschoben.

Einzelheiten stehen in Benutzerhandbuch, Datenschutz und Speicherung, Installation und Verifizierte Funktionen.

MCP bleibt eine separat freizugebende Funktion nach rc.2 und ist hier nicht implementiert. Diese Dokumentation beinhaltet keine neue Änderung an Produktion oder Internet Identity.
