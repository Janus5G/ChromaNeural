# Native builds

Use a clean checkout on the target OS. The workflow pins Actions by full commit SHA and requests Windows 2025 x64 and Ubuntu 24.04 amd64 only. Official runner reference: https://docs.github.com/en/actions/reference/runners/github-hosted-runners

Run `python packaging/build.py`, then `python packaging/smoke.py` with the documented platform prerequisites. Existing output is preserved; use a fresh checkout for a new build. `assets.lock.json` contains exact accepted model/runtime hashes. A supplied `--asset-cache` may avoid redownloading but every byte stream is still hash checked. SDK packaging uses the unchanged npm lock. No private II credentials or production network calls are used.

Windows uses the native OS IExpress packaging tool around the existing verified PowerShell installer. Linux uses dpkg-deb. Only these two platform targets are accepted by the package builder and native workflows. No signing identity or cloud release permission is requested.

RC4 Windows x64 and Linux amd64 package acceptance and owner manual checks passed. See [verification](../VERIFICATION.md) for current scope and explicitly historical native results. The final source archive adds reviewed documentation only; accepted native artifacts are preserved, not rebuilt. Future workflow runs still require their own successful evidence.
