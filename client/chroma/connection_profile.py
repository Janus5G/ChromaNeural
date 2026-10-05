"""Public API metadata only. Never credentials, node admission, or an II session."""
from pathlib import Path
import base64
import binascii
import copy
import json
import os
import tempfile
import time
import uuid

APP_ID = "01a09729-ea2b-731d-9190-cb11a7778be4"
ORIGIN = "https://chroma-neural-wl9.caffeine.xyz"
LOGIN_URL = ORIGIN + "/api"
FIELDS = frozenset(("version", "app_id", "network", "host", "connection_target",
                    "backend_canister_id", "frontend_canister_id", "identity_provider",
                    "ii_derivation_origin", "principal"))
LIMIT = 8192


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Dubleret felt i API-indstillinger")
        result[key] = value
    return result


def principal_bytes(text):
    if not isinstance(text, str) or not 1 <= len(text) <= 63:
        raise ValueError("Ugyldigt Principal-format")
    compact = text.replace("-", "")
    if any(c not in "abcdefghijklmnopqrstuvwxyz234567" for c in compact):
        raise ValueError("Ugyldigt Principal-format")
    try:
        decoded = base64.b32decode(compact.upper() + "=" * (-len(compact) % 8))
    except (binascii.Error, ValueError):
        raise ValueError("Ugyldigt Principal-format") from None
    if not 4 <= len(decoded) <= 33:
        raise ValueError("Ugyldig Principal-længde")
    raw = decoded[4:]
    checksum = binascii.crc32(raw).to_bytes(4, "big")
    encoded = base64.b32encode(checksum + raw).decode().lower().rstrip("=")
    canonical = "-".join(encoded[i:i+5] for i in range(0, len(encoded), 5))
    if checksum != decoded[:4] or canonical != text:
        raise ValueError("Principal-checksum eller kanonisk format er forkert")
    if raw in (b"", b"\x04"):
        raise ValueError("Anonym eller management-Principal kan ikke bruges her")
    return raw


def parse_profile(text):
    if not isinstance(text, str) or len(text.encode("utf-8")) > LIMIT:
        raise ValueError("API-indstillinger må højst fylde 8 KiB")
    try:
        value = json.loads(text.lstrip("\ufeff"), object_pairs_hook=_object)
    except (ValueError, RecursionError):
        raise ValueError("API-indstillinger skal være ét gyldigt JSON-objekt uden dublerede felter") from None
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError("Indsæt kun forbindelses-JSON fra API-siden; ingen nøgler, tokens eller ekstra felter")
    if type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("API-indstillingernes version understøttes ikke")
    if any(not isinstance(value[k], str) for k in FIELDS - {"version"}):
        raise ValueError("API-indstillinger indeholder ugyldige felttyper")
    if value["app_id"] != APP_ID or str(uuid.UUID(value["app_id"])) != APP_ID:
        raise ValueError("Indstillingerne tilhører ikke denne ChromaNeural-app")
    if value["network"] != "mainnet" or value["connection_target"] != "backend_canister":
        raise ValueError("Vælg appens ICP-mainnet backend-forbindelse")
    if value["host"] not in ("https://icp0.io", "https://icp-api.io"):
        raise ValueError("Ukendt ICP-host; forbindelsen er ikke aktiveret")
    if value["identity_provider"] != "https://id.ai/authorize" or value["ii_derivation_origin"] != ORIGIN:
        raise ValueError("Internet Identity-provider eller app-origin stemmer ikke")
    for key in ("backend_canister_id", "frontend_canister_id", "principal"):
        principal_bytes(value[key])
    if value["backend_canister_id"] == value["frontend_canister_id"]:
        raise ValueError("Backend og frontend skal være forskellige mål")
    # IDs are imported, never substituted with a hardcoded draft/live target.
    # A well-formed principal is an unverified claim, not authentication.
    return copy.deepcopy(value)


class ConnectionProfile:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / "api-connection-v1.json"
        self.value = None
        self.error = ""
        if self.path.exists():
            try:
                with self.path.open("rb") as stream:
                    data = stream.read(LIMIT + 1)
                self.value = parse_profile(data.decode("utf-8"))
            except (OSError, UnicodeError, ValueError):
                self.error = "Gemte API-indstillinger kunne ikke læses. Originalen er bevaret."

    @property
    def status(self):
        return "CONFIGURED_NOT_AUTHENTICATED" if self.value is not None else "UNCONFIGURED"

    def save(self, text):
        checked = parse_profile(text)
        self.directory.mkdir(parents=True, exist_ok=True)
        if self.error and self.path.exists():
            backup = self.directory / ("api-connection.invalid." + str(time.time_ns()) + ".json")
            # Preserve invalid input without loading an unbounded file into memory.
            import shutil
            shutil.copyfile(self.path, backup)
        fd, temporary = tempfile.mkstemp(prefix=".api-profile-", dir=self.directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(checked, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            self.value = checked
            self.error = ""
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return copy.deepcopy(checked)

    def forget(self):
        # Removing metadata neither logs out the web browser nor revokes server grants.
        self.path.unlink(missing_ok=True)
        self.value = None
        self.error = ""

    def open_login(self, opener):
        # Fixed verified application origin; never open a URL supplied in pasted JSON.
        if not opener(LOGIN_URL):
            raise RuntimeError("Browseren kunne ikke åbnes. Åbn ChromaNeurals API-side manuelt.")
        return LOGIN_URL
