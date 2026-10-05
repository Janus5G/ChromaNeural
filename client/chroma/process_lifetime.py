"""Keep GUI-owned native child processes tied to the Windows client lifetime."""
import os
_job=None

def protect_process_tree():
    global _job
    if os.name!='nt' or _job is not None:return
    import ctypes as c
    from ctypes import wintypes as w
    class BASIC(c.Structure):
        _fields_=[('processTime',c.c_longlong),('jobTime',c.c_longlong),('flags',w.DWORD),('minWorkingSet',c.c_size_t),('maxWorkingSet',c.c_size_t),('activeProcesses',w.DWORD),('affinity',c.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
    class IO(c.Structure):
        _fields_=[(name,c.c_ulonglong) for name in ('readOps','writeOps','otherOps','readBytes','writeBytes','otherBytes')]
    class EXTENDED(c.Structure):
        _fields_=[('basic',BASIC),('io',IO),('processMemory',c.c_size_t),('jobMemory',c.c_size_t),('peakProcessMemory',c.c_size_t),('peakJobMemory',c.c_size_t)]
    kernel=c.WinDLL('kernel32',use_last_error=True)
    kernel.CreateJobObjectW.argtypes=[c.c_void_p,w.LPCWSTR];kernel.CreateJobObjectW.restype=w.HANDLE
    kernel.SetInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD];kernel.SetInformationJobObject.restype=w.BOOL
    kernel.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE];kernel.AssignProcessToJobObject.restype=w.BOOL
    kernel.GetCurrentProcess.restype=w.HANDLE;kernel.CloseHandle.argtypes=[w.HANDLE]
    handle=kernel.CreateJobObjectW(None,None)
    if not handle:raise c.WinError(c.get_last_error())
    limits=EXTENDED();limits.basic.flags=0x2000 # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not kernel.SetInformationJobObject(handle,9,c.byref(limits),c.sizeof(limits)):
        error=c.get_last_error();kernel.CloseHandle(handle);raise c.WinError(error)
    if not kernel.AssignProcessToJobObject(handle,kernel.GetCurrentProcess()):
        error=c.get_last_error();kernel.CloseHandle(handle);raise c.WinError(error)
    # Non-inheritable handle lives until this process exits. Closing it earlier
    # would terminate the GUI before Tk/log cleanup; the OS closes it on exit.
    _job=handle
