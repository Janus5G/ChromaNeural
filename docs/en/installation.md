# Install the RC5 candidate

[Dansk](../da/installation.md) · [Guide](guide.md)

RC5 is not published. Use only the exact candidate supplied for manual acceptance and its accompanying SHA256SUMS. Do not substitute a withdrawn RC4 package. Public release requires separate owner approval and production-signing review.

## Windows x64

Install Python 3.14 or newer with Tk and the py/pyw launchers, and Node.js 24 or newer. The installer does not download prerequisites, models or user state.

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\ChromaNeural-0.2.21-rc.5-windows-x64.exe'
Get-AuthenticodeSignature -LiteralPath '.\ChromaNeural-0.2.21-rc.5-windows-x64.exe'
```

Compare the entire hash. Unsigned/local and self-signed test builds are not trusted public-signing builds. Do not disable Windows security protections.

Run the graphical Inno Setup installer. The default per-user directory is `%LOCALAPPDATA%\Programs\ChromaNeural\App`. It adds **ChromaNeural** to the Start Menu and Installed Apps. It creates no desktop shortcut, does not launch the client automatically and does not import an existing account. Launch it yourself from the Start Menu.

A reinstall of the same Inno-managed version replaces its program files. A later Inno-managed version uses the same installation identity/directory; downgrade is rejected. The earlier versioned RC4 installation is not silently removed or migrated. Close the client before install/update/removal. User state is separate and survives uninstall; existing user state is not evidence of package contamination. For first-launch acceptance use an isolated empty `--state-dir`.

Uninstall from Windows **Installed Apps**. The installer removes its registered program files and Start Menu shortcut, preserving user data/workspaces. An arbitrary file you put into the program directory is not an installer-owned file. Installer diagnostics use Inno Setup logging; a manual explicit log can be requested with `/LOG="<chosen-log-file>"`.

## Linux amd64

Use the native Ubuntu 24.04 amd64 acceptance profile. Dependencies: Python 3.11+ (including Python 3.12 compatibility), Tk, distribution cryptography, Node.js 20+ and libgomp1.

```sh
sha256sum chromaneural_0.2.21.rc.5_amd64.deb
sudo apt install ./chromaneural_0.2.21.rc.5_amd64.deb
chromaneural
```

The existing package layout is `/opt/chromaneural`, `/usr/bin/chromaneural` and the desktop entry under `/usr/share/applications`. Removal uses the distribution package manager and must not be confused with deletion of separate user data.

## Clean first launch

Open Resources, leave contribution off, save, then open Login & connection. The editor must be empty and no profile/account identity should be loaded. Do not insert personal connection data in release acceptance. Review the English and Danish GUI separately using the language selector. Actual RC5 install/startup/uninstall/signing results are recorded in [release status](../../RELEASE_NOTES.md); prior RC4 acceptance does not certify a new installer.
