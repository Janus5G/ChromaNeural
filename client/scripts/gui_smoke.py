"""Runs real Windows Tk widgets; no claim about human visual/assistive-technology review."""
import ctypes,json,time,traceback
from pathlib import Path
from unittest.mock import patch
def memory_bytes():
 from ctypes import wintypes as w
 class PMC(ctypes.Structure):
  _fields_=[("cb",w.DWORD),("PageFaultCount",w.DWORD),("PeakWorkingSetSize",ctypes.c_size_t),("WorkingSetSize",ctypes.c_size_t),("QuotaPeakPagedPoolUsage",ctypes.c_size_t),("QuotaPagedPoolUsage",ctypes.c_size_t),("QuotaPeakNonPagedPoolUsage",ctypes.c_size_t),("QuotaNonPagedPoolUsage",ctypes.c_size_t),("PagefileUsage",ctypes.c_size_t),("PeakPagefileUsage",ctypes.c_size_t)]
 k=ctypes.WinDLL("kernel32");k.GetCurrentProcess.restype=w.HANDLE
 ps=ctypes.WinDLL("psapi");ps.GetProcessMemoryInfo.argtypes=[w.HANDLE,ctypes.POINTER(PMC),w.DWORD]
 info=PMC();info.cb=ctypes.sizeof(info)
 if not ps.GetProcessMemoryInfo(k.GetCurrentProcess(),ctypes.byref(info),info.cb):raise OSError("Memory query")
 return info.WorkingSetSize
def exercise(app,report,start):
 result={"platform":"Windows real Tk","checks":[],"startup_seconds":time.perf_counter()-start}
 try:
  def check(name,condition):
   if not condition:raise AssertionError(name)
   result["checks"].append({"name":name,"status":"PASS"})
  check("window_mapped",bool(app.root.winfo_ismapped()))
  check("tray_added",app.tray.available)
  check("footer_visible",bool(app.footer.winfo_ismapped()) and app.footer.winfo_y()+app.footer.winfo_height()<=app.root.winfo_height())
  check("diagnostics_visible",app.output.winfo_height()>70)
  raw=b"\xef\xbb\xbf"+'var data = 7;\r\nprint data;\r\n'.encode()
  app.workspace.write("input.cpl",raw)
  with patch("chroma.ui.filedialog.askopenfilename",return_value=str(app.workspace.root/"input.cpl")):app.open_file()
  app.save();check("open_save_byte_identical",app.workspace.read("input.cpl")==raw)
  with patch("chroma.ui.filedialog.asksaveasfilename",return_value=str(app.workspace.root/"saved.cpl")):app.save(True)
  check("save_as_byte_identical",app.workspace.read("saved.cpl")==raw)
  app.editor.insert("end","// changed\n");app.save()
  check("manual_edit_saved",b"// changed" in app.workspace.read("saved.cpl"))
  app.toggle_theme();app.root.update();check("dark_theme",app.editor.cget("background")=="#202C3D")
  from scripts.window_capture import capture
  capture(app.root,Path(report).with_suffix(".dark.png"))
  app.toggle_theme();app.root.update();check("light_theme",app.editor.cget("background")=="#FFFFFF")
  capture(app.root,Path(report).with_suffix(".light.png"))
  app.hide();app.root.update();check("tray_hide",not app.root.winfo_ismapped())
  app.show();app.root.update();check("tray_restore",bool(app.root.winfo_ismapped()))
  app.stop();check("remote_disabled",not app.policy.remote_execution)
  result["working_set_bytes"]=memory_bytes();result["status"]="PASS"
 except BaseException:result["status"]="FAIL";result["error"]=traceback.format_exc()
 finally:
  result["uptime_seconds"]=time.perf_counter()-start
  Path(report).write_text(json.dumps(result,indent=2),encoding="utf-8")
  app.tray.close();app.root.destroy()
