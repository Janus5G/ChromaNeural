# RC5 verification boundaries

The application baseline is commit `3296f174cd003d084711f149dd4c113d2abf630b`. `packaging/rc4-application.json` binds the unchanged client and scripts byte-for-byte. Historical provider, WorkQueue, ChromaSpeechAI and MCP evidence is reused only for those unchanged bytes. In particular, the real-model MCP baseline used Ollama `qwen3:4b-instruct` with structured tool calls; it does not certify every model.

RC5 documentation is newly authored in English and Danish. Twelve fresh actual GUI captures, clean account state and their visual review are bound by [the screenshot manifest](docs/SCREENSHOT_MANIFEST.json). They do not prove live network admission or package lifecycle.

The new Inno installer requires its own install/startup/reinstall/uninstall checks. `packaging/rc5_smoke.py` runs these against the actual executable using isolated state and keeps the true result in `dist/RC5_PACKAGE_ACCEPTANCE.json`. Windows search UI and manual wizard review remain owner checks. Linux package extraction/startup is a separate native gate. Neither a source hash nor Windows success implies Linux success.

GitHub-hosted clean builds and SignPath test signing have NOT VERIFIED execution status until an authorized workflow actually completes. Production signing is BLOCKED pending the appropriate approval/certificate. See [signing gates](docs/SIGNING.md) and [release notes](RELEASE_NOTES.md). No local unsigned installer is a production-signed release.

Private II end-to-end, live node admission/migration and LAN Build05/main health compatibility are NOT VERIFIED. No optical/GPU performance, AI correctness or earnings are inferred from software tests. Remote execution remains disabled. Historical RC4 source and evidence remain preserved outside the RC5 release inputs.
