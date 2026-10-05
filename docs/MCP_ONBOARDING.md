# AI and MCP setup - ChromaNeural 0.2.21-rc.3

MCP and integrated onboarding are VERIFIED/PASS within the scope below. Public publication is a separate final gate. The verified 0.2.21-rc.2 pre-MCP baseline remains independently preserved; its documentation/PDFs are unchanged. This focused supplement describes rc.3. See [release notes](../RELEASE_NOTES.md) for the accepted version, source and platform limits.

**ChromaSpeechAI is node-to-node. MCP is node-to-tool.** MCP does not replace the peer protocol, queue, results or publication. ChromaNeural starts and performs ordinary local work without MCP.

## Local AI

Open **AI & tools setup** from the dashboard overview or Studio. Choose **Discover local AI**. Discovery checks the bundled runtime/model at its known application paths and the existing supported Ollama endpoint, 127.0.0.1:11434. It does not scan arbitrary ports, install software, download models, start services or change external settings.

Select a discovered provider/model and **Use selection**. **Test connection** asks consent before harmless inference through the existing adapter. An empty list means no supported provider is available; nothing is installed automatically. Studio uses the saved selection as its default and still permits explicit model choice. Existing queued jobs retain their approved provider.

The bundled CPU adapter is unchanged and does not call MCP tools. MCP-enabled Studio tasks require an explicitly selected Ollama model supporting Ollama's chat tool API. No silent provider/model fallback occurs.

## MCP connections

A website is not automatically MCP-enabled. Use its MCP server, or an installed MCP adapter exposing the service/API.

1. **Add** a connection and a descriptive name.
2. Choose **Remote service** and enter the HTTPS MCP endpoint, without credentials, query parameters or fragments. Plain HTTP is permitted only for literal loopback addresses.
3. Alternatively, choose **Local process** and an absolute path to a trusted installed executable, with arguments as a JSON list. Shells and package installers are rejected. ChromaNeural does not install servers. Local processes run with your user-account permissions; this is not an OS sandbox.
4. Save. The connection is configured, unapproved and disabled.
5. **Approve connection** after reviewing the exact target. This permits an explicit test/discovery only. Testing a local stdio server launches that approved executable.
6. **Test connection**, then select individual tools and inspect their descriptions/schemas. **Approve selected tools**, then **Enable**. New or changed tool definitions need new approval. Server annotations do not establish trust.

Connections open for bounded operations and then close. “Connection test passed” describes the completed test, not a permanently open connection. Resources are discovered for inspection; automatic resource reads, sampling, roots, elicitation and arbitrary shell authority are not granted.

## Tool use

Studio requests separate consent for the named enabled connections on each task. Only individually approved tools with unchanged definitions are offered.

Task → local Ollama AI → approved MCP tool → external result → local AI → source proposal. The source still requires the existing review/apply step. Tool results are untrusted data, not peer messages or execution authority. Existing WorkQueue/peer jobs do not implicitly acquire tool access.

Limits: four servers, sixteen offered tools, four calls per task, the existing provider deadline (normally 90 seconds), and bounded discovery/argument/result/context sizes. Tool failures return sanitized error data. No automatic code execution or publication occurs. Malicious or inaccurate tool content remains possible; approve tools carefully and review results.

## Credentials, persistence and revocation

Only non-secret configuration is stored in ai-tools.json beside existing preferences.json. The existing preferences schema and language registry are unchanged. Invalid configuration fails closed without replacing the original.

An optional bearer token is entered in a masked field and held only for this application session. It is bound to the exact connection ID, transport, endpoint, executable and arguments. A different identity cannot reuse it. Editing a connection clears the session association and revokes approvals; the token field is never pre-filled. Credentials go to the worker through its private input pipe, not command arguments or logs, and are sent only to HTTPS endpoints.

No persistent credential store or OAuth/browser authorization flow is added. Unknown authorization-server settings are rejected, never ignored. Services requiring those flows need a separately reviewed integration. Do not put secrets in names, URLs, executable arguments or source files. No browser, Internet Identity or ambient service credentials are reused.

**Disable** blocks subsequent tool calls. **Revoke** clears approvals and the session token. **Remove** removes the configuration and token. Current approval and the tool definition are checked before calls. Revocation cannot undo an operation already sent to an external service.

## Troubleshooting and packaging

- No local AI: confirm an existing supported runtime/model is available. Discovery never starts or installs it.
- Connection failure: check the approved endpoint or absolute executable and JSON argument list.
- No available tools: test, select and approve the tools, then enable the connection.
- Changed definition: inspect and approve again.
- Authentication failure: enter a fresh session token for that exact HTTPS target.
- Missing SDK: MCP fails cleanly; normal no-MCP operation remains independent.

The official Python SDK is mcp 2.3.0 (MIT), supporting protocol 2026-07-28 and negotiated earlier servers over stdio and Streamable HTTP. Exact dependencies/hashes are in packaging/requirements-mcp.txt and [MCP_DEPENDENCIES.json](MCP_DEPENDENCIES.json). Build-time staging retains wheel license files and cryptography 46.0.5. Nothing is installed at application startup.

## Verified scope

Native MCP runtime acceptance on Windows x64, Linux amd64 and macOS Intel,
trust controls, credential-target binding and GUI startup: VERIFIED/PASS.
Final native installer/package acceptance also passed, reusing closed gates.

Real-model acceptance on NODE_A: VERIFIED/PASS using actual
`qwen3:4b-instruct` on Ollama 0.35.1. The real model emitted a structured
tool call for one approved controlled MCP `fetch_record` tool. Dispatch
occurred, the exact tool result was inserted unchanged into the next real-model
request, and the final answer used that result exactly. Ordinary inference
with MCP disabled or unavailable/unselected passed. Evidence archive SHA-256:
`3abc9a5d219590749b79b0ee76e0ac9373d699643ecd612eb2c9692987c43a50`.

This is real-model evidence, not only a mocked provider contract test.
It does not certify every model or service: a model must support structured
Ollama chat tool calls. JSON text imitating a tool call is not supported.
`qwen2.5-coder:0.5b` did not satisfy that structured-call requirement in the
tested path. No content-JSON parsing fallback was added.

MCP remains optional. ChromaNeural's ordinary task/provider operation,
WorkQueue and ChromaSpeechAI do not depend on MCP. No live backend,
Internet Identity, Caffeine or production storage change accompanies rc.3.
