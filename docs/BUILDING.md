# RC6 clean Linux builds

Official release: Linux amd64 only. Portable Windows/macOS/mobile source is not official platform support. Inno Setup and SignPath are historical Windows tooling, not active release dependencies.

The historical application/wizard baseline remains recorded. `packaging/rc6-acceptance.json` binds the tested local REA/MCP/Fair Use source changes and disabled production status to exact hashes. The validator filename is retained for compatibility; it validates the RC6 candidate. Existing passed feature suites are not rerun by the release workflow.

In a fresh Linux amd64 checkout, run:

```sh
python -B packaging/validate_rc5.py
python -B packaging/build.py
xvfb-run -a /usr/bin/python3 -B packaging/rc5_smoke.py
python -B packaging/source_archive.py
python -B packaging/finalize_candidate.py
```

Use the prerequisites and pinned tool versions in [the active workflow](../.github/workflows/native-packages.yml). Native smoke uses Ubuntu 24.04 system Python 3.12, Tk, cryptography, Node.js and libgomp1. Build directories must not already exist. The existing explicit hash-bound allowlist, locked SDK/model inputs and private-state rejection remain fail closed. Developer HOME/runtime state is never a build input.

The workflow runs on the Linux release preparation branch or manual dispatch, never automatically publishes, and uses read-only permissions and pinned actions. The package is extracted and its actual bytes, source/document inclusion and offline Tk startup are verified. Final checksums cover only the DEB and source ZIP. CI evidence is uploaded separately from the public three-file asset set. Controlled inputs aid reproducibility; cross-run byte identity is NOT VERIFIED.

Historical Windows/Linux CI and Windows signing evidence is retained in [verification](../VERIFICATION.md) and [signing history](SIGNING.md); it is not acceptance of this newly built Linux package.
