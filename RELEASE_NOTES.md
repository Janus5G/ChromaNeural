# ChromaNeural 0.2.21-rc.5

NOT VERIFIED as a release candidate. Not published.

RC5 preserves the RC4 application baseline and replaces the Windows container with Inno Setup. Release documentation is newly authored in English and Danish with fresh actual GUI captures. All seven application locales remain. Windows x64 and Linux amd64 are the release targets.

Clean builds, installer lifecycle, screenshots, signing and manual acceptance are separate gates. Windows and Linux clean GitHub-hosted builds and package acceptance passed in [GitHub Actions run 38047651276](https://github.com/Janus5G/ChromaNeural/actions/runs/38047651276) at commit `0f7a69414556a5be2f46327e36f9740ab6f59a99`. Windows acceptance covered isolated install/startup/reinstall/uninstall; Linux acceptance included actual extracted Tk startup on Ubuntu 24.04.

Separate SignPath TEST signing, signature presence, expected test certificate and signed-artifact hash correlation passed according to owner-provided evidence. A self-signed TEST artifact is not trusted production signing. Integrated CI signing remains BLOCKED because the Trusted Build System is unavailable. Foundation/production signing is BLOCKED pending the external SignPath response. Final owner acceptance remains pending; no public RC5 release is authorized by these results.

ChromaSpeechAI remains node-to-node; MCP remains optional node-to-tool; REMOTE_EXECUTION=DISABLED. No Internet Identity, Caffeine, backend or application behavior change is included. [Limitations](KNOWN_LIMITATIONS.md) · [Signing](docs/SIGNING.md).
