# LAN/WAN API contract

LAN/WAN API CONTRACT = NOT VERIFIED / DEFERRED.

The separate ChromaNeural-LAN-Mesh-Build05 archive is owner-verified with SHA-256 `CC8FC7AF834D754712BCB79F622045175C76E26E8C0D6E10EFDA75F9C59DE0C9`; static verification and 83 protocol assertions are accepted as supplied evidence, not rerun here.

The main RC4 client has outbound ICP SDK calls and ChromaSpeechAI peer transport, not an existing authenticated HTTPS `/api/health` service. The checked client/scripts and backend Candid interface expose no suitable HTTP server/health route. Adding an Internet-facing gateway or Caffeine HTTP/auth surface would exceed this release's narrow compatibility boundary. No endpoint or protocol change was made.

The LAN product is not merged or modified. Its disabled-by-default, admin-configured outbound HTTPS health probe remains exact-host allowlisted and authenticated. `apiCompatible=false` is not changed. No LAN server/P2P/jobs port is exposed to WAN, no inbound LAN access, synchronization, job transfer, resource sharing or remote execution is introduced. Four data colors × seven shades and UV parity/control remain unchanged.

A future authorized integration must prove valid host/token, missing/invalid token rejection, HTTP/wrong-host rejection, redirect refusal, response bounds, token redaction and absence of automatic data disclosure against a real main-side endpoint. No such end-to-end test ran; WAN data interoperability remains a separate security gate.
