# ChromaNeural

[English](ChromaNeural-User-Guide.md) · [Dansk](../da/ChromaNeural-User-Guide-DA.md) · [Deutsch](../de/ChromaNeural-User-Guide.md) · [Français](../fr/ChromaNeural-User-Guide.md) · [日本語](../ja/ChromaNeural-User-Guide.md) · [简体中文](../zh-CN/ChromaNeural-User-Guide.md) · [हिन्दी](../hi-IN/ChromaNeural-User-Guide.md)
## User Guide

ChromaNeural 0.2.21-rc.2 documentation | Unreleased candidate | 3 October 2026

**rc.2 documentation status:** This candidate has not been publicly released. Localization and extensible i18n passed local verification; rc.2 native package/build acceptance is still pending. Installation, platform, LAN/WAN, inference and live-service evidence below is historical rc.1 evidence unless explicitly labelled rc.2. Links to rc.1 downloads do not provide rc.2 localization.

## 1. Install and start

Download the correct platform package from the official GitHub release and compare its SHA-256 with the checksum list. Install the runtime prerequisites in the Installation guide. The locked ICP SDK is included; you do not need npm or an old development environment.

On Windows, run Start-ChromaNeural.ps1 from the versioned per-user installation folder. On Linux use the application menu or chromaneural. On macOS open ChromaNeural.app after installing its documented prerequisites. Packages are unsigned; do not disable OS security globally to open them.

First start displays resource preferences. Choose your settings and save. Saving preferences does not automatically admit the client to a production network. These examples use stopped participation without an account or private data.

![Overview after saving preferences, with participation stopped.](../images/chroma-neural-overview.png)

These preserved rc.1 screenshots are in Danish and do not show the rc.2 language selector. **Oversigt** means Overview; **Ressourcer** means Resources; **Aktivitet** means Activity; **Login & forbindelse** means Login & connection. The steps retain those historical labels with their English equivalents. The rc.2 client starts in English unless you have explicitly selected another language.

A dash means a confirmed value is unavailable. It is neither a zero balance nor estimated earnings. Use the left navigation to change pages.

## Language in the rc.2 client

One client supports English, Dansk, Deutsch, Français, 日本語, 简体中文 and हिन्दी. English is the default and fallback, independently of the OS language. Use the sidebar language selector to change application-owned labels immediately. Existing inputs, source text, connection JSON and participation state are preserved; a language change does not start another worker or network probe. OS-owned file-picker controls retain the OS language.

An explicit GUI selection saves only version and locale in `ui-language.json`, beside the existing `preferences.json`. It does not alter that file's schema or create another state root. The choice is restored at next start. Missing, invalid, oversized or unsupported language preferences fall back to English without rewriting the original. An explicit later save preserves an invalid original; a failed save keeps the current language.

The optional `--language` CLI argument overrides the language for that launch without saving the override. Windows launchers forward `-Language`. Supported locale identifiers come from `client/locale-registry.json`; the initial shipping set is `en`, `da`, `de`, `fr`, `ja`, `zh-CN`, `hi-IN`. A future language requires one catalogue with the same message keys and one registry entry containing its name and number-format metadata. The temporary eighth verification locale is not shipped.

For the rc.2 client, the corresponding labels in this guide’s language are:

| Historical screenshot label | rc.2 label in English |
|---|---|
| Oversigt | Overview |
| Ressourcer | Resources |
| Aktivitet | Activity |
| Login & forbindelse | Login & connection |
| Udviklerværktøjer  ↗ | Developer tools  ↗ |
| Afslut ChromaNeural | Exit ChromaNeural |
| Gem ændringer | Save changes |
| Gem og fortsæt | Save and continue |
| Log ind med Internet Identity | Log in with Internet Identity |
| Gem forbindelsesdata | Save connection data |
| Kontrollér forbindelse | Check connection |
| Backend svarer · offentligt API nået<br>Privat login er fortsat i browseren | Backend responding · public API reached<br>Private login remains in the browser |
| Lokal AI | Local AI |
| Privat II-lagring | Private II storage |

<!-- page -->
## 2. Resources and participation

![Actual resource preferences. CPU contribution is not enabled in this example.](../images/chroma-neural-resources.png)

1. Open **Ressourcer** (Resources).
2. Choose the maximum inference thread count and memory preference.
3. Choose whether computation is allowed only while idle and whether it pauses on battery.
4. Choose system-tray behaviour where the platform supports it.
5. Select **Gem ændringer** (Save changes), or **Gem og fortsæt** (Save and continue) at first start. Return using **Oversigt** in the sidebar.

A setting is a limit, not a reservation of hardware. The documented Windows bundled-CPU profile enforces CPU scheduling, inference threads and committed memory. Total physical RAM/RSS is not guaranteed. Controlled Ollama, Linux, macOS and GPU contribution are unsupported and must not be advertised as enforced profiles.

General resource sharing remains disabled. Starting or pausing participation does not bypass job approvals, node admission or resource controls. Installed or unused hardware does not earn points.

<!-- page -->
## 3. Login and connection

![Login and connection without a loaded profile. Browser login and API checking are separate.](../images/chroma-neural-connection.png)

1. Open **Login & forbindelse** (Login & connection).
2. **Log ind med Internet Identity** opens the existing web application in your browser. Use your own existing identity. Never share session material or recovery information.
3. Find the web application's API connection data. Copy the profile, paste it into the client and select **Gem forbindelsesdata** (Save connection data).
4. Select **Kontrollér forbindelse** (Check connection). This public API check does not transfer your private browser session to the client.
5. Success displays **Backend svarer · offentligt API nået** and **Privat login er fortsat i browseren**: the backend responds; the public API was reached; private login remains in the browser.

This success message was observed in historical rc.1 Windows acceptance. It demonstrates public API reachability, not private access, node admission or production migration. This guide does not instruct you to deploy or change a backend.

On failure, check internet access, the selected profile and the Python/Node prerequisites. Share only a redacted error description; logs can contain local paths. Do not reset identities or delete state as the first troubleshooting step.

Actual live II end-to-end remains NOT VERIFIED. Local access-guard corrections must not be assumed to be deployed to the public web application just because this client was released.

<!-- page -->
## 4. Activity, pause and exit

![Activity with a real local settings-save event.](../images/chroma-neural-activity.png)

Activity shows events recorded by the client. Use it to understand whether settings were saved or an action produced a status. An event alone does not prove verified AI quality, publication or points.

Pause and stop must be respected by the supported worker. Existing approved local jobs retain identity in the queue across controlled restart. Received peer content must remain inert.

Use **Afslut ChromaNeural** (Exit ChromaNeural) in the sidebar to close the application completely. The window close button can instead hide the client when system-tray mode is enabled and supported. Exit before backing up or moving its state.

<!-- page -->
## 5. Local AI and advanced work

The existing local AI path is under **Udviklerværktøjer** (Developer tools). Open or save the relevant local text file. Choose **Local AI**, specify the supported local provider/model and instruction, and approve the exact input. Review the proposed change before accepting and saving it. A proposal does not automatically replace your file.

Bundled CPU/Qwen is available on Windows/Linux. An installed local Ollama model is selected explicitly. macOS has no bundled Qwen runtime. There is no automatic fallback to another provider. Manual local AI is separate from the network's controlled resource profile.

Queue and peer operations are advanced CLI functions in this RC. Existing commands include queue-ai, result, task-question, task-accept, task-reply, task-collect and task-status. Use their --help and an explicitly chosen local configuration. They are not an automatic live-onboarding path.

## 6. Private files and results

Work only in folders you explicitly choose. The desktop **Private II storage** entry shows information; it does not perform private file upload/download. Browser-owner data and desktop files are not yet connected by an authorised file channel.

A local result can be reviewed as a proposal. An approved peer response is not automatically verified even when its SHA-256 matches. Global publication still requires verification, sharing consent, roles and backend acceptance. Downloading or reviewing does not award ChromaPoints.

Screenshots preserve the historical rc.1 client. The legacy 0.2.5 footer is an internal component label; the documented distribution is 0.2.21-rc.1.

MCP remains a separately gated post-rc.2 feature and is not implemented here. No new production or Internet Identity change is implied by this documentation.
