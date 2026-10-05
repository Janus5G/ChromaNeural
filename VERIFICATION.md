# Verification and evidence boundaries

This is curated evidence, not a dump of private diagnostics. Historical checks are reused only where their relevant bytes/contracts remain unchanged. Passing a hash or software test does not verify AI correctness or physical hardware performance.

| Area | Evidence | Scope / limitation |
|---|---|---|
| Result publication v0.2.9 | PASS local integration | Consent, verification and backend role requirements preserved; no new live publication claim |
| Physical two-node LAN | PASS actual separate Windows PCs | Both directions, reply correlation, TLS peer identity, SHA-256/byte identity, persistent SQLite inbox, restart/retry, deduplication, unknown-peer rejection, inert payload |
| Direct WAN | PASS actual cellular-to-home TCP and ChromaSpeechAI | TLS 1.3 / chromaspeech-prsm-v1, approved peer, 100000-byte SHA-256 equality, restart retry sent_fragments=0, unknown-peer rejection before storage, persistent inbox |
| Reverse separate WAN initiation | NOT VERIFIED | Test-environment limitation, not product failure |
| Platform acceptance | PASS actual Windows / user observed | Lifecycle, settings, public connection; historical missing SDK environment corrected |
| Actual Ollama | PASS actual Windows NODE_A | Ollama 0.34.4 / qwen2.5-coder:0.5b; queue/output/SQLite hash correlation, no duplicate/fallback/points/publication. Control plane was fixture, inference was real |
| M1 background worker | PASS | 25 targeted M1/M2 checks + 18 direct regressions, actual Windows bundled-Qwen background inference; mock control plane |
| M2 resource enforcement | PASS scoped Windows profile | CPU/threads/committed-memory and lifecycle; no total physical-RAM guarantee |
| M3 task/peer correlation | PASS | 18 targeted + 12 direct regression tests; actual local Windows TLS/SQLite; AI/backend mock |
| M4 node setup/connection | PASS local | 12 Python, 8 JS, 15 integration checks; actual Windows SDK against local PocketIC/WASM; no production registration |
| Privacy/access guards | PASS local | Owner checks, cache/session cleanup, download integrity; actual user-II end-to-end NOT VERIFIED |
| Audit metadata correction | PASS local v0.2.17 | Prior v0.2.16 review FAIL retained: anonymous/cross-owner metadata leak. Restricted to existing admin role; 39 checks; no new private-content rights |
| Integrated guards v0.2.18 | PASS local | Existing components consolidated; no live deployment |
| M8 v0.2.19 installer | PASS scoped integrity; connection FAIL on clean install | 409 manifest bytes correct, but SDK dependency tree absent; earlier copy tests did not prove full runtime completeness |
| M8 v0.2.20 correction | PASS actual Windows | Locked SDK and 10 dependencies bundled; 24 checks; 1572 installed payload hashes; launchers, CLI, Tk and anonymous live read-only probe |
| M8 final GUI | PASS user observed 2026-10-01 | Public API reachable status and browser-only private-login notice displayed clearly; normal exit |
| RC Windows x64 EXE | PASS native Windows CI | Clean installation, payload integrity, SDK, CLI, offline Tk, existing-state preservation and extraction cleanup; 18 release checks |
| RC Linux amd64 DEB | PASS native Ubuntu 24.04 CI | Build, extraction, payload integrity, SDK, CLI, Xvfb/Tk; 18 release checks. Full dpkg install/remove lifecycle not tested |
| RC macOS x86_64 app/ZIP | PASS native macOS 15 Intel CI | Build, package integrity, SDK, CLI, offline Tk; 18 release checks. Manual GUI NOT VERIFIED; not Universal 2 |

## Defects and corrections

Missing task-to-peer linkage was corrected without a parallel task store. Background jobs and resource settings were connected through existing queue/lifecycle contracts. Anonymous private endpoint guards and admin-only global audit access corrected actual backend privacy gaps locally. The BigInt export change is a compatibility correction, not claimed as a reproduced universal runtime failure. The latest distribution fix bundles the exact existing npm lock, rather than depending on a developer NODE_PATH. False diagnostic alarms about the source-only installer, runtime pycache and a wrongly located GUI-smoke helper were corrected in diagnostics, not by changing product semantics.

## Reproduction

Native CI uses a clean checkout, immutable Actions commit pins, exact Python/Node selections, npm ci from the accepted lock, checked asset SHA-256 and accepted application-source hashes. No Internet Identity secrets, private state or backend deployment are required. Package smoke uses isolated state and offline GUI/CLI/dependency checks. The already completed public live probe is not rerun by CI.

Release payloads and output artifacts have separate manifests. OS image updates, system libraries and executable metadata can affect artifact hashes; byte-identical installer output across different runner images is not claimed. Preserve BUILD_INFO.json, CI runner metadata, PACKAGE_SMOKE.json and SHA256SUMS.txt for each actual build.

## Hardware distinction

Physical LAN/WAN and NODE_A inference observations are physical evidence for those systems only. Local mocks, PocketIC, simulation and any future Wokwi results are software/simulation evidence. No dedicated optical/GPU/device hardware performance, throughput or readiness is inferred. No hardware LOI or hardware files are needed to install this software.

Remaining NOT VERIFIED and deferred items are enumerated in KNOWN_LIMITATIONS.md. AI output remains unverified; SHA-256 establishes byte integrity, not correctness or permission to publish.

## Accepted native runs and final documentation review

Windows: run **36878986730**, job **110425631415**, commit `cab3fbb345181c0f08e75e03013b63a63d05aea0`. Linux: run **36850929767**, job **110332149953**; macOS: the same run, job **110332149677**, commit `00f547e89954a9b88339bf68195a7b7951aa43e9`. The latter run as a whole failed on the earlier Windows job; only its successful Linux/macOS jobs are accepted. Earlier failed/cancelled runs remain historical evidence.

The subsequent packaging fixes affected Windows bootstrap/cleanup and the optional Windows-only workflow selection; Linux/macOS packages were not rebuilt without a regression reason. The current workflow is the successfully verified Windows revision and retains the accepted Linux/macOS paths.

CI exposed a Windows PowerShell module-discovery failure and a short/long temporary-path comparison failure. The release bootstrap now selects the native utility module explicitly and canonicalises both cleanup paths while preserving its exact parent/name guard. Application code, dependency versions and licenses did not change. The final Windows payload matched all 1,547 accepted local payload files.

The final public review corrects stale pre-CI status text only. The published source ZIP is the final documentation-reviewed tree. Native binaries remain the accepted CI artifacts from the commits above; their bundled documentation is the earlier snapshot. Current repository documentation and release notes supersede those pre-CI status statements. No identical rebuild from the documentation-only revision is claimed. See [curated build evidence](NATIVE_BUILD_EVIDENCE.json) and the release SHA256SUMS.txt. No private diagnostics or runtime state are included.

## Public presentation update - 2026-10-01

The repository was renamed to ChromaNeural with its history, tag and five assets preserved. New actual Windows screenshots use isolated stopped state; they are documentation captures, not renewed live acceptance. English primary PDFs describe the same accepted software. No application source, dependency, backend, license grant or release-asset bytes changed. Linux/macOS icon-only packaging metadata for a future build has local structural checks; it is not new native package acceptance.
