"""Opt-in limits for fixed bundled inference. Never controls the owner's manual AI."""
import os,sys,time,copy,contextlib

class WorkerBlocked(RuntimeError):pass
class WorkerCancelled(RuntimeError):pass

def environment():
    """Current interactive Windows session; unknown power/input fails closed."""
    if os.name!='nt':raise WorkerBlocked('Controlled worker unsupported on this OS')
    import ctypes as c
    from ctypes import wintypes as w
    class INPUT(c.Structure):_fields_=[('size',w.UINT),('tick',w.DWORD)]
    class POWER(c.Structure):
        _fields_=[('ac',w.BYTE),('flags',w.BYTE),('percent',w.BYTE),('reserved',w.BYTE),('life',w.DWORD),('full',w.DWORD)]
    k=c.WinDLL('kernel32',use_last_error=True);u=c.WinDLL('user32',use_last_error=True)
    info=INPUT(c.sizeof(INPUT),0);power=POWER()
    k.GetTickCount.restype=w.DWORD
    if not u.GetLastInputInfo(c.byref(info)) or not k.GetSystemPowerStatus(c.byref(power)):
        raise WorkerBlocked('Idle/battery observation unavailable')
    return {'idle_seconds':((k.GetTickCount()-info.tick)&0xffffffff)/1000,'ac':power.ac}

@contextlib.contextmanager
def queue_lock(path):
    """One controlled inference per existing queue, including across processes."""
    path=str(path)+'.worker-lock'
    if os.path.islink(path):raise WorkerBlocked('Worker lock symlink')
    with open(path,'a+b') as f:
        if os.fstat(f.fileno()).st_size==0:f.write(b'0');f.flush()
        f.seek(0)
        if os.name!='nt':raise WorkerBlocked('Controlled worker unsupported on this OS')
        import msvcrt
        try:msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:yield False;return
        try:yield True
        finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)

class WorkerResources:
    def __init__(self,resources,allowed):
        self.resources=copy.deepcopy(resources);self.allowed=allowed;self.job=None
        self.deadline=None;self.check_claim=lambda:True
    def check(self):
        if not self.allowed() or not self.check_claim():raise WorkerCancelled('Worker paused, stopped, reconfigured or cancelled')
        if self.deadline is not None and time.monotonic()>=self.deadline:raise TimeoutError('Controlled inference deadline exceeded')
        r=self.resources
        if os.name!='nt' or sys.maxsize<=2**32:raise WorkerBlocked('Controlled profile requires Windows x64')
        if r.get('cpu') is not True or r.get('gpu') is not False:raise WorkerBlocked('CPU opt-in required; GPU unsupported')
        if type(r.get('threads')) is not int or not 1<=r['threads']<=8:raise WorkerBlocked('Unsupported threads')
        if type(r.get('ram_mib')) is not int or r['ram_mib'] not in (512,1024,2048,4096,8192):raise WorkerBlocked('Unsupported RAM limit')
        if any(type(r.get(k)) is not bool for k in ('idle_only','pause_on_battery')):raise WorkerBlocked('Missing activity policy')
        if r['idle_only'] or r['pause_on_battery']:
            e=environment()
            if r['idle_only'] and e['idle_seconds']<60:raise WorkerBlocked('Waiting for 60 seconds without user input')
            if r['pause_on_battery'] and e['ac']!=1:raise WorkerBlocked('AC power not confirmed')
    def supports(self,choice):
        if choice is not None:raise WorkerBlocked('External Ollama service has no controlled CPU/RAM/cancellation profile')
        self.check()
    def inference(self,source,instruction,bundled):
        self.check();self.deadline=time.monotonic()+90
        try:
            with WindowsJob(self.resources['threads'],self.resources['ram_mib']) as self.job:
                return bundled(source,instruction,timeout=90,threads=self.resources['threads'],execution=self)
        finally:self.job=None;self.deadline=None
    def spawn(self,cmd,*,stdout,stderr,env,**unused):
        self.check()
        if self.job is None:raise WorkerBlocked('Missing resource job')
        return self.job.spawn(cmd,stdout,stderr,env)

class WindowsJob:
    """Windows 10+ atomic job assignment, affinity and aggregate committed-memory cap.

    One fixed inference process, no breakaway or child processes. Not a sandbox for
    arbitrary code and not a quota on shared OS cache or the whole desktop client.
    """
    def __init__(self,threads,ram_mib):
        if os.name!='nt':raise WorkerBlocked('Windows Job Objects required')
        import ctypes as c
        from ctypes import wintypes as w
        self.c=c;self.w=w;self.k=c.WinDLL('kernel32',use_last_error=True);self.handle=None
        class BASIC(c.Structure):
            _fields_=[('processTime',c.c_longlong),('jobTime',c.c_longlong),('flags',w.DWORD),('minWorkingSet',c.c_size_t),('maxWorkingSet',c.c_size_t),('activeProcesses',w.DWORD),('affinity',c.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
        class IO(c.Structure):_fields_=[(n,c.c_ulonglong) for n in ('readOps','writeOps','otherOps','readBytes','writeBytes','otherBytes')]
        class LIMITS(c.Structure):_fields_=[('basic',BASIC),('io',IO),('processMemory',c.c_size_t),('jobMemory',c.c_size_t),('peakProcessMemory',c.c_size_t),('peakJobMemory',c.c_size_t)]
        self.LIMITS=LIMITS
        self.k.GetActiveProcessorGroupCount.restype=w.WORD
        if self.k.GetActiveProcessorGroupCount()!=1:raise WorkerBlocked('Multiple CPU groups are not verified for this profile')
        signatures={
          'CreateJobObjectW':([c.c_void_p,w.LPCWSTR],w.HANDLE),
          'SetInformationJobObject':([w.HANDLE,c.c_int,c.c_void_p,w.DWORD],w.BOOL),
          'QueryInformationJobObject':([w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.c_void_p],w.BOOL),
          'GetCurrentProcess':([],w.HANDLE),
          'GetProcessAffinityMask':([w.HANDLE,c.POINTER(c.c_size_t),c.POINTER(c.c_size_t)],w.BOOL),
          'CloseHandle':([w.HANDLE],w.BOOL),
          'DuplicateHandle':([w.HANDLE,w.HANDLE,w.HANDLE,c.POINTER(w.HANDLE),w.DWORD,w.BOOL,w.DWORD],w.BOOL),
          'InitializeProcThreadAttributeList':([c.c_void_p,w.DWORD,w.DWORD,c.POINTER(c.c_size_t)],w.BOOL),
          'UpdateProcThreadAttribute':([c.c_void_p,w.DWORD,c.c_size_t,c.c_void_p,c.c_size_t,c.c_void_p,c.c_void_p],w.BOOL),
          'DeleteProcThreadAttributeList':([c.c_void_p],None),
          'CreateProcessW':([w.LPCWSTR,w.LPWSTR,c.c_void_p,c.c_void_p,w.BOOL,w.DWORD,c.c_void_p,w.LPCWSTR,c.c_void_p,c.c_void_p],w.BOOL),
          'WaitForSingleObject':([w.HANDLE,w.DWORD],w.DWORD),
          'GetExitCodeProcess':([w.HANDLE,c.POINTER(w.DWORD)],w.BOOL),
          'TerminateJobObject':([w.HANDLE,w.UINT],w.BOOL)}
        for name,(args,result) in signatures.items():fn=getattr(self.k,name);fn.argtypes=args;fn.restype=result
        current=c.c_size_t();system=c.c_size_t()
        self.ok(self.k.GetProcessAffinityMask(self.k.GetCurrentProcess(),c.byref(current),c.byref(system)))
        bits=[1<<i for i in range(c.sizeof(c.c_size_t)*8) if current.value&(1<<i)]
        if not bits:raise WorkerBlocked('CPU affinity unavailable')
        self.affinity=sum(bits[:threads]);self.memory=ram_mib*1024*1024
        self.handle=self.k.CreateJobObjectW(None,None)
        if not self.handle:raise c.WinError(c.get_last_error())
        try:
            limits=LIMITS();limits.basic.flags=0x2000|0x200|0x10|0x8
            limits.basic.affinity=self.affinity;limits.basic.activeProcesses=1;limits.jobMemory=self.memory
            self.ok(self.k.SetInformationJobObject(self.handle,9,c.byref(limits),c.sizeof(limits)))
            observed=self.limits()
            if observed.basic.flags!=limits.basic.flags or observed.basic.affinity!=self.affinity or observed.jobMemory!=self.memory:
                raise WorkerBlocked('OS did not retain requested limits')
        except BaseException:self.close();raise
    def ok(self,result):
        if not result:raise self.c.WinError(self.c.get_last_error())
    def limits(self):
        value=self.LIMITS();self.ok(self.k.QueryInformationJobObject(self.handle,9,self.c.byref(value),self.c.sizeof(value),None));return value
    def __enter__(self):return self
    def __exit__(self,*a):self.close()
    def close(self):
        if self.handle:self.k.CloseHandle(self.handle);self.handle=None
    def spawn(self,cmd,stdout,stderr,env):
        import msvcrt,subprocess
        c=self.c;w=self.w;k=self.k
        class START(c.Structure):
            _fields_=[('cb',w.DWORD),('reserved',w.LPWSTR),('desktop',w.LPWSTR),('title',w.LPWSTR)]+[(n,w.DWORD) for n in ('x','y','width','height','cx','cy','fill','flags')]+[('show',w.WORD),('reservedSize',w.WORD),('reservedBytes',c.c_void_p),('stdin',w.HANDLE),('stdout',w.HANDLE),('stderr',w.HANDLE)]
        class EX(c.Structure):_fields_=[('start',START),('attributes',c.c_void_p)]
        class PI(c.Structure):_fields_=[('process',w.HANDLE),('thread',w.HANDLE),('pid',w.DWORD),('tid',w.DWORD)]
        inherited=[];attributes=None;initialized=False
        try:
            with open(os.devnull,'rb') as null:
                for stream in (null,stdout,stderr):
                    target=w.HANDLE();self.ok(k.DuplicateHandle(k.GetCurrentProcess(),msvcrt.get_osfhandle(stream.fileno()),k.GetCurrentProcess(),c.byref(target),0,True,2));inherited.append(target.value)
                size=c.c_size_t();k.InitializeProcThreadAttributeList(None,2,0,c.byref(size))
                attributes=c.create_string_buffer(size.value)
                self.ok(k.InitializeProcThreadAttributeList(attributes,2,0,c.byref(size)));initialized=True
                jobs=(w.HANDLE*1)(self.handle);handles=(w.HANDLE*3)(*inherited)
                self.ok(k.UpdateProcThreadAttribute(attributes,0,0x2000D,jobs,c.sizeof(jobs),None,None))
                self.ok(k.UpdateProcThreadAttribute(attributes,0,0x20002,handles,c.sizeof(handles),None,None))
                start=EX();start.start.cb=c.sizeof(EX);start.start.flags=0x100;start.start.stdin,start.start.stdout,start.start.stderr=inherited;start.attributes=c.cast(attributes,c.c_void_p)
                info=PI();command=c.create_unicode_buffer(subprocess.list2cmdline(cmd))
                block=c.create_unicode_buffer('\0'.join(k+'='+v for k,v in sorted(env.items()))+'\0\0')
                self.ok(k.CreateProcessW(str(cmd[0]),command,None,None,True,0x08000000|0x00080000|0x400,block,None,c.byref(start),c.byref(info)))
                k.CloseHandle(info.thread)
                return JobProcess(self,info.process,info.pid)
        finally:
            if initialized:k.DeleteProcThreadAttributeList(attributes)
            for handle in inherited:k.CloseHandle(handle)

class JobProcess:
    def __init__(self,job,handle,pid):self.job=job;self.handle=handle;self.pid=pid;self.returncode=None
    def poll(self):
        if self.returncode is not None:return self.returncode
        status=self.job.k.WaitForSingleObject(self.handle,0)
        if status==258:return None
        if status!=0:raise self.job.c.WinError(self.job.c.get_last_error())
        code=self.job.w.DWORD();self.job.ok(self.job.k.GetExitCodeProcess(self.handle,self.job.c.byref(code)));self.returncode=code.value
        return self.returncode
    def kill(self):self.job.ok(self.job.k.TerminateJobObject(self.job.handle,1))
    def wait(self,timeout):
        status=self.job.k.WaitForSingleObject(self.handle,int(timeout*1000))
        if status!=0:raise TimeoutError('Controlled worker did not terminate')
        result=self.poll();self.job.k.CloseHandle(self.handle);self.handle=None;return result
