# ChromaNeural

[English](ChromaNeural-Overview.md) · [Dansk](../da/ChromaNeural-Overview-DA.md) · [Deutsch](../de/ChromaNeural-Overview.md) · [Français](../fr/ChromaNeural-Overview.md) · [日本語](../ja/ChromaNeural-Overview.md) · [简体中文](../zh-CN/ChromaNeural-Overview.md) · [हिन्दी](../hi-IN/ChromaNeural-Overview.md)
## Overview

ChromaNeural 0.2.21-rc.2 documentation | Unreleased candidate | 3 October 2026

**rc.2 documentation status:** This candidate has not been publicly released. Localization and extensible i18n passed local verification; rc.2 native package/build acceptance is still pending. Installation, platform, LAN/WAN, inference and live-service evidence below is historical rc.1 evidence unless explicitly labelled rc.2. Links to rc.1 downloads do not provide rc.2 localization.

### Local intelligence. Explicit collaboration.

ChromaNeural connects local AI work, a persistent work queue and communication between approved peers. You choose the input to process and which contributions may be shared. An AI answer does not become correct or verified simply because a model produced it.

The supported collaboration profile in this release is code proposals. This is not a general marketplace that automatically accepts and executes arbitrary remote jobs. The desktop does not yet have a general problem/study submission button for every task type.

![The actual Windows client with participation stopped. No private account or data is loaded.](../images/chroma-neural-overview.png)

### Language support in rc.2

The single client ships with en, da, de, fr, ja, zh-CN and hi-IN. English is the default and fallback. The sidebar selector changes application-owned text and saves the choice for the next start. The extensible registry supports future catalogues without separate clients or GUI logic. See the User Guide for preference and launch-override details.

### What you can use today

- View participation status and save resource preferences.
- Check whether the public backend API responds.
- Use the existing local AI feature to propose changes to a selected file.
- Process already approved local jobs through the background worker in the supported Windows profile.
- Use the existing advanced CLI for explicitly approved, correlated peer collaboration.

<!-- page -->
## From input to result

General resource sharing remains disabled. Installation and a successful connection check do not grant network admission, assign work or award ChromaPoints.

### 1. Input and permission

An existing job identifies its source input, instruction and selected provider/model. Local AI processing and network use require their respective approvals. Opening a folder is not permission to share it.

### 2. Queue and processing

The existing SQLite queue preserves job identity and status. A lease reserves work for a worker. Controlled pause, cancellation, stop and restart are verified within the documented Windows profile. No parallel job database is introduced.

### 3. Optional peer collaboration

Questions and replies remain linked to the original task. ChromaSpeechAI uses approved peer identities and TLS. Received content is stored in an inbox and remains inert: it is data, not permission to execute code. Source disclosure requires explicit consent.

### 4. Integrity and review

A result carries identity, hashes and origin where the existing flow provides them. Local and peer-generated contributions can be distinguished. A matching SHA-256 establishes matching bytes; it does not assess technical quality. Results remain unverified until accepted by the existing authoritative verification process.

### 5. Optional publication

Global sharing uses the existing publication flow with verification, consent, roles and backend acceptance. Private files do not automatically become Shared Network Knowledge. Publication software is locally verified; this release does not establish a working production publication service.

Direct private requester access to an authoritatively verified result before optional global sharing is deferred for this version. That capability must not be confused with reading a local, still-unverified job result.

<!-- page -->
## Privacy and trust

### Three separate areas

**Your computer:** work files, settings, queue data, results and logs. A local AI provider processes explicitly selected input locally. The application does not automatically encrypt this data at rest.

**Your browser:** the existing web application uses your Internet Identity. The actual authenticated caller determines owner access. Copied connection metadata is not a login session.

**Approved peers and shared results:** the relevant approval controls what content is sent through the supported flow. Network connections can reveal IP addresses and peer identity; ChromaNeural does not promise anonymity.

In a service that processes prompts on an external server, input must leave the user's computer. ChromaNeural's local provider path can process selected input on the computer. Choosing peer collaboration or browser storage still crosses a data boundary. The distinction is explicit control and separation, not a promise that network use never shares information.

### What is verified?

Windows client and clean installation have automated checks and human GUI acceptance. Windows, Linux amd64 and macOS Intel have native build/package checks. Actual two-computer LAN, direct cellular-to-home WAN and local model inference are documented. Tests with synthetic backend state or identity are not live Internet Identity tests.

### What remains unverified?

Actual live Internet Identity end-to-end, live admission and live migration. Manual macOS GUI and the complete Linux DEB install/remove lifecycle are also outside acceptance. Native private file upload/download through browser-owner authority is not implemented. Specialised hardware performance is not physically verified.

Packages are unsigned; macOS is not notarized. Windows, Linux and macOS are official platforms within these prerelease limits.

Official Android and iOS support is deferred to a later time.

See the User Guide, Privacy and Storage, Installation and Verified Capabilities guides for details.

MCP remains a separately gated post-rc.2 feature and is not implemented here. No new production or Internet Identity change is implied by this documentation.
