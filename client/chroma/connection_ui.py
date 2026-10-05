"""Browser II login plus user-approved API metadata import. No browser session copying."""
import copy,json,queue,threading,webbrowser
import tkinter as tk
from .connection_profile import ConnectionProfile,LIMIT,parse_profile
from .connection_probe import probe_profile
from .localized_views import diagnostic

class ConnectionPanel:
    def __init__(self,app):
        self.locale=app.locale
        self.app=app;self.profile=ConnectionProfile(app.settings.directory)
        self.generation=0;self.busy=False;self.results=queue.Queue();self.last_probe=None
        p=app.page("connection",(self.locale.msg('nav.connection')),(self.locale.msg('connection.subtitle')))
        card=app.card(p);card.grid(row=2,column=0,sticky="ew");card.grid_columnconfigure(0,weight=1)
        app.label(card,(self.locale.msg('connection.step1')),size=13,bold=True).grid(row=0,column=0,sticky="w",padx=22,pady=(18,8))
        self.login_button=app.button(card,(self.locale.msg('connection.login')),self.open_login,"accent","on_accent")
        self.login_button.grid(row=1,column=0,sticky="w",padx=22)
        self.browser_status=self.locale.variable(app.root,value=(self.locale.msg('connection.browser')))
        app.label(card,variable=self.browser_status,fg="muted",wraplength=730,justify="left").grid(row=2,column=0,sticky="w",padx=22,pady=(8,12))
        app.label(card,(self.locale.msg('connection.step2')),size=13,bold=True).grid(row=3,column=0,sticky="w",padx=22,pady=(0,8))
        self.editor=tk.Text(card,height=6,width=66,wrap="word",font=("Consolas",10),bd=0,padx=10,pady=8,undo=True)
        self.editor.grid(row=4,column=0,sticky="ew",padx=22);app.skinned.append((self.editor,"raised","fg"))
        self.editor.bind("<<Paste>>",self.paste)
        if self.profile.value:self.editor.insert("1.0",json.dumps(self.profile.value,ensure_ascii=False,indent=2))
        actions=app.frame(card,"card");actions.grid(row=5,column=0,sticky="w",padx=22,pady=12)
        self.paste_button=app.button(actions,(self.locale.msg('connection.paste')),self.paste);self.paste_button.pack(side="left")
        self.save_button=app.button(actions,(self.locale.msg('connection.save')),self.save,"accent","on_accent");self.save_button.pack(side="left",padx=8)
        self.probe_button=app.button(actions,(self.locale.msg('connection.check')),self.check_connection);self.probe_button.pack(side="left")
        self.status=self.locale.variable(app.root);self.error=self.locale.variable(app.root)
        app.label(p,variable=self.status,fg="cyan",bold=True,bg="bg",wraplength=780,justify="left").grid(row=3,column=0,sticky="w",pady=(12,4))
        app.label(p,variable=self.error,fg="muted",bg="bg",wraplength=780,justify="left").grid(row=4,column=0,sticky="w")
        app.label(p,(self.locale.msg('connection.privacy')),fg="muted",bg="bg",wraplength=780,
                  justify="left").grid(row=5,column=0,sticky="w",pady=(10,6))
        app.label(p,(self.locale.msg('connection.peer')),fg="muted",bg="bg",wraplength=780,
                  justify="left").grid(row=6,column=0,sticky="w")
        self.refresh()

    def refresh(self):
        self.status.set((self.locale.msg('connection.saved') + ' ')+self.profile.value["backend_canister_id"] if self.profile.value else (self.locale.msg('connection.missing')))
        self.probe_button.config(state="normal" if self.profile.value and not self.busy else "disabled")
        if self.profile.error:self.error.set((self.locale.msg('connection.invalid')))

    def open_login(self):
        try:self.profile.open_login(webbrowser.open_new_tab)
        except (OSError,RuntimeError) as e:self.browser_status.set(diagnostic(self.locale,e));return
        self.browser_status.set((self.locale.msg('connection.opened')))

    def paste(self,event=None):
        try:
            text=self.app.root.clipboard_get()
            if len(text.encode("utf-8"))>LIMIT:raise ValueError((self.locale.msg('error.paste.size')))
            checked=parse_profile(text)
        except (tk.TclError,ValueError):
            self.error.set((self.locale.msg('connection.paste.error')));return "break"
        self.editor.delete("1.0","end");self.editor.insert("1.0",json.dumps(checked,ensure_ascii=False,indent=2))
        self.error.set((self.locale.msg('connection.review')))
        return "break"

    def save(self):
        try:self.profile.save(self.editor.get("1.0","1.0+8193c"))
        except (OSError,ValueError,UnicodeError) as e:
            self.error.set(self.locale.msg("connection.not.saved")+" "+diagnostic(self.locale,e)+". "+self.locale.msg("connection.copy"));return
        self.generation+=1;self.last_probe=None;self.error.set("");self.refresh()
        self.app.service.event("Offentlige API-forbindelsesdata gemt lokalt; ingen upload eller adgangsrettigheder ændret")

    def check_connection(self):
        if self.busy or not self.profile.value:return
        self.busy=True;self.probe_button.config(state="disabled");self.error.set("")
        self.status.set((self.locale.msg('connection.checking')))
        generation=self.generation;profile=copy.deepcopy(self.profile.value)
        def run():
            try:self.results.put((generation,True,probe_profile(profile)))
            except Exception as e:self.results.put((generation,False,str(e)))
        threading.Thread(target=run,daemon=True,name="chroma-public-connection-check").start()

    def poll(self):
        try:generation,ok,value=self.results.get_nowait()
        except queue.Empty:return
        self.busy=False;self.refresh()
        if generation!=self.generation:return
        if ok:
            self.last_probe=value
            self.status.set((self.locale.msg('connection.success')))
        else:
            self.last_probe=None;self.status.set((self.locale.msg('connection.failed')))
            self.error.set(diagnostic(self.locale,str(value)[:360]))
