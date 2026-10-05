# Installation

RC4 is a local candidate; new package acceptance is pending. See [status](RELEASE_NOTES.md).

Use only release artifacts whose SHA-256 matches the separately published SHA256SUMS.txt. SHA-256 detects changed bytes; it does not by itself authenticate a publisher. Packages in this RC are unsigned and macOS is not notarized. Windows SmartScreen and macOS Gatekeeper may warn or prevent opening; no blanket disabling of OS protections is recommended.

## Windows x64

Requires Python 3.14 with Tk and the py/pyw launchers, plus Node.js 24. The EXE is an offline, per-user portable installer, not a frozen Python executable. It installs into `%LOCALAPPDATA%/Programs/ChromaNeural/0.2.21-rc.4`; existing destinations are rejected. After a successful installation, use the per-user **ChromaNeural** Start Menu shortcut (also available through Windows search), or start `Start-ChromaNeural.ps1` from that folder. The installer creates no desktop shortcut, does not launch the client, and finishes without a success dialog. No automatic participation or startup registration occurs. The installer log is `%TEMP%/ChromaNeural-install.log`. Allow approximately 2 GB temporary/free space during extraction.

Pinned ICP production dependencies are bundled. Do not run npm or set NODE_PATH. There is no automated in-place upgrade or uninstaller. After closing the client, remove the versioned installation directory and the per-user Start Menu shortcut `%APPDATA%\Microsoft\Windows\Start Menu\Programs\ChromaNeural.lnk` together; user state is separate and must not be removed unintentionally.

## Linux amd64

Install `chromaneural_0.2.21.rc.4_amd64.deb` using the distribution package manager (`sudo apt install ./chromaneural_0.2.21.rc.4_amd64.deb`). Dependencies: Python >=3.11, Tk, distribution cryptography, Node.js >=20 and libgomp1. Launch ChromaNeural from the application menu or `chromaneural`. The native CI profile is Ubuntu 24.04 amd64; this does not promise every Linux distribution works. No post-install network script or user-state migration is included.

## macOS Intel x86_64

Requires macOS 15+, Python 3.14 with working Tk, Node.js 24, and the pinned Python crypto packages in `packaging/requirements-runtime.txt`. Use the same Python installation for these prerequisites. Extract the ZIP and move ChromaNeural.app to Applications. This is an Intel package, not Universal 2; Apple Silicon/Rosetta is not an accepted profile. Manual macOS GUI acceptance is NOT VERIFIED.

The macOS package has no bundled Qwen/llama.cpp runtime because the existing provider does not support macOS. The existing explicit Ollama adapter remains available with a separately installed owner-selected local model, without a fallback or changed default. Controlled background contribution on macOS is unsupported and fails closed. The Linux-only compiler sandbox is not supplied for macOS.

## State and boundaries

Existing platform state conventions and explicit `--state-dir` remain unchanged. Back up your own state before changing versions. Installation does not import identities, log into Internet Identity, grant admission, publish results or award points. Private browser access uses the existing external Internet Identity flow; this release does not deploy a backend.

## Illustrated English guides

[Installation PDF](docs/pdf/ChromaNeural-Installation.pdf) · [User guide](docs/pdf/ChromaNeural-User-Guide.pdf) · [Exact state paths](docs/en/ChromaNeural-Privacy-and-Storage.md) · [Downloads and checksums](docs/DOWNLOADS.md).

GitHub normalised the DEB download filename from `~` to `.`; bytes and the internal Debian version are unchanged. The Windows EXE creates only the per-user Start Menu shortcut after successful installation. The current Linux/macOS packages lack product-specific launcher/bundle icons; see [branding status](docs/BRANDING.md).
