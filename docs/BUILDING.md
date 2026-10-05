# Native builds

Use a clean checkout on the target OS. The workflow pins Actions by full commit SHA and requests Windows 2025 x64, Ubuntu 24.04 amd64 and macOS 15 Intel. Official runner reference: https://docs.github.com/en/actions/reference/runners/github-hosted-runners

Run `python packaging/build.py`, then `python packaging/smoke.py` with the documented platform prerequisites. Existing output is preserved; use a fresh checkout for a new build. `assets.lock.json` contains exact accepted model/runtime hashes. A supplied `--asset-cache` may avoid redownloading but every byte stream is still hash checked. SDK packaging uses the unchanged npm lock. No private II credentials or production network calls are used.

Windows uses the native OS IExpress packaging tool around the existing verified PowerShell installer. Linux uses dpkg-deb. macOS uses plistlib/plutil and ditto to produce an Intel .app ZIP. No signing identity, notarization or cloud release permission is requested.

Native Windows x64, Ubuntu 24.04 amd64 and macOS 15 Intel execution passed for the selected artifacts. See ../VERIFICATION.md and ../NATIVE_BUILD_EVIDENCE.json for exact commits/jobs and scope. The final source archive adds reviewed documentation only; accepted native artifacts are preserved, not rebuilt. Future workflow runs still require their own successful evidence.
