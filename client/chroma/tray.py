"""Native Windows notification icon and controls; no extra GUI runtime."""
import os,queue,sys
from pathlib import Path
from .i18n import LocaleContext
class Tray:
    def __init__(self,root,on_open,on_pause=None,on_resources=None,on_quit=None,enabled=True,locale=None):
        self.locale=locale or LocaleContext()
        self.available=False;self.root=root;self.on_open=on_open;self.on_pause=on_pause;self.on_resources=on_resources;self.on_quit=on_quit
        self.events=queue.SimpleQueue();self.poll_id=None
        self.version4=False;self.paused=False;self.closed=False;self.tooltip="ChromaNeural";self.owns_icon=False
        if os.name!="nt" or not enabled:return
        import ctypes as c
        from ctypes import wintypes as w
        self.c=c;self.user=c.WinDLL("user32",use_last_error=True);self.shell=c.WinDLL("shell32",use_last_error=True)
        class NID(c.Structure):
            _fields_=[("cbSize",w.DWORD),("hWnd",w.HWND),("uID",w.UINT),("uFlags",w.UINT),("uCallbackMessage",w.UINT),("hIcon",w.HICON),("szTip",w.WCHAR*128),("dwState",w.DWORD),("dwStateMask",w.DWORD),("szInfo",w.WCHAR*256),("uVersion",w.UINT),("szInfoTitle",w.WCHAR*64),("dwInfoFlags",w.DWORD),("guid",c.c_byte*16),("hBalloonIcon",w.HICON)]
        self.user.LoadIconW.argtypes=[w.HINSTANCE,c.c_void_p];self.user.LoadIconW.restype=w.HICON
        self.user.LoadImageW.argtypes=[w.HINSTANCE,w.LPCWSTR,w.UINT,c.c_int,c.c_int,w.UINT];self.user.LoadImageW.restype=w.HANDLE
        self.user.DestroyIcon.argtypes=[w.HICON];self.user.DestroyIcon.restype=w.BOOL
        self.user.GetAncestor.argtypes=[w.HWND,w.UINT];self.user.GetAncestor.restype=w.HWND
        self.user.DefWindowProcW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];self.user.DefWindowProcW.restype=c.c_ssize_t
        self.user.CreateWindowExW.argtypes=[w.DWORD,w.LPCWSTR,w.LPCWSTR,w.DWORD,c.c_int,c.c_int,c.c_int,c.c_int,w.HWND,w.HMENU,w.HINSTANCE,c.c_void_p];self.user.CreateWindowExW.restype=w.HWND
        self.user.DestroyWindow.argtypes=[w.HWND];self.user.DestroyWindow.restype=w.BOOL
        self.user.UnregisterClassW.argtypes=[w.LPCWSTR,w.HINSTANCE];self.user.UnregisterClassW.restype=w.BOOL
        kernel=c.WinDLL('kernel32',use_last_error=True);kernel.GetModuleHandleW.argtypes=[w.LPCWSTR];kernel.GetModuleHandleW.restype=w.HINSTANCE
        self.instance=kernel.GetModuleHandleW(None)
        self.user.RegisterWindowMessageW.argtypes=[w.LPCWSTR];self.user.RegisterWindowMessageW.restype=w.UINT
        self.user.CreatePopupMenu.restype=w.HMENU
        self.user.AppendMenuW.argtypes=[w.HMENU,w.UINT,c.c_size_t,w.LPCWSTR];self.user.AppendMenuW.restype=w.BOOL
        self.user.TrackPopupMenu.argtypes=[w.HMENU,w.UINT,c.c_int,c.c_int,c.c_int,w.HWND,c.c_void_p];self.user.TrackPopupMenu.restype=w.UINT
        self.user.DestroyMenu.argtypes=[w.HMENU];self.user.DestroyMenu.restype=w.BOOL
        self.user.GetCursorPos.argtypes=[c.POINTER(w.POINT)];self.user.GetCursorPos.restype=w.BOOL
        self.user.SetForegroundWindow.argtypes=[w.HWND];self.user.SetForegroundWindow.restype=w.BOOL
        self.user.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];self.user.PostMessageW.restype=w.BOOL
        self.shell.Shell_NotifyIconW.argtypes=[w.DWORD,c.POINTER(NID)];self.shell.Shell_NotifyIconW.restype=w.BOOL
        self.nid=NID();self.nid.cbSize=c.sizeof(NID);self.nid.uID=1;self.nid.uFlags=1|2|4|0x80
        self.nid.uCallbackMessage=0x8001
        icon=Path(__file__).resolve().parents[1]/"assets/chroma.ico"
        loaded=self.user.LoadImageW(None,str(icon),1,32,32,0x10) if icon.exists() else None
        self.nid.hIcon=loaded or self.user.LoadIconW(None,32512);self.owns_icon=bool(loaded);self.nid.szTip=self.tooltip
        self.taskbar_message=self.user.RegisterWindowMessageW("TaskbarCreated")
        PROC=c.WINFUNCTYPE(c.c_ssize_t,w.HWND,w.UINT,w.WPARAM,w.LPARAM)
        def callback(h,m,wp,lp):
            if not self.closed and m==self.taskbar_message:self.events.put(self._add);return 0
            if not self.closed and m==0x8001:
                event=lp&0xFFFF
                if event==0x7B or (event==0x205 and not self.version4):self.events.put(self.menu);return 0
                if (self.version4 and event in (0x400,0x401)) or (not self.version4 and event in (0x202,0x203)):self.events.put(on_open);return 0
            return self.user.DefWindowProcW(h,m,wp,lp)
        # Never subclass Tk's HWND or call Tcl/Tk from a native WndProc.
        # A non-visible top-level tool window receives shell broadcasts for the
        # lifetime of the tray. It uses the existing Tk thread's message pump.
        self.proc=PROC(callback)
        class WNDCLASS(c.Structure):
            _fields_=[('style',w.UINT),('proc',c.c_void_p),('classExtra',c.c_int),('windowExtra',c.c_int),('instance',w.HINSTANCE),('icon',w.HICON),('cursor',w.HANDLE),('brush',w.HBRUSH),('menu',w.LPCWSTR),('name',w.LPCWSTR)]
        self.class_name='ChromaNeuralTray.'+str(os.getpid())+'.'+str(id(self))
        wc=WNDCLASS();wc.proc=c.cast(self.proc,c.c_void_p).value;wc.instance=self.instance;wc.name=self.class_name
        self.user.RegisterClassW.argtypes=[c.POINTER(WNDCLASS)];self.user.RegisterClassW.restype=w.WORD
        if not self.user.RegisterClassW(c.byref(wc)):raise c.WinError(c.get_last_error())
        self.nid.hWnd=self.user.CreateWindowExW(0x80,self.class_name,'ChromaNeural tray',0,0,0,0,0,None,None,self.instance,None)
        if not self.nid.hWnd:
            error=c.get_last_error();self.user.UnregisterClassW(self.class_name,self.instance);raise c.WinError(error)
        self._add()
        self.poll_id=root.after(50,self._drain_events)
    def _drain_events(self):
        if self.closed:return
        while not self.events.empty():
            callback=self.events.get_nowait()
            try:callback()
            except Exception:self.root.report_callback_exception(*sys.exc_info())
            if self.closed:return
        self.poll_id=self.root.after(50,self._drain_events)
    def _add(self):
        self.available=bool(self.shell.Shell_NotifyIconW(0,self.c.byref(self.nid)))
        if self.available:
            self.nid.uVersion=4;self.version4=bool(self.shell.Shell_NotifyIconW(4,self.c.byref(self.nid)))
    def update(self,text,paused=False):
        self.paused=paused
        if self.tooltip==text or not self.available:return
        self.tooltip=text[:127];self.nid.szTip=self.tooltip
        if not self.shell.Shell_NotifyIconW(1,self.c.byref(self.nid)):self.available=False
    def commands(self):
        return [(1,(self.locale.msg('tray.open')),self.on_open),
                (2,(self.locale.msg('action.resume')) if self.paused else (self.locale.msg('tray.pause')),self.on_pause),
                (3,(self.locale.msg('nav.resources')),self.on_resources),(4,(self.locale.msg('common.exit')),self.on_quit)]
    def dispatch(self,command):
        for key,_,callback in self.commands():
            if key==command and callback:self.root.after_idle(callback);return
    def menu(self):
        if not self.available:return
        from ctypes import wintypes as w
        menu=self.user.CreatePopupMenu()
        try:
            for key,label,callback in self.commands():
                if callback:self.user.AppendMenuW(menu,0,key,str(label))
            point=w.POINT();self.user.GetCursorPos(self.c.byref(point));self.user.SetForegroundWindow(self.nid.hWnd)
            choice=self.user.TrackPopupMenu(menu,0x100|0x80|0x2,point.x,point.y,0,self.nid.hWnd,None)
            self.user.PostMessageW(self.nid.hWnd,0,0,0);self.dispatch(choice)
        finally:self.user.DestroyMenu(menu)
    def close(self):
        if self.closed:return
        self.closed=True
        if self.poll_id is not None:self.root.after_cancel(self.poll_id);self.poll_id=None
        if hasattr(self,"nid"):
            self.shell.Shell_NotifyIconW(2,self.c.byref(self.nid))
            self.user.DestroyWindow(self.nid.hWnd);self.user.UnregisterClassW(self.class_name,self.instance)
            if self.owns_icon:self.user.DestroyIcon(self.nid.hIcon)
        self.available=False
