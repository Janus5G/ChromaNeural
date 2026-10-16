# Ressourcebaseret Fair Use V2 — RC6-status

ChromaPoints beskriver rimeligt ressourceforbrug, ikke penge. Ét værktøjskald koster
ikke ét point. Den fremadrettede DATA+CPU-model bruger
`102400000000 × dataBytes + 107374182400 × cpuMicros` ticks, med
`107374182400000000` ticks pr. point. Dermed svarer 1 MiB eller 1 CPU-sekund til ét
point i ressourceværdi. Alle ticks/carry bevares; afrundet visning ændrer ikke
regnskabet. RAM×tid og GPU-afregning er deaktiveret, ikke stiltiende prissat til nul.

Discovery, initialisering, helbredstjek, værktøjslister, opsætning og godkendelser
er gratis. Data er arbejdsdata gennem den kontrollerede broker: input plus output
én gang. Protokolindpakning, kontroltrafik og interne kopier udelades. CPU betyder
betroet samlet CPU-tid for procestræet, ikke forløbet vægtid.

En udtrykkeligt godkendt teknisk ramme bestemmer reservationen. Samtidige opgaver
kan ikke reservere samme tilladte forbrug. Kendt afslutning afregner målt forbrug
og frigiver resten. Afvisning før afsendelse koster nul. Tvetydig kørsel bevarer
reservationen til afstemning; intet automatisk gratis genforsøg eller refundering.
Fire kald er en sikkerhedsgrænse, ikke en pris. Loftet på samlet 100 udestående
reserverede point er adgangskontrol og afkorter aldrig den målte pris.

Forbindelser og individuelle værktøjer kræver fortsat godkendelse. Serverens egne
priser eller telemetri kan ikke afregne journalen. Resultater er ubetroede data.
Journalen gemmer ID'er, fingeraftryk, hashes, grænser og målinger, ikke tokens,
prompts eller resultatindhold. Lokalt MCP-debit adskilles fra netværkets forbrug.

## Aktivering og verificering

Den lokale software implementerer præcis aritmetik, vedvarende reservation/afregning
og central håndhævelse gennem en udtrykkelig betroet kørselsadapter. Den isolerede
Motoko-kandidat projicerer samme formel ind i den eksisterende Account-kontopost.
Ingen af delene udsteder lokale netværkspoint eller konverterer gamle saldi.
Starttildeling og historisk optjening er ikke automatisk anvendelige i V2.

Produktionsregnskab, produktionsmåling og den numeriske afregnings-GUI er **NOT TESTED — deaktiveret** i RC6. Den levende V2-autoritets-/tildelingsadapter,
vedvarende ledger-carry med fremadrettet epokeovergang og den komplette betroede
produktionsmåler er ikke implementeret fra ende til ende. Den eksisterende V1-bridge
kan ikke aktivere V2. Historisk deployment-proveniens er ikke længere en blocker.

Den lokale journal bevarer præcise brøkdebiteringer gennem procesgenstart og en
udtrykkelig epokeovergang for samme politik/konto/tildeling. Autoritetens kumulative
værdier må ikke nulstilles, og uafklaret arbejde blokerer overgangen. Denne overgang
i klienten implementerer ikke vedvarende carry i selve ledger-aktøren.

Softwarekontroller bruger syntetiske tildelinger og testdata. Cgroup-forsøget beviser
den lokale CPU-tæller, ikke hele produktionsafregningen. Den faktiske lokale
RoboForge-gateway og compiler bestod Python-MCP-kontrollen af request-metadata,
Ed25519-grant, kvittering og replay-afvisning. Testen brugte en syntetisk værtsmåler
og beviser derfor ikke produktionsmåling eller -afregning. Kontrollerede MCP-kald
bruger SDK'ens enkelt-request-metode uden automatiske værktøjsgenforsøg. Manglende
eller forkerte RoboForge-kvitteringer bevarer reservationen.
Live-integration og accept af numerisk afregning er fortsat **NOT TESTED**. Ti faktiske Linux-GUI-kontroller bestod på engelsk og dansk med simulerede AI-svar: start, annullering, eksplicit lokal fortsættelse, godkendelse/anvendelse af forslag og nedlukning.
RoboForge har ingen ChromaPoints-saldo eller prisfastsættelse. Ingen levende backend
eller konto er ændret. Lokal AI og kernen er uafhængige af det valgfrie MCP-regnskab.
RC6 indeholder denne inaktive infrastruktur og hævder ikke færdigt produktionsregnskab.
