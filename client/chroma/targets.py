"""Read-only information from the existing target catalog; never a compiler selector."""
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "docs" / "TARGETS.json"
MAX_CATALOG_BYTES = 65536
FIELDS = (
    ("architecture", "Architecture", "NOT SPECIFIED"),
    ("toolchain", "Required toolchain", "NOT SPECIFIED"),
    ("output", "Output format", "NOT SPECIFIED"),
    ("libraries", "Required libraries", "NOT SPECIFIED; verify for the selected toolchain and board"),
    ("hardware", "Hardware dependencies / verification", "Board and processor must be selected; hardware NOT VERIFIED"),
    ("version", "Firmware / program version", "NOT SPECIFIED; no versioned device build selected"),
    ("status", "Test status", "NOT VERIFIED"),
    ("cpl_native_backend", "Native CPL backend", "No native device backend claimed; see architecture above"),
    ("hardware_tests", "Required hardware tests", "NOT VERIFIED; acceptance on the actual selected device is required before deployment"),
    ("deployment", "Deployment", "No deployment from this view"),
)

def load_catalog(path=CATALOG):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_CATALOG_BYTES + 1)
    if len(raw) > MAX_CATALOG_BYTES:
        raise ValueError("Target catalog exceeds 64 KiB")
    data = json.loads(raw)
    if not isinstance(data, dict) or type(data.get("schemaVersion")) is not int or data["schemaVersion"] != 1:
        raise ValueError("Unsupported target catalog schema")
    targets = data.get("targets")
    if not isinstance(targets, list) or not 1 <= len(targets) <= 64:
        raise ValueError("Target catalog must contain 1–64 targets")
    seen = set()
    for target in targets:
        if not isinstance(target, dict):
            raise ValueError("Invalid target entry")
        for key in ("id", "architecture", "toolchain", "output", "status"):
            if not isinstance(target.get(key), str) or not target[key].strip():
                raise ValueError("Missing target field: " + key)
        for key in ("id",) + tuple(field[0] for field in FIELDS):
            if key in target and (not isinstance(target[key], str) or not target[key].strip() or len(target[key]) > 4096):
                raise ValueError("Invalid target text: " + key)
        if target["id"] in seen:
            raise ValueError("Duplicate target ID")
        seen.add(target["id"])
    return tuple(targets)

def describe(target):
    return target["id"] + "\n\n" + "\n\n".join(
        label + ":\n" + target.get(key, default) for key, label, default in FIELDS
    )
