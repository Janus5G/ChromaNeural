# ChromaNeural 0.2.21-rc.4

**LOCAL CANDIDATE — NOT RELEASED. New artifact/security acceptance pending.**

This candidate is prepared locally. No repository, tag or public release has
been created. Previous release downloads and checksums are not valid for RC4.
Use only the new candidate's SHA256SUMS.txt after its acceptance is complete.

ChromaSpeechAI remains node-to-node. MCP remains optional node-to-tool.
ChromaNeural remains usable without MCP; remote execution remains disabled.

## RC4 release scope

Only Windows x64 and Linux amd64 are release targets. macOS, Android and iOS are outside this release. Portable code and historical documentation remain unchanged.

The Overview and Windows tray now share a compact ChromaPoints/network status from the existing accounting state. Developer accounting remains available; no local action awards points.

## Packaging boundary

Release inputs are explicit, individually hash-bound paths in
packaging/release-inputs.json. Unknown source files and private runtime state
fail the release gate. Dependency console launchers containing build-machine
interpreter paths are excluded at dependency staging. Libraries are obtained
fresh using the existing hash-locked dependency versions.

The source archive and packages are built only from these clean inputs.
User connection profiles, preferences, identities and sessions are never
release inputs. A fresh, isolated first launch must have an empty connection
editor. Existing user state is separate and is not silently deleted or migrated.

## Evidence boundaries

Unchanged application functionality may reuse its previously verified evidence
only with matching source hashes. This does not certify new RC4 artifacts.
The verified MCP real-model flow used Ollama and qwen3:4b-instruct with a genuine
structured tool call; qwen2.5-coder:0.5b is not a verified MCP tool-calling model.
The existing seven locales, screenshots and PDF guides retain their historical
labels. They are not evidence that a new RC4 installer has passed.

The RC4 Windows and Linux package, contamination and clean-install gates
remain pending until separately recorded as passed. No native macOS result is
inferred from Windows or Linux.

## Important limits

- Packages are unsigned. macOS is not notarized, is Intel-only and has no bundled native inference runtime. OS warnings may appear.
- Manual macOS GUI, full Linux DEB install/remove lifecycle, live Internet Identity end-to-end, live migration and live node admission remain **NOT VERIFIED**.
- General resource sharing remains disabled. Total physical RAM is not guaranteed; controlled Ollama/Linux/macOS/GPU contribution is unsupported.
- Native private-file browser/desktop integration and direct private owner-result retrieval before optional global sharing are not delivered.
- SHA-256 is integrity, not AI correctness; a peer response does not self-verify or automatically publish. Downloading does not award ChromaPoints.
- [Current package-icon limitations](docs/BRANDING.md) are documented separately from application functionality.
- This is a software release. No specialised optical/GPU hardware performance is claimed as physically verified.

Official Android and iOS support is deferred to a later time.

## Licenses

ChromaNeural's own code: Apache-2.0. The four documented Refract files, identified ChromaPlex/CPL/CPA and ChromaSpeechAI components retain MIT. PRISME retains its separate restrictive terms. Other dependencies retain their licenses and notices. [Exact license boundaries](docs/LICENSING.md).

