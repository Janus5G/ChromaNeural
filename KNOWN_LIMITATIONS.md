# Known limitations

- Release candidate; not v1.0 and not general production-network acceptance.
- Windows, Linux amd64 and macOS x86_64 native CI package verification passed. Windows manual acceptance is reused for the byte-identical application payload. Manual macOS GUI acceptance remains NOT VERIFIED; Linux DEB installation/removal lifecycle was not tested beyond native package extraction and smoke checks.
- Existing Internet Identity live end-to-end, live node admission and live migration remain NOT VERIFIED. M5 local readiness is frozen; no backend/draft/live deployment is included.
- Native private file save/load via browser-owner authority remains blocked/frozen. Direct requester access to an authoritatively verified private result before global sharing is deferred for this version.
- Resource enforcement is only accepted for the documented Windows bundled-CPU profile: CPU scheduling, inference threads and committed memory. Total physical RAM/RSS is not guaranteed. Controlled Ollama/Linux/macOS/GPU profiles are unsupported; general resource sharing remains disabled.
- Peer cooperation supports explicitly approved code-proposal tasks, not arbitrary remote jobs. No remote execution.
- Separate WAN NODE_A to HOME succeeded. Reverse independent WAN application initiation was NOT VERIFIED due to the available test environment. No overlay was counted as direct WAN evidence.
- Prior native Linux desktop evidence includes successful observations, an offline guest limitation and preserved historical failures. It does not establish current DEB or live II acceptance.
- macOS has no bundled native inference runtime and no accepted compiler sandbox. Selecting a local provider is explicit; no fallback is introduced.
- Compiler execution requires the existing exact approved non-setuid Linux sandbox binary; absent prerequisites fail closed. The packages do not silently substitute an unapproved sandbox.
- GUI improvements remain deferred. Legacy internal component/UI version labels may differ from the RC distribution version in VERSION; these labels are not evidence of a different verified backend.
- Packages are unsigned; macOS notarization is absent. OS warnings are expected.
- No GPU, optical hardware, Q8, dedicated hardware performance or hardware deployment claim is made.

Official Android and iOS support is deferred to a later time.

## License audit — 2026-10-01

The earlier four-file license blocker was resolved by Janus' first MIT license for Refract Editor on 2026-10-01. PRISME terms remain unchanged. See docs/LICENSING.md. This does not reopen the accepted v0.2.20 functionality tests. Native EXE/DEB/macOS package verification is accepted within the scopes in VERIFICATION.md. The approved 0.2.21-rc.1 prerelease is public.

## Presentation and package icons

English is the primary public documentation language. Danish sources are secondary translations. Current guides and screenshots are linked from [documentation](docs/README.md). Published package-icon limitations and prepared metadata improvements are recorded in [branding](docs/BRANDING.md); no accepted release binary has been replaced.
