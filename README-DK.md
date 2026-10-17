# ChromaNeural

Lokalt AI-arbejde. Eksplicit samarbejde. Dit valg.

<p align="center">
  <img src="docs/images/chroma-neural-hero.png" alt="Konceptillustration af ChromaNeural-visionen" width="1200">
</p>
<p align="center"><sub>Konceptoversigt over ChromaNeural-visionen. Aktuelt RC6-release-scope og verificerede funktioner fremgår nedenfor.</sub></p>

## Hurtig navigation

[English](README.md) · [Brugervejledning](docs/da/guide.md) · [Installation](docs/da/installation.md) · [Privatliv](docs/da/privacy.md) · [Releasenoter](RELEASE_NOTES.md) · [Verificering](VERIFICATION.md)

## Hvad ChromaNeural er

ChromaNeural er en desktopklient til Linux amd64 til godkendt lokalt AI-arbejde og autentificeret samarbejde mellem noder. Den samler lokale AI-forslag, ressourceindstillinger og bekræftet regnskabsstatus i én brugerflade med eksplicit brugerkontrol over forbindelser og værktøjer.

Engelsk er dokumentationens autoritative standardsprog; dansk er det sekundære dokumentationssprog. Applikationen beholder alle syv eksisterende UI-sprog. ChromaSpeechAI håndterer kommunikation fra node til node; valgfrie MCP-forbindelser giver adgang fra node til værktøj.

## Hvorfor ChromaNeural

- Lokalt AI-arbejde med forslag, som du gennemgår før anvendelse.
- Autentificeret nodesamarbejde gennem særskilt godkendte forbindelser.
- ChromaSpeechAI til kommunikation fra node til node.
- Valgfri MCP-adgang til særskilt godkendte eksterne værktøjer.
- Eksplicit brugergodkendelse og kontrol over providere, forbindelser og værktøjer.
- Privat lokalt arbejde holdes adskilt fra delte resultater og publicering.

## Centrale funktioner

- **Lokale AI-forslag:** brug den eksisterende medfølgende CPU-provider eller en eksplicit valgt Ollama-provider, og gennemgå foreslåede ændringer før anvendelse.
- **Opgaver og værktøjer:** behold godkendte opgaver i den eksisterende WorkQueue, og konfigurer og godkend valgfrie MCP-forbindelser. Kontrolleret MCP-værktøjsudførelse er deaktiveret i denne prerelease, indtil produktionsregnskab og -måling er tilsluttet. Almindeligt lokalt arbejde fungerer uden MCP. Den guidede opsætning har et kurateret katalog; profilerne er NOT VERIFIED eller EXPERIMENTAL, ikke verificeret leverandørunderstøttelse.
- **Ressourcer og regnskab:** gem ressourceindstillinger, og se bekræftede ChromaPoints, forbrug og netværksstatus. En tankestreg betyder utilgængelig, ikke nul indtjening; lokale handlinger kan ikke tildele point.
- **Forbindelseskontrol:** hold browserens Internet Identity-login adskilt fra desktopklientens kontrol af det offentlige API.



## Download / release-scope

**Officiel release: Linux amd64.** Kildekoden er fortsat tilgængelig til community-ports og tilpasning til andre platforme. Windows, macOS og mobile platforme er ikke aktuelt officielt supporteret eller verificeret.

[ChromaNeural 0.2.21-rc.6 prerelease](https://github.com/Janus5G/ChromaNeural/releases/tag/v0.2.21-rc.6) · [SHA256SUMS.txt](https://github.com/Janus5G/ChromaNeural/releases/download/v0.2.21-rc.6/SHA256SUMS.txt)

Linux-DEB og den kuraterede source-ZIP er releasefilerne. RC6 er en prerelease, ikke en stabil release.

## Dokumentation & verificering

Start med den [danske brugervejledning](docs/da/guide.md), [installationsvejledningen](docs/da/installation.md) og [privatlivsoplysningerne](docs/da/privacy.md), eller læs den autoritative [engelske guide](docs/en/guide.md). Vejledningerne bruger bevarede ægte RC5-screenshots på det tilsvarende sprog; tilbagetrukne RC4-guides og screenshots er fortsat udeladt.

Ejerens accept af dokumentation, screenshots og den guidede AI/MCP-opsætning er PASS. Den aktive buildproces bruger et rent GitHub-hostet Linux-checkout; se [verificering](VERIFICATION.md) for afgrænsning og historik.

[Verificeringens afgrænsning](VERIFICATION.md) · [Buildproces](docs/BUILDING.md)

**Fair Use V2-produktionsstatus: NOT TESTED — deaktiveret.** Produktionsregnskab, produktionsmåling og den numeriske afregnings-GUI er ikke tilsluttet fra ende til ende. Lokale softwaretests og simulerede GUI-forløb bestod; de er ikke produktionsaccept. Kontrollerede MCP-værktøjer er fortsat sat på pause; lokal AI fortsætter efter et eksplicit valg. Se [ressourcebaseret Fair Use](docs/da/mcp-usage.md).

## RC6-scope og sikkerhedsgrænser

**Understøttet nu:** RC6 understøtter lokalt AI-arbejde, WorkQueue, autentificeret ChromaSpeechAI-samarbejde fra node til node og valgfri MCP-opsætning med eksplicit godkendelse af forbindelser og værktøjer. Den officielle releaseplatform er Linux amd64.

**Bevidste sikkerhedsgrænser:** private filer og lokalt arbejde uploades ikke automatisk. Deling, netværksadgang og publicering kræver eksplicit godkendelse og kontrol. Fjernudførelse er bevidst deaktiveret.

**Uden for aktuelt scope / endnu ikke verificeret:** generel ressourcedeling er fortsat deaktiveret; generelle Linux-/Ollama-/GPU-ressourcebidrag ligger uden for aktuelt RC6-scope. Live Internet Identity fra ende til ende, live nodeadgang, live migration og samspil mellem LAN Build05 og hovedapplikationens API er fortsat **NOT VERIFIED**. Der fremsættes ingen påstand om fysisk optisk/GPU-ydeevne.

Se [kendte begrænsninger](KNOWN_LIMITATIONS.md). Konceptillustrationen udvider ikke det officielle Linux-release-scope og verificerer ikke fremtidige funktioner.

## Licenser

ChromaNeural-koden bruger Apache-2.0; identificerede komponenter beholder deres egne vilkår. Se [licensgrænser](docs/LICENSING.md), [LICENSE](LICENSE), [NOTICE](NOTICE) og [tredjepartslicenser](THIRD_PARTY_LICENSES.md).
