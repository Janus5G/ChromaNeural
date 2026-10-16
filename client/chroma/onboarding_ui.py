"""Guided AI/tool setup with separate expert management; existing backend contracts."""
import json, queue, threading, tkinter as tk, uuid
from tkinter import ttk, filedialog
from .ai_provider import selection
from .mcp_config import Config, fingerprint, connection_key
from .localized_dialogs import Dialogs
from .onboarding import discover, discover_mcp, test_provider

class ConnectionManager:
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

from pathlib import Path
import webbrowser
from .mcp_catalog import PROFILES, candidates, installed_program, checked_connection, needs_extra_consent
from . import mcp_rea


class Wizard(ConnectionManager):
    """Presentation-only coordinator; Config and worker remain the authority."""
    def __init__(self, parent, locale, directory=None, secrets=None):
        self.locale = locale
        self.config = Config(directory)
        self.secrets = secrets if secrets is not None else {}
        self.config.load()  # Fail closed before presenting an invalid saved configuration.
        self.window = tk.Toplevel(parent)
        self.window.geometry("1000x780")
        self.window.minsize(820, 620)
        self.window.transient(parent)
        self.window.configure(bg="#F4F6FA")
        locale.title(self.window, locale.msg("tools_setup.title"))
        self.dialogs = Dialogs(self.window, locale)
        self.results = queue.Queue()
        self.busy = False
        self.closed = False
        self.providers = []
        self.scanned = False
        self.page = "ai"
        self.profile = None
        self.identifier = None
        self.tested = None
        self.tools = []
        self.tool_vars = {}
        self.args = []
        self.name = tk.StringVar(self.window)
        self.target = tk.StringVar(self.window)
        self.token = tk.StringVar(self.window)
        self.enable_at_finish = tk.BooleanVar(self.window, False)
        self.allow_changes = tk.BooleanVar(self.window, False)
        self.status = locale.variable(self.window, locale.msg("wizard.welcome"))
        self.progress = locale.variable(self.window)
        locale.widget(tk.Label, self.window, textvariable=self.progress,
                      font=("Segoe UI", 11), bg="#F4F6FA", fg="#506079", anchor="w").pack(fill="x", padx=24, pady=(16, 4))
        self.heading = locale.variable(self.window)
        locale.widget(tk.Label, self.window, textvariable=self.heading,
                      font=("Segoe UI", 20, "bold"), bg="#F4F6FA", fg="#17263E", anchor="w").pack(fill="x", padx=24, pady=8)
        self.canvas = tk.Canvas(self.window, highlightthickness=0, bg="#F4F6FA")
        scroll = ttk.Scrollbar(self.window, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.nav = tk.Frame(self.window, bg="#F4F6FA")
        self.nav.pack(side="bottom", fill="x", padx=20, pady=14)
        locale.widget(tk.Label, self.window, textvariable=self.status, anchor="w", justify="left",
                      wraplength=900, bg="#F4F6FA", fg="#506079").pack(side="bottom", fill="x", padx=24, pady=8)
        self.canvas.pack(fill="both", expand=True, padx=20)
        self.body = tk.Frame(self.canvas, bg="#F4F6FA")
        self.body_id = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.body_id, width=e.width))
        self.window.bind("<MouseWheel>", self.scroll)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        locale.listen(self.window, self.refresh)
        self.show("ai")
        self.poll_id = self.window.after(100, self.poll)
        self.window.after(150, self.scan_ai)

    def label(self, parent, key, **kw):
        return self.locale.widget(tk.Label, parent, text=self.locale.msg(key), justify="left",
                                 anchor="w", font=("Segoe UI", 10), fg="#263449", **kw)

    def button(self, parent, key, command):
        return self.locale.widget(tk.Button, parent, text=self.locale.msg(key),
            command=lambda: self.safe(command), font=("Segoe UI", 10), relief="flat",
            bg="#E5EAF4", activebackground="#D8E2F5", fg="#173D77", padx=12, pady=8)

    def scroll(self, event):
        if not isinstance(event.widget, (tk.Listbox, tk.Entry, ttk.Combobox)):
            self.canvas.yview_scroll(-int(event.delta / 120), "units")

    def text(self, key, **values):
        return self.locale.text(key, **values)

    def paragraph(self, key, parent=None, **values):
        label = self.locale.widget(tk.Label, parent or self.body, text=self.locale.msg(key, **values),
                                   justify="left", anchor="w", wraplength=750, bg="#F4F6FA", fg="#263449", font=("Segoe UI", 10))
        label.pack(fill="x", padx=10, pady=7)
        return label

    def action(self, parent, key, command, **pack):
        result = self.button(parent, key, command)
        result.pack(padx=5, pady=5, **pack)
        return result

    def safe(self, command):
        if self.busy or self.closed:
            return
        try:
            return command()
        except (ValueError, PermissionError, OSError, IndexError):
            self.status.set(self.locale.msg("wizard.error.config"))
        except Exception:
            self.status.set(self.locale.msg("wizard.error.operation"))

    def run(self, work, done, error_key="wizard.error.operation"):
        if self.busy or self.closed:
            return
        self.busy = True
        self.status.set(self.locale.msg("tools_setup.working"))
        self.set_navigation(False)
        def job():
            try:
                self.results.put((True, work(), done, error_key))
            except Exception as error:
                # Store only the exception class. Never retain response bodies or credentials.
                self.results.put((False, type(error).__name__, done, error_key))
        threading.Thread(target=job, daemon=True).start()

    def set_navigation(self, enabled):
        for widget in self.nav.winfo_children():
            if isinstance(widget, tk.Button):
                widget.configure(state="normal" if enabled else "disabled")

    def poll(self):
        if self.closed:
            return
        try:
            ok, value, done, error_key = self.results.get_nowait()
            self.busy = False
            self.set_navigation(True)
            if ok:
                self.safe(lambda: done(value))
            else:
                key = "wizard.error.timeout" if value == "TimeoutError" else error_key
                self.status.set(self.locale.msg(key))
                self.error_kind = value
        except queue.Empty:
            pass
        self.poll_id = self.window.after(100, self.poll)

    def show(self, page):
        if page != self.page:
            self.status.set(self.locale.msg("wizard.page_status." + page))
        self.page = page
        for frame in (self.body, self.nav):
            for widget in frame.winfo_children():
                widget.destroy()
        pages = ("ai", "optional", "catalog", "configure", "review", "tools", "finish")
        self.progress.set(self.locale.msg("wizard.progress", step=pages.index(page) + 1, total=len(pages)))
        self.heading.set(self.locale.msg("wizard.heading." + page))
        self.canvas.yview_moveto(0)
        getattr(self, "page_" + page)()
        if self.busy:
            self.set_navigation(False)

    def refresh(self):
        if not self.closed:
            self.show(self.page)

    def back_next(self, back=None, next_action=None, next_key="wizard.next"):
        if back:
            self.action(self.nav, "wizard.back", lambda: self.show(back), side="left")
        if next_action:
            button = self.action(self.nav, next_key, next_action, side="right")
            button.configure(bg="#2459A6", fg="white", activebackground="#1D4887", activeforeground="white")
            return button

    def provider_name(self, choice):
        return self.text("wizard.builtin") if choice is None else "Ollama — " + choice["model"]

    def page_ai(self):
        self.paragraph("wizard.ai.intro")
        self.provider_list = tk.Listbox(self.body, height=max(2, min(4, len(self.providers))), exportselection=False,
                                       font=("Segoe UI", 11), activestyle="dotbox")
        self.provider_list.pack(fill="x", padx=10, pady=10)
        self.render_providers()
        row = tk.Frame(self.body); row.pack(fill="x", padx=5)
        self.action(row, "wizard.scan", self.scan_ai, side="left")
        self.action(row, "wizard.use", self.select_provider, side="left")
        self.action(row, "wizard.ai.test", self.test_ai, side="left")
        self.action(row, "wizard.help", lambda: self.help("wizard.ai.help"), side="left")
        choice = self.config.load()["provider"]
        name = self.provider_name(choice)
        if self.scanned and not any(selection(p["provider"], p["model"]) == choice for p in self.providers):
            name += " — " + self.text("wizard.ai.not_detected")
        self.paragraph("tools_setup.selected", provider=name)
        if self.scanned and not any(p["provider"] == "ollama" for p in self.providers):
            self.paragraph("wizard.ai.no_ollama")
        if self.scanned and not self.providers:
            self.paragraph("tools_setup.none")
        self.paragraph("wizard.ai.tools")
        self.back_next(next_action=self.continue_ai)

    def render_providers(self):
        self.provider_list.delete(0, "end")
        choice = self.config.load()["provider"]
        for index, item in enumerate(self.providers):
            selected = selection(item["provider"], item["model"])
            name = self.provider_name(selected)
            if item["provider"] == "ollama" and item["model"] == "qwen3:4b-instruct":
                name += " — " + self.text("wizard.recommended")
            self.provider_list.insert("end", name + " · " + self.text("wizard.detected"))
            if selected == choice:
                self.provider_list.selection_set(index)

    def scan_ai(self):
        self.run(discover, self.found_providers, "wizard.error.ai.discovery")

    def found_providers(self, items):
        self.providers = items
        self.scanned = True
        self.status.set(self.locale.msg("wizard.ai.scan.done"))
        if self.page == "ai":
            self.show("ai")

    def select_provider(self):
        selected = self.provider_list.curselection()
        if not selected:
            self.status.set(self.locale.msg("wizard.ai.choose")); return False
        item = self.providers[selected[0]]
        self.config.select(selection(item["provider"], item["model"]))
        self.status.set(self.locale.msg("wizard.ai.selected"))
        self.show("ai")
        return True

    def continue_ai(self):
        if self.select_provider():
            self.show("optional")

    def test_ai(self):
        if not self.select_provider():
            return
        choice = self.config.load()["provider"]
        if self.dialogs.askyesno(self.locale.msg("wizard.ai.test"), self.locale.msg("tools_setup.inference.consent")):
            def done(result):
                if not result or not getattr(result, "source", b"") or self.config.load()["provider"] != choice:
                    self.status.set(self.locale.msg("wizard.error.ai.test")); return
                self.status.set(self.locale.msg("wizard.ai.test.ok"))
            self.run(lambda: test_provider(choice), done, "wizard.error.ai.test")

    def page_optional(self):
        self.paragraph("wizard.optional.intro")
        self.action(self.body, "wizard.connect", lambda: self.show("catalog"), anchor="w")
        self.action(self.body, "wizard.skip", self.skip, anchor="w")
        self.paragraph("wizard.management.note")
        self.action(self.body, "wizard.management", self.manage, anchor="w")
        self.back_next("ai")

    def skip(self):
        # Do not disable or otherwise alter pre-existing user configurations.
        self.profile = None
        self.identifier = None
        self.tested = None
        self.token.set("")
        self.show("finish")

    def manage(self):
        manager = ConnectionManager(self.window, self.locale, self.config.directory, self.secrets)
        self.locale.title(manager.window, self.locale.msg("wizard.management"))
        manager.window.grab_set()
        self.window.wait_window(manager.window)
        self.refresh()

    def page_catalog(self):
        self.paragraph("wizard.catalog.intro")
        grid = tk.Frame(self.body, bg="#F4F6FA")
        grid.pack(fill="x", padx=5, pady=6)
        grid.columnconfigure(0, weight=1, uniform="cards")
        grid.columnconfigure(1, weight=1, uniform="cards")
        servers = self.config.load()["servers"]
        self.catalog_cards = []
        for index, profile in enumerate(PROFILES):
            found = candidates(profile, servers)
            detection = "wizard.detected" if found else "wizard.needs_setup"
            card = tk.Frame(grid, bg="white", highlightbackground="#D8DFEA", highlightthickness=1, padx=12, pady=10)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=5, pady=5)
            self.catalog_cards.append(card)
            self.locale.widget(tk.Label, card, text=self.locale.msg("wizard.profile." + profile.id + ".name"),
                bg="white", fg="#17263E", font=("Segoe UI", 11, "bold"), wraplength=340,
                anchor="w", justify="left").pack(fill="x", pady=(0, 6))
            self.label(card, "wizard.profile." + profile.id + ".description", wraplength=340, bg="white").pack(fill="x")
            self.locale.widget(tk.Label, card, text=self.locale.msg("wizard.catalog.state",
                maturity=profile.maturity, state=self.locale.msg(detection)), anchor="w", justify="left",
                bg="white", fg="#506079", wraplength=340).pack(fill="x", pady=6)
            if profile.id == "rea" and found:
                self.locale.widget(tk.Label, card, text=self.locale.msg("wizard.rea.detected",
                    version=found[0]["version"]), wraplength=340, bg="white").pack(fill="x")
            self.action(card, "wizard.configure" if profile.transport else "wizard.setup_help",
                        lambda p=profile: self.choose_profile(p), anchor="e")
        self.paragraph("wizard.realtime")
        self.back_next("optional")

    def choose_profile(self, profile):
        self.profile = profile
        self.identifier = ("rea-" if profile.id == "rea" else "") + uuid.uuid4().hex
        self.tested = None
        self.tools = []
        self.tool_vars = {}
        self.allow_changes.set(False)
        self.enable_at_finish.set(False)
        self.name.set(self.text("wizard.profile." + profile.id + ".name"))
        self.target.set(profile.endpoint)
        self.token.set("")
        self.args = []
        self.detected = candidates(profile, self.config.load()["servers"])
        self.tooling_found = bool(installed_program(profile.tooling))
        if profile.id == "rea":
            self.rea_runtime = mcp_rea.runtime_status(self.detected[0]["command"] if self.detected else None)
        if len(self.detected) == 1:
            candidate = self.detected[0]
            self.target.set(candidate.get("command", candidate.get("endpoint", "")))
            self.args = [tk.StringVar(self.window, value=a) for a in candidate.get("args", [])]
        self.show("configure")

    def help(self, key):
        self.dialogs.showinfo(self.locale.msg("wizard.help"), self.locale.msg(key))

    def field(self, key, variable, secret=False):
        self.paragraph(key)
        entry = tk.Entry(self.body, textvariable=variable, show="*" if secret else "", font=("Segoe UI", 11))
        entry.pack(fill="x", padx=10, pady=(0, 5))
        return entry

    def page_configure(self):
        p = self.profile
        self.paragraph("wizard.profile." + p.id + ".description")
        self.paragraph("wizard.profile." + p.id + ".hint")
        row = tk.Frame(self.body); row.pack(fill="x", padx=5)
        self.action(row, "wizard.help", lambda: self.help("wizard.profile." + p.id + ".help"), side="left")
        self.action(row, "wizard.official_docs", lambda: webbrowser.open(p.docs), side="left")
        if p.transport is None:
            self.paragraph("wizard.profile.unavailable")
            self.paragraph("wizard.tooling.detected" if self.tooling_found else "wizard.tooling.absent")
            self.back_next("catalog")
            return
        if p.id == "rea":
            runtime = self.rea_runtime
            self.paragraph("wizard.rea.node.ok" if runtime["compatible"] else "wizard.rea.node.missing",
                           version=runtime["node"] or self.text("wizard.rea.unknown"))
            if runtime["npm"]:
                self.paragraph("wizard.rea.npm.ok", version=runtime["npm"])
            else:
                self.paragraph("wizard.rea.npm.missing")
            self.paragraph("wizard.rea.compatibility")
            self.paragraph("wizard.rea.optional_engines")
            self.paragraph("wizard.rea.authorized")
            self.paragraph("wizard.rea.untrusted")
            if not self.detected and not self.target.get():
                self.paragraph("wizard.rea.absent")
                self.action(self.body, "wizard.setup_help", lambda: self.help("wizard.profile.rea.help"), anchor="w")
                self.action(self.body, "wizard.scan", self.find_local, anchor="w")
                self.action(self.body, "wizard.choose_application", self.browse, anchor="w")
                self.back_next("catalog")
                return
            for item in self.detected:
                self.paragraph("wizard.rea.detected", version=item["version"])
        if self.profile_blocker():
            self.paragraph(self.profile_blocker())
        if p.id != "rea":
            self.paragraph("wizard.profile.unverified")
        self.name_entry = self.field("wizard.name", self.name)
        self.paragraph("wizard.name.hint")
        self.target_entry = self.field("wizard.address" if p.transport == "http" else "wizard.application", self.target)
        if p.endpoint or p.id == "rea":
            self.target_entry.configure(state="readonly")
        row = tk.Frame(self.body); row.pack(fill="x", padx=5)
        if p.transport == "http":
            self.paragraph("wizard.address.hint")
            if not p.endpoint:
                self.action(row, "wizard.paste", lambda: self.paste(self.target), side="left")
            self.action(row, "wizard.check", self.validate_fields, side="left")
            self.action(row, "wizard.where", lambda: self.help("wizard.profile." + p.id + ".help"), side="left")
            self.token_entry = self.field("wizard.token", self.token, secret=True)
            self.paragraph("wizard.token.hint")
            row = tk.Frame(self.body); row.pack(fill="x", padx=5)
            self.action(row, "wizard.paste.secure", lambda: self.paste(self.token), side="left")
            self.action(row, "wizard.show_hide", self.toggle_token, side="left")
            self.action(row, "wizard.where", lambda: self.help("wizard.token.help"), side="left")
        else:
            self.paragraph("wizard.local.hint")
            self.action(row, "wizard.find", self.find_local, side="left")
            self.action(row, "wizard.choose_application", self.browse, side="left")
            self.action(row, "wizard.help_find", lambda: self.help(
                "wizard.profile.rea.help" if p.id == "rea" else "wizard.local.help"), side="left")
            if not self.detected:
                self.paragraph("wizard.local.none")
            for candidate in self.detected:
                self.locale.widget(tk.Button, self.body, text=candidate["name"],
                    command=lambda c=candidate: self.pick_candidate(c)).pack(anchor="w", padx=15, pady=4)
            self.advanced = tk.Frame(self.body)
            self.action(self.body, "wizard.advanced", self.toggle_advanced, anchor="w")
            self.draw_args()
        self.validation = self.locale.variable(self.body)
        self.locale.widget(tk.Label, self.body, textvariable=self.validation, wraplength=740,
                           anchor="w", justify="left").pack(fill="x", padx=10, pady=8)
        self.next_button = self.back_next("catalog", self.review_connection)
        # Validate after individual edits, without connecting or writing settings.
        self.name_entry.bind("<KeyRelease>", lambda e: self.validate_fields())
        self.target_entry.bind("<KeyRelease>", lambda e: self.target_edited())
        self.validate_fields()

    def toggle_token(self):
        self.token_entry.configure(show="" if self.token_entry.cget("show") else "*")

    def paste(self, variable):
        try:
            value = self.window.clipboard_get()
        except tk.TclError:
            self.status.set(self.locale.msg("wizard.clipboard.empty")); return
        variable.set(value.strip())
        if variable is self.target:
            self.target_edited()

    def target_edited(self):
        self.token.set("")
        self.invalidate()
        self.validate_fields()

    def invalidate(self):
        if self.identifier and any(s["id"] == self.identifier for s in self.config.load()["servers"]):
            self.config.update(self.identifier, approved=False)
        if self.identifier:
            self.secrets.pop(self.identifier, None)
        self.tested = None
        self.tools = []
        self.tool_vars = {}
        self.enable_at_finish.set(False)

    def profile_blocker(self):
        if self.profile.id == "rea":
            from .rea_isolation import available
            if not available():
                return "wizard.rea.blocked"
        return self.profile.connection_blocker

    def current_draft(self):
        if self.profile_blocker():
            raise ValueError("Optional integration execution gate is blocked")
        if self.profile.endpoint and self.target.get().strip() != self.profile.endpoint:
            raise ValueError("Profile target changed")
        if self.profile.id == "rea" and (not self.rea_runtime["compatible"] or not mcp_rea.valid_launch(
                self.target.get().strip(), [a.get() for a in self.args])):
            raise ValueError("REA requires its installed official MCP entrypoint and compatible Node.js")
        if self.profile.executable and Path(self.target.get().strip()).stem.casefold() != self.profile.executable.casefold():
            raise ValueError("Choose the documented profile program")
        return checked_connection(self.identifier, self.name.get(), self.profile.transport,
                                  self.target.get(), [a.get() for a in self.args])

    def validate_fields(self):
        try:
            self.current_draft()
            ok, key = True, "wizard.valid"
        except (ValueError, OSError):
            ok = False
            key = "wizard.error.address" if self.profile.transport == "http" else "wizard.error.program"
            if self.profile.id == "rea":
                key = "wizard.rea.invalid" if self.rea_runtime["compatible"] else "wizard.rea.runtime_required"
            if not self.name.get().strip() or len(self.name.get().strip()) > 80:
                key = "wizard.error.name"
        if self.profile_blocker():
            ok, key = False, self.profile_blocker()
        self.validation.set(self.locale.msg(key))
        self.next_button.configure(state="normal" if ok and not self.busy else "disabled")
        return ok

    def find_local(self):
        self.detected = candidates(self.profile, self.config.load()["servers"])
        if self.profile.id == "rea":
            self.rea_runtime = mcp_rea.runtime_status(self.detected[0]["command"] if self.detected else None)
        if len(self.detected) == 1:
            self.pick_candidate(self.detected[0])
        else:
            self.show("configure")

    def pick_candidate(self, candidate):
        self.invalidate()
        if self.profile.id == "rea":
            self.rea_runtime = mcp_rea.runtime_status(candidate["command"])
        self.target.set(candidate["command"])
        self.args = [tk.StringVar(self.window, value=a) for a in candidate.get("args", [])]
        self.show("configure")

    def browse(self):
        path = filedialog.askopenfilename(parent=self.window, title=self.text("wizard.choose_application"))
        if path:
            if self.profile.id == "rea":
                candidate = mcp_rea.candidate(path)
                if not candidate:
                    self.status.set(self.locale.msg("wizard.rea.invalid"))
                    return
                self.detected = [candidate]
                self.pick_candidate(candidate)
                return
            self.invalidate()
            self.target.set(path)
            self.args = []
            self.show("configure")

    def toggle_advanced(self):
        if self.advanced.winfo_manager():
            self.advanced.pack_forget()
        else:
            self.advanced.pack(fill="x", padx=10, pady=5)

    def draw_args(self):
        for child in self.advanced.winfo_children():
            child.destroy()
        self.label(self.advanced, "wizard.arguments.hint", wraplength=730).pack(fill="x")
        for variable in self.args:
            row = tk.Frame(self.advanced); row.pack(fill="x")
            entry = tk.Entry(row, textvariable=variable); entry.pack(side="left", fill="x", expand=True)
            entry.bind("<KeyRelease>", lambda e: self.target_edited())
            self.action(row, "wizard.remove_argument", lambda v=variable: self.remove_argument(v), side="right")
        self.action(self.advanced, "wizard.add_argument", self.add_argument, anchor="w")

    def add_argument(self):
        if len(self.args) < 32:
            self.invalidate()
            self.args.append(tk.StringVar(self.window))
            self.draw_args(); self.validate_fields()

    def remove_argument(self, variable):
        self.invalidate(); self.args.remove(variable)
        self.draw_args(); self.validate_fields()

    def review_connection(self):
        if self.validate_fields():
            token = self.token.get()
            if token and (len(token) > 8192 or any(ord(c) < 33 or ord(c) > 126 for c in token)
                          or not self.target.get().strip().startswith("https://")):
                self.status.set(self.locale.msg("wizard.error.token")); return
            self.show("review")

    def page_review(self):
        s = self.current_draft()
        self.paragraph("wizard.review.intro")
        # The target must be visible for meaningful consent; tokens are never included.
        self.locale.widget(tk.Label, self.body, text=s["name"] + "\n" + (s["endpoint"] or s["command"]),
                           justify="left", anchor="w", wraplength=750, font=("Segoe UI", 12, "bold")).pack(fill="x", padx=10, pady=12)
        if s["args"]:
            self.paragraph("wizard.review.args", arguments="\n".join(s["args"]))
        self.paragraph("wizard.review.no_tools")
        self.paragraph("tools_setup.edit.revokes")
        self.paragraph("wizard.realtime")
        self.action(self.body, "wizard.details", lambda: self.help("wizard.limits"), anchor="w")
        self.back_next("configure", self.approve_and_test, "wizard.approve_test")

    def approve_and_test(self):
        if self.profile_blocker():
            self.status.set(self.locale.msg(self.profile_blocker()))
            return
        s = self.current_draft()
        token = self.token.get()
        if token and (not s["endpoint"].startswith("https://") or len(token) > 8192
                      or any(ord(c) < 33 or ord(c) > 126 for c in token)):
            self.status.set(self.locale.msg("wizard.error.token")); return
        self.config.put(s)  # Revokes all prior authority even on a retry.
        self.secrets.pop(s["id"], None)
        if token:
            self.secrets[s["id"]] = {"target": connection_key(s), "token": token}
        self.config.update(s["id"], approved=True)
        snapshot = self.config.server(s["id"])
        def done(value):
            if self.config.server(s["id"]) != snapshot:
                self.status.set(self.locale.msg("wizard.error.changed")); return
            self.tested = snapshot
            self.tools = value.get("tools", [])
            self.tool_vars = {t["name"]: tk.BooleanVar(self.window, False) for t in self.tools}
            self.allow_changes.set(False)
            self.status.set(self.locale.msg("wizard.connection.ok"))
            self.show("tools")
        error = "wizard.error.remote" if s["transport"] == "http" else "wizard.error.local"
        if self.profile.id == "rea":
            error = "wizard.rea.test_failed"
        self.run(lambda: discover_mcp(self.config.directory, s["id"],
                 {s["id"]: self.secrets.get(s["id"], "")}), done, error)

    def page_tools(self):
        self.paragraph("wizard.tools.intro")
        self.paragraph("wizard.tools.untrusted")
        if not self.tools:
            self.paragraph("wizard.tools.none")
        self.locale.widget(tk.Checkbutton, self.body, text=self.locale.msg("wizard.tools.changes"),
                           variable=self.allow_changes, command=self.change_permission).pack(anchor="w", padx=10, pady=8)
        for tool in self.tools:
            card = ttk.Frame(self.body, padding=8); card.pack(fill="x", padx=10, pady=3)
            risky = needs_extra_consent(self.profile, tool)
            button = self.locale.widget(tk.Checkbutton, card, text=tool["name"], variable=self.tool_vars[tool["name"]])
            button.pack(anchor="w")
            button.configure(state="normal" if not risky or self.allow_changes.get() else "disabled")
            description = tool.get("description") or self.text("wizard.tools.no_description")
            tk.Label(card, text=description[:1200], wraplength=710, justify="left", anchor="w").pack(fill="x", padx=20)
            if risky:
                self.label(card, "wizard.tools.unknown", wraplength=710).pack(fill="x", padx=20)
        self.action(self.body, "wizard.select_none", self.select_none, anchor="w")
        self.back_next("review", self.approve_tools, "wizard.tools.continue")

    def change_permission(self):
        if self.allow_changes.get():
            if not self.dialogs.askyesno(self.locale.msg("wizard.tools.changes"), self.locale.msg("wizard.tools.risk")):
                self.allow_changes.set(False)
        if not self.allow_changes.get():
            for tool in self.tools:
                if needs_extra_consent(self.profile, tool):
                    self.tool_vars[tool["name"]].set(False)
        self.show("tools")

    def select_none(self):
        for variable in self.tool_vars.values():
            variable.set(False)

    def approve_tools(self):
        if self.config.server(self.identifier) != self.tested:
            self.status.set(self.locale.msg("wizard.error.changed")); return
        selected = [t for t in self.tools if self.tool_vars[t["name"]].get()]
        if any(needs_extra_consent(self.profile, t) for t in selected) and not self.allow_changes.get():
            self.status.set(self.locale.msg("wizard.error.approval")); return
        if selected and not self.dialogs.askyesno(self.locale.msg("tools_setup.allow"),
                self.locale.msg("tools_setup.tools.consent", tools=", ".join(t["name"] for t in selected))):
            return
        self.config.update(self.identifier, tools={t["name"]: fingerprint(t) for t in selected}, enabled=False)
        self.tested = self.config.server(self.identifier)
        self.show("finish")

    def page_finish(self):
        value = self.config.load()
        self.paragraph("tools_setup.selected", provider=self.provider_name(value["provider"]))
        if self.identifier and self.tested:
            self.paragraph("wizard.finish.connection", name=self.tested["name"], count=len(self.tested["tools"]))
            self.paragraph("wizard.finish.security")
            checkbox = self.locale.widget(tk.Checkbutton, self.body, text=self.locale.msg("wizard.finish.enable"),
                                         variable=self.enable_at_finish)
            checkbox.pack(anchor="w", padx=10, pady=12)
            if not self.tested["tools"] or value["provider"] is None:
                self.enable_at_finish.set(False); checkbox.configure(state="disabled")
                self.paragraph("wizard.ai.tools")
        else:
            self.paragraph("wizard.finish.skipped")
        self.paragraph("wizard.finish.existing", count=sum(s["enabled"] for s in value["servers"]))
        self.paragraph("tools_setup.boundary")
        self.back_next("tools" if self.tested else "optional", self.finish, "wizard.finish")

    def finish(self):
        if self.identifier and self.tested:
            if self.config.server(self.identifier) != self.tested:
                self.status.set(self.locale.msg("wizard.error.changed")); return
            if self.enable_at_finish.get():
                if self.config.load()["provider"] is None or not self.tested["tools"]:
                    self.status.set(self.locale.msg("wizard.error.approval")); return
                self.config.update(self.identifier, enabled=True)
        self.close()

    def close(self):
        self.closed = True
        self.token.set("")
        if hasattr(self, "poll_id"):
            self.window.after_cancel(self.poll_id)
        self.window.destroy()