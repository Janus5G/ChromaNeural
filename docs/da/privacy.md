# Privatliv og lokal tilstand

[English](../en/privacy.md) · [Brugervejledning](guide.md)

Klienten, browseridentiteten og godkendte peer-/værktøjstjenester er separate tillidsgrænser. En kopieret API-profil er forbindelsesmetadata, ikke et browserlogin eller ejerskabsbevis. Brugerspecifikke forbindelsesmetadata er private releasedata, også uden adgangskode.

Windows-tilstand ligger normalt i `%LOCALAPPDATA%\ChromaNeural\client`. Linux bruger `${XDG_STATE_HOME:-$HOME/.local/state}/chroma-neural/client`. Eksplicit `--state-dir` har forrang frem for `CHROMA_STATE_DIR`. Indstillinger, gemt sprog, API-profiler, regnskabscache, kø og logs er brugertilstand og må aldrig være releaseinput.

Releasen starter uden profil. Tilstand kan gemmes efter eksplicit brugerhandling; geninstallation af programfiler sletter ikke eksisterende tilstand. Arbejdsmapper og nodeidentiteter kan ligge andre valgte steder. Luk klienten før sikkerhedskopiering, og beskyt nøgler, databaser og logs med operativsystemets konto-/diskbeskyttelse. Kryptering ved lagring og anonymitet på netværket er ikke garanteret.

MCP-konfiguration gemmer kun ikke-hemmelige indstillinger ved siden af præferencerne. Et valgfrit bearer-token findes kun i den aktuelle session og er bundet til det præcise forbindelsesmål; målændringer ophæver bindingen. Læg aldrig hemmeligheder i navne, URL'er, programargumenter, prompts eller screenshots. Kun godkendte, aktive værktøjer tilbydes en opgave med eksplicit samtykke. Eksterne værktøjsresultater kan være skadelige eller forkerte.

ChromaSpeechAI-deling med peers og global publicering kræver egne godkendelser. Valg af en mappe er ikke delingssamtykke. Internet Identity forbliver i browseren. Informationsvisningen Privat II-lagring er ikke en native privat filkanal. Se [sikkerhedsrapportering](../../SECURITY.md) og [begrænsninger](../../KNOWN_LIMITATIONS.md).
