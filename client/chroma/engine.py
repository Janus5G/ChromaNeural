"""Local compiler service client; fixed executable, bounded request, no remote endpoint."""
from pathlib import Path
import json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def linux_path(path):
    p=Path(path).absolute()
    if os.name!="nt": return str(p)
    if not p.drive or p.drive.startswith("\\\\"): raise ValueError("Install on a local drive for WSL")
    return "/mnt/"+p.drive[0].lower()+"/"+"/".join(p.parts[1:])
def command():
    if os.name=="nt":
        return [str(Path(os.environ["SystemRoot"])/"System32/wsl.exe"),"--exec","/usr/bin/python3",linux_path(ROOT/"chroma/sandbox.py")]
    return [sys.executable,str(ROOT/"chroma/sandbox.py")]
def run(profile,action,source):
    if len(source.encode())>65536: raise ValueError("Source limit 64 KiB")
    args=command()
    options={"creationflags":subprocess.CREATE_NO_WINDOW} if os.name=="nt" else {}
    try:
        result=subprocess.run(args,input=json.dumps({"profile":profile,"action":action,"source":source}),capture_output=True,text=True,timeout=12,**options)
    except subprocess.TimeoutExpired as e: raise RuntimeError("Compiler service timeout; inner sandbox has its own 5-second kill deadline") from e
    if len(result.stdout)>150000 or len(result.stderr)>32768: raise RuntimeError("Service response too large")
    try: reply=json.loads(result.stdout)
    except ValueError: raise RuntimeError("Sandbox unavailable: "+result.stderr[:1000])
    if result.returncode or not reply.get("ok"): raise RuntimeError(reply.get("error","Compiler failed"))
    return reply
