"""Curated presentation profiles. No network, execution, installation or authority.

Official sources are kept with each profile. NOT VERIFIED means that a documented
route exists but has not passed ChromaNeural end-to-end vendor acceptance.
Detection is a bounded file lookup, never a server launch or permission grant.
"""
from dataclasses import dataclass
import os
from pathlib import Path
from .mcp_config import DEFAULT, validate


@dataclass(frozen=True)
class Profile:
    id: str
    transport: str | None
    maturity: str
    docs: str
    endpoint: str = ""
    executable: str = ""
    tooling: str = ""
    read_tools: tuple[str, ...] = ()
    enabled: bool = False
    # These are enforced by the existing worker/client/provider, not new limits.
    discovery_seconds: int = 20
    request_seconds: int = 10
    result_bytes: int = 32768
    concurrent_calls: int = 1
    task_calls: int = 4
    connection_blocker: str = ""


PROFILES = (
    Profile("opcua", "stdio", "NOT VERIFIED",
            "https://github.com/OPCFoundation/UA-.NETStandard/blob/master/tools/Opc.Ua.Mcp/README.md",
            executable="opcua-mcp", read_tools=("Read", "HistoryRead", "Browse", "BrowseNext",
            "ReadValue", "ReadValues", "ReadNode", "GetConnectionStatus", "GetConfiguration")),
    Profile("ros2", None, "EXPERIMENTAL", "https://discourse.openrobotics.org/t/ros-mcp-server-release/50024",
            tooling="ros2"),
    Profile("isaac", "http", "NOT VERIFIED",
            "https://github.com/NVIDIA-Omniverse/kit-usd-agents/blob/main/source/mcp/isaacsim_mcp/README.md",
            read_tools=("search_isaac_sim_settings",)),
    Profile("emqx", None, "EXPERIMENTAL", "https://www.emqx.com/mqtt-for-ai/mcp-over-mqtt/"),
    Profile("homeassistant", "http", "NOT VERIFIED",
            "https://www.home-assistant.io/integrations/mcp_server/", read_tools=("GetLiveContext",)),
    Profile("siemens", "http", "NOT VERIFIED",
            "https://developer.siemens.com/ai-registry/developer-portal/developer-portal-mcp.html",
            endpoint="https://mcp.developer.xcelerator.rocks/mcp", read_tools=("askDeveloperPortal",)),
    Profile("rea", "stdio", "SUPPORTED", "https://github.com/morluto/rea",
            read_tools=('inspect_managed_artifact', 'inspect_managed_members', 'inspect_managed_native_boundaries', 'inspect_analysis_view', 'inspect_pe_resources', 'inspect_electron_fuses', 'analyze_javascript_application', 'get_evidence_bundle')),
    Profile("arduino", None, "EXPERIMENTAL",
            "https://blog.arduino.cc/2026/08/12/arduino-app-lab-0-10-meet-agentic-mode/",
            tooling="arduino-cli"),
)


def local_path(path):
    """Do not probe UNC, mapped network drives, or Windows reparse targets."""
    path = Path(path)
    if not path.is_absolute() or len(str(path)) > 4096 or str(path).startswith(("\\\\", "//")):
        return False
    if os.name == "nt":
        import ctypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
        kernel.GetDriveTypeW.restype = ctypes.c_uint
        if kernel.GetDriveTypeW(path.anchor) not in (2, 3, 6):
            return False
        kernel.GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
        kernel.GetFileAttributesW.restype = ctypes.c_uint
        for part in (*reversed(path.parents), path):
            attr = kernel.GetFileAttributesW(str(part))
            if attr != 0xFFFFFFFF and attr & 0x400:
                return False
    else:
        if any(p.is_symlink() for p in (path, *path.parents)):
            return False
    return True


def installed_program(name):
    """Search explicit PATH directories only, excluding the current directory.
    A matching filename is a candidate, not proof of publisher or compatibility.
    """
    if not name:
        return None
    directories = [p for p in os.get_exec_path()[:128] if local_path(p)
                   and Path(p) != Path.cwd()]
    suffixes = (".exe",) if os.name == "nt" else ("",)
    for folder in directories[:128]:
        for suffix in suffixes:
            candidate = Path(folder) / (name + suffix)
            if local_path(candidate) and candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate.resolve())
    return None


def candidates(profile, servers):
    """Only own saved configurations plus one exact documented program name."""
    if profile.id == "rea":
        from .mcp_rea import discover
        return discover(servers)
    found = []
    for server in servers[:16]:
        if profile.transport == "stdio" and server["transport"] == "stdio" and profile.executable:
            path = Path(server["command"])
            if path.stem.casefold() == profile.executable.casefold() and local_path(path) and path.is_file():
                found.append({"command": str(path), "args": list(server["args"]), "name": server["name"]})
        elif profile.endpoint and server["transport"] == "http" and server["endpoint"] == profile.endpoint:
            found.append({"endpoint": server["endpoint"], "name": server["name"]})
    path = installed_program(profile.executable)
    if path and not any(v.get("command") == path for v in found):
        found.append({"command": path, "args": [], "name": profile.executable})
    return found


def checked_connection(identifier, name, transport, target, args=()):
    """UI validation uses the authoritative backend validator without writing."""
    value = {"id": identifier, "name": name.strip(), "transport": transport,
             "endpoint": target.strip() if transport == "http" else "",
             "command": target.strip() if transport == "stdio" else "",
             "args": list(args) if transport == "stdio" else [],
             "approved": False, "enabled": False, "tools": {}}
    validate(dict(DEFAULT, servers=[value]))
    if transport == "stdio" and (not local_path(value["command"]) or not Path(value["command"]).is_file()):
        raise ValueError("wizard.error.program")
    return value


def needs_extra_consent(profile, tool):
    # Server annotations are untrusted hints, never authority to permit writes.
    return tool["name"] not in profile.read_tools