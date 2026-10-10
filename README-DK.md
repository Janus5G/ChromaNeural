# ChromaNeural

Lokalt AI-arbejde. Eksplicit samarbejde. Dit valg.

**0.2.21-rc.5 - udviklingskandidat, endnu ikke offentliggjort.**
[English](README.md) · [Brugervejledning](docs/da/guide.md) · [Installation](docs/da/installation.md) · [Privatliv](docs/da/privacy.md)

ChromaNeural er en desktopklient til Windows/Linux til godkendt lokalt AI-arbejde og autentificeret samarbejde mellem noder. Engelsk er standardsproget; applikationen beholder alle syv eksisterende UI-sprog. RC5-dokumentationen vedligeholdes på engelsk og dansk.

<img src="docs/da/images/overview.png" alt="Dansk RC5-oversigt uden konto og uden tilgængelige ChromaPoints" width="960" height="600">

## Hvad klienten kan

- Gemme ressourceindstillinger og vise bekræftet regnskabsstatus. En tankestreg betyder utilgængelig, ikke nul indtjening.
- Foreslå lokale AI-ændringer gennem den eksisterende medfølgende CPU-provider eller en eksplicit valgt Ollama-provider. Gennemgå forslaget før anvendelse.
- Bevare godkendte opgaver i den eksisterende WorkQueue. ChromaSpeechAI håndterer kommunikation fra node til node.
- Tilbyde valgfri MCP-adgang fra node til værktøj gennem særskilt godkendte forbindelser og værktøjer. Almindeligt lokalt arbejde fungerer uden MCP.
- Holde browserens Internet Identity-login adskilt fra desktopklientens kontrol af det offentlige API.

Generel ressourcedeling er fortsat deaktiveret. Lokale handlinger kan ikke tildele ChromaPoints. Fjernudførelse er deaktiveret. Private filer uploades ikke automatisk; netværksadgang og global publicering sker heller ikke automatisk.

## RC5-distribution

Releaseplatformene er Windows x64 og Linux amd64. Windows-kandidaten bruger Inno Setup; det planlagte autoritative build starter fra et rent GitHub Actions-checkout. Testsignering bruger kun ejerens eksisterende SignPath-testpolitik. Et selvsigneret testcertifikat er **ikke** betroet signering til en offentlig release.

Der annonceres ingen RC5-download eller PASS for produktionssignering her. Tilbagetrukne RC4-guides og screenshots genbruges ikke. Se [releasestatus](RELEASE_NOTES.md), [build- og signing-gates](docs/BUILDING.md) og [politik for kodesignering](docs/SIGNING.md).

## Begrænsninger og licenser

Live Internet Identity fra ende til ende, live nodeadgang, live migration og samspil mellem LAN Build05 og hovedapplikationens API er NOT VERIFIED. Generel kontrolleret Linux-/Ollama-/GPU-deling understøttes ikke. Der fremsættes ingen påstand om fysisk optisk/GPU-ydeevne.

ChromaNeural-koden bruger Apache-2.0; identificerede komponenter beholder deres egne vilkår. Se [licensgrænser](docs/LICENSING.md), [LICENSE](LICENSE), [NOTICE](NOTICE) og [tredjepartslicenser](THIRD_PARTY_LICENSES.md). Hovedlicensen alene fastslår ikke egnethed til SignPath Foundation.
