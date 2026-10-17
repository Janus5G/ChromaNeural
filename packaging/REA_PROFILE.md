# REA optional profile: audited Linux scope

REA 6.5.0 (MIT) is supported only through the eight audited compact contracts
below, on Linux hosts where the required isolation can be established.
This does not approve the entire upstream catalog or certify every analysis
backend. Other REA versions fail closed pending review. REA is never a core
startup dependency and is disabled until explicit connection/tool consent.

## Audited contracts

- inspect_managed_artifact: static managed artifact metadata.
- inspect_managed_members: static managed member inventory.
- inspect_managed_native_boundaries: static managed/native boundaries.
- inspect_analysis_view: retained analysis view inspection.
- inspect_pe_resources: static PE resource inspection.
- inspect_electron_fuses: static Electron fuse inspection.
- analyze_javascript_application: static JavaScript/application analysis.
- get_evidence_bundle: retained evidence retrieval.

The actual compact schemas/descriptions and upstream
dist/contracts/toolEffects.js were inspected. The first seven may modify
session evidence; the evidence getter has no declared effects. None declares
target execution, network access, target writes, device changes or live
instrumentation. Tools declaring subprocess launches or filesystem writes,
including the current WASM inspection contract, were excluded. Full definition
fingerprints are pinned in client/chroma/mcp_rea.py; changed/missing definitions
fail closed. Retained session evidence does not persist across separate calls.

Official source: https://github.com/morluto/rea
Official contracts: https://github.com/morluto/rea/blob/main/docs/mcp-contracts.md
No agent registration, rea setup or automatic installation is performed.

## Limits and authority

Only the REA child receives REA_MCP_INPUT_SCHEMA_PROFILE=compact and
REA_MCP_OUTPUT_SCHEMA_PROFILE=off. The adapter validates up to 512 tools,
eight pages, 1 MiB canonical catalog data and 32 KiB per upstream definition.
It exposes only the eight audited definitions through ordinary 16 KiB
definition / 64 KiB discovery bounds. Generic MCP's 32-tool discovery limit
is unchanged. The actual observed count was 207; that count is not hard-coded.

Existing connection consent, per-tool fingerprints, target-edit revocation,
enabled state, task limits and untrusted-result handling remain authoritative.
Returned content never grants execution authority or additional permissions.

| Linux control | Fixed profile limit |
| --- | --- |
| Aggregate memory | 1.5 GiB; zero swap; whole-group OOM kill |
| Aggregate CPU | 100% of one logical CPU |
| Tasks/threads | 64 |
| Concurrent active REA workers | One per user, nonblocking lock |
| SDK startup/request deadline | Existing 10 seconds |
| Discovery/call deadline | 25 seconds including startup/catalog |
| systemd service lifetime | 30 seconds |
| Stop | Entire control group; 2-second grace then SIGKILL |
| Transport frame/session output | 4 MiB / 8 MiB |
| Child stderr | 128 KiB, discarded rather than logged |
| Transport input | 64 KiB |
| Delivered tool result | Existing 32 KiB |

Limits are fixed reviewed profile constants, not arbitrary user/environment
overrides. Before Node starts, actual cgroup memory, swap, CPU, task and OOM
settings are checked. The service uses private networking, read-only system/home
access, only its private temporary directory writable, no ambient credentials,
no user-manager bus access and no namespace/cgroup delegation.
Absent controllers, permissions, user systemd or hardening support block REA:
there is no unrestricted fallback. systemd's lifetime bound also survives an
abrupt parent-worker exit. Normal cancellation explicitly stops the whole group.

## Actual acceptance

Linux testing used Node 22.22.1 and isolated REA 6.5.0. Initialization, actual
207-tool listing, eight-tool filtering, explicit approval of
inspect_electron_fuses and a static call on a project-owned synthetic binary
passed. The structured evidence result was 2,220 bytes; fixture bytes were
unchanged. The call took 11.41 seconds, peak memory was 263,233,536 bytes
(about 251 MiB) and 11 tasks were observed. These measurements informed the
profile's headroom. Revocation, process-tree cleanup and Local AI afterward
passed. Missing REA and failed-worker GUI paths preserve the optional flow.

Controlled exhaustion used the same mechanism with 64 MiB memory, 25% CPU,
eight tasks and four seconds. Whole-group OOM, CPU throttling, task refusal
and deadline termination passed; child processes were gone and Local AI
worked afterward. Unrelated historical test suites were not rerun.

Only the static subset is supported, not REA runtime instrumentation or device
control. Missing optional analysis engines, excessive results and timeouts fail
locally. Use REA only on software, devices and data you are authorized to analyze.
