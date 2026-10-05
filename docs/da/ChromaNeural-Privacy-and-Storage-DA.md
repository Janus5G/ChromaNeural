# ChromaNeural

[English](../en/ChromaNeural-Privacy-and-Storage.md) · [Dansk](ChromaNeural-Privacy-and-Storage-DA.md) · [Deutsch](../de/ChromaNeural-Privacy-and-Storage.md) · [Français](../fr/ChromaNeural-Privacy-and-Storage.md) · [日本語](../ja/ChromaNeural-Privacy-and-Storage.md) · [简体中文](../zh-CN/ChromaNeural-Privacy-and-Storage.md) · [हिन्दी](../hi-IN/ChromaNeural-Privacy-and-Storage.md)
## Privatliv og lagring

ChromaNeural 0.2.21-rc.2-dokumentation | Ikke offentliggjort kandidat | 3. oktober 2026

**Status for rc.2-dokumentationen:** Denne kandidat er ikke offentliggjort. Lokalisering og udvidelig i18n har bestået lokal verifikation; native build- og pakkeaccept for rc.2 afventer stadig. Installations-, platforms-, LAN/WAN-, inference- og live-tjenesteevidens nedenfor er historisk rc.1-evidens, medmindre den udtrykkeligt er mærket rc.2. Links til rc.1-downloads giver ikke rc.2-lokalisering.

## Tre datagrænser

**Lokal klient:** arbejdsfiler, lokale jobs, indstillinger og logs findes på computeren. Brugeren vælger workspace og handlinger. Der er ikke automatisk upload af en valgt mappe.

**Browser og Internet Identity:** privat webadgang sker gennem den eksisterende webapp og den faktisk autentificerede caller. Et Principal-felt i JSON er en identifikator, ikke bevis for ejerautoritet. Noden må ikke låne menneskets browser-session.

**Peers og offentlig viden:** særskilt godkendte oplysninger kan sendes til godkendte peers. Global publication har egne verification-, consent-, rolle- og backendkrav. Privat data bliver ikke automatisk Shared Network Knowledge.

Denne adskillelse ændrer ikke Internet Identity, webappens storage-model eller eksisterende ejerrettigheder. Den betyder heller ikke, at diskdata er krypteret, eller at netværkskommunikation er anonym.

### Sammenligning med central promptbehandling

Når en central AI-tjeneste behandler en prompt på en ekstern server, forlader prompten computeren. Ved lokal inference i ChromaNeural kan input behandles lokalt. Hvis brugeren vælger netværkssamarbejde, sendes det godkendte indhold stadig ud. Hvis private data gemmes i webappen, er det webappens eksisterende owner-model, der regulerer adgang.

ChromaNeural hævder ikke, at alle andre AI-systemer mangler privatliv, eller at lokal lagring alene giver fuld beskyttelse. Operativsystem, backups, valgte providers og det indhold, brugeren godkender, er fortsat relevante.

### Ingen skjult rettighedsoverførsel

API-profilen indeholder offentlige forbindelsesfelter og eventuelt en Principal-identifikator. Den er ikke et login-token. Nodeidentiteten er særskilt og opbevares på en valgt lokal sti. Registrering af en node giver ikke automatisk admission. Ressourcevalg giver ikke automatisk ret til private objekter.

<!-- page -->
## Hvor data ligger

### Standardmappe til klientstate

Windows:
```
%LOCALAPPDATA%\ChromaNeural\client
```

Linux og macOS:
```
${XDG_STATE_HOME:-$HOME/.local/state}/chroma-neural/client
```

macOS bruger i denne klient samme XDG/fallback-konvention som Linux, ikke automatisk Library/Application Support. En eksplicit --state-dir har forrang; ellers kan CHROMA_STATE_DIR vælge en anden mappe. Brug samme statevalg ved efterfølgende start, hvis samme lokale profil skal fortsættes.

### Filer i klientstate

- **preferences.json:** tema, deltagelsesvalg, CPU/tråde/RAM, idle/batteri og sti til valgt nodekonfiguration. Ingen II-session.
- **ui-language.json (rc.2):** kun version 1 og det registrerede locale-id; gemmes ved udtrykkeligt GUI-sprogvalg i denne samme statemappe. Filen indeholder ingen II-session og ændrer ikke preferences.json. En manglende, ugyldig, for stor eller ikke understøttet værdi giver engelsk fallback uden destruktiv overskrivning. En senere udtrykkelig gemning bevarer en ugyldig original; fejlet gemning beholder det aktuelle sprog. Startparameteren --language gemmes ikke.
- **api-connection-v1.json:** gemt API-profil. En Principal kan være personhenførbar; offentlig metadata er ikke det samme som anonym data.
- **work-queue.db:** den eksisterende SQLite-arbejdskø og tilhørende publication-state. Jobs kan indeholde kildetekst, instruktioner, resultater og referencer. SQLite kan desuden oprette -wal og -shm-filer under brug.
- **balance-cache.json:** tidligere hentet regnskabsstatus. En cache er ikke en ny autoritativ pointtildeling.
- **client.log:** roterende klientlog med højst 1 MiB pr. fil og tre backups. Fejlspor kan indeholde lokale filstier.

Ugyldige indstillings-/profilfiler bevares ved læsning. Ved en senere eksplicit gemning kan klienten bevare en dateret backup af den ugyldige fil. Slet ikke sådanne filer automatisk som del af fejlsøgning.

### Andre eksplicit valgte placeringer

Arbejdsfiler ligger i brugerens workspace. Nodekonfiguration og nodeidentitet bruger de mapper, der vælges ved opsætningen; nodeidentiteten kan bl.a. omfatte private_key.pem og public_key.json. Peertransportens inbox og avancerede CLI-køer bruger de valgte databaseplaceringer. De er ikke nødvendigvis samlet i standardmappen ovenfor.

Del aldrig private_key.pem, identitetsmapper, kødatabaser eller urensede logs offentligt. Vejledningen efterspørger ikke nogen af dem.

<!-- page -->
## Private stier og filer

Et workspace er en eksisterende lokal mappe, som brugeren vælger. Den almindelige filvej gemmes og bruges som en lokal OS-sti, ikke som en overførsel af ejerrettigheder. GUI'ens aktive workspace er en sessionstilstand; der er ikke en generel recent-folder-synkronisering i dette flow.

Der kan stadig være vedvarende stier andre steder: preferences.json kan pege på en nodekonfiguration, og collaboration-/publicationdata kan referere til en inbox. Logs kan også indeholde stier. Derfor må man ikke antage, at en filsti aldrig gemmes, blot fordi workspacevinduet lukkes.

Den eksisterende lokale filadapter er begrænset til navngivne tekstfiler. Den kontrollerer bl.a. filnavne, symlinks/reparse points og ændringer af filen mellem læsning og skrivning. Gemning sker via midlertidig fil og atomisk erstatning med de eksisterende integritetskontroller. Det er ikke en generel cloud-drive-klient.

Ingen af disse mekanismer krypterer lokale data. Beskyt OS-kontoen og disken, og tag backup efter dine egne krav. Luk klienten før kopiering af SQLite-state; en aktiv WAL-database må ikke behandles som én vilkårlig løs fil. Flytning af programfiler flytter ikke automatisk workspace, identiteter eller state.

### Hvad sendes til en provider eller peer?

Lokal AI bruger det input, brugeren har valgt og godkendt. Den eksisterende jobmodel kan gemme input og instruktion i køen. Peerdisclosure kræver særskilt godkendelse. Hvis brugeren selv inkluderer en privat sti, hemmelighed eller persondata i teksten, gør en godkendt transport ikke dette indhold ufølsomt.

TLS beskytter den autentificerede peerforbindelse. Det fjerner ikke afsender/modtagers IP-adresser fra deres respektive netværk og lover ikke beskyttelse mod en kompromitteret endpointmaskine.

<!-- page -->
## Browser, session og privat webadgang

Login foregår på den eksisterende webapp med Internet Identity. Den native klient overtager ikke brugerens II-session. **Kontrollér forbindelse** foretager en anonym kontrol af det offentlige API; successen siger intet om private records eller login-sessionens gyldighed.

Den lokalt verificerede browserkorrektionspakke rydder privat cache/formularstate ved logout og brugerskift, håndterer sessionsudløb og kontrollerer owner og SHA-256 før download. Anonyme private endpoints og globale auditmetadata er afgrænset i backendkorrektionerne. Det er lokal softwareevidens. Denne prerelease har ikke deployet disse rettelser, og faktisk live II end-to-end er fortsat NOT VERIFIED.

Log ud i browserens eksisterende brugerflow, når privat webadgang skal afsluttes. At lukke desktopklienten eller glemme en API-profil er ikke et browserlogout og tilbagekalder ikke i sig selv grants. Eventuelle eksisterende grants/revoke-operationer skal ske gennem deres allerede autoriserede interfaces; denne release tilføjer ingen nye granttyper.

### Privat filgem/hent fra desktop

Desktopindgangen **Private II storage** er informationsvisning. Den manglende autoriserede browser/native-filkanal er ikke implementeret. Noden må ikke skrive som den menneskelige ejer, og en læsegrant må ikke omfortolkes som skriveret. Der oprettes ingen alternativ privat storage for at omgå denne grænse.

### Private resultater og global viden

Lokale forslag og peer-svar er ikke færdigverificeret viden. Verifikation, delingstilladelse, roller og backendaccept regulerer eventuel publication. Integritetsmatch alene er ikke et kvalitetsstempel eller en publiceringsret.

Direkte privat requester-download af et autoritativt verificeret resultat før valgfri global deling er udsat. Denne vejledning lover derfor ikke, at klienten kan hente et sådant resultat gennem en endnu ikke implementeret owner-kanal.

### Ved fejl eller mistanke om datalæk

Stop den relevante handling, bevar din lokale dokumentation sikkert og følg SECURITY.md. Send en renset beskrivelse og version, ikke kontonøgler, sessionsdata eller private databaser. Et SHA-256-mismatch betyder, at bytes ikke matcher; en manglende fil eller hash er en anden fejl og må ikke beskrives som påvist manipulation.

MCP er fortsat en særskilt gated funktion efter rc.2 og er ikke implementeret her. Denne dokumentation indebærer ingen ny produktions- eller Internet Identity-ændring.
