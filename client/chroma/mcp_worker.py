"""Fixed isolated MCP task/diagnostic worker. JSON pipes; no shell or secret logging."""
import asyncio, json, logging, os, signal, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
logging.disable(logging.CRITICAL)

def run_operation(operation):
    # Cancel through AnyIO so the SDK's shielded stdio cleanup can finish.
    # Native Task.cancel() and SIGKILL bypass that cleanup.
    from chroma.mcp_client import sdk_path
    sdk_path()
    import anyio
    async def run():
        with anyio.CancelScope() as scope:
            loop = asyncio.get_running_loop()
            if os.name != "nt":
                loop.add_signal_handler(signal.SIGTERM, scope.cancel)
            try:
                return await operation
            finally:
                if os.name != "nt":
                    loop.remove_signal_handler(signal.SIGTERM)
        raise TimeoutError("MCP operation cancelled")
    return anyio.run(run)

def main():
    from chroma.process_lifetime import protect_process_tree
    protect_process_tree()
    from chroma.mcp_config import strict
    raw = sys.stdin.buffer.read(196609)
    if len(raw) > 196608:
        raise ValueError("Input limit")
    req = strict(raw)
    if not isinstance(req, dict):
        raise ValueError("Invalid MCP request")
    if req.get("operation") == "discover" and set(req) == {"operation", "directory", "identifier", "secrets"}:
        from chroma.mcp_client import Host
        value = run_operation(Host(req["directory"], req["secrets"]).discover(req["identifier"]))
    elif req.get("operation") == "infer" and set(req) == {"operation", "directory", "identifiers", "secrets", "model", "source", "instruction"}:
        from chroma.ai_provider import selection
        selection("ollama", req["model"])
        if not isinstance(req["source"], str) or len(req["source"].encode()) > 8192:
            raise ValueError("Source limit")
        if not isinstance(req["instruction"], str) or not 0 < len(req["instruction"]) <= 2000:
            raise ValueError("Instruction limit")
        from chroma.mcp_provider import infer
        value = {"proposal": run_operation(infer(req["source"], req["instruction"], req["model"],
                   req["directory"], req["identifiers"], req["secrets"]))}
    else:
        raise ValueError("Invalid MCP operation")
    body = json.dumps(value, ensure_ascii=True)
    if len(body.encode()) > 524288:
        raise ValueError("MCP output limit")
    sys.stdout.write(body)

if __name__ == "__main__":
    try:
        main()
    except BaseException:
        sys.stderr.write("MCP operation failed\n")
        raise SystemExit(1)
