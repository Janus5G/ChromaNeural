"""Non-secret, additive owner configuration. Importing this module has no side effects."""
import copy, hashlib, json, os, re, tempfile
from pathlib import Path
from urllib.parse import urlsplit
from .ai_provider import validate_selection
from .settings import state_directory

LIMIT = 131072
DEFAULT = {"version": 1, "provider": None, "servers": []}
IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
KEYS = {"id", "name", "transport", "endpoint", "command", "args", "approved", "enabled", "tools"}

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def fingerprint(tool):
    return hashlib.sha256(canonical(tool).encode()).hexdigest()

def connection_key(server):
    return fingerprint({key: server[key] for key in ("id", "transport", "endpoint", "command", "args")})

def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Invalid AI/tool configuration")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Invalid configuration")))

def validate(value):
    if not isinstance(value, dict) or set(value) != set(DEFAULT) or type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("Invalid AI/tool configuration")
    validate_selection(value["provider"])
    servers = value["servers"]
    if not isinstance(servers, list) or len(servers) > 16:
        raise ValueError("MCP server limit")
    ids = set()
    for s in servers:
        if not isinstance(s, dict) or set(s) != KEYS:
            raise ValueError("Invalid MCP connection")
        if not isinstance(s["id"], str) or not IDENT.fullmatch(s["id"]) or s["id"] in ids:
            raise ValueError("Invalid MCP identifier")
        ids.add(s["id"])
        if not isinstance(s["name"], str) or not 1 <= len(s["name"]) <= 80 or any(ord(c) < 32 for c in s["name"]):
            raise ValueError("Invalid MCP name")
        if any(type(s[k]) is not bool for k in ("approved", "enabled")) or (s["enabled"] and not s["approved"]):
            raise ValueError("Invalid MCP approval")
        if not isinstance(s["tools"], dict) or len(s["tools"]) > 32:
            raise ValueError("MCP tool limit")
        if s["tools"] and not s["approved"]:
            raise ValueError("Unapproved tools")
        for name, digest in s["tools"].items():
            if not isinstance(name, str) or not IDENT.fullmatch(name) or not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
                raise ValueError("Invalid MCP tool approval")
        if not isinstance(s["args"], list) or len(s["args"]) > 32 or any(not isinstance(a, str) or len(a) > 1024 or "\x00" in a for a in s["args"]):
            raise ValueError("Invalid MCP arguments")
        if not all(isinstance(s[k], str) for k in ("endpoint", "command")):
            raise ValueError("Invalid MCP target")
        if s["transport"] == "stdio":
            command = Path(s["command"])
            if not command.is_absolute() or "\x00" in s["command"] or len(s["command"]) > 4096 or s["endpoint"]:
                raise ValueError("MCP requires an explicit local executable")
            if command.stem.lower() in {"cmd", "powershell", "pwsh", "sh", "bash", "zsh", "npx", "npm", "uv", "pip", "pip3"}:
                raise ValueError("Shells and package installers are not MCP executables")
        elif s["transport"] == "http":
            u = urlsplit(s["endpoint"])
            if (not u.hostname or u.username or u.password or u.query or u.fragment or
                len(s["endpoint"]) > 2048 or any(ord(c) < 33 for c in s["endpoint"]) or
                s["command"] or s["args"] or
                not (u.scheme == "https" or (u.scheme == "http" and u.hostname in {"127.0.0.1", "::1"}))):
                raise ValueError("MCP requires HTTPS; credentials must not be in the URL")
            if u.port is not None and not 1 <= u.port <= 65535:
                raise ValueError("Invalid MCP port")
        else:
            raise ValueError("Unsupported MCP transport")
    if len(canonical(value).encode()) > LIMIT:
        raise ValueError("AI/tool configuration size")
    return copy.deepcopy(value)

class Config:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else state_directory()
        self.path = self.directory / "ai-tools.json"

    def load(self):
        if not self.path.exists():
            return copy.deepcopy(DEFAULT)
        if self.path.is_symlink() or self.path.stat().st_size > LIMIT:
            raise ValueError("Invalid AI/tool configuration")
        return validate(strict(self.path.read_bytes()))

    def save(self, value):
        checked = validate(value)
        self.directory.mkdir(parents=True, exist_ok=True)
        if self.path.is_symlink():
            raise ValueError("Invalid AI/tool configuration")
        fd, tmp = tempfile.mkstemp(prefix=".ai-tools-", dir=self.directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(checked, stream, ensure_ascii=True, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def put(self, server):
        """Every connection edit revokes all prior authority."""
        value = self.load()
        server = dict(server, approved=False, enabled=False, tools={})
        value["servers"] = [s for s in value["servers"] if s["id"] != server["id"]] + [server]
        self.save(value)

    def server(self, identifier, *, enabled=False):
        server = next((s for s in self.load()["servers"] if s["id"] == identifier), None)
        if server is None or not server["approved"] or (enabled and not server["enabled"]):
            raise PermissionError("MCP connection is not approved and enabled")
        return server

    def update(self, identifier, *, approved=None, enabled=None, tools=None):
        value = self.load()
        server = next((s for s in value["servers"] if s["id"] == identifier), None)
        if server is None:
            raise PermissionError("MCP connection removed")
        if approved is not None:
            server["approved"] = approved
            if not approved:
                server["enabled"] = False
                server["tools"] = {}
        if enabled is not None:
            server["enabled"] = enabled
        if tools is not None:
            server["tools"] = tools
        self.save(value)

    def remove(self, identifier):
        value = self.load()
        value["servers"] = [s for s in value["servers"] if s["id"] != identifier]
        self.save(value)

    def select(self, choice):
        value = self.load()
        value["provider"] = validate_selection(choice)
        self.save(value)
