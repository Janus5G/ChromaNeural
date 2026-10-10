# Privacy and local state

[Dansk](../da/privacy.md) · [Guide](guide.md)

The client, browser identity and approved peer/tool services are separate trust boundaries. A copied API profile is connection metadata, not a browser login or proof of ownership. User-specific connection metadata remains private release data even without a password.

Windows state normally resides in `%LOCALAPPDATA%\ChromaNeural\client`. Linux uses `${XDG_STATE_HOME:-$HOME/.local/state}/chroma-neural/client`. An explicit `--state-dir` takes precedence over `CHROMA_STATE_DIR`. Preferences, saved language, API profiles, accounting cache, queue and logs belong to user state, never to release inputs.

The release starts without a profile. State can be saved after explicit user action; reinstalling program files does not delete existing state. Workspaces and node identities may use separately selected locations. Back up only after closing the client, and protect keys, databases and logs with your OS account/disk controls. Encryption at rest and network anonymity are not promised.

MCP configuration stores only non-secret settings beside preferences. An optional bearer token is held for the current session, bound to the exact connection target; changing target invalidates the association. Never put secrets in names, URLs, executable arguments, prompts or screenshots. Only approved/enabled tools are offered to an explicitly consenting task. External tool results may be malicious or incorrect.

ChromaSpeechAI peer disclosure and global publication require their own approvals. A selected directory is not sharing consent. Internet Identity remains in the browser. The informational Private II storage view is not a native private-file channel. See [security reporting](../../SECURITY.md) and [limits](../../KNOWN_LIMITATIONS.md).
