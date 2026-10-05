"""Controlled acceptance service only; never shipped as a ChromaNeural server."""
import json, sys
from pathlib import Path
import os
if os.environ.get("CHROMA_MCP_CLIENT"):
    sys.path.insert(0,os.environ["CHROMA_MCP_CLIENT"])
    from chroma.mcp_client import sdk_path
    sdk_path()
from mcp.server import MCPServer

server = MCPServer("ChromaNeural acceptance data")
data = Path(sys.argv[1])
calls = Path(sys.argv[2])

@server.tool()
def fetch_record(key: str) -> str:
    """Read one harmless acceptance record by key."""
    value = json.loads(data.read_text(encoding="utf-8"))[key]
    with calls.open("a", encoding="utf-8") as stream:
        stream.write("fetch_record\n")
    return value

@server.tool()
def unapproved_tool() -> str:
    """Must never be approved or called by acceptance."""
    with calls.open("a", encoding="utf-8") as stream:
        stream.write("UNAPPROVED\n")
    return "not allowed"

@server.resource("test://record")
def record() -> str:
    return "Acceptance resource; discovery only."

if __name__ == "__main__":
    if len(sys.argv) > 3:
        server.run(transport="streamable-http", host="127.0.0.1", port=int(sys.argv[3]))
    else:
        server.run()
