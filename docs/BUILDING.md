# RC5 clean candidate builds

Only Windows x64 and Linux amd64 are release targets. Application source is bound to the working RC4 baseline; packaging and documentation are a separate RC5 generation.

Run `python -B packaging/validate_rc5.py` in a clean checkout, then `python -B packaging/build.py` and `python -B packaging/rc5_smoke.py` on Windows, or `xvfb-run -a /usr/bin/python3 -B packaging/rc5_smoke.py` on Linux. The native builder retains the existing explicit hash-bound input allowlist, locked SDK/models and private-state rejection. It never copies developer HOME/state. Unknown source files fail closed. Build output must not exist before a fresh build.

Windows requires Python 3.14/Tk/py/pyw, Node.js 24 and the verified Inno Setup 7.1.0 compiler. Set `CHROMA_ISCC` to its ISCC.exe. The workflow downloads the official hash-bound tool, validates its Authenticode publisher and installs it into the runner's temporary directory. The compiler uses an explicit file list derived from the verified payload manifest, not an arbitrary directory wildcard. Linux retains the existing DEB builder.

Inno manages per-user program files, Start Menu and uninstall registration. It does not start the app, create a desktop shortcut, import profiles, delete separate user state, or install prerequisites. Same-version reinstall is supported; numeric downgrade is rejected. Old RC4 installation directories remain separate.

The manually dispatched GitHub workflow uses read-only repository permissions and pinned actions. No Actions run, push, signing request or public release has been performed by local preparation. [Signing setup and external blockers](SIGNING.md). Controlled inputs aid reproducibility; cross-run binary byte identity is NOT VERIFIED.

[English installation](en/installation.md) · [Dansk installation](da/installation.md)
