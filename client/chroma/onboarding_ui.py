"""Integrated, explicit AI and MCP setup. No automatic discovery, install or approval."""
import json, queue, threading, tkinter as tk, uuid
from tkinter import ttk, filedialog
from .ai_provider import selection
from .mcp_config import Config, fingerprint, connection_key
from .localized_dialogs import Dialogs
from .onboarding import discover, discover_mcp, test_provider

class Wizard:
    def __init__(self, parent, locale, directory=None, secrets=None):
        self.locale = locale
        self.config = Config(directory)
        self.secrets = secrets if secrets is not None else {}
        self.window = tk.Toplevel(parent)
        self.window.geometry("940x720")
        self.window.minsize(820,640)
        self.window.transient(parent)
        locale.title(self.window, locale.msg("tools_setup.title"))
        self.dialogs = Dialogs(self.window, locale)
        self.results = queue.Queue()
        self.busy = False
        self.providers = []
        self.discovered = {}
        self.connection_states = {}
        self.status = locale.variable(self.window, locale.msg("tools_setup.ready"))
        self.label(self.window, "tools_setup.intro", wraplength=860).pack(fill="x", padx=20, pady=12)
        self.tabs = ttk.Notebook(self.window)
        self.tabs.pack(fill="both", expand=True, padx=18)
        self.ai = tk.Frame(self.tabs)
        self.mcp = tk.Frame(self.tabs)
        self.review = tk.Frame(self.tabs)
        for frame, key in [(self.ai,"tools_setup.ai"),(self.mcp,"tools_setup.mcp"),(self.review,"tools_setup.review")]:
            self.tabs.add(frame, text=locale.text(key))
        self.label(self.ai,"tools_setup.discovery",wraplength=840).pack(fill="x",padx=12,pady=14)
        self.provider_list = tk.Listbox(self.ai, height=9, exportselection=False)
        self.provider_list.pack(fill="both",expand=True,padx=12)
        actions = tk.Frame(self.ai); actions.pack(fill="x",padx=12,pady=10)
        self.button(actions,"tools_setup.discover",lambda:self.run(discover,self.found_providers)).pack(side="left",padx=4)
        self.button(actions,"tools_setup.select",self.select_provider).pack(side="left",padx=4)
        self.button(actions,"tools_setup.test",self.test_ai).pack(side="left",padx=4)
        self.selected = locale.variable(self.ai)
        self.locale.widget(tk.Label,self.ai,textvariable=self.selected,anchor="w",wraplength=820).pack(fill="x",padx=12,pady=12)
        self.label(self.mcp,"tools_setup.trust",wraplength=840).pack(fill="x",padx=12,pady=10)
        self.server_list = tk.Listbox(self.mcp,height=5,exportselection=False)
        self.server_list.pack(fill="x",padx=12)
        self.server_list.bind("<<ListboxSelect>>",lambda _:self.show_tools())
        row = tk.Frame(self.mcp);row.pack(fill="x",padx=12,pady=6)
        for key,command in [("tools_setup.add",lambda:self.edit()),("tools_setup.edit",lambda:self.edit(self.current())),
                            ("tools_setup.approve",self.approve),("tools_setup.test",self.test_mcp),
                            ("tools_setup.revoke",self.revoke),("tools_setup.remove",self.remove)]:
            self.button(row,key,command).pack(side="left",padx=3)
        self.tool_list=tk.Listbox(self.mcp,height=5,selectmode="multiple",exportselection=False)
        self.tool_list.pack(fill="both",expand=True,padx=12)
        self.tool_list.bind("<<ListboxSelect>>",lambda _:self.tool_details())
        self.details=tk.Text(self.mcp,height=4,wrap="word",state="disabled")
        self.details.pack(fill="x",padx=12,pady=4)
        row=tk.Frame(self.mcp);row.pack(fill="x",padx=12,pady=8)
        for key,command in [("tools_setup.allow",self.allow_tools),("tools_setup.enable",lambda:self.enable(True)),
                            ("tools_setup.disable",lambda:self.enable(False))]:
            self.button(row,key,command).pack(side="left",padx=3)
        self.label(self.review,"tools_setup.boundary",wraplength=820).pack(fill="x",padx=16,pady=18)
        self.summary=locale.variable(self.review)
        self.locale.widget(tk.Label,self.review,textvariable=self.summary,justify="left",anchor="nw",
                           wraplength=820).pack(fill="both",expand=True,padx=16,pady=10)
        self.locale.widget(tk.Label,self.window,textvariable=self.status,anchor="w",wraplength=850).pack(fill="x",padx=20,pady=8)
        self.button(self.window,"tools_setup.close",self.window.destroy).pack(anchor="e",padx=20,pady=(0,12))
        locale.listen(self.window,self.refresh)
        self.refresh()
        self.window.after(100,self.poll)

    def label(self,parent,key,**kw):
        return self.locale.widget(tk.Label,parent,text=self.locale.msg(key),justify="left",anchor="w",**kw)

    def button(self,parent,key,command):
        return self.locale.widget(tk.Button,parent,text=self.locale.msg(key),command=lambda:self.safe(command),padx=8,pady=7)

    def safe(self,command):
        try:
            command()
        except Exception:
            self.status.set(self.locale.msg("tools_setup.error"))

    def run(self,work,done):
        if self.busy:
            return
        self.busy=True
        self.status.set(self.locale.msg("tools_setup.working"))
        def job():
            try:self.results.put((True,work(),done))
            except Exception:self.results.put((False,None,done))
        threading.Thread(target=job,daemon=True).start()

    def poll(self):
        if not self.window.winfo_exists():return
        try:
            ok,value,done=self.results.get_nowait()
            self.busy=False
            if ok:
                self.status.set(self.locale.msg("tools_setup.success"))
                self.safe(lambda:done(value))
            else:
                self.status.set(self.locale.msg("tools_setup.error"));self.refresh()
        except queue.Empty:pass
        self.window.after(100,self.poll)

    def found_providers(self,items):
        self.providers=items
        self.provider_list.delete(0,"end")
        for item in items:
            self.provider_list.insert("end",item["provider"]+" / "+(item["model"] or "bundled-cpu")+"  "+item["endpoint"])
        if not items:self.status.set(self.locale.msg("tools_setup.none"))

    def select_provider(self):
        item=self.providers[self.provider_list.curselection()[0]]
        self.config.select(selection(item["provider"],item["model"]))
        self.refresh()

    def test_ai(self):
        choice=self.config.load()["provider"]
        if self.dialogs.askyesno(self.locale.msg("tools_setup.test"),self.locale.msg("tools_setup.inference.consent")):
            self.run(lambda:test_provider(choice),lambda _:None)

    def refresh(self):
        for frame,key in [(self.ai,"tools_setup.ai"),(self.mcp,"tools_setup.mcp"),(self.review,"tools_setup.review")]:
            self.tabs.tab(frame,text=self.locale.text(key))
        value=self.config.load()
        choice=value["provider"]
        provider="bundled-cpu" if choice is None else "ollama / "+choice["model"]
        self.selected.set(self.locale.msg("tools_setup.selected",provider=provider))
        selected=self.server_list.curselection()
        old=selected[0] if selected else None
        self.servers=value["servers"]
        self.server_list.delete(0,"end")
        for s in self.servers:
            states=[self.locale.text("tools_setup.configured")]
            if s["approved"]:states.append(self.locale.text("tools_setup.approved"))
            states.append(self.locale.text("tools_setup.enabled" if s["enabled"] else "tools_setup.disabled"))
            if s["id"] in self.connection_states:states.append(self.locale.text(self.connection_states[s["id"]]))
            self.server_list.insert("end",s["name"]+" ["+self.locale.text("tools_setup.local" if s["transport"]=="stdio" else "tools_setup.remote")+"] — "+", ".join(states))
        if old is not None and old<len(self.servers):self.server_list.selection_set(old)
        self.summary.set(self.locale.msg("tools_setup.summary",provider=provider,
                         count=sum(s["approved"] and s["enabled"] for s in self.servers)))
        self.show_tools()

    def current(self):
        return self.servers[self.server_list.curselection()[0]]

    def show_tools(self):
        self.tool_list.delete(0,"end")
        self.details.config(state="normal");self.details.delete("1.0","end");self.details.config(state="disabled")
        try:
            s=self.current()
            self.current_tools=self.discovered.get(s["id"],{}).get("tools",[])
            for index,t in enumerate(self.current_tools):
                self.tool_list.insert("end",t["name"])
                if s["tools"].get(t["name"])==fingerprint(t):self.tool_list.selection_set(index)
        except (IndexError,AttributeError):
            self.current_tools=[]

    def tool_details(self):
        selected=[self.current_tools[i] for i in self.tool_list.curselection()]
        text=json.dumps(selected,ensure_ascii=False,indent=2)
        self.details.config(state="normal");self.details.delete("1.0","end");self.details.insert("1.0",text);self.details.config(state="disabled")

    def edit(self,server=None):
        win=tk.Toplevel(self.window);win.transient(self.window);win.geometry("820x510");win.minsize(760,480)
        self.locale.title(win,self.locale.msg("tools_setup.connection"))
        identifier=server["id"] if server else uuid.uuid4().hex
        vals={k:tk.StringVar(win,value=(json.dumps(server[k],ensure_ascii=False) if k=="args" else server[k]) if server else ("[]" if k=="args" else "")) for k in ("name","endpoint","command","args")}
        transport=tk.StringVar(win,value=server["transport"] if server else "http")
        self.label(win,"tools_setup.secret.note",wraplength=750).grid(row=0,column=0,columnspan=3,sticky="ew",padx=14,pady=12)
        modes=tk.Frame(win);modes.grid(row=1,column=0,columnspan=3,sticky="w",padx=14)
        for mode,key in [("http","tools_setup.remote"),("stdio","tools_setup.local")]:
            self.locale.widget(tk.Radiobutton,modes,text=self.locale.msg(key),value=mode,variable=transport).pack(side="left")
        for i,(key,var) in enumerate(vals.items(),2):
            self.label(win,"tools_setup."+key).grid(row=i,column=0,sticky="w",padx=14,pady=8)
            tk.Entry(win,textvariable=var).grid(row=i,column=1,sticky="ew",padx=8,pady=8)
        def browse():
            path=filedialog.askopenfilename(parent=win)
            if path:vals["command"].set(path)
        self.button(win,"tools_setup.browse",browse).grid(row=4,column=2,padx=8)
        token=tk.StringVar(win,value="")
        self.label(win,"tools_setup.token").grid(row=6,column=0,sticky="w",padx=14,pady=8)
        tk.Entry(win,textvariable=token,show="*").grid(row=6,column=1,sticky="ew",padx=8,pady=8)
        self.label(win,"tools_setup.edit.revokes",wraplength=750).grid(row=7,column=0,columnspan=3,sticky="ew",padx=14,pady=12)
        def save():
            local=transport.get()=="stdio"
            s={"id":identifier,"name":vals["name"].get(),"transport":transport.get(),
               "endpoint":"" if local else vals["endpoint"].get(),
               "command":vals["command"].get() if local else "",
               "args":json.loads(vals["args"].get()) if local else []}
            self.config.put(s)
            self.secrets.pop(identifier,None)
            if token.get() and not local:self.secrets[identifier]={"target":connection_key(s),"token":token.get()}
            self.discovered.pop(identifier,None);self.connection_states.pop(identifier,None)
            token.set("");win.destroy();self.refresh()
        self.button(win,"tools_setup.save",save).grid(row=8,column=1,sticky="e",padx=8,pady=8)
        win.grid_columnconfigure(1,weight=1)

    def approve(self):
        s=self.current()
        target=s["command"]+" "+json.dumps(s["args"]) if s["transport"]=="stdio" else s["endpoint"]
        if self.dialogs.askyesno(self.locale.msg("tools_setup.approve"),self.locale.msg("tools_setup.approval",target=target)):
            self.config.update(s["id"],approved=True)
            self.refresh()

    def test_mcp(self):
        s=self.current()
        self.config.server(s["id"])
        identifier=s["id"]
        def done(value):
            if self.config.server(identifier)!=s:raise PermissionError("Configuration changed")
            self.discovered[identifier]=value
            self.connection_states[identifier]="tools_setup.connected"
            self.refresh()
        self.connection_states[identifier]="tools_setup.unavailable"
        self.run(lambda:discover_mcp(self.config.directory,identifier,{identifier:self.secrets.get(identifier,"")}),done)

    def allow_tools(self):
        s=self.current()
        approved={self.current_tools[i]["name"]:fingerprint(self.current_tools[i]) for i in self.tool_list.curselection()}
        if self.dialogs.askyesno(self.locale.msg("tools_setup.allow"),self.locale.msg("tools_setup.tools.consent",tools=", ".join(approved))):
            self.config.update(s["id"],tools=approved)
            self.refresh()

    def enable(self,enabled):
        self.config.update(self.current()["id"],enabled=enabled)
        self.refresh()

    def revoke(self):
        identifier=self.current()["id"]
        self.config.update(identifier,approved=False)
        self.secrets.pop(identifier,None);self.discovered.pop(identifier,None);self.connection_states.pop(identifier,None)
        self.refresh()

    def remove(self):
        identifier=self.current()["id"]
        self.config.remove(identifier)
        self.secrets.pop(identifier,None);self.discovered.pop(identifier,None);self.connection_states.pop(identifier,None)
        self.refresh()
