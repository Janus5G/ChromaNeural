# ChromaNeural

[English](ChromaNeural-Verified-Capabilities.md) · [Dansk](../da/ChromaNeural-Verified-Capabilities-DA.md) · [Deutsch](../de/ChromaNeural-Verified-Capabilities.md) · [Français](../fr/ChromaNeural-Verified-Capabilities.md) · [日本語](../ja/ChromaNeural-Verified-Capabilities.md) · [简体中文](../zh-CN/ChromaNeural-Verified-Capabilities.md) · [हिन्दी](../hi-IN/ChromaNeural-Verified-Capabilities.md)
## Verified Capabilities

ChromaNeural 0.2.21-rc.2 documentation | Unreleased candidate | 3 October 2026

**rc.2 documentation status:** This candidate has not been publicly released. Localization and extensible i18n passed local verification; rc.2 native package/build acceptance is still pending. Installation, platform, LAN/WAN, inference and live-service evidence below is historical rc.1 evidence unless explicitly labelled rc.2. Links to rc.1 downloads do not provide rc.2 localization.

## rc.2 localization evidence

Phase B and Phase C passed local verification: 303 messages across seven shipping locales, persisted selection, English fallback, protected input/state, modal actions and synthetic control/probe checks. Actual Tk capture and visual acceptance passed; the Chinese connection capture blocker was traced to desktop capture interference and resolved with window-specific capture in verification tooling. Existing failures remain part of the record.

The extensible-i18n gate also passed. One data-only registry supplies identifiers, display names and number formatting. An isolated eighth catalogue plus one registry entry passed selection, persistence, fallback, Windows launcher and packaging/resource-discovery checks; the test locale was removed. The 476 number-format and 2,121 message comparisons passed, and all 331 expected source hashes matched. These are local source/behavior checks, not rc.2 native package, live II or production acceptance. No public rc.2 release occurred.

## Reading the historical rc.1 evidence

**Actual physical:** traffic or inference was observed on the real machines. **Native CI:** a real runner for the operating system built and checked the package. **Local software:** isolated code/state was exercised; a synthetic backend or session is not production. **Not verified:** sufficient evidence is not yet available. A test-environment limitation is not automatically a product failure.

### Windows

Clean installation, payload integrity, bundled ICP SDK, CLI, Tk, existing-state preservation and cleanup are verified. Final human GUI observation showed the public API responding and the notice that private login remains in the browser. The client exited normally.

### Linux and macOS

The Linux amd64 package was built and checked on native Ubuntu 24.04: extraction, integrity, SDK, CLI and Xvfb/Tk. The macOS Intel package was built and checked on native macOS 15: package integrity, SDK, CLI and Tk. These are actual native runner results, not human GUI acceptance on all end-user systems.

There are 18 release checks per platform. The Windows CI payload matched all 1,547 files in the previously accepted local payload. Final download files were SHA-256 verified.

### Actual local model inference

Bundled Qwen background inference ran on Windows. Ollama 0.34.4 with qwen2.5-coder:0.5b ran on a separate physical Windows test machine. Provider/model selection and output/queue/SQLite hashes were correlated. There were no duplicates, fallback, points or publication. The control plane was an isolated fixture; model inference was real.

<!-- page -->
## Communication and workflow

### Two physical Windows computers on LAN

Both directions and question/reply return were verified. Coverage included TLS peer identity, byte equality, SHA-256, persistent SQLite inbox, restart/retry, duplicate protection, unknown-peer rejection, inert received content and controlled shutdown.

### Direct WAN through the internet and NAT

A node on a separate cellular connection established direct TCP to the home network. The existing ChromaSpeechAI transport then passed with TLS 1.3, ALPN chromaspeech-prsm-v1, approved peer authentication and a 100,000-byte payload. SHA-256 and bytes matched. Restart/retry sent zero new fragments for the already received message. An unknown peer was rejected before storage; the inbox persisted.

The reverse independently initiated WAN connection could not be verified in the available environment. No overlay was counted as a substitute. The temporary router rule was removed afterwards.

### Background work, resources and correlation

The existing queue is connected to the client's background lifecycle. The Windows profile has targeted lease, retry, pause, stop, cancellation and restart checks. Resource enforcement covers CPU scheduling, inference threads and committed memory, not a guarantee for total physical RAM.

Task/peer correlation was tested with actual local Windows TLS and SQLite; AI/backend were mock in that specific test. Local node setup and authorised connection used the Windows SDK against existing WASM in local PocketIC. That is not live node admission.

### Privacy, review and publication

Private endpoint guards, owner isolation, cache/session cleanup and download integrity are locally verified. Global audit endpoints are restricted to the existing admin role without granting new access to private record content. Existing publication tests preserve verification, consent, roles and backend acceptance. None of this establishes a new production deployment.

<!-- page -->
## Corrections and remaining limits

### Defects actually corrected

- A missing SDK in a clean Windows distribution was fixed by packaging the existing locked @icp-sdk/core 5.4.0 and ten runtime dependencies at release build time. No dependency upgrade or end-user npm installation.
- Missing task/peer-message linkage was connected through existing identities, queue and inbox.
- Private endpoint and audit-metadata defects were corrected locally without changing Internet Identity, owner model, Candid or stable schema.
- Windows package PowerShell module discovery and short/long temporary-path handling were corrected in packaging. Historical failed CI runs remain recorded.

The BigInt export correction is a compatibility correction, not a universally reproduced runtime failure. Earlier PASS evidence is reused when relevant bytes and contracts are unchanged. This presentation update is not a new functional test campaign.

### Still unverified or not delivered

- Actual live Internet Identity end-to-end, live admission and live migration.
- Manual macOS GUI and the complete Linux DEB install/remove lifecycle.
- Reverse WAN initiation in the separate mobile test environment.
- Native private file access through browser-owner authority and direct private owner-result access before global sharing.
- Controlled Ollama/Linux/macOS/GPU contribution; general resource sharing remains disabled.
- Packages are unsigned and macOS is not notarized. Platform-icon limitations are documented separately.

Official Android and iOS support is deferred to a later time.

### Hardware and reproducibility

This is software. Actual LAN/WAN and inference support the tested machines and connections. Simulation, local backend execution and hardware models do not establish physical optical/GPU/specialised-hardware performance.

Native workflows use clean checkout, pinned Actions/dependencies, the npm lock and hash-checked runtime assets. Runner systems and executable metadata can affect package hashes; identical binaries across all build environments are not claimed. VERIFICATION.md and NATIVE_BUILD_EVIDENCE.json identify accepted builds. Download hashes are in docs/DOWNLOADS.md and release SHA256SUMS.txt.

MCP remains a separately gated post-rc.2 feature and is not implemented here. No new production or Internet Identity change is implied by this documentation.
