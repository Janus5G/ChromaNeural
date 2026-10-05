# ChromaNeural

[English](../en/ChromaNeural-Overview.md) · [Dansk](ChromaNeural-Overview-DA.md) · [Deutsch](../de/ChromaNeural-Overview.md) · [Français](../fr/ChromaNeural-Overview.md) · [日本語](../ja/ChromaNeural-Overview.md) · [简体中文](../zh-CN/ChromaNeural-Overview.md) · [हिन्दी](../hi-IN/ChromaNeural-Overview.md)
## Overblik

ChromaNeural 0.2.21-rc.2-dokumentation | Ikke offentliggjort kandidat | 3. oktober 2026

**Status for rc.2-dokumentationen:** Denne kandidat er ikke offentliggjort. Lokalisering og udvidelig i18n har bestået lokal verifikation; native build- og pakkeaccept for rc.2 afventer stadig. Installations-, platforms-, LAN/WAN-, inference- og live-tjenesteevidens nedenfor er historisk rc.1-evidens, medmindre den udtrykkeligt er mærket rc.2. Links til rc.1-downloads giver ikke rc.2-lokalisering.

### Lokal AI. Samarbejde med eksplicit godkendelse.

ChromaNeural forbinder lokalt AI-arbejde, en vedvarende arbejdskø og kommunikation mellem godkendte peers. Brugeren bestemmer, hvilket input der behandles, og hvilke bidrag der må deles. AI-output bliver ikke automatisk korrekt eller verificeret, fordi en model har frembragt det.

Den understøttede samarbejdsprofil i denne version er kodeforslag. Klienten er ikke en generel markedsplads, der automatisk modtager og udfører vilkårlige opgaver fra internettet. Der er heller ikke en generel problem-/studieknap til alle opgavetyper i denne release.

![Den faktiske Windows-klient i stoppet tilstand. Ingen private konti eller data er indlæst.](../images/chroma-neural-overview.png)

### Sprogunderstøttelse i rc.2

Den ene klient leveres med en, da, de, fr, ja, zh-CN og hi-IN. Engelsk er standard og fallback. Sidepanelets sprogvælger ændrer programmets egne tekster og gemmer valget til næste start. Det udvidelige register understøtter fremtidige kataloger uden separate klienter eller GUI-logik. Se brugervejledningen om præferencer og sprogvalg ved start.

### Hvad du kan bruge klienten til

- Se deltagelsesstatus og gemme dine ressourcepræferencer.
- Kontrollere, om det offentlige backend-API svarer.
- Bruge den eksisterende lokale AI-funktion til forslag på en valgt fil.
- Behandle allerede lokalt oprettede og godkendte jobs gennem baggrundsarbejderen i den understøttede Windows-profil.
- Benytte de eksisterende avancerede CLI-værktøjer til eksplicit godkendt, korreleret peersamarbejde.

Generel ressourcedeling er fortsat deaktiveret. Installation og en vellykket forbindelseskontrol giver ikke i sig selv nodeadgang, arbejde eller ChromaPoints.

<!-- page -->
## Fra input til resultat

### 1. Input og tilladelse

Et eksisterende job identificerer kildeinput, instruktion og valgt provider/model. Lokal AI-behandling og netværksbrug kræver deres respektive godkendelser. Åbning af en mappe er ikke en godkendelse til at dele den.

### 2. Arbejdskø og behandling

Den eksisterende SQLite-kø bevarer jobidentitet og status. En lease reserverer arbejdet til en worker. Kontrolleret pause, cancellation, stop og genstart er verificeret i den dokumenterede Windows-profil. Ingen parallel jobdatabase er nødvendig.

### 3. Eventuelt peersamarbejde

Spørgsmål og svar knyttes til den oprindelige opgave. ChromaSpeechAI bruger godkendte peer-identiteter og TLS. Modtaget indhold lagres i en inbox og forbliver inert: det er data, ikke en tilladelse til at køre kode. Deling af kildeindhold kræver eksplicit samtykke.

### 4. Integritet og review

Et resultat har identitet, hash og oprindelse, hvor det eksisterende flow leverer dem. Lokale og peer-genererede bidrag kan skelnes. En SHA-256-kontrol bekræfter de samme bytes; den vurderer ikke svarets faglige kvalitet. Resultatet forbliver uverificeret, indtil den eksisterende verifikationskæde accepterer det.

### 5. Valgfri publicering

Global deling bruger det eksisterende publication-flow med verification, consent, roller og backendaccept. Private filer bliver ikke automatisk Shared Network Knowledge. Den lokale publication-software er verificeret; en fungerende offentlig production-publication er ikke dokumenteret af denne release.

Direkte privat adgang til et autoritativt verificeret resultat for task owner før global deling er udsat i denne version. Den rettighed må ikke forveksles med at læse et lokalt, endnu uverificeret jobresultat.

<!-- page -->
## Privatliv og tillid

### Tre adskilte områder

**Din computer:** arbejdsfiler, indstillinger, kødata, resultater og logs. En lokal AI-provider behandler det udtrykkeligt valgte input lokalt. Data er ikke automatisk krypteret på disken.

**Din browser:** den eksisterende webapp anvender brugerens Internet Identity. Den faktiske autentificerede caller afgør ejeradgang. Kopierede forbindelsesdata er ikke en login-session.

**Godkendte peers og delte resultater:** kun det indhold, der er omfattet af den relevante godkendte handling, sendes gennem det understøttede flow. Netværksforbindelser kan afsløre eksempelvis IP-adresser og peer-identitet; systemet lover ikke anonymitet.

I en central tjeneste, der behandler prompts på sin server, skal input forlade brugerens computer. ChromaNeurals lokale providervej kan behandle det valgte input på computeren. Hvis brugeren vælger peersamarbejde eller webapp-lagring, krydser data stadig en grænse. Forskellen ligger i de konkrete valg og adskillelser, ikke i et løfte om at netværksbrug aldrig deler data.

### Hvad er faktisk verificeret?

Windows-klient og ren installation har både automatiseret og menneskelig GUI-accept. Windows, Linux amd64 og macOS Intel har native build-/pakketests. Faktisk LAN mellem to Windows-PC'er, direkte mobilnet-til-hjem WAN og lokal modelinference er dokumenteret. Softwaretests med syntetisk backend eller identitet er ikke live Internet Identity-tests.

### Hvad er endnu ikke verificeret?

Faktisk live Internet Identity end-to-end, live nodeoptagelse og live migration. Manuel macOS-GUI og fuld Linux DEB install-/fjern-livscyklus er heller ikke dækket. Native privat filgem/hent via browserens ejerautoritet er ikke implementeret. Specialiseret hardwareperformance er ikke fysisk verificeret.

Pakker er usignerede; macOS er ikke notariseret. Windows, Linux og macOS er de officielle platforme inden for disse prereleasegrænser.

Officiel understøttelse af Android og iOS er udsat til senere.

Se også **Brugervejledning**, **Privatliv og lagring**, **Installation** og **Verificerede kapabiliteter** i denne dokumentationsserie.

MCP er fortsat en særskilt gated funktion efter rc.2 og er ikke implementeret her. Denne dokumentation indebærer ingen ny produktions- eller Internet Identity-ændring.
