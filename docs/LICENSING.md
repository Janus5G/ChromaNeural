# License and code boundaries

**ChromaNeural: Apache-2.0. Refract Editor component: MIT. Historical source-license decision retained. RC5 release signing and Foundation eligibility are separate, unverified gates.**

Copyright (c) 2026 Janus Rokkjær applies to Janus-owned ChromaNeural code, not to upstream authors' work. The unmodified Apache license text is in `LICENSE`. `LICENSE_SCOPE.json` identifies the accepted source files by path/hash and their separate licenses. Release documentation and new packaging scripts are ChromaNeural-authored. Existing notices are preserved; there is no bulk source-header rewrite.

## Covered ChromaNeural work

The ChromaNeural client, work queue, resource controls, provider adapters, authenticated peer integration and release tooling identified in the scope manifest are the open-source work. The root license is not a license grant for the exclusions below. Final native package acceptance and publication approval remain separate requirements.

## Refract Editor: separate MIT component

Janus Rokkjær first licensed the Refract-owned code in the following files under MIT on 2026-10-01, confirming ownership and no previous public release/license:

- client/reference_core/cpl_adapter.py: CPL/CPA integration and adaptation.
- client/reference_core/optical_bridge.py: OPTB/SpectralIR conversion and PRISME-format adaptation.
- client/reference_core/prisme_isa.py: instruction-format assembler/disassembler.
- client/reference_core/prisme_runner.py: local byte VM.

The full MIT text and notice are in client/reference_core/LICENSE and NOTICE. Copyright (c) 2026 Janus Rokkjær. Source hashes remain in LICENSE_SCOPE.json. All four files match the original Refract Editor/Studio archives byte-for-byte. No source or imports changed.

This is a first license, not a claim that a historical Refract MIT license was found. Vendor MIT licenses did not previously license the parent editor. No conflicting file license, third-party author notice or direct restricted PRISME-core copy was identified. The PRISME/OPTB adaptation is explicit: the matching historical HTML reference and optical compiler occur in a separately MIT-marked local reference tree. Its Janus5G notice is preserved in docs/licenses/PRISME-reference-historical-MIT.txt. This does not grant a new license to current PRISME projects or provide patent clearance.

## PRISME boundary

PRISME and PRISME Binary Extension remain All Rights Reserved under their existing separate terms. Retained texts are in `docs/licenses/PRISME.txt` and `docs/licenses/PRISME-Binary-Extension.txt`. Existing separately agreed research/university permissions are neither revoked nor broadened here; this audit did not establish a general research exception from those license texts.

No nonempty direct byte-identical PRISME-core implementation copy was established in the release from the inspected PRISME repository snapshots. This is a bounded provenance finding, not proof that protocol implementations are free of all third-party or patent rights. The four Refract implementations retain their explicitly authorized MIT component license, not Apache-2.0. Protocol names, PRSM magic and compatible wire formats alone do not determine code ownership.

Apache section 3 applies as written to necessarily infringed contributor patent claims within its defined scope. This documentation does not retract that grant or promise that a separate-project label excludes an overlapping patent claim. No patent portfolio/non-infringement clearance is claimed. Excluded PRISME material is not intentionally contributed to the Apache work. The Refract rights are based on the explicit owner decision, not on a root license alone.

## Separate MIT components

`client/vendor/chromaplex-toolchain/` retains MIT, Copyright 2026 Janus Rokkjær. `client/vendor/chromaplex-main/` retains MIT, Copyright 2025 ChromaPlex OS Contributors. CPL/CPA compiler and VM copies remain under those licenses. The latter's `crystal_simulator.py` differs from the inspected upstream copy by moving the optional NumPy import to plane visualization; this existing modification is not claimed to be an unchanged upstream file. No modification was made in this audit.

`client/chroma/speech_wire/` retains its MIT license, Copyright 2026 Janus Rokkjær. It contains the ChromaSpeech frame implementation and bounded TCP adapter. Its frame differs from the bundled v0.2.4 reference; the historical v0.2.3 header is not evidence of byte identity to v0.2.4. Both retain their existing MIT terms. The full reference/hardware demonstration tree is not part of this public staging allowlist.

## External dependencies and packaging

See `THIRD_PARTY_LICENSES.md`. npm packages, optional Python wheels, model and native runtime binaries keep their own licenses. The service package is private packaging metadata, not a separate public npm publication; its existing version/lock are unchanged.

The native builder copies the root license, notices, third-party table and the complete `docs` tree into each platform payload, retaining embedded vendor/dependency licenses. All payload files are then manifested. Source checkouts include these documents; source archives must retain them. The builder refuses packaging while `publicDistributionCleared` is false. No platform artifact is approved by this document: see VERIFICATION.md for subsequent native package results; previous failures remain preserved.

## Choice: Apache-2.0 versus MIT

Both licenses permit forks, modification, commercial use and redistribution, with notices retained. Neither is limited to an operating system, and neither solves missing provenance. MIT has fewer conditions. Apache adds explicit contributor patent terms, contribution rules and preservation of applicable NOTICE information. Apache was selected for the defined ChromaNeural work because those explicit terms aid a multi-contributor network client and fit the existing Apache-licensed SDK/model alongside MIT/BSD dependencies. The additional notice handling is addressed by the manifest and packaging. No new PRISME grant follows from choosing it. There is no simultaneous MIT main license.

Authoritative license texts: https://www.apache.org/licenses/LICENSE-2.0 and https://opensource.org/license/mit .
