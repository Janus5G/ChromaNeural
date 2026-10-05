# Third-party and separately licensed components

The root Apache-2.0 license covers only the identified ChromaNeural-authored work. This table records the inspected dependency licenses, not a transfer of authorship to Janus. Refract first-license decision is resolved as MIT; publication approval remains separate.

## npm runtime dependencies

Versions and integrity pins come from the accepted package-lock. No upgrade occurred. Original licenses remain inside installed node_modules; additional byte-identical copies are retained below so a clean source checkout also includes attribution. None of the inspected package trees contained a separate NOTICE file.

| Component | Locked version | License | Retained text |
| --- | --- | --- | --- |
| @dfinity/cbor | 0.2.3 | Apache-2.0 | `docs/licenses/npm/@dfinity_cbor/LICENSE` |
| @icp-sdk/core | 5.4.0 | Apache-2.0 | `docs/licenses/icp-sdk-core-5.4.0-LICENSE` |
| @noble/curves | 1.9.7 | MIT | `docs/licenses/npm/@noble_curves/LICENSE` |
| @noble/hashes | 1.8.0 | MIT | `docs/licenses/npm/@noble_hashes/LICENSE` |
| @scure/base | 1.2.6 | MIT | `docs/licenses/npm/@scure_base/LICENSE` |
| @scure/bip32 | 1.7.0 | MIT | `docs/licenses/npm/@scure_bip32/LICENSE` |
| @scure/bip39 | 1.6.0 | MIT | `docs/licenses/npm/@scure_bip39/LICENSE` |
| asn1js | 3.0.10 | BSD-3-Clause | `docs/licenses/npm/asn1js/LICENSE` |
| pvtsutils | 1.3.6 | MIT | `docs/licenses/npm/pvtsutils/LICENSE` |
| pvutils | 1.2.0 | MIT | `docs/licenses/npm/pvutils/LICENSE` |
| tslib | 2.8.1 | 0BSD | `docs/licenses/npm/tslib/LICENSE.txt` |

The published @icp-sdk/core 5.4.0 npm payload omitted LICENSE. npm's version metadata identifies commit `f5fe3d6a625cd1f9b8a8c8da10ba99bfbc362f19`; its full root Apache LICENSE is now retained. Its packages/core/LICENSE is a symbolic reference to ../../LICENSE, not another license. The upstream tree at that commit contained no NOTICE. The tiny reference file is retained as provenance alongside the actual full text. No SDK code or lockfile changed.

## Other bundled material

| Component | Version / source | Terms and location |
| --- | --- | --- |
| ChromaPlex toolchain | accepted source hashes | MIT; `client/vendor/chromaplex-toolchain/LICENSE` |
| ChromaPlex main / CPA / CPL | accepted source hashes | MIT; `client/vendor/chromaplex-main/LICENSE`; existing modified simulator disclosed in docs/LICENSING.md |
| ChromaSpeech wire | accepted frame/TCP implementation | MIT; `client/chroma/speech_wire/LICENSE` |
| Qwen2.5-Coder-0.5B-Instruct GGUF | pinned revision/asset digest in packaging/assets.lock.json | Apache-2.0; `docs/licenses/Qwen.txt`, installed `models/QWEN_LICENSE` |
| llama.cpp | b10964, pinned native assets | MIT; `docs/licenses/llama.cpp.txt` and native archive license |
| LLVM OpenMP runtime | accepted Windows binary | Apache-2.0 WITH LLVM-exception; full historical terms retained in `docs/licenses/LLVM-OpenMP.txt` |
| cryptography | 46.0.5 | Apache-2.0 OR BSD-3-Clause; all three original license files retained in packaging/windows-optional-deps/cryptography-46.0.5.dist-info/licenses |
| cffi | 2.1.1 | MIT-0 (the actual file says MIT No Attribution), subject to file-specific exceptions; original license retained in packaging/windows-optional-deps/cffi-2.1.1.dist-info/licenses |
| pycparser | 3.0 | BSD-3-Clause, Eli Bendersky; original license retained in packaging/windows-optional-deps/pycparser-3.0.dist-info/licenses |
| Refract Editor adapters/VM | four exact source copies | MIT, Copyright (c) 2026 Janus Rokkjær; client/reference_core/LICENSE and NOTICE |
| PRISME / Binary Extension | inspected license snapshots | All Rights Reserved; retained notices in docs/licenses; not relicensed |

Windows optional dependency directories become client/optional-deps in the installed payload. Linux system packages retain their own distribution terms. Python/Tk and Node.js themselves are not bundled by this RC. NumPy is an optional existing visualization import, not bundled or newly required for scalar execution. PyQt/Refract editor, wallet and SHIP are not bundled.

MIT notices must remain with copies/substantial portions. BSD attribution/disclaimers must be retained for source and binary distributions; endorsement restrictions remain. Apache license text, applicable attribution/NOTICE and modification notices must be preserved. LLVM exceptions are not replaced by plain Apache text. Original copyright holders and authors remain credited by their retained texts. Model/native binaries have not been relabeled as ChromaNeural code.

The audit checked shipped package-level license files and declared versions. It does not constitute a patent non-infringement opinion or a reconstruction of every statically linked upstream build input. No incompatible copyleft requirement was found in the inspected declared dependency licenses. Native package license-payload checks passed on all three platforms; source license boundaries are preserved. This document does not authorize publication.


## Optional MCP client dependency payload

Official mcp 2.3.0 (MIT) and its exact transitive dependencies are enumerated with upstream license expressions and wheel hashes in docs/MCP_DEPENDENCIES.json. Native packages preserve their distribution metadata/license files under client/mcp-deps. packaging/requirements-mcp.txt pins the build inputs; cryptography remains 46.0.5. No CLI extras or model runtime are added by this SDK integration. Existing component licenses are unchanged.
