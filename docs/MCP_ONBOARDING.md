# AI and MCP setup

[English current guide](en/guide.md#local-ai-and-optional-mcp) · [Dansk vejledning](da/guide.md#lokal-ai-og-valgfri-mcp)

ChromaSpeechAI is node-to-node; MCP is optional node-to-tool. Existing Local AI discovery and MCP backend/protocol remain unchanged. The guided first-time wizard and curated catalog are included; their functional baseline is owner-accepted. The real-model baseline used Ollama `qwen3:4b-instruct` with a structured tool call. This is not new RC5 package acceptance.

## Curated catalog scope

OPC UA, NVIDIA Isaac Sim, Home Assistant and Siemens Xcelerator: **NOT VERIFIED end-to-end**. ROS 2, MQTT / EMQX and Arduino: **EXPERIMENTAL**. Actual vendor services have not been accepted end-to-end. No profile is labelled SUPPORTED.

All profiles are disabled by default. Discovery may prefill but never approves a target. Connection approval does not approve tools. Unknown/potential control tools require separate explicit consent. Existing bounded calls are reused; the catalog does not poll, install software, scan the LAN or synchronize data. MCP is not a realtime motion/safety controller. Custom connections remain under Advanced / Developer. Access tokens remain memory-only.
