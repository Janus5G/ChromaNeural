"""Task-level point consent. No MCP connection or tool invocation in this dialog."""
import queue, threading, tkinter as tk
from .mcp_usage import Usage, POINT, task_digest

def points(value):
    return f"{value // POINT}.{value % POINT:06d}"

class Consent:
    def __init__(self,parent,locale,directory,servers,source,instruction,model,*,usage=None):
        self.locale=locale;self.usage=usage or Usage(directory);self.servers=servers
        self.identifiers=[s["id"] for s in servers]
        self.request=task_digest(source,instruction,model,self.identifiers)
        self.result=None;self.closed=False;self.busy=False;self.quote=None
        self.queue=queue.Queue();self.delivery_lock=threading.Lock();self.window=tk.Toplevel(parent)
        self.window.geometry("670x520");self.window.minsize(620,490)
        self.window.transient(parent);locale.title(self.window,locale.msg("usage.title"))
        locale.widget(tk.Label,self.window,text=locale.msg("usage.title"),font=("Segoe UI",17,"bold"),
                      anchor="w").pack(fill="x",padx=22,pady=(20,12))
        locale.widget(tk.Label,self.window,text=locale.msg("usage.optional"),justify="left",
                      wraplength=610,anchor="w").pack(fill="x",padx=22)
        locale.widget(tk.Label,self.window,text=locale.msg("usage.connections",names=", ".join(s["name"] for s in servers)),
                      justify="left",wraplength=610,anchor="w").pack(fill="x",padx=22,pady=10)
        self.summary=locale.variable(self.window,locale.msg("usage.loading"))
        locale.widget(tk.Label,self.window,textvariable=self.summary,justify="left",
                      wraplength=610,anchor="w",font=("Segoe UI",11)).pack(fill="both",expand=True,padx=22,pady=12)
        locale.widget(tk.Label,self.window,text=locale.msg("usage.rule"),justify="left",
                      wraplength=610,anchor="w").pack(fill="x",padx=22,pady=10)
        row=tk.Frame(self.window);row.pack(fill="x",padx=18,pady=16)
        self.approve=locale.widget(tk.Button,row,text=locale.msg("usage.approve"),command=self.accept,state="disabled")
        self.approve.pack(side="left",padx=4)
        self.local=locale.widget(tk.Button,row,text=locale.msg("usage.local"),command=lambda:self.close(([],None)))
        self.local.pack(side="left",padx=4)
        self.cancel=locale.widget(tk.Button,row,text=locale.msg("usage.cancel"),command=lambda:self.close(None))
        self.cancel.pack(side="right",padx=4)
        self.window.protocol("WM_DELETE_WINDOW",lambda:self.close(None))
        self.window.grab_set()
        self.poll_id=self.window.after(80,self.poll)
        self.start("quote",self.usage.quote)

    def start(self,kind,fn):
        self.busy=True;self.approve.configure(state="disabled")
        def run():
            try:
                value=fn()
                with self.delivery_lock:
                    abandoned=self.closed
                    if not abandoned:self.queue.put((kind,True,value))
                if abandoned and kind=="reserve":
                    self.usage.finish(value[0])
            except Exception:
                self.queue.put((kind,False,None))
        threading.Thread(target=run,daemon=True).start()

    def poll(self):
        if self.closed:return
        try:
            kind,ok,value=self.queue.get_nowait();self.busy=False
            # No numeric quote or approval may be invented while normalization
            # is unavailable, even if a stale dialog worker returns old v1 data.
            self.quote=None;self.summary.set(self.locale.msg("usage.unavailable"))
        except queue.Empty:pass
        self.poll_id=self.window.after(80,self.poll)

    def accept(self):
        # Resource policy v2 is not activated. Only local-only/cancel are available.
        self.quote=None;self.approve.configure(state="disabled")
        self.summary.set(self.locale.msg("usage.unavailable"))

    def close(self,result):
        if self.closed:return
        with self.delivery_lock:
            self.result=result;self.closed=True
        self.window.after_cancel(self.poll_id)
        # If reservation completed before cancellation but its event is pending,
        # attempt cleanup; blocked or ambiguous state stays preserved.
        while True:
            try:
                kind,ok,value=self.queue.get_nowait()
                if kind=="reserve" and ok and (result is None or result[1]!=value[0]):
                    try:self.usage.finish(value[0])
                    except Exception:pass # Reconciliation remains required; never assume a refund.
            except queue.Empty:break
        self.window.grab_release();self.window.destroy()

def confirm_task(parent,locale,directory,servers,source,instruction,model):
    dialog=Consent(parent,locale,directory,servers,source,instruction,model)
    parent.wait_window(dialog.window)
    return dialog.result