"""ChromaNeural local client; optional native dependencies are confined to this installation."""
__version__ = "0.2.2"
REMOTE_EXECUTION = False
import os
if os.name == "nt":
    import sys
    from pathlib import Path
    _deps = Path(__file__).resolve().parents[1] / "optional-deps"
    if _deps.is_dir():
        sys.path.insert(0, str(_deps))
