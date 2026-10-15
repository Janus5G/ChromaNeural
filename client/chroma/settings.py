"""Small, versioned local preferences. No identity, points or project data."""
from pathlib import Path
import json,os,tempfile,copy,time
DEFAULTS={"version":1,"onboarded":False,"participation":False,"paused":False,
          "theme":"dark","close_to_tray":True,"start_hidden":False,"connection":"",
          "resources":{"cpu":False,"threads":2,"ram_mib":2048,"gpu":False,"idle_only":True,"pause_on_battery":True}}
def state_directory():
    if os.environ.get("CHROMA_STATE_DIR"):return Path(os.environ["CHROMA_STATE_DIR"])
    if os.name=="nt":return Path(os.environ.get("LOCALAPPDATA",Path.home()/"AppData/Local"))/"ChromaNeural"/"client"
    return Path(os.environ.get("XDG_STATE_HOME",Path.home()/".local/state"))/"chroma-neural"/"client"
def validate(value):
    if not isinstance(value,dict) or set(value)!=set(DEFAULTS) or type(value["version"]) is not int or value["version"]!=1:raise ValueError("Unsupported preferences format")
    for key in ("onboarded","participation","paused","close_to_tray","start_hidden"):
        if type(value[key]) is not bool:raise ValueError("Invalid preference "+key)
    if value["theme"] not in ("dark","light"):raise ValueError("Invalid theme")
    if not isinstance(value["connection"],str) or len(value["connection"])>4096 or "\x00" in value["connection"]:raise ValueError("Invalid connection path")
    r=value["resources"]
    if not isinstance(r,dict) or set(r)!=set(DEFAULTS["resources"]):raise ValueError("Invalid resource preferences")
    for key in ("cpu","gpu","idle_only","pause_on_battery"):
        if type(r[key]) is not bool:raise ValueError("Invalid resource consent")
    if type(r["threads"]) is not int or not 1<=r["threads"]<=8:raise ValueError("CPU thread preference outside 1..8")
    if type(r["ram_mib"]) is not int or r["ram_mib"] not in (512,1024,2048,4096,8192):raise ValueError("RAM preference outside supported choices")
    if r["gpu"]:raise ValueError("GPU contribution is not verified")
    return copy.deepcopy(value)
class Settings:
    def __init__(self,directory=None):
        self.directory=Path(directory) if directory else state_directory()
        self.directory.mkdir(parents=True,exist_ok=True)
        self.path=self.directory/"preferences.json";self.error=""
        self.value=copy.deepcopy(DEFAULTS)
        if self.path.exists():
            try:
                if self.path.stat().st_size>16384:raise ValueError("Preferences size")
                self.value=validate(json.loads(self.path.read_text(encoding="utf-8")))
            except Exception as e:
                self.error=str(e) # Preserve corrupt original until the user explicitly saves new preferences.
    def save(self,value):
        checked=validate(value)
        if self.error and self.path.exists():
            backup=self.directory/("preferences.invalid."+str(time.time_ns())+".json")
            backup.write_bytes(self.path.read_bytes())
        fd,temp=tempfile.mkstemp(prefix=".preferences-",dir=self.directory)
        try:
            with os.fdopen(fd,"w",encoding="utf-8") as f:
                json.dump(checked,f,indent=2);f.flush();os.fsync(f.fileno())
            os.replace(temp,self.path);self.value=checked;self.error=""
        finally:
            if os.path.exists(temp):os.unlink(temp)
