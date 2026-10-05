# ChromaNeural branding and package icons

The product name is **ChromaNeural**. `0.2.21-rc.1` is its version; Release Candidate / Prerelease is its status, not part of a replacement product name.

## Published 0.2.21-rc.1 packages

| Surface | Actual status |
|---|---|
| Windows application window | Existing `client/assets/chroma.ico` is used by the unchanged Tk client. Confirmed in the actual screenshots. |
| Windows installer EXE | IExpress/default executable branding; a product-specific EXE resource icon is not configured. |
| Windows shortcuts | No shortcut is automatically created by this release. A manually created shortcut can select the existing installed `client/assets/chroma.ico`. |
| Linux application menu | The published desktop entry has no Icon field and installs no application-menu icon. |
| Linux application window | No platform-specific window-icon setup is implemented in the accepted client. |
| macOS app bundle | The published bundle has no CFBundleIconFile / product ICNS. |
| macOS application window | Manual GUI appearance is NOT VERIFIED. |

The accepted tag and five published assets are immutable in this presentation update. No binary was silently replaced and no new native-build acceptance is claimed.

## Prepared packaging assets

`packaging/branding/` supplies Linux PNG/SVG and macOS ICNS assets derived from the client's existing prism geometry, plus the existing ICO copied byte-for-byte. The native package builder now includes the Linux hicolor PNG/SVG with an Icon field and the macOS ICNS with CFBundleIconFile for a future versioned build. These metadata-only paths are locally checked. The accepted workflow and runtime code are unchanged. Windows EXE/shortcut branding still requires a later packaging decision and extraction validation.

A native rebuild and package-specific validation are needed before claiming those launcher/installer changes in downloadable apps. Current icons therefore remain a documented presentation limitation, not a completed product fix.

## Public artwork

`docs/images/chroma-neural-hero.png` is the README header. `docs/images/chroma-neural-social-preview.png` is a 1200 × 630 social-preview image prepared for repository settings. Both use the fixed product name, existing client palette and prism mark. No Android/iOS or hardware-performance claims are included.
