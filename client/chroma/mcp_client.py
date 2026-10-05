"""Optional SDK client. No peer protocol, roots, sampling, or ambient credentials."""
import asyncio, contextlib, json, os, sys
from pathlib import Path
from .mcp_config import Config, IDENT, canonical, fingerprint, connection_key

def sdk_path():
    """Release-built native dependencies only; never install anything at runtime."""
    folder = Path(__file__).resolve().parents[1] / "mcp-deps"
    if folder.is_dir():
        sys.path.insert(0, str(folder))
        if os.name == "nt":
            for name in ("win32", "win32/lib", "Pythonwin"):
                sys.path.insert(0, str(folder / name))
            dll = folder / "pywin32_system32"
            if dll.is_dir() and not hasattr(sdk_path, "_dll"):
                sdk_path._dll = os.add_dll_directory(str(dll))
                sys.path.insert(0, str(dll))

def definition(tool):
    name = tool.name
    if not IDENT.fullmatch(name):
        raise ValueError("Unsupported MCP tool name")
    result = {"name": name, "description": tool.description or "", "input_schema": tool.input_schema,
              "output_schema": tool.output_schema,
              "annotations": tool.annotations.model_dump(mode="json") if tool.annotations else None}
    if len(canonical(result).encode()) > 16384:
        raise ValueError("MCP tool definition limit")
    return result

@contextlib.asynccontextmanager
async def connect(server, token=""):
    sdk_path()
    from mcp import Client, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.streamable_http import streamable_http_client
    async with contextlib.AsyncExitStack() as stack:
        if server["transport"] == "stdio":
            if token:
                raise ValueError("Remote bearer credential cannot be used for a local server")
            if not Path(server["command"]).is_file():
                raise ValueError("MCP executable unavailable")
            # No inherited API tokens; SDK supplies only its documented minimal environment.
            errlog = stack.enter_context(open(os.devnull, "w"))
            transport = stdio_client(StdioServerParameters(command=server["command"], args=server["args"],
                                                          env={}), errlog=errlog)
        else:
            import httpx2
            headers = {}
            if token:
                if not isinstance(token, str) or len(token) > 8192 or any(ord(c) < 33 or ord(c) > 126 for c in token):
                    raise ValueError("Invalid session credential")
                if not server["endpoint"].startswith("https://"):
                    raise ValueError("Credentials require HTTPS")
                headers["Authorization"] = "Bearer " + token
            expected_target = httpx2.URL(server["endpoint"])
            async def exact_target(request):
                # SDK redirects may otherwise follow another path on the same origin.
                # A configured target change requires fresh approval/authorization.
                if request.url != expected_target:
                    raise PermissionError("MCP connection target changed")
            http = await stack.enter_async_context(httpx2.AsyncClient(
                headers=headers, timeout=10, follow_redirects=False, trust_env=False,
                event_hooks={"request": [exact_target]}))
            transport = streamable_http_client(server["endpoint"], http_client=http, max_sse_event_size=131072)
        client = await stack.enter_async_context(Client(transport, read_timeout_seconds=10, cache=None))
        yield client

async def tools(client):
    if client.server_capabilities.tools is None:
        return []
    result, cursor, cursors = [], None, set()
    for _ in range(8):
        page = await client.list_tools(cursor=cursor)
        result.extend(definition(tool) for tool in page.tools)
        if len(result) > 32 or len(canonical(result).encode()) > 65536:
            raise ValueError("MCP discovery limit")
        cursor = page.next_cursor
        if cursor is None:
            if len({t["name"] for t in result}) != len(result):
                raise ValueError("Duplicate MCP tool")
            return result
        if cursor in cursors:
            raise ValueError("Invalid MCP pagination")
        cursors.add(cursor)
    raise ValueError("MCP pagination limit")

class Host:
    def __init__(self, directory=None, secrets=None):
        self.config = Config(directory)
        self.secrets = dict(secrets or {})

    def credential(self, server):
        value = self.secrets.get(server["id"])
        if not value:
            return ""
        if not isinstance(value, dict) or set(value) != {"target", "token"} or value["target"] != connection_key(server):
            raise PermissionError("Session credential target changed")
        return value["token"]

    def check(self, identifier, snapshot=None, *, enabled=False):
        current = self.config.server(identifier, enabled=enabled)
        if snapshot is not None and current != snapshot:
            raise PermissionError("MCP approval changed")
        return current

    async def discover(self, identifier):
        server = self.check(identifier)
        async with asyncio.timeout(15):
            async with connect(server, self.credential(server)) as client:
                found = await tools(client)
                resources = []
                if client.server_capabilities.resources is not None:
                    page = await client.list_resources()
                    if len(page.resources) > 32 or page.next_cursor is not None:
                        raise ValueError("MCP resource discovery limit")
                    resources = [{"name": r.name, "uri": str(r.uri)} for r in page.resources]
                    if len(canonical(resources).encode()) > 16384:
                        raise ValueError("MCP resource discovery limit")
                self.check(identifier, server)
                return {"protocol": client.protocol_version, "tools": found, "resources": resources}

    async def capabilities(self, identifiers):
        if not isinstance(identifiers, list) or len(identifiers) > 4 or len(set(identifiers)) != len(identifiers):
            raise ValueError("MCP task server limit")
        found = {}
        for identifier in identifiers:
            server = self.check(identifier, enabled=True)
            discovery = await self.discover(identifier)
            self.check(identifier, server, enabled=True)
            for tool in discovery["tools"]:
                if server["tools"].get(tool["name"]) == fingerprint(tool):
                    alias = "mcp_" + str(len(found))
                    found[alias] = (identifier, server, tool)
        if len(found) > 16:
            raise ValueError("MCP task tool limit")
        return found

    async def call(self, entry, arguments):
        identifier, server, tool = entry
        self.check(identifier, server, enabled=True)
        if server["tools"].get(tool["name"]) != fingerprint(tool):
            raise PermissionError("MCP tool is not approved")
        if not isinstance(arguments, dict) or len(canonical(arguments).encode()) > 8192:
            raise ValueError("MCP argument limit")
        sdk_path()
        from jsonschema import Draft202012Validator
        from referencing import Registry
        # Empty registry and no retrieval callback: schemas cannot fetch external URLs.
        Draft202012Validator(tool["input_schema"], registry=Registry()).validate(arguments)
        async with asyncio.timeout(15):
            async with connect(server, self.credential(server)) as client:
                actual = await tools(client)
                if tool not in actual:
                    raise PermissionError("MCP tool changed; approval required")
                self.check(identifier, server, enabled=True)
                result = await client.call_tool(tool["name"], arguments)
                self.check(identifier, server, enabled=True)
                text = "\n".join(b.text for b in result.content if b.type == "text")
                if len(text.encode()) > 32768 or "\x00" in text:
                    raise ValueError("MCP result limit")
                # Never interpret server instructions or execute returned code.
                return {"is_error": result.is_error, "text": text}
