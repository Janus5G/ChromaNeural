# Resource Fair Use V2 — RC6 status

ChromaPoints express resource fair use, not money. One tool call is not one point.
The prospective DATA+CPU model uses `102400000000 × dataBytes + 107374182400 × cpuMicros`
ticks, with `107374182400000000` ticks per point. Thus 1 MiB or 1 CPU second is one
point of resource value. Exact ticks/carry are retained; display rounding is not
accounting. RAM×time and GPU settlement are disabled, not silently priced at zero.

Discovery, initialization, health checks, tool listing, setup and approvals remain
free. Data means workload payload bytes crossing the controlled broker boundary,
input plus output once; protocol framing, control traffic and internal copies are
excluded. CPU means trusted aggregate process-tree CPU time, not wall time.

An explicitly approved technical envelope determines the reservation. Concurrent
tasks cannot reserve the same allowance. Known completion settles measured usage
and releases the remainder. Pre-dispatch rejection costs zero. Ambiguous execution
retains its reservation for reconciliation; no automatic free retry/refund occurs.
Four calls is a security limit, not a price. The 100-point aggregate outstanding
reservation ceiling is admission control, never a clamp on the measured price.

Connection and individual tool approval remain mandatory. Server-reported prices
or telemetry cannot settle the journal. Results remain untrusted data. The journal
stores IDs, fingerprints, digests, bounds and metrics, not tokens, prompts or result
bodies. Local MCP debit remains distinct from authoritative network spending.

## Activation and verification

The local software implements exact arithmetic, durable reservation/settlement,
and central-host enforcement using an explicit trusted execution adapter. The
isolated Motoko candidate projects the same formula into the existing Account
record. Neither component creates local network earnings or converts old balances.
Bootstrap and legacy earnings are not automatically eligible for V2.

Production accounting, production resource measurement and the numeric settlement GUI are **NOT TESTED — disabled** in RC6. The live V2 authority/allowance adapter,
persistent ledger carry and prospective epoch transition, and the complete trusted
production execution meter are not implemented end-to-end. The existing V1 bridge
cannot enable V2. Historical deployment provenance is no longer a blocker.

The local journal preserves exact fractional debits across process restart and
an explicit epoch advance for the same policy/account/allowance. Cumulative
authority values cannot reset, and unresolved work blocks the transition. This
client-side transition does not implement persistent carry in the ledger actor.

Software checks use synthetic allowances and fixtures. The cgroup experiment
proves local CPU counter behavior, not the full production accounting chain.
The actual local RoboForge gateway and compiler passed the Python MCP request
metadata, Ed25519 grant, receipt and replay checks. That test used a synthetic
host meter: it does not prove production resource measurement or settlement.
Controlled MCP dispatch uses the SDK's single-request method without automatic
tool retries. Missing or mismatched RoboForge receipts retain the reservation.
Live integration and numeric settlement acceptance remain **NOT TESTED**. Ten actual Linux GUI checks passed across English and Danish with simulated AI responses: startup, cancellation, explicit local-only continuation, proposal approval/application and shutdown. RoboForge has no
ChromaPoints balance or pricing.
No live backend or account was changed. Local AI and core functionality remain
independent of optional MCP accounting. RC6 includes this inactive infrastructure;
it does not claim completed production resource accounting.
