# ChromaNeural

[English](ChromaNeural-Installation.md) · [Dansk](../da/ChromaNeural-Installation-DA.md) · [Deutsch](../de/ChromaNeural-Installation.md) · [Français](../fr/ChromaNeural-Installation.md) · [日本語](../ja/ChromaNeural-Installation.md) · [简体中文](../zh-CN/ChromaNeural-Installation.md) · [हिन्दी](../hi-IN/ChromaNeural-Installation.md)
## Installation

ChromaNeural 0.2.21-rc.2 documentation | Unreleased candidate | 3 October 2026

**rc.2 documentation status:** This candidate has not been publicly released. Localization and extensible i18n passed local verification; rc.2 native package/build acceptance is still pending. Installation, platform, LAN/WAN, inference and live-service evidence below is historical rc.1 evidence unless explicitly labelled rc.2. Links to rc.1 downloads do not provide rc.2 localization.

## Historical rc.1 installation reference

There is no public rc.2 package to install yet. The filenames and commands below intentionally remain rc.1 examples. They do not install the language selector or registry. For an already prepared local rc.2 candidate, --language selects a launch-only locale; Windows accepts -Language. GUI selection persists the choice. Do not rename an rc.1 package or substitute an unverified rc.2 download URL.

## Before installation

Download packages from the official release:

../../RELEASE_NOTES.md

Choose the exact platform and architecture. Packages are unsigned; macOS is not notarized. Your OS may warn or block opening. Do not disable security protections globally. Check the origin and checksum before deciding to open a package.

- Windows x64: ChromaNeural-0.2.21-rc.1-windows-x64.exe
- Linux amd64: chromaneural_0.2.21.rc.1_amd64.deb
- macOS Intel x86_64: ChromaNeural-0.2.21-rc.1-macos-x86_64.zip
- Source snapshot: ChromaNeural-0.2.21-rc.1-source.zip
- Checksums: SHA256SUMS.txt

GitHub normalised the DEB download name from ~rc.1 to .rc.1. Bytes and SHA-256 are unchanged; the internal Debian version still uses ~rc.1.

### Check SHA-256

Run the appropriate command in the directory containing your downloaded package.

Windows PowerShell:
```
Get-FileHash -Algorithm SHA256 -LiteralPath '.\ChromaNeural-0.2.21-rc.1-windows-x64.exe'
```

Linux:
```
sha256sum chromaneural_0.2.21.rc.1_amd64.deb
```

macOS:
```
shasum -a 256 ChromaNeural-0.2.21-rc.1-macos-x86_64.zip
```

Compare all 64 characters with the line for that exact filename in SHA256SUMS.txt. Stop if they differ. A checksum verifies byte integrity, not independently the publisher's identity. All five published hashes are also in docs/DOWNLOADS.md.

<!-- page -->
## Windows x64

### Prerequisites

Install Python 3.14 with Tk and the py/pyw launchers, plus Node.js 24. The EXE is an offline per-user installer, not a complete frozen Python/Node runtime. Allow approximately 2 GB free space for temporary extraction and installation.

### Steps

1. Verify the downloaded EXE as described on the previous page.
2. Open it and confirm installation after reviewing OS warnings.
3. Program files are installed into this versioned directory:
```
%LOCALAPPDATA%\Programs\ChromaNeural\0.2.21-rc.1
```
4. Start Start-ChromaNeural.ps1 from that directory. PowerShell example:
```
& "$env:LOCALAPPDATA\Programs\ChromaNeural\0.2.21-rc.1\Start-ChromaNeural.ps1"
```
5. Save resource preferences at first start. Use Login & connection for an optional public API check.

The installer log is %TEMP%\ChromaNeural-install.log. Existing destinations are rejected; this is not an automatic in-place upgrader. No automatic participation or OS startup registration occurs. This RC does not automatically create a desktop shortcut.

The ICP SDK and locked runtime dependencies are included. Do not run npm ci as an installation requirement or set NODE_PATH to an old development environment.

### Removal and user state

Exit the client completely. Removing only the versioned installation directory removes program files. Client state under %LOCALAPPDATA%\ChromaNeural\client, selected workspaces and separate identity directories must be retained or handled separately by your explicit choice. No automatic uninstaller is included.

<!-- page -->
## Linux amd64

The native verification profile is Ubuntu 24.04 amd64. This is not acceptance for every distribution or version. WSL is not counted as a substitute for native Linux package verification.

The package requires Python 3.11+, Tk, distribution cryptography, Node.js 20+ and libgomp1. Use your distribution's package manager for dependencies. From the download directory:
```
sudo apt install ./chromaneural_0.2.21.rc.1_amd64.deb
```

Start from the application menu or:
```
chromaneural
```

Program files are under /opt/chromaneural, the launcher is /usr/bin/chromaneural, and desktop metadata is /usr/share/applications/chromaneural.desktop. There is no post-install npm network download or automatic user-state migration.

Native build, extraction, integrity, SDK, CLI and Xvfb/Tk are verified. The full dpkg install/remove lifecycle is not yet verified. The published desktop entry lacks a product-specific icon reference; launching remains available.

## macOS Intel x86_64

Requires macOS 15+, Python 3.14 with working Tk, and Node.js 24. Use the same Python installation for pinned crypto dependencies. From the accepted source snapshot's root:
```
python3 -m pip install --require-hashes -r packaging/requirements-runtime.txt
```

The locked set is cryptography 46.0.5, cffi 2.1.1 and pycparser 3.0. These are runtime prerequisites, not a request for II credentials.

Extract the ZIP, move ChromaNeural.app to Applications, and open it after checking origin and OS warnings. The package is Intel-only; Universal 2, Apple Silicon and Rosetta are not accepted profiles in this release.

Native build, integrity, SDK, CLI and Tk are verified. Manual macOS GUI is not verified. The package is unsigned, not notarized and lacks a product-specific bundle icon. There is no bundled Qwen/llama.cpp runtime on macOS. The explicit local Ollama adapter requires your separately installed model; controlled background contribution is unsupported.

<!-- page -->
## First start and follow-up

![Resource settings in the actual Windows client. Window decorations can differ by platform.](../images/chroma-neural-resources.png)

Select preferences and save. Overview shows confirmed figures only; a dash is not an earnings promise. General resource sharing remains disabled. Use **Afslut ChromaNeural** (Exit ChromaNeural) to close completely.

If startup fails, check the documented prerequisites and the correct package/architecture first. Preserve existing state. Do not reset identities or post private data in issue reports. See the User Guide and Privacy and Storage guide.

Installation does not change Internet Identity, the production backend or your browser session. Public API reachability was verified on Windows. Actual live II end-to-end, live admission and live migration remain unverified.

Official Android and iOS support is deferred to a later time.

Current online documentation may be newer than text inside the immutable RC binaries and source ZIP. Release files are not replaced merely to update documentation or icons. See docs/BRANDING.md for current icon status.

MCP remains a separately gated post-rc.2 feature and is not implemented here. No new production or Internet Identity change is implied by this documentation.
