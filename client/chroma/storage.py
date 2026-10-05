"""Local, flat project workspace. No scanning, networking, or implicit grants."""
from pathlib import Path
import contextlib, hashlib, os, re, stat, tempfile
MAX_FILE = 1024 * 1024
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,119}\Z")

def filename(value):
    if not isinstance(value, str) or not NAME.fullmatch(value) or value.endswith((".", " ")):
        raise ValueError("Use a plain filename inside the selected project")
    if value.split(".")[0].upper() in {"CON","PRN","AUX","NUL", *("COM"+str(i) for i in range(10)), *("LPT"+str(i) for i in range(10))}:
        raise ValueError("Reserved filename")
    return value

class Workspace:
    def __init__(self, root):
        raw = Path(root).absolute()
        if not raw.is_dir(): raise ValueError("Select an existing project folder")
        if any(part.lower().startswith(("refract-studio", "refract editor")) for part in raw.parts):
            raise PermissionError("Choose a ChromaNeural workspace outside Refract reference storage")
        self.root = raw
        initial=raw.stat(follow_symlinks=False)
        self.identity=(initial.st_dev,initial.st_ino)
        self.active = True
        with self.guard(): pass

    @contextlib.contextmanager
    def guard(self):
        if not self.active: raise PermissionError("Project access revoked")
        handles = []
        try:
            if os.name == "nt":
                import ctypes
                from ctypes import wintypes as w
                k = ctypes.WinDLL("kernel32", use_last_error=True)
                k.CreateFileW.argtypes = [w.LPCWSTR,w.DWORD,w.DWORD,w.LPVOID,w.DWORD,w.DWORD,w.HANDLE]
                k.CreateFileW.restype = w.HANDLE
                k.CloseHandle.argtypes = [w.HANDLE]
                # Hold every directory without FILE_SHARE_DELETE, preventing ancestor swaps.
                for p in [*reversed(self.root.parents), self.root]:
                    h = k.CreateFileW(str(p),0x80,3,None,3,0x02000000|0x00200000,None)
                    if h == w.HANDLE(-1).value: raise OSError(ctypes.get_last_error(),str(p))
                    handles.append((k,h))
                    if p.lstat().st_file_attributes & 0x400: raise PermissionError("Reparse points are denied")
                current=self.root.stat(follow_symlinks=False)
                if (current.st_dev,current.st_ino)!=self.identity: raise PermissionError("Project directory was replaced")
                yield None
            else:
                fd = os.open("/", os.O_RDONLY|os.O_DIRECTORY)
                handles.append(fd)
                for part in self.root.parts[1:]:
                    fd = os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
                    handles.append(fd)
                current=os.fstat(fd)
                if (current.st_dev,current.st_ino)!=self.identity: raise PermissionError("Project directory was replaced")
                yield fd
        finally:
            for h in reversed(handles):
                if os.name == "nt": h[0].CloseHandle(h[1])
                else: os.close(h)

    def _target(self, name, directory):
        return str(self.root/filename(name)) if directory is None else filename(name)

    def read(self, name):
        with self.guard() as directory:
            target = self._target(name,directory)
            flags = os.O_RDONLY|getattr(os,"O_BINARY",0)|getattr(os,"O_NOFOLLOW",0)
            if directory is None and Path(target).exists():
                s=Path(target).lstat()
                if s.st_file_attributes & 0x400: raise PermissionError("Reparse file denied")
            # Windows directory is locked, but final file swaps need a native handle too.
            if os.name == "nt":
                import ctypes, msvcrt
                from ctypes import wintypes as w
                k=ctypes.WinDLL("kernel32",use_last_error=True)
                k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,w.LPVOID,w.DWORD,w.DWORD,w.HANDLE]
                k.CreateFileW.restype=w.HANDLE
                h=k.CreateFileW(target,0x80000000,1,None,3,0x00200000,None)
                if h==w.HANDLE(-1).value: raise OSError(ctypes.get_last_error(),target)
                fd=msvcrt.open_osfhandle(h,os.O_RDONLY|os.O_BINARY)
            else: fd=os.open(target,flags,dir_fd=directory)
            with os.fdopen(fd,"rb") as stream:
                s=os.fstat(stream.fileno())
                if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or s.st_size > MAX_FILE:
                    raise ValueError("Only single-link regular files up to 1 MiB")
                if getattr(s,"st_file_attributes",0)&0x400: raise PermissionError("Reparse file denied")
                data=stream.read(MAX_FILE+1)
                if len(data)>MAX_FILE: raise ValueError("File too large")
                return data

    def write(self, name, data, expected=None):
        if not isinstance(data,bytes) or len(data)>MAX_FILE: raise ValueError("File too large")
        filename(name)
        with self.guard() as directory:
            target=self._target(name,directory)
            if expected is not None:
                try: current=self.read(name)
                except FileNotFoundError: current=b""
                if hashlib.sha256(current).hexdigest()!=expected: raise RuntimeError("File changed; review again")
            # Never follow the old destination; replacement creates a new regular file.
            token=".chroma-"+os.urandom(12).hex()
            temp=str(self.root/token) if directory is None else token
            fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_BINARY",0),0o600,dir_fd=directory)
            try:
                with os.fdopen(fd,"wb") as stream:
                    stream.write(data);stream.flush();os.fsync(stream.fileno())
                if not self.active: raise PermissionError("Revoked")
                os.replace(temp,target,src_dir_fd=directory,dst_dir_fd=directory)
                if directory is not None: os.fsync(directory)
            finally:
                try: os.unlink(temp,dir_fd=directory)
                except FileNotFoundError: pass

    def revoke(self): self.active=False

class Document:
    def __init__(self, data=b""):
        self.raw=data
        self.text=data.decode("utf-8-sig")
        self.bom=data.startswith(b"\xef\xbb\xbf")
        self.newline="\r\n" if "\r\n" in self.text else "\n"
        self.display=self.text.replace("\r\n","\n")
    def encode(self,text):
        if text==self.display: return self.raw
        return (b"\xef\xbb\xbf" if self.bom else b"")+text.replace("\n",self.newline).encode("utf-8")
