# ChromaNeural 0.2.21-rc.6

Linux amd64 prerelease. RC5 is preserved unchanged.

This candidate includes the current tested local REA/MCP integration and resource-based Fair Use V2 infrastructure. Fair Use is resource-based, not one point per tool call. Existing local AI discovery, guided optional-tool setup, connection/tool approval and untrusted-result boundaries are preserved.

## Production status

- Production accounting: **NOT TESTED — disabled**.
- Production resource measurement: **NOT TESTED — disabled**.
- Numeric settlement GUI: **NOT TESTED — disabled**.

The end-to-end production adapters and numeric settlement display are not connected. Controlled MCP execution therefore remains paused; this is a deliberate safe default, not a failed production test. Setup, discovery and approvals remain free. Users can explicitly continue without external tools. No live ChromaPoints, historical balance conversion or live backend changes are included. RAM×time and GPU settlement remain disabled.

## Existing software evidence

- 68 affected Python tests PASS; 1 explicit live integration test skipped.
- Local RoboForge gateway/compiler MCP protocol acceptance PASS with synthetic allowance and resource meter; production settlement is NOT TESTED.
- 10/10 new actual Linux GUI checks PASS across English and Danish, using simulated AI responses: startup, cancellation, explicit local-only continuation, proposal review/application and shutdown.
- Existing mathematical, Motoko, Linux CPU-counter, REA and wizard evidence is retained for its original scope. These suites were not rerun for this release.

The clean GitHub-hosted Linux build checks the new package bytes, documentation inclusion, privacy, extracted offline startup and final hashes. Its exact commit/run and artifact hashes appear in the GitHub release description.

## Platform and scope

Official release: **Linux amd64 only**. Source remains available for community ports. Windows, macOS and mobile platforms are not officially supported or verified. No Windows binary or signing dependency is part of RC6.

English is the default documentation language; Danish documentation is retained. Existing genuine RC5 screenshots retain their original provenance; no new screenshot campaign or production Fair Use screenshot acceptance is claimed. Withdrawn RC4 documentation/screenshots remain excluded.

OPC UA, NVIDIA Isaac Sim, Home Assistant and Siemens Xcelerator remain NOT VERIFIED end-to-end; ROS 2, MQTT / EMQX and Arduino remain EXPERIMENTAL. REA's previous local isolated tests do not enable production Fair Use or certify other vendor connections. RoboForge has no points balance or pricing system.

Remote execution remains disabled. [Resource Fair Use](docs/en/mcp-usage.md) · [Dansk](docs/da/mcp-usage.md) · [Verification](VERIFICATION.md) · [Downloads](docs/DOWNLOADS.md).
