"""Bounded launcher smoke; no model/network/backend gate repetition."""
from pathlib import Path
import json,time,sys,os,ctypes
def exercise(app,report,start):
    result={"scope":"actual Windows pyw launcher / dashboard","checks":[]}
    def check(name,value):
        if not value:raise AssertionError(name)
        result["checks"].append({"name":name,"status":"PASS"})
    try:
        app.root.update()
        result['executable']=sys.executable;result['pid']=os.getpid()
        check('actual_windowless_python',Path(sys.executable).name.lower()=='pythonw.exe')
        check('no_console_window',not ctypes.windll.kernel32.GetConsoleWindow())
        check("dashboard_shell_visible",app.root.winfo_ismapped())
        check("first_start_resources",app.current_page=="resources")
        check("no_automatic_participation",not app.service.value["participation"])
        check("tray_registered",app.tray.available)
        from .gui_smoke import memory_bytes
        result["working_set_bytes"]=memory_bytes();result["startup_seconds"]=time.perf_counter()-start
        result["status"]="PASS"
    except Exception as e:result.update(status="FAIL",error=str(e))
    finally:
        Path(report).write_text(json.dumps(result,indent=2),encoding="utf-8");app.quit()
