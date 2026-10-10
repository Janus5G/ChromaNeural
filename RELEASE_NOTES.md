# ChromaNeural 0.2.21-rc.5

NOT VERIFIED as a release candidate. Not published.

RC5 preserves the RC4 application baseline and replaces the Windows container with Inno Setup. Release documentation is newly authored in English and Danish with fresh actual GUI captures. All seven application locales remain. Windows x64 and Linux amd64 are the release targets.

Clean builds, installer lifecycle, screenshots, signing and manual acceptance are separate gates. A self-signed SignPath test artifact is not trusted production signing. Production signing and GitHub-native execution remain BLOCKED pending external configuration/authorization.

ChromaSpeechAI remains node-to-node; MCP remains optional node-to-tool; REMOTE_EXECUTION=DISABLED. No Internet Identity, Caffeine, backend or application behavior change is included. [Limitations](KNOWN_LIMITATIONS.md) · [Signing](docs/SIGNING.md).
