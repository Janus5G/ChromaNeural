# RC5 verification boundaries

The application baseline is commit `3296f174cd003d084711f149dd4c113d2abf630b`. `packaging/rc4-application.json` binds the unchanged client and scripts byte-for-byte. Historical provider, WorkQueue, ChromaSpeechAI and MCP evidence is reused only for those unchanged bytes. In particular, the real-model MCP baseline used Ollama `qwen3:4b-instruct` with structured tool calls; it does not certify every model.

RC5 documentation is newly authored in English and Danish. Twelve fresh actual GUI captures, clean account state and their visual review are bound by [the screenshot manifest](docs/SCREENSHOT_MANIFEST.json). They do not prove live network admission or package lifecycle.

The new Inno installer requires its own install/startup/reinstall/uninstall checks. `packaging/rc5_smoke.py` runs these against the actual executable using isolated state and keeps the true result in `dist/RC5_PACKAGE_ACCEPTANCE.json`. Windows search UI and manual wizard review remain owner checks. Linux package extraction/startup is a separate native gate. Neither a source hash nor Windows success implies Linux success.

[GitHub Actions run 38047651276](https://github.com/Janus5G/ChromaNeural/actions/runs/38047651276) passed Windows and Linux clean builds and package acceptance at `0f7a69414556a5be2f46327e36f9740ab6f59a99`. Windows installed-client startup, reinstall and uninstall passed; Linux extracted Tk startup passed on Ubuntu 24.04. Exact unsigned CI EXE hash retrieval remains NOT VERIFIED locally after transport timeouts; the artifact-container digest is not the EXE hash.

Separate SignPath TEST signing is PASS according to owner-provided signature/certificate/hash evidence, not a rerun of the skipped CI signing job. The reported Windows `UnknownError` is attributed to the self-signed untrusted root for that specific test; public trust is not applicable. Integrated CI signing is BLOCKED because the Trusted Build System is unavailable. Foundation/production signing remains BLOCKED pending the external SignPath response. See [signing gates](docs/SIGNING.md) and [release notes](RELEASE_NOTES.md). No local unsigned or self-signed TEST installer is a trusted production-signed release.

Private II end-to-end, live node admission/migration and LAN Build05/main health compatibility are NOT VERIFIED. No optical/GPU performance, AI correctness or earnings are inferred from software tests. Remote execution remains disabled. Historical RC4 source and evidence remain preserved outside the RC5 release inputs.
