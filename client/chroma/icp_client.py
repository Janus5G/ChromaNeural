"""Optional Node SDK process provider. The protocol is independent of desktop UI."""
from pathlib import Path
import json,shutil,subprocess,os
def call(config,operation,**fields):
    selected=json.loads(Path(config).read_text(encoding="utf-8"))
    script=Path(__file__).resolve().parents[1]/"services/icp_bridge.mjs"
    config_arg=str(config)
    if selected.get("runtimeProvider")=="wsl":
        if os.name!="nt":raise ValueError("WSL provider is only a Windows launcher option")
        from .engine import linux_path
        linux_node=selected.get("nodeExecutable")
        if not isinstance(linux_node,str) or not linux_node.startswith("/") or "\\x00" in linux_node:raise ValueError("Choose the installed WSL Node executable")
        cmd=[str(Path(os.environ["SystemRoot"])/"System32/wsl.exe"),"--exec",linux_node,linux_path(script)]
        config_arg=linux_path(config)
    else:
        node=shutil.which("node")
        if not node:raise RuntimeError("Native Node.js provider unavailable; local editor/AI remain available")
        cmd=[node,str(script)]
    opts={"creationflags":subprocess.CREATE_NO_WINDOW} if os.name=="nt" else {}
    p=subprocess.run(cmd,input=json.dumps({"config":config_arg,"operation":operation,**fields}),capture_output=True,text=True,timeout=30,**opts)
    if len(p.stdout)>1048576 or len(p.stderr)>32768:raise RuntimeError("ICP bridge output limit")
    try:reply=json.loads(p.stdout)
    except ValueError:raise RuntimeError("ICP bridge failed: "+p.stderr[-800:])
    if p.returncode or not reply.get("ok"):raise RuntimeError(reply.get("error","ICP request failed"))
    return reply["result"]
