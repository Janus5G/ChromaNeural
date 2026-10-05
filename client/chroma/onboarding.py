"""Read-only supported provider discovery and bounded optional MCP worker calls."""
import http.client, json, math, os, signal, subprocess, sys
from pathlib import Path
from .ai_provider import selection

def discover():
    found = []
    from .native_ai import runtime
    try:
        runtime()
        found.append({"provider": "bundled-cpu", "model": None, "endpoint": "", "status": "discovered"})
    except (OSError, ValueError, RuntimeError):
        pass
    conn = http.client.HTTPConnection("127.0.0.1", 11434, timeout=2)
    try:
        conn.request("GET", "/api/tags")
        response = conn.getresponse()
        if response.status != 200:
            return found
        raw = response.read(262145)
        if len(raw) > 262144:
            return found
        value = json.loads(raw)
        for item in value.get("models", [])[:64]:
            name = item.get("name")
            selection("ollama", name)
            found.append({"provider": "ollama", "model": name, "endpoint": "http://127.0.0.1:11434",
                          "status": "discovered"})
    except (OSError, ValueError, TypeError, AttributeError, http.client.HTTPException):
        pass
    finally:
        conn.close()
    return found

def worker(request, timeout=90):
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0 < timeout <= 120:
        raise ValueError("MCP deadline")
    body = json.dumps(request, ensure_ascii=True).encode()
    if len(body) > 196608:
        raise ValueError("MCP request limit")
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen([sys.executable, "-I", "-B", str(Path(__file__).with_name("mcp_worker.py"))],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **options)
    try:
        output, _ = process.communicate(body, timeout=timeout)
        if process.returncode or len(output) > 524288:
            raise RuntimeError("MCP operation failed")
        return json.loads(output)
    except subprocess.TimeoutExpired:
        raise TimeoutError("MCP operation deadline exceeded") from None
    finally:
        if os.name != "nt":
            if process.poll() is None:
                # SDK servers own separate groups. First let the worker cancel
                # the SDK context, which closes stdin and terminates its group.
                process.terminate()
                try:
                    process.communicate(timeout=8)
                except subprocess.TimeoutExpired:
                    pass
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        elif process.poll() is None:
            # Worker creates a kill-on-close Job Object before opening any MCP server.
            process.kill()
        process.communicate()

def test_provider(choice):
    from .ai_provider import selected_inference
    from .native_ai import infer
    return selected_inference("print(1)\n", "Return the source unchanged.", choice,
                              bundled=infer, timeout=30)

def discover_mcp(directory, identifier, secrets=None):
    return worker({"operation": "discover", "directory": str(directory), "identifier": identifier,
                   "secrets": dict(secrets or {})}, timeout=20)
