# ChromaNeural package branding

Derived from the existing application prism/cube geometry and palette in `client/chroma/dashboard.py`. ChromaNeural-owned packaging artwork: Apache-2.0. The ICO is copied byte-for-byte from `client/assets/chroma.ico`; it is not a new product icon design.

Linux PNG/SVG resources are integrated into the current Windows/Linux-only package builder. The macOS ICNS is a retained historical asset with no active build target. Historical 0.2.21-rc.1 assets remain unchanged outside this RC5 acceptance scope. These resources do not establish new native GUI acceptance.

The RC5 Inno Setup installer uses `packaging/branding/ChromaNeural.ico` and creates a Start Menu shortcut using the installed client icon. It creates no desktop shortcut. The former IExpress installer is historical and is not the RC5 installer.

See `docs/BRANDING.md` for current-versus-prepared status. No runtime, dependency, identity or storage behaviour changes.
