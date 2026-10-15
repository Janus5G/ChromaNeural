# RC5 verification boundaries

Official release: Linux amd64 only. Documentation and screenshot owner acceptance: PASS. Guided AI/MCP wizard human acceptance: PASS — functional baseline accepted. The existing focused evidence is 24 distinct wizard tests; unchanged backend gates remain closed. Vendor catalog connections are not end-to-end verified.

The final Linux build performs fresh package/hash/privacy/source-inclusion and native offline Tk startup checks. The published release description identifies its exact successful CI run. Historical Windows/signing work below is not a current release dependency.

The application baseline is commit `3296f174cd003d084711f149dd4c113d2abf630b`. `packaging/rc4-application.json` preserves the historical client/scripts baseline; `packaging/rc5-wizard-acceptance.json` binds the four accepted wizard/runtime-localization changes, while all other client/scripts hashes must still match. Historical provider, WorkQueue, ChromaSpeechAI and MCP evidence is reused only for those unchanged bytes. In particular, the real-model MCP baseline used Ollama `qwen3:4b-instruct` with structured tool calls; it does not certify every model.

RC5 documentation is newly authored in English and Danish. Twelve accepted actual GUI captures, clean account state and their visual review are bound by [the screenshot manifest](docs/SCREENSHOT_MANIFEST.json). They do not prove live network admission or package lifecycle.

## Historical Windows evidence

The former Inno installer required its own install/startup/reinstall/uninstall checks. `packaging/rc5_smoke.py` runs these against the actual executable using isolated state and keeps the true result in `dist/RC5_PACKAGE_ACCEPTANCE.json`. The new guided wizard functional baseline is now owner-accepted; the older installer evidence below remains historical. Linux package extraction/startup is a separate native gate. Neither a source hash nor Windows success implies Linux success.

[GitHub Actions run 38047651276](https://github.com/Janus5G/ChromaNeural/actions/runs/38047651276) passed Windows and Linux clean builds and package acceptance at `0f7a69414556a5be2f46327e36f9740ab6f59a99`. Windows installed-client startup, reinstall and uninstall passed; Linux extracted Tk startup passed on Ubuntu 24.04. Exact unsigned CI EXE hash retrieval remains NOT VERIFIED locally after transport timeouts; the artifact-container digest is not the EXE hash.

Separate SignPath TEST signing is PASS according to owner-provided signature/certificate/hash evidence, not a rerun of the skipped CI signing job. The reported Windows `UnknownError` is attributed to the self-signed untrusted root for that specific test; public trust is not applicable. Integrated CI signing is BLOCKED because the Trusted Build System is unavailable. Foundation/production signing remains BLOCKED pending the external SignPath response. See [signing gates](docs/SIGNING.md) and [release notes](RELEASE_NOTES.md). No local unsigned or self-signed TEST installer is a trusted production-signed release.

Private II end-to-end, live node admission/migration and LAN Build05/main health compatibility are NOT VERIFIED. No optical/GPU performance, AI correctness or earnings are inferred from software tests. Remote execution remains disabled. Historical RC4 source and evidence remain preserved outside the RC5 release inputs.
