# ChromaNeural

[English](../en/ChromaNeural-User-Guide.md) · [Dansk](ChromaNeural-User-Guide-DA.md) · [Deutsch](../de/ChromaNeural-User-Guide.md) · [Français](../fr/ChromaNeural-User-Guide.md) · [日本語](../ja/ChromaNeural-User-Guide.md) · [简体中文](../zh-CN/ChromaNeural-User-Guide.md) · [हिन्दी](../hi-IN/ChromaNeural-User-Guide.md)
## Brugervejledning

ChromaNeural 0.2.21-rc.2-dokumentation | Ikke offentliggjort kandidat | 3. oktober 2026

**Status for rc.2-dokumentationen:** Denne kandidat er ikke offentliggjort. Lokalisering og udvidelig i18n har bestået lokal verifikation; native build- og pakkeaccept for rc.2 afventer stadig. Installations-, platforms-, LAN/WAN-, inference- og live-tjenesteevidens nedenfor er historisk rc.1-evidens, medmindre den udtrykkeligt er mærket rc.2. Links til rc.1-downloads giver ikke rc.2-lokalisering.

## 1. Installér og start

Hent den rigtige platformspakke fra den officielle GitHub-release, og sammenlign SHA-256 med checksumlisten. Installer runtimeforudsætningerne i installationsvejledningen. Pakken indeholder det låste ICP SDK; du skal ikke køre npm eller genbruge et udviklingsmiljø.

På Windows installeres programmet pr. bruger. Åbn Start-ChromaNeural.ps1 i den versionsbestemte installationsmappe. På Linux bruges programmenuen eller kommandoen chromaneural. På macOS åbnes ChromaNeural.app efter installation af de dokumenterede forudsætninger. Pakkerne er usignerede; slå ikke operativsystemets sikkerhed generelt fra for at åbne dem.

Første start viser ressourcevalg. Vælg dine præferencer og gem. Klienten bliver ikke automatisk optaget i et produktionsnetværk, blot fordi indstillingerne er gemt. Eksemplerne her bruger stoppet deltagelse uden konto eller private data.

![Oversigt efter gemte præferencer, med deltagelse stoppet.](../images/chroma-neural-overview.png)

Disse bevarede rc.1-skærmbilleder er på dansk og viser ikke rc.2-sprogvælgeren. Oversigt svarer til Overview, Ressourcer til Resources, Aktivitet til Activity og Login & forbindelse til Login & connection. Trinnene bevarer de historiske knaptekster; rc.2 starter på engelsk, medmindre du udtrykkeligt har valgt et andet sprog.

Oversigt samler status, balance og ressourcer. En streg betyder, at en bekræftet værdi ikke er tilgængelig. Det er ikke nul optjening og heller ikke en beregnet indtjening. Brug menuen til venstre til at skifte side.

## Sprog i rc.2-klienten

Én klient understøtter English, Dansk, Deutsch, Français, 日本語, 简体中文 og हिन्दी. Engelsk er standard og fallback uanset operativsystemets sprog. Brug sprogvælgeren i sidepanelet til straks at ændre programmets egne tekster. Eksisterende input, kildekode, forbindelses-JSON og deltagelsesstatus bevares; et sprogskift starter ikke endnu en worker eller netværkskontrol. Operativsystemets egne filvælgerkontroller beholder OS-sproget.

Et udtrykkeligt sprogvalg i GUI'en gemmer kun version og locale i `ui-language.json` ved siden af den eksisterende `preferences.json`. Det ændrer ikke denne fils skema og opretter ikke en ekstra statemappe. Valget gendannes ved næste start. Manglende, ugyldige, for store eller ikke understøttede sprogpræferencer giver engelsk fallback uden at overskrive originalen. En senere udtrykkelig gemning bevarer en ugyldig original; hvis gemning fejler, beholdes det aktuelle sprog.

Det valgfrie CLI-argument `--language` tilsidesætter sproget for den pågældende start uden at gemme valget. Windows-launcherne videresender `-Language`. Understøttede locale-id'er kommer fra `client/locale-registry.json`; det første leverede sæt er `en`, `da`, `de`, `fr`, `ja`, `zh-CN`, `hi-IN`. Et fremtidigt sprog kræver ét katalog med de samme meddelelsesnøgler og én registreringspost med navn og metadata for talformat. Det midlertidige ottende testsprog leveres ikke.

I rc.2-klienten er de tilsvarende tekster på denne guides sprog:

| Historisk skærmbilledtekst | rc.2-tekst på dansk |
|---|---|
| Oversigt | Oversigt |
| Ressourcer | Ressourcer |
| Aktivitet | Aktivitet |
| Login & forbindelse | Login & forbindelse |
| Udviklerværktøjer  ↗ | Udviklerværktøjer  ↗ |
| Afslut ChromaNeural | Afslut ChromaNeural |
| Gem ændringer | Gem ændringer |
| Gem og fortsæt | Gem og fortsæt |
| Log ind med Internet Identity | Log ind med Internet Identity |
| Gem forbindelsesdata | Gem forbindelsesdata |
| Kontrollér forbindelse | Kontrollér forbindelse |
| Backend svarer · offentligt API nået<br>Privat login er fortsat i browseren | Backend svarer · offentligt API nået<br>Privat login er fortsat i browseren |
| Lokal AI | Lokal AI |
| Privat II-lagring | Privat II-lagring |

<!-- page -->
## 2. Ressourcer og deltagelse

![Ressourcevalg i den faktiske klient. CPU-bidrag er ikke aktiveret i eksemplet.](../images/chroma-neural-resources.png)

1. Åbn **Ressourcer**.
2. Vælg det maksimale antal inferencetråde og den ønskede hukommelsesgrænse.
3. Vælg om arbejde kun må foregå, når computeren er ledig, og om det skal pauses på batteri.
4. Vælg ønsket adfærd for systembakken. Funktionen afhænger af platformens understøttelse.
5. Tryk **Gem ændringer** eller **Gem og fortsæt** ved første start. Skift tilbage via **Oversigt** i sidemenuen.

En indstilling er en øvre grænse, ikke en reservation af hardware. Windows-profilen for bundled CPU har dokumenteret håndhævelse af CPU, tråde og committed memory. Samlet fysisk RAM/RSS er ikke garanteret. Kontrolleret Ollama, Linux, macOS og GPU-bidrag er ikke understøttet; de må ikke præsenteres som håndhævede profiler.

Generel ressourcedeling er deaktiveret. Start/pause på Oversigt er ikke en genvej uden om jobgodkendelser, nodeadgang eller ressourcekontrol. Installeret eller ubrugt hardware giver ikke point.

<!-- page -->
## 3. Login og forbindelse

![Login og forbindelse uden indlæst profil. Browserlogin og API-kontrol er adskilte handlinger.](../images/chroma-neural-connection.png)

1. Åbn **Login & forbindelse**.
2. Knappen **Log ind med Internet Identity** åbner den eksisterende webapp i browseren. Log ind med din egen eksisterende identitet. Del aldrig sessionmateriale eller recoveryoplysninger.
3. Find webappens API-forbindelsesdata. Kopiér forbindelsesprofilen, indsæt den i klientens felt, og vælg **Gem forbindelsesdata**.
4. Vælg **Kontrollér forbindelse**. En offentlig API-kontrol sender ikke din private browser-session til klienten.
5. Ved succes vises **Backend svarer · offentligt API nået** og **Privat login er fortsat i browseren**.

Den succesbesked blev observeret i den historiske rc.1 Windows-slutaccept. Den beviser API-rækkevidde, ikke privat adgang, nodeoptagelse eller production-migration. Denne vejledning giver ingen anvisning på at deploye eller ændre backend.

Ved fejl: kontrollér internetadgang, den valgte profil og at Python/Node-forudsætningerne er installeret. Del kun en renset fejlbeskrivelse. Loggen kan indeholde lokale stier. Ændr ikke identitet eller slet state som første fejlsøgningstrin.

Den endelige live II-brugertest er fortsat ikke verificeret. Lokale guards må ikke antages at være installeret på den offentlige webapp alene på grund af denne klientrelease.

<!-- page -->
## 4. Aktivitet, pause og afslutning

![Aktivitet med en faktisk lokal hændelse: indstillinger blev gemt.](../images/chroma-neural-activity.png)

Aktivitet viser klientens registrerede hændelser. Brug den til at forstå, om indstillinger er gemt, eller om en handling har givet en status. En hændelse er ikke i sig selv dokumentation for verificeret AI-kvalitet, publication eller point.

Pause/stop skal respekteres af den understøttede worker. Allerede godkendte lokale jobs bevarer deres identitet i den eksisterende kø ved kontrolleret genstart. Modtaget peer-indhold må fortsat ikke automatisk eksekveres.

Brug **Afslut ChromaNeural** i sidemenuen, når programmet skal lukkes helt. Vindueskrydset kan i stedet skjule klienten, hvis systembakkevalget er aktiveret og understøttet. Luk klienten før backup eller flytning af dens state.

## 5. Lokal AI og avanceret arbejde

Den eksisterende lokale AI-vej findes under **Udviklerværktøjer**. Åbn eller gem den relevante lokale tekstfil. Vælg **Local AI**, angiv den understøttede lokale provider/model og instruktion, og godkend det præcise input. Gennemgå forslaget før du accepterer og gemmer det. Et forslag erstatter ikke automatisk din fil.

Bundled CPU/Qwen findes på Windows/Linux. En lokalt installeret Ollama-model vælges eksplicit. macOS har ikke en bundled Qwen-runtime. Der sker ingen automatisk fallback til en anden provider. Den manuelle lokale AI-vej er adskilt fra netværkets kontrollerede ressourceprofil.

Queue- og peeroperationer er avancerede CLI-funktioner i denne RC. De eksisterende kommandoer omfatter queue-ai, result, task-question, task-accept, task-reply, task-collect og task-status. Brug deres --help og en bevidst valgt lokal konfiguration. De må ikke opfattes som en automatisk live-onboardingvej.

## 6. Private filer og resultater

Arbejd kun i mapper, du udtrykkeligt vælger. Privat II storage i desktop viser information; det udfører ikke privat filupload/download. Browserens private ejerdata og desktopfiler er endnu ikke forbundet af en autoriseret filkanal.

Et lokalt resultat kan gennemgås som et forslag. Et peer-svar er ikke automatisk verificeret, selv om afsenderen er godkendt og SHA-256 matcher. Global publicering kræver den eksisterende verifikation, delingstilladelse, roller og backendaccept. Download eller review udløser ikke automatisk ChromaPoints.

Skærmbillederne viser den historiske rc.1-klient. Footerens interne komponentmærke 0.2.5 er bevaret; den dokumenterede distribution er 0.2.21-rc.1.

MCP er fortsat en særskilt gated funktion efter rc.2 og er ikke implementeret her. Denne dokumentation indebærer ingen ny produktions- eller Internet Identity-ændring.
