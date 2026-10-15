"""Reuse the installed ICP SDK for an explicit anonymous query; no private identity."""
from pathlib import Path
import json,os,shutil,subprocess
from .connection_profile import parse_profile

def probe_profile(value):
    checked=parse_profile(json.dumps(value))
    node=shutil.which("node")
    if not node:
        raise RuntimeError("Node.js mangler til forbindelsestesten. Dine indstillinger er gemt; lokal AI og ChromaSpeechAI er uændrede.")
    command=[node]
    if os.name=="nt":command.append("--use-system-ca")
    command.append(str(Path(__file__).resolve().parents[1]/"services/connection_probe.mjs"))
    options={"creationflags":subprocess.CREATE_NO_WINDOW} if os.name=="nt" else {}
    result=subprocess.run(command,input=json.dumps(checked),capture_output=True,text=True,timeout=30,**options)
    if len(result.stdout)>32768 or len(result.stderr)>32768:raise RuntimeError("Forbindelsestestens outputgrænse blev overskredet")
    try:response=json.loads(result.stdout)
    except ValueError:raise RuntimeError("Forbindelsestesten kunne ikke starte med den installerede Node.js-runtime") from None
    if result.returncode or response.get("ok") is not True:
        raise RuntimeError(response.get("error","Forbindelsestesten mislykkedes"))
    data=response["result"]
    if data.get("backendReachable") is not True or data.get("backendCanisterId")!=checked["backend_canister_id"] or data.get("host")!=checked["host"] or data.get("caller")!="anonymous" or data.get("privateAccess")!="NOT_VERIFIED":
        raise RuntimeError("Uventet resultat fra forbindelsestesten")
    return data
