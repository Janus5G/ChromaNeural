# ChromaNeural 0.2.21-rc.5

PUBLISHED PRERELEASE — Linux amd64 official distribution.

**Official release: Linux amd64.** Source code remains available for community ports and experimentation on other platforms. Windows, macOS and mobile platforms are not currently officially supported or verified.

Windows binary distribution is no longer part of the official release. SignPath, Authenticode and Inno Setup are not dependencies of this Linux release. Historical Windows/signing evidence remains [historical](docs/SIGNING.md).

The guided AI/MCP setup is included; its functional baseline has been manually accepted by Janus. Existing Local AI discovery is preserved. MCP is optional and can be skipped completely. Connection approval and individual tool approval remain separate; session tokens remain memory-only. The curated catalog does not certify vendor interoperability:

- OPC UA, NVIDIA Isaac Sim, Home Assistant and Siemens Xcelerator: **NOT VERIFIED end-to-end**.
- ROS 2, MQTT / EMQX and Arduino: **EXPERIMENTAL**.

All profiles are disabled by default. Discovery is not approval. Potential write/control capabilities require separate explicit consent; MCP is not a realtime machine safety/control loop. No live vendor connection acceptance is claimed.

English is the default documentation language; Danish documentation and accepted language-matched captures are retained. All seven application UI languages remain available. Withdrawn RC4 documentation/screenshots are excluded.

The Linux-only workflow builds the DEB and curated source ZIP from a clean checkout, verifies package startup, release inputs, privacy and hashes. The release description identifies the exact build commit and successful CI run for its attached files. SHA256SUMS.txt covers the final DEB and source ZIP only.

ChromaSpeechAI remains node-to-node; MCP remains optional node-to-tool; REMOTE_EXECUTION=DISABLED. No Internet Identity, Caffeine, backend or network architecture change is included. [Scope and known limits](KNOWN_LIMITATIONS.md) · [Verification](VERIFICATION.md).
