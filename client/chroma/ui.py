from pathlib import Path
import json,queue,threading,time,tkinter as tk
from tkinter import filedialog,messagebox,simpledialog,ttk
from .storage import Workspace,Document,filename
from .theme import THEMES
from .policy import Policy
from .tray import Tray
from . import engine
from .i18n import LocaleContext
from .localized_dialogs import Dialogs
from .localized_views import diagnostic,ledger
class App:
    def __init__(self,root,workspace=None,standalone=True,on_network=None,on_stop=None,locale=None,settings_dir=None,mcp_secrets=None):
        self.locale=locale or LocaleContext();self.dialogs=Dialogs(root,self.locale)
        self.settings_dir=settings_dir;self.mcp_secrets=mcp_secrets if mcp_secrets is not None else {}
        self.on_network=on_network;self.on_stop=on_stop;self.closed=False
        self.root=root;self.policy=Policy();self.workspace=None;self.name=None;self.doc=Document()
        self.queue=queue.Queue();self.busy=False;self.theme_name="light"
        self.locale.title(root,(self.locale.msg('studio.local.title')));root.geometry("960x720");root.minsize(840,620);root.grid_columnconfigure(0,weight=1);root.grid_rowconfigure(3,weight=1)
        self.status=self.locale.variable(root,value=(self.locale.msg('studio.initial')))
        self.profile=tk.StringVar(value="cpl-legacy")
        self.top=tk.Frame(root);self.top.grid(row=0,column=0,sticky="ew",padx=14,pady=10)
        self.locale.widget(tk.Label,self.top,text="ChromaNeural",font=("Segoe UI",18,"bold")).pack(side="left")
        self.buttons=[]
        self.button(self.top,self.locale.msg("tools_setup.title"),self.open_setup).pack(side="right")
        self.button(self.top,(self.locale.msg('studio.theme')),self.toggle_theme).pack(side="right")
        self.button(self.top,(self.locale.msg('studio.network')),self.network_window).pack(side="right")
        self.button(self.top,(self.locale.msg('studio.stop')),self.stop).pack(side="right",padx=6)
        self.bar=tk.Frame(root);self.bar.grid(row=1,column=0,sticky="ew",padx=14)
        for label,fn in [((self.locale.msg('studio.new')),self.new_project),((self.locale.msg('studio.open')),self.open_file),((self.locale.msg('studio.save')),self.save),((self.locale.msg('studio.saveas')),lambda:self.save(True)),((self.locale.msg('studio.private')),self.private_storage),((self.locale.msg('studio.targets')),self.target_platforms)]:
            self.button(self.bar,label,fn).pack(side="left",padx=(0,5),pady=5)
        self.location=self.locale.widget(tk.Label,root,text=(self.locale.msg('studio.folder')),anchor="w")
        self.location.grid(row=2,column=0,sticky="ew",padx=16)
        self.editor=tk.Text(root,undo=True,wrap="none",font=("Consolas",12),padx=12,pady=12)
        self.editor.grid(row=3,column=0,sticky="nsew",padx=14,pady=8)
        self.tools=tk.Frame(root);self.tools.grid(row=4,column=0,sticky="ew",padx=14)
        self.select=ttk.Combobox(self.tools,textvariable=self.profile,state="readonly",width=18,values=("cpl-legacy","cpl-spec","cpa-legacy","cpa-spec","prisme-asm"))
        self.select.pack(side="left",padx=(0,8))
        for label,fn in [((self.locale.msg('studio.compile')),lambda:self.compute("compile")),((self.locale.msg('studio.simulate')),lambda:self.compute("simulate")),((self.locale.msg('studio.ai')),self.ask_local_ai),((self.locale.msg('studio.review')),self.review_proposal),((self.locale.msg('studio.hide')),self.hide)]:
            self.button(self.tools,label,fn).pack(side="left",padx=(0,5))
        self.output=tk.Text(root,height=6,wrap="word",font=("Consolas",10),padx=10,pady=8,state="disabled")
        self.output.grid(row=5,column=0,sticky="ew",padx=14,pady=8)
        self.footer=self.locale.widget(tk.Label,root,textvariable=self.status,anchor="w",font=("Segoe UI",10))
        self.footer.grid(row=6,column=0,sticky="ew",padx=16,pady=(0,10))
        self.tray=Tray(root,self.show,enabled=standalone,locale=self.locale)
        root.protocol("WM_DELETE_WINDOW",self.close)
        root.bind("<Control-s>",lambda e:self.save());root.bind("<Control-o>",lambda e:self.open_file())
        self.apply_theme()
        if workspace:self.set_workspace(workspace)
        self.poll_id=root.after(100,self.poll)

    def button(self,parent,label,fn):
        b=self.locale.widget(tk.Button,parent,text=label,command=lambda:self.safe(fn),font=("Segoe UI",10),relief="flat",padx=10,pady=7)
        self.buttons.append(b);return b
    def safe(self,fn):
        try:return fn()
        except Exception as e: self.show_output(str(e));self.dialogs.showerror("ChromaNeural",diagnostic(self.locale,e))
    def set_workspace(self,path):
        ws=Workspace(path)
        if self.workspace:self.workspace.revoke()
        self.workspace=ws;self.locale.option(self.location,str(ws.root))
    def dirty(self):return self.doc.encode(self.editor.get("1.0","end-1c"))!=self.doc.raw
    def discard_ok(self):return not self.dirty() or self.dialogs.askyesno((self.locale.msg('studio.unsaved')),(self.locale.msg('studio.discard')))
    def new_project(self):
        if not self.discard_ok():return
        base=filedialog.askdirectory(title=(self.locale.msg('studio.parent')))
        if not base:return
        name=self.dialogs.askstring((self.locale.msg('studio.new')),(self.locale.msg('studio.name')))
        if not name:return
        name=filename(name);p=Path(base)/name;p.mkdir(exist_ok=False)
        self.set_workspace(p);self.name=None;self.load(b"")
    def load(self,data):
        doc=Document(data) # Reject binary/non-UTF8 before changing current editor.
        self.doc=doc;self.editor.delete("1.0","end");self.editor.insert("1.0",doc.display);self.editor.edit_reset()
    def open_file(self):
        if not self.discard_ok():return
        path=filedialog.askopenfilename(title=(self.locale.msg('studio.open.title')),filetypes=[((self.locale.msg('file.source')),"*.cpl *.cpa *.prisme *.asm *.txt *.json"),((self.locale.msg('file.all')),"*.*")])
        if not path:return
        p=Path(path);ws=Workspace(p.parent);data=ws.read(p.name);Document(data)
        self.set_workspace(p.parent);self.name=p.name;self.load(data)
        ext=p.suffix.lower()
        if ext==".cpa":self.profile.set("cpa-legacy")
        elif ext in (".prisme",".asm"):self.profile.set("prisme-asm")
        elif ext==".cpl":self.profile.set("cpl-legacy")
    def save(self,as_new=False):
        if not self.workspace or not self.name or as_new:
            path=filedialog.asksaveasfilename(title=(self.locale.msg('studio.save.title')),initialdir=str(self.workspace.root) if self.workspace else None,initialfile=self.name or "main.cpl",defaultextension=".cpl",filetypes=[("CPL","*.cpl"),("CPA","*.cpa"),("PRISME ASM","*.prisme"),((self.locale.msg('file.text')),"*.txt"),("JSON","*.json")])
            if not path:return
            p=Path(path);self.set_workspace(p.parent);self.name=p.name
        data=self.doc.encode(self.editor.get("1.0","end-1c"))
        self.workspace.write(self.name,data);self.doc=Document(data)
        self.status.set(self.locale.msg("studio.saved.message",name=self.name))
    def compute(self,action):
        if self.busy:raise RuntimeError((self.locale.msg('studio.busy')))
        self.busy=True;source=self.editor.get("1.0","end-1c");profile=self.profile.get()
        self.status.set(self.locale.msg("studio.operation.message",action=self.locale.msg("studio."+action)))
        def job():
            try:self.queue.put((True,engine.run(profile,action,source)))
            except Exception as e:self.queue.put((False,str(e)))
        threading.Thread(target=job,daemon=True).start()
    def poll(self):
        if self.closed:return
        try:
            ok,result=self.queue.get_nowait();self.busy=False
            if ok and isinstance(result,dict) and "ai_proposal" in result:
                self.review_bytes(result["ai_proposal"],result["workspace"],result["name"])
            else:self.show_output(result.get("output","")+"\n"+result.get("state","") if ok else result)
            self.status.set(((self.locale.msg('studio.complete')) if ok else (self.locale.msg('studio.failed')))+(' ' + self.locale.msg('remote.disabled')))
        except queue.Empty:pass
        self.poll_id=self.root.after(100,self.poll)
    def show_output(self,text):
        self.output.config(state="normal");self.output.delete("1.0","end");self.output.insert("1.0",text);self.output.config(state="disabled")
    def target_platforms(self):
        from .target_ui import TargetDialog
        dialog=getattr(self,"target_dialog",None)
        if dialog and dialog.window.winfo_exists():
            dialog.window.deiconify();dialog.window.lift();return
        self.target_dialog=TargetDialog(self.root,self.profile.get(),THEMES[self.theme_name],locale=self.locale)
    def private_storage(self):
        self.dialogs.showinfo((self.locale.msg('studio.private.title')),(self.locale.msg('studio.private.info')))
    def review_proposal(self):
        if not self.workspace or not self.name or self.dirty():raise ValueError((self.locale.msg('studio.save.before')))
        path=filedialog.askopenfilename(title=(self.locale.msg('studio.proposal.file')))
        if not path:return
        from .assistance import propose,accept
        p=Path(path);proposed=Workspace(p.parent).read(p.name)
        self.review_bytes(proposed,self.workspace,self.name)
    def review_bytes(self,proposed,workspace,name):
        from .assistance import propose,accept
        proposal=propose(workspace.read(name),proposed)
        win=tk.Toplevel(self.root);self.locale.title(win,(self.locale.msg('studio.review.title')));win.geometry("800x600")
        view=tk.Text(win,wrap="none",font=("Consolas",11));view.pack(fill="both",expand=True);view.insert("1.0",proposal.diff);view.config(state="disabled")
        def apply():
            if self.workspace is not workspace or self.name!=name or self.dirty():raise RuntimeError((self.locale.msg('studio.target.changed')))
            accept(workspace,name,proposal,approved=True);self.load(proposed);win.destroy()
        self.locale.widget(tk.Button,win,text=(self.locale.msg('studio.approve')),command=lambda:self.safe(apply)).pack(pady=8)
    def open_setup(self):
        from .onboarding_ui import Wizard
        existing=getattr(self,"setup_wizard",None)
        if existing and existing.window.winfo_exists():existing.window.lift();return
        self.setup_wizard=Wizard(self.root,self.locale,self.settings_dir,self.mcp_secrets)
    def ask_local_ai(self):
        if self.busy or not self.workspace or not self.name or self.dirty():raise ValueError((self.locale.msg('studio.save.wait')))
        from .mcp_config import Config
        from .ai_provider import selection
        config=Config(self.settings_dir).load()
        selected=config["provider"]
        model=self.dialogs.askstring((self.locale.msg('studio.ai')), (self.locale.msg('studio.provider')),initialvalue=selected["model"] if selected else "bundled-cpu")
        if not model:return
        instruction=self.dialogs.askstring((self.locale.msg('studio.ai')), (self.locale.msg('studio.instruction')))
        if not instruction:return
        if not self.dialogs.askyesno((self.locale.msg('studio.consent.title')), (self.locale.msg('studio.consent'))):return
        servers=[]
        if model!="bundled-cpu":
            available=[s for s in config["servers"] if s["approved"] and s["enabled"] and s["tools"]]
            if available and self.dialogs.askyesno(self.locale.msg("tools_setup.mcp"),self.locale.msg("tools_setup.task.consent",servers=", ".join(s["name"] for s in available))):
                servers=[s["id"] for s in available]
        source=self.editor.get("1.0","end-1c");workspace=self.workspace;name=self.name;self.busy=True
        def job():
            try:
                if servers:
                    from .ai_provider import selected_inference
                    from .native_ai import infer
                    proposed=selected_inference(source,instruction,selection("ollama",model),bundled=infer,
                        mcp_servers=servers,mcp_directory=self.settings_dir,
                        mcp_secrets={s:self.mcp_secrets.get(s,"") for s in servers}).source
                else:
                    from .local_ai import suggest
                    proposed=suggest(source,model,instruction)
                self.queue.put((True,{"ai_proposal":proposed,"workspace":workspace,"name":name}))
            except Exception as e:self.queue.put((False,str(e)))
        threading.Thread(target=job,daemon=True).start()
    def network_window(self):
        if self.on_network:return self.on_network()
        from .network_state import NetworkState
        if getattr(self,"network_dialog",None) and self.network_dialog.winfo_exists():
            self.network_dialog.lift();return
        win=tk.Toplevel(self.root);self.network_dialog=win;self.locale.title(win,(self.locale.msg('studio.network.title')));win.geometry("850x340")
        text=self.locale.variable(win,value=(self.locale.msg('studio.network.none')))
        label=self.locale.widget(tk.Label,win,textvariable=text,justify="left",wraplength=800,padx=18,pady=18);label.pack(fill="both",expand=True)
        config={"path":None,"state":None,"busy":False};self.network_config=config;results=queue.Queue()
        def choose():
            path=filedialog.askopenfilename(title=(self.locale.msg('studio.network.choose')),filetypes=[("JSON","*.json")])
            if path:
                from pathlib import Path
                config["path"]=path;config["state"]=NetworkState(Path(path).with_suffix(".balance-cache.json"))
                config["state"].network_enabled=True
                refresh()
        def refresh():
            if not win.winfo_exists() or not config["path"] or config["busy"] or not config["state"].network_enabled:return
            config["busy"]=True
            def job():
                try:
                    from .icp_client import call
                    results.put((True,call(config["path"],"balance")))
                except Exception as e:results.put((False,str(e)))
            threading.Thread(target=job,daemon=True).start()
        def poll():
            if not win.winfo_exists():return
            try:
                ok,data=results.get_nowait();config["busy"]=False
                try:
                    if ok:config["state"].update(data)
                    else:config["state"].unavailable(data)
                except Exception as e:config["state"].unavailable(str(e))
                text.set(ledger(self.locale,config["state"]))
            except queue.Empty:pass
            win.after(250,poll)
        self.locale.widget(tk.Button,win,text=(self.locale.msg('studio.network.select')),command=choose).pack(pady=8)
        self.locale.widget(tk.Button,win,text=(self.locale.msg('studio.network.refresh')),command=refresh).pack(pady=8)
        def periodic():
            if win.winfo_exists():
                refresh();win.after(30000,periodic)
        win.after(250,poll);win.after(30000,periodic);self.apply_theme()

    def stop(self):
        if self.on_stop:self.on_stop()
        self.policy.stop()
        config=getattr(self,"network_config",None)
        if config and config["state"]:
            config["state"].network_enabled=False;config["state"].sharing_enabled=False
        self.status.set((self.locale.msg('studio.network.stopped')))
    def hide(self):
        if not self.tray.available:raise RuntimeError((self.locale.msg('studio.tray.error')))
        self.root.withdraw()
    def show(self):self.root.deiconify();self.root.lift()
    def close(self):
        if not self.discard_ok():return
        self.shutdown()
    def shutdown(self):
        self.closed=True
        if hasattr(self,"poll_id"):self.root.after_cancel(self.poll_id)
        self.tray.close()
        if self.workspace:self.workspace.revoke()
        self.root.destroy()
    def toggle_theme(self):
        self.theme_name="dark" if self.theme_name=="light" else "light";self.apply_theme()
    def apply_theme(self):
        t=THEMES[self.theme_name]
        def visit(widget):
            if isinstance(widget,(tk.Frame,tk.Tk,tk.Toplevel)):widget.config(bg=t["bg"])
            elif isinstance(widget,tk.Label):widget.config(bg=t["bg"],fg=t["fg"])
            elif isinstance(widget,tk.Button):widget.config(bg=t["accent"],fg=t["on_accent"],activebackground=t["accent"],activeforeground=t["on_accent"])
            for child in widget.winfo_children():visit(child)
        visit(self.root)
        for w in (self.editor,self.output):w.config(bg=t["panel"],fg=t["fg"],insertbackground=t["fg"],selectbackground=t["accent"],selectforeground=t["on_accent"])
        dialog=getattr(self,"target_dialog",None)
        if dialog and dialog.window.winfo_exists():dialog.apply_theme(t)
        style=ttk.Style();style.theme_use("clam")
        style.configure("TCombobox",fieldbackground=t["panel"],background=t["panel"],foreground=t["fg"],arrowcolor=t["fg"])
        style.map("TCombobox",fieldbackground=[("readonly",t["panel"])],foreground=[("readonly",t["fg"])],selectbackground=[("readonly",t["accent"])],selectforeground=[("readonly",t["on_accent"])])
