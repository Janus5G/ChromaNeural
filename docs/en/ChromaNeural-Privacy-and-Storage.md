# ChromaNeural

[English](ChromaNeural-Privacy-and-Storage.md) · [Dansk](../da/ChromaNeural-Privacy-and-Storage-DA.md) · [Deutsch](../de/ChromaNeural-Privacy-and-Storage.md) · [Français](../fr/ChromaNeural-Privacy-and-Storage.md) · [日本語](../ja/ChromaNeural-Privacy-and-Storage.md) · [简体中文](../zh-CN/ChromaNeural-Privacy-and-Storage.md) · [हिन्दी](../hi-IN/ChromaNeural-Privacy-and-Storage.md)
## Privacy and Storage

ChromaNeural 0.2.21-rc.2 documentation | Unreleased candidate | 3 October 2026

**rc.2 documentation status:** This candidate has not been publicly released. Localization and extensible i18n passed local verification; rc.2 native package/build acceptance is still pending. Installation, platform, LAN/WAN, inference and live-service evidence below is historical rc.1 evidence unless explicitly labelled rc.2. Links to rc.1 downloads do not provide rc.2 localization.

## Three data boundaries

**Local client:** work files, local jobs, settings and logs reside on your computer. You select a workspace and actions. Choosing a folder does not automatically upload it.

**Browser and Internet Identity:** private web access uses the existing application and actual authenticated caller. A Principal in JSON is an identifier, not proof of ownership authority. The node must not borrow a human's browser session.

**Peers and shared knowledge:** separately approved content can be sent to approved peers. Global publication has its own verification, consent, role and backend requirements. Private data does not automatically become Shared Network Knowledge.

This separation does not change Internet Identity, the web application's storage model or existing ownership rights. It does not imply encryption at rest or network anonymity.

### Compared with central prompt processing

When a central AI service processes a prompt on an external server, that input leaves the computer. With ChromaNeural's local inference path, selected input can be processed locally. If you choose network collaboration, approved content is still sent out. If you store private data in the web application, its existing owner model controls access.

ChromaNeural does not claim that every other AI system lacks privacy, or that local storage alone is sufficient protection. Your operating system, backups, selected provider and approved content remain relevant.

### No implicit authority transfer

The API profile contains public connection fields and may contain a Principal identifier. It is not a login token. The node has a separate identity kept at a selected local path. Node registration does not automatically grant admission. Resource preferences do not grant access to private objects.

<!-- page -->
## Where data lives

### Default client state directory

Windows:
```
%LOCALAPPDATA%\ChromaNeural\client
```

Linux and macOS:
```
${XDG_STATE_HOME:-$HOME/.local/state}/chroma-neural/client
```

This client uses the same XDG/fallback convention on macOS as on Linux, not automatically Library/Application Support. An explicit --state-dir takes precedence; otherwise CHROMA_STATE_DIR can select a different directory. Use the same state selection on later launches to continue the same local profile.

### Files in client state

- **preferences.json:** theme, participation, CPU/thread/memory, idle/battery choices and the selected node-configuration path. No II session.
- **ui-language.json (rc.2):** only version 1 and the registered locale identifier; saved on explicit GUI language selection in this same state directory. It contains no II session and does not change preferences.json. An absent/invalid/oversized/unsupported value falls back to English without destructive rewriting. An explicit later save preserves an invalid original; a failed save retains the current language. The --language launch override is not persisted.
- **api-connection-v1.json:** saved API profile. A Principal can identify a person; public metadata is not anonymous data.
- **work-queue.db:** the existing SQLite work queue and associated publication state. Jobs can contain source text, instructions, results and references. SQLite can also create -wal and -shm files during use.
- **balance-cache.json:** previously fetched accounting status. A cache does not create an authoritative points award.
- **client.log:** rotating client log, up to 1 MiB per file with three backups. Tracebacks can include local paths.

Invalid settings/profile files are preserved on read. A later explicit save can preserve a dated backup of the invalid file. Do not delete these automatically during troubleshooting.

### Other explicitly selected locations

Work files live in your selected workspace. Node configuration and identity use the directories chosen during setup; a node identity can include private_key.pem and public_key.json. Peer inboxes and advanced CLI queues use explicitly selected database paths and need not reside in the default directory above.

Never post private_key.pem, identity directories, queue databases or unredacted logs publicly. This guide does not request them.

<!-- page -->
## Private paths and files

A workspace is a local folder explicitly selected by you. A normal file path is used as an OS path, not as a transfer of ownership rights. The GUI's active workspace is session state; this flow does not provide a general recent-folder synchronisation service.

Paths can nevertheless persist elsewhere: preferences.json can reference a node configuration, and collaboration/publication data can reference an inbox. Logs can include paths. Closing a workspace window therefore does not mean every path reference has disappeared.

The existing local file adapter handles named text files. It checks filenames, symlinks/reparse points and changes between reading and writing. Saving uses a temporary file and atomic replacement with the existing integrity checks. It is not a general cloud-drive client.

These mechanisms do not encrypt local data. Protect your OS account and disk, and back up according to your needs. Close the client before copying SQLite state; an active WAL database must not be treated as one arbitrary standalone file. Moving program files does not automatically move your workspace, identity or state.

### What reaches a provider or peer?

Local AI uses the selected, approved input. The existing job model can persist input and instructions in its queue. Peer disclosure requires separate approval. If you include a private path, secret or personal data in the input text, an approved transport does not make that content harmless.

TLS protects the authenticated peer connection. It does not remove endpoint IP addresses from their networks or guarantee protection against a compromised endpoint computer.

<!-- page -->
## Browser sessions and private access

Login uses the existing web application and Internet Identity. The native client does not take over your II session. **Kontrollér forbindelse** checks the public API anonymously; success says nothing about private records or whether your browser session is valid.

The locally verified browser correction clears private cache/form state on logout and user changes, handles session expiry, and checks owner and SHA-256 before download. Backend corrections restrict anonymous private access and global audit metadata. This is local software evidence. This prerelease did not deploy those changes; actual live II end-to-end remains NOT VERIFIED.

Log out through the browser's existing user flow to end private web access. Closing the desktop or forgetting an API profile is not a browser logout and does not itself revoke grants. Existing grant/revoke operations must use their authorised interfaces; this release introduces no new grant types.

### Native private file access

The desktop **Private II storage** entry is informational. The missing authorised browser/native file channel is not implemented. The node may not write as the human owner, and a read grant may not be reinterpreted as write permission. No alternative private storage system bypasses this boundary.

### Private results and global knowledge

Local proposals and peer replies are not completed verified knowledge. Verification, sharing consent, roles and backend acceptance govern optional publication. Integrity equality alone is neither quality approval nor permission to publish.

Direct private requester-download of an authoritatively verified result before optional global sharing is deferred. This guide does not promise retrieval through an unimplemented owner channel.

### Errors and suspected disclosure

Stop the relevant action, preserve evidence privately and follow SECURITY.md. Provide a redacted description and version, not keys, session data or private databases. A SHA-256 mismatch means bytes differ; a missing file or hash is a different error and must not be described as proven tampering.

MCP remains a separately gated post-rc.2 feature and is not implemented here. No new production or Internet Identity change is implied by this documentation.
