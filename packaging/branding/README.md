# ChromaNeural package branding

Derived from the existing application prism/cube geometry and palette in `client/chroma/dashboard.py`. ChromaNeural-owned packaging artwork: Apache-2.0. The ICO is copied byte-for-byte from `client/assets/chroma.ico`; it is not a new product icon design.

Linux PNG/SVG resources are integrated into the current Windows/Linux-only package builder. The macOS ICNS is a retained historical asset with no active build target. The published 0.2.21-rc.1 assets remain unchanged. These resources do not establish new native GUI acceptance.

Windows application-window branding already works. The existing IExpress EXE has a default shell icon and the installer creates no shortcut. An EXE resource change needs a separately versioned rebuild and extraction validation; no resource patch is applied to the accepted self-extracting EXE.

See `docs/BRANDING.md` for current-versus-prepared status. No runtime, dependency, identity or storage behaviour changes.
