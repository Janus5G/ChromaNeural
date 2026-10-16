# Install RC6 on Linux

[Dansk](../da/installation.md) · [Guide](guide.md)

**Official release: Linux amd64.** Source code remains available for community ports and experimentation on other platforms. Windows, macOS and mobile platforms are not currently officially supported or verified.

[RC6 prerelease / SHA256SUMS](https://github.com/Janus5G/ChromaNeural/releases/tag/v0.2.21-rc.6)

## Linux amd64

Use the native Ubuntu 24.04 amd64 acceptance profile. Dependencies: Python 3.11+ (including Python 3.12 compatibility), Tk, distribution cryptography, Node.js 20+ and libgomp1.

```sh
sha256sum chromaneural_0.2.21.rc.6_amd64.deb
sudo apt install ./chromaneural_0.2.21.rc.6_amd64.deb
chromaneural
```

The existing package layout is `/opt/chromaneural`, `/usr/bin/chromaneural` and the desktop entry under `/usr/share/applications`. Removal uses the distribution package manager and must not be confused with deletion of separate user data.

## Clean first launch

Open Resources, leave contribution off, save, then open Login & connection. The editor must be empty and no profile/account identity should be loaded. Do not insert personal connection data in release acceptance. Review the English and Danish GUI separately using the language selector. Linux package verification and hashes are recorded in [release status](../../RELEASE_NOTES.md).
