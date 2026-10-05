# ChromaNeural

[English](../en/ChromaNeural-Verified-Capabilities.md) · [Dansk](ChromaNeural-Verified-Capabilities-DA.md) · [Deutsch](../de/ChromaNeural-Verified-Capabilities.md) · [Français](../fr/ChromaNeural-Verified-Capabilities.md) · [日本語](../ja/ChromaNeural-Verified-Capabilities.md) · [简体中文](../zh-CN/ChromaNeural-Verified-Capabilities.md) · [हिन्दी](../hi-IN/ChromaNeural-Verified-Capabilities.md)
## Verificerede kapabiliteter

ChromaNeural 0.2.21-rc.2-dokumentation | Ikke offentliggjort kandidat | 3. oktober 2026

**Status for rc.2-dokumentationen:** Denne kandidat er ikke offentliggjort. Lokalisering og udvidelig i18n har bestået lokal verifikation; native build- og pakkeaccept for rc.2 afventer stadig. Installations-, platforms-, LAN/WAN-, inference- og live-tjenesteevidens nedenfor er historisk rc.1-evidens, medmindre den udtrykkeligt er mærket rc.2. Links til rc.1-downloads giver ikke rc.2-lokalisering.

## rc.2-lokaliseringsevidens

Phase B og Phase C bestod lokal verifikation: 303 meddelelser på syv leverede sprog, gemt sprogvalg, engelsk fallback, beskyttede input/state, modalhandlinger og syntetiske kontrol-/probetests. Faktisk Tk-optagelse og visuel accept bestod; blokeringen i det kinesiske forbindelsesbillede blev sporet til interferens i skrivebordsoptagelsen og løst med vinduesspecifik optagelse i verifikationsværktøjet. Tidligere fejl er bevaret i historikken.

Gaten for udvidelig i18n bestod også. Ét dataregister leverer id'er, viste navne og talformat. Et isoleret ottende katalog og én registreringspost bestod valg, persistens, fallback, Windows-launcher og pakke-/ressourceopdagelse; testsproget blev fjernet. De 476 talformatsammenligninger og 2.121 meddelelsessammenligninger bestod, og alle 331 forventede kildehashes matchede. Dette er lokale kilde-/adfærdskontroller, ikke rc.2 native pakkeaccept, live II eller produktionsaccept. Ingen offentlig rc.2-release fandt sted.

## Sådan læses den historiske rc.1-evidens

**Faktisk fysisk:** trafik eller inference er observeret på de rigtige maskiner. **Native CI:** en rigtig runner for operativsystemet byggede og kontrollerede pakken. **Lokal softwaretest:** isoleret kode/state blev afprøvet; en syntetisk backend eller session er ikke en production-test. **Ikke verificeret:** tilstrækkelig evidens findes endnu ikke. En miljøbegrænsning er ikke automatisk en produktfejl.

### Windows

Ren installation, payloadintegritet, det medfølgende ICP SDK, CLI, Tk, statebevarelse og oprydning er verificeret. Den afsluttende menneskelige GUI-observation viste et svarende offentligt API og beskeden om, at privat login fortsat er i browseren. Klienten blev afsluttet normalt.

### Linux og macOS

Linux amd64-pakken er bygget og kontrolleret på native Ubuntu 24.04: udpakning, integritet, SDK, CLI og Xvfb/Tk. macOS Intel-pakken er bygget og kontrolleret på native macOS 15: pakkeintegritet, SDK, CLI og Tk. Begge er reel native runner-evidens, men ikke menneskelig GUI-accept på alle slutbrugermaskiner.

Der er 18 releasekontroller pr. platform. Windows CI-payload matchede alle 1.547 filer i den tidligere accepterede lokale payload. De endelige downloadfiler er SHA-256-kontrolleret.

### Faktisk lokal modelinference

Bundled Qwen-baggrundsinference er gennemført på Windows. Ollama 0.34.4 med qwen2.5-coder:0.5b er gennemført på en separat fysisk Windows-testmaskine. Provider/modelvalg og output/kø/SQLite-hashes er korreleret. Der var ingen fallback, duplicate, point eller publication. Kontrolplanet var en isoleret fixture; modelinference var faktisk.

<!-- page -->
## Kommunikation og arbejdsflow

### To fysiske Windows-PC'er på LAN

Begge retninger og spørgsmål/svar-returen er verificeret. Testen omfattede TLS-peeridentitet, byteidentitet, SHA-256, vedvarende SQLite-inbox, restart/retry, duplicatebeskyttelse, ukendt peer-afvisning, inert modtaget indhold og kontrolleret stop.

### Direkte WAN gennem internet og NAT

En node på separat mobilnet etablerede direkte TCP til hjemmenetværket. Derpå blev den eksisterende ChromaSpeechAI-transport verificeret med TLS 1.3, ALPN chromaspeech-prsm-v1, approved peer authentication og en payload på 100.000 bytes. SHA-256 og bytes matchede. Restart/retry sendte nul nye fragments for den allerede modtagne besked. Ukendt peer blev afvist før storage; inbox var persistent.

Den modsatte, selvstændigt initierede WAN-forbindelse var ikke verificerbar i testmiljøet. Der blev ikke brugt overlay som erstatning. Den midlertidige routerregel blev fjernet igen.

### Baggrund, ressourcer og korrelation

Den eksisterende kø er koblet til klientens baggrundslivscyklus. Windows-profilen har målrettede tests for leases, retry, pause, stop, cancellation og genstart. Ressourcehåndhævelse omfatter CPU-planlægning, inferencetråde og committed memory, ikke en garanti for samlet fysisk RAM.

Task-/peer-korrelation er testet med faktisk lokal Windows TLS og SQLite; AI/backend var mock i netop denne test. Lokal nodeopsætning og autoriseret forbindelse blev testet med Windows SDK mod eksisterende WASM i lokal PocketIC. Det er ikke en live nodeoptagelse.

### Privatliv, review og publication

Private endpointguards, owner-isolation, cache/session-oprydning og downloadintegritet er lokalt verificeret. Globale auditendpoints er begrænset til eksisterende adminrolle; det giver ikke admin nye rettigheder til privat recordindhold. Eksisterende publication-tests bevarer verification, consent, roller og backendaccept. Intet af dette dokumenterer en ny production-deployment.

<!-- page -->
## Rettede fejl og præcise begrænsninger

### Faktiske rettelser

- Manglende SDK i en ren Windows-distribution blev løst ved at pakke det allerede låste @icp-sdk/core 5.4.0 og ti runtimeafhængigheder ved release-build. Ingen dependencyopgradering og ingen slutbruger-npm-installation.
- Manglende sammenkobling mellem jobs og peer-beskeder blev løst gennem eksisterende identiteter, queue og inbox.
- Private endpoint- og auditmetadatafejl blev rettet lokalt uden ændring af Internet Identity, owner-model, Candid eller stable-schema.
- Windows-pakkens PowerShell module-discovery og kort/lang midlertidig sti blev korrigeret i packaging. Historiske fejlede CI-kørsler er bevaret.

BigInt-eksportkorrektionen er en kompatibilitetsrettelse; den beskrives ikke som en universelt reproduceret runtimefejl. Dokumentationen genbruger eksisterende PASS, når relevante bytes og kontrakter ikke ændres. Denne præsentationsopdatering er ikke en ny funktionel testkampagne.

### Fortsat ikke verificeret eller ikke leveret

- Faktisk live Internet Identity end-to-end, live admission og live migration.
- Manuel macOS-GUI og fuld Linux DEB installation/afinstallation.
- Reverse WAN-initiering i det separate mobile testmiljø.
- Native privat filgem/hent via browser-owner og direkte privat owner-resultatadgang før global deling.
- Kontrolleret Ollama/Linux/macOS/GPU-ressourcebidrag; generel ressourcedeling er deaktiveret.
- Pakker er usignerede; macOS er ikke notariseret. Platformikoner har særskilt dokumenterede begrænsninger.

Officiel understøttelse af Android og iOS er udsat til senere.

### Hardware og reproducerbarhed

Dette er software. Fysisk LAN/WAN og inference er evidens for de afprøvede maskiner og forbindelser. Simulation, lokal backend og eventuelle hardwaremodeller beviser ikke fysisk optisk/GPU-/specialhardwareperformance.

Native buildworkflow bruger clean checkout, fastlåste Actions/dependencies, npm-lock og hashkontrollerede runtimeaktiver. Runnersystem og eksekverbar metadata kan påvirke pakkehash; identiske binaries på tværs af alle buildmiljøer påstås ikke. VERIFICATION.md og NATIVE_BUILD_EVIDENCE.json identificerer de accepterede builds. Downloadhashes findes i docs/DOWNLOADS.md og releasens SHA256SUMS.txt.

MCP er fortsat en særskilt gated funktion efter rc.2 og er ikke implementeret her. Denne dokumentation indebærer ingen ny produktions- eller Internet Identity-ændring.
