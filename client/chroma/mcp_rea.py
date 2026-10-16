"""Bounded REA npm-install discovery; no setup, downloads, or MCP launches.

Upstream: github.com/morluto/rea, package/scripts/rea.mjs, verified 6.5.0.
Resolve npm launchers to the official script, never execute a shell wrapper.
Package metadata identifies a candidate, not publisher trust or tool approval.
"""
import json
import os
from pathlib import Path
import re
import subprocess
from .mcp_catalog import local_path, installed_program

NAMES = ("rea", "rea-agents")


def _metadata(path):
    try:
        if not local_path(path) or not path.is_file() or path.stat().st_size > 131072:
            return {}
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (ValueError, OSError, RecursionError):
        return {}


def package_entry(program):
    """Only exact npm layouts and an explicit official entrypoint; no disk crawl."""
    path = Path(program)
    if not path.is_absolute() or str(path).startswith(("//", "\\\\")):
        return None
    try:
        # npm's POSIX bin is a symlink. Inspect one link; reject network/reparse
        # destinations before resolving, and never follow an arbitrary chain.
        if os.name != "nt" and path.is_symlink():
            if path.name not in NAMES or not local_path(path.parent):
                return None
            target = Path(os.readlink(path))
            path = Path(os.path.abspath(path.parent / target))
        if not local_path(path) or not path.is_file():
            return None
        options = [path] if path.name == "rea.mjs" else []
        if path.stem in NAMES:
            options += [path.parent / "node_modules/rea-agents/scripts/rea.mjs",
                        path.parent.parent / "rea-agents/scripts/rea.mjs"]
        for entry in options:
            package = entry.parent.parent
            data = _metadata(package / "package.json")
            if (data.get("name") == "rea-agents" and
                    re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9.-]+)?", str(data.get("version", ""))) and
                    isinstance(data.get("bin"), dict) and
                    all(data["bin"].get(n) == "scripts/rea.mjs" for n in NAMES) and
                    local_path(entry) and entry.is_file() and
                    local_path(package / "dist/mcp/main.js") and (package / "dist/mcp/main.js").is_file()):
                return str(entry), data["version"]
    except OSError:
        pass
    return None


def candidate(program, node=None):
    entry = package_entry(program)
    if not entry:
        return None
    node = node or installed_program("node")
    if not node or Path(node).stem != "node" or not local_path(node) or not Path(node).is_file():
        return None
    script, version = entry
    return {"command": str(node), "args": [script, "mcp"], "name": "REA", "version": version}


def valid_launch(command, args):
    if len(args) != 2 or args[1] != "mcp":
        return False
    found = candidate(args[0], command)
    return bool(found and found["version"] == "6.5.0" and found["args"] == list(args))


def discover(servers):
    found = []
    for server in servers[:16]:
        if server.get("transport") != "stdio":
            continue
        args = server.get("args", [])
        command = server.get("command", "")
        item = None
        if valid_launch(command, args):
            item = candidate(args[0], command)
        elif Path(command).stem in NAMES and args == ["mcp"]:
            item = candidate(command)
        if item:
            item["name"] = server.get("name", "REA")
            found.append(item)
    directories = [Path(p) for p in os.get_exec_path()[:128]
                   if local_path(p) and Path(p) != Path.cwd()]
    # Preserve requested priority: configured, rea, then rea-agents.
    for name in NAMES:
        for directory in directories:
            for suffix in ((".cmd", ".exe", "") if os.name == "nt" else ("",)):
                item = candidate(directory / (name + suffix))
                if item and not any(v["command"] == item["command"] and v["args"] == item["args"] for v in found):
                    found.append(item)
    return found


def compatible_node(version):
    match = re.fullmatch(r"v?([0-9]+)\.([0-9]+)\.([0-9]+)", version)
    if not match:
        return False
    major, minor, patch = map(int, match.groups())
    return ((major == 22 and (minor, patch) >= (19, 0)) or
            (major == 24 and (minor, patch) >= (11, 0)) or major >= 26)


def runtime_status(node=None):
    """Explicit profile/scan action only; never called while browsing catalog.
    Only Node --version runs, with no NODE_OPTIONS or inherited credentials.
    npm's version is read from its installed metadata, never by invoking npm.
    """
    node = node or installed_program("node")
    version, npm = "", ""
    if node and local_path(node) and Path(node).is_file() and Path(node).stem == "node":
        try:
            result = subprocess.run([node, "--version"], stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=2,
                env={k: os.environ[k] for k in ("SystemRoot", "WINDIR", "PATH") if k in os.environ},
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            text = result.stdout[:80].decode("ascii", errors="replace").strip()
            if result.returncode == 0 and re.fullmatch(r"v?[0-9]+\.[0-9]+\.[0-9]+", text):
                version = text
        except (OSError, subprocess.TimeoutExpired):
            pass
        for folder in (Path(node).parent, Path(node).parent.parent / "lib"):
            data = _metadata(folder / "node_modules/npm/package.json")
            if data.get("name") == "npm" and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", str(data.get("version", ""))):
                npm = data["version"]
                break
    return {"node": version, "compatible": compatible_node(version), "npm": npm}

# REA 6.5.0 compact/off contracts audited against upstream TOOL_EFFECTS.
# Only session evidence changes; no target writes, network, foreign-code
# execution or device actions. Definition changes require a fresh audit.
AUDITED_TOOLS = {
    "inspect_managed_artifact": "eacbb3cd84f92370d50d29239ae0c57ff4d34ce455c3eb4366227a55879b7e04",
    "inspect_managed_members": "860955c2d0b41bdfef1489ab6af5efe86b9552f8799791fd6ad212a403818b6e",
    "inspect_managed_native_boundaries": "03093174da2df9589cede04746f55e2550b59b06225b3af461b53cb038875b10",
    "inspect_analysis_view": "43c08e790e9699952d0623329222fd79f8e2ee626f67f8a547101824b8c8ad22",
    "inspect_pe_resources": "06ea78ac760cd14b0489f12e8b4b98f540921663a72e1a91a7715712e64abc15",
    "inspect_electron_fuses": "d7854cea0d165c47d2e4120eeff67fb15f5b95fefe3bf3208700db6608fcdb97",
    "analyze_javascript_application": "c6b8176d81c14a701b226d1146a2214e04f17fc567962257e25d143ff82a6ab2",
    "get_evidence_bundle": "bf8fdaa17a446788207cdcc3b855dcee71beec1786f658eee48d41dd87f056e4"
}
MAX_CATALOG_TOOLS = 512
MAX_CATALOG_BYTES = 1024 * 1024
MAX_CATALOG_DEFINITION = 32768


def is_rea_target(server):
    # Recognition survives a missing/broken installation: never fall back
    # to unrestricted generic stdio after a REA validation failure.
    if server.get("transport") != "stdio":
        return False
    args = server.get("args", [])
    return (server.get("id", "").startswith("rea-") or
            Path(server.get("command", "")).stem in NAMES or
            any(Path(a).name == "rea.mjs" for a in args))


async def curated_tools(client):
    from .mcp_client import definition
    from .mcp_config import IDENT, canonical, fingerprint
    if client.server_capabilities.tools is None:
        raise ValueError("REA tool catalog missing")
    seen, selected, cursors = set(), {}, set()
    cursor, total_bytes = None, 0
    for _ in range(8):
        page = await client.list_tools(cursor=cursor)
        for tool in page.tools:
            if not IDENT.fullmatch(tool.name) or tool.name in seen:
                raise ValueError("REA invalid or duplicate tool")
            seen.add(tool.name)
            raw = tool.model_dump(mode="json", by_alias=True, exclude_none=True)
            size = len(canonical(raw).encode())
            total_bytes += size
            if (len(seen) > MAX_CATALOG_TOOLS or size > MAX_CATALOG_DEFINITION or
                    total_bytes > MAX_CATALOG_BYTES or not isinstance(tool.input_schema, dict)):
                raise ValueError("REA upstream catalog limit")
            if tool.name in AUDITED_TOOLS:
                item = definition(tool)  # Ordinary 16 KiB bound still applies.
                if fingerprint(item) != AUDITED_TOOLS[tool.name]:
                    raise ValueError("REA audited tool contract changed")
                selected[tool.name] = item
        cursor = page.next_cursor
        if cursor is None:
            if set(selected) != set(AUDITED_TOOLS):
                raise ValueError("REA audited tool missing")
            result = [selected[name] for name in AUDITED_TOOLS]
            if len(canonical(result).encode()) > 65536:
                raise ValueError("REA curated discovery limit")
            client.chroma_rea_catalog_count = len(seen)
            return result
        if cursor in cursors:
            raise ValueError("REA invalid catalog pagination")
        cursors.add(cursor)
    raise ValueError("REA catalog pagination limit")
