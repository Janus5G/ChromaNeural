"""One-shot Linux service. Fixed local compiler/VM only. No unsandboxed fallback."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
BWRAP=Path.home()/".local/chroma-sandbox/bubblewrap-0.12.0/bin/bwrap"
APPROVED="0da08f808a19c22b5c32c63c6b29a1d2075ac6184d5ac284f7d72f533988e37c"
def arguments(backend=BWRAP):
    if not backend.is_file() or backend.stat().st_mode&0o6000: raise RuntimeError("Approved non-setuid sandbox missing")
    if hashlib.sha256(backend.read_bytes()).hexdigest()!=APPROVED: raise RuntimeError("Sandbox binary differs from verified host release")
    return ["/usr/bin/prlimit","--cpu=2","--as=268435456","--nofile=64","--fsize=1048576","--core=0","--",str(backend),
        "--unshare-user","--unshare-pid","--unshare-net","--unshare-ipc","--unshare-uts",
        "--die-with-parent","--new-session","--clearenv","--proc","/proc","--dev","/dev","--tmpfs","/tmp",
        "--ro-bind","/usr","/usr","--symlink","usr/bin","/bin","--symlink","usr/lib","/lib",
        "--symlink","usr/lib64","/lib64","--dir","/app",
        "--ro-bind",str(ROOT/"chroma"),"/app/chroma",
        "--ro-bind",str(ROOT/"reference_core"),"/app/reference_core",
        "--ro-bind",str(ROOT/"vendor"),"/app/vendor",
        "--setenv","PATH","/usr/bin:/bin","--setenv","LANG","C.UTF-8","--setenv","PYTHONDONTWRITEBYTECODE","1",
        "--remount-ro","/","--chdir","/app",
        "/usr/bin/prlimit","--nproc=32","--","/usr/bin/python3","-B","/app/chroma/worker.py"]
def execute(raw,backend=BWRAP):
    if len(raw)>70000: raise ValueError("Request too large")
    p=subprocess.Popen(arguments(backend),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try: stdout,stderr=p.communicate(raw,timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate(timeout=2)
        return {"ok":False,"error":"Sandbox deadline exceeded","exitcode":124,"stderr":stderr.decode(errors="replace")[:2000]}
    if len(stdout)>140000: return {"ok":False,"error":"Output budget exceeded","exitcode":p.returncode}
    try: reply=json.loads(stdout)
    except ValueError: reply={"ok":False,"error":"Sandbox did not return a valid result"}
    reply.update(exitcode=p.returncode,stderr=stderr.decode(errors="replace")[:2000])
    if p.returncode:reply["ok"]=False
    return reply
if __name__=="__main__":
    try:
        result=execute(sys.stdin.buffer.read(70001));print(json.dumps(result));sys.exit(0 if result["ok"] else 1)
    except Exception as e:print(json.dumps({"ok":False,"error":str(e)}));sys.exit(1)
