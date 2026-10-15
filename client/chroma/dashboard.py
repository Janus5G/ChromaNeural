"""Ordinary-user shell over the existing local studio and authoritative ledger."""
from pathlib import Path
import copy,os,tkinter as tk
from tkinter import ttk,filedialog,messagebox
from .settings import Settings
from .participation import Participation
from .tray import Tray
from .i18n import LocaleContext,LanguagePreference,LOCALES,NAMES,packaged_version
from .localized_dialogs import Dialogs
from .localized_views import activity,ledger,diagnostic
PALETTES={
 "dark":{"bg":"#0D111B","nav":"#101522","card":"#171E2E","raised":"#202940","fg":"#F2F4FC","muted":"#A6B1C8","accent":"#B6A0FF","on_accent":"#151027","cyan":"#68DFD6","line":"#303C55","good":"#83E6BB"},
 "light":{"bg":"#F1F3FA","nav":"#E7EBF5","card":"#FFFFFF","raised":"#E8EDF8","fg":"#1A2340","muted":"#526079","accent":"#5634A8","on_accent":"#FFFFFF","cyan":"#126B72","line":"#C3CCDE","good":"#176746"}}
def amount(value,suffix=""):
    if value is None:return "—"
    text=f"{value:,.6f}".rstrip("0").rstrip(".").replace(","," ").replace(".",",")
    return text+suffix
def bytes_text(value):
    if value is None:return "—"
    if value>=1048576:return amount(value/1048576," MiB")
    if value>=1024:return amount(value/1024," KiB")
    return str(value)+" B"

class App:
    def __init__(self,root,workspace=None,state_dir=None,controller=None,locale=None,language=None):
        self.root=root;self.workspace_arg=workspace;self.settings=Settings(state_dir);self.service=controller or Participation(self.settings)
        self.language_preference=LanguagePreference(self.settings.directory)
        self.locale=locale or LocaleContext(language or self.language_preference.locale)
        self.dialogs=Dialogs(root,self.locale)
        self.theme_name=self.settings.value["theme"];self.skinned=[];self.pages={};self.navbuttons={};self.studio=None;self.closed=False;self.mcp_secrets={}
        self.vars={k:self.locale.variable(root,value="—") for k in ("title","subtitle","pill","points","balance","spent","contribution","consumed","ratio","cpu","ram","ai","fresh","credits","resources_note","footer")}
        root.title("ChromaNeural")
        if os.name=="nt":root.iconbitmap(str(Path(__file__).resolve().parents[1]/"assets/chroma.ico"))
        root.geometry("1120x780");root.minsize(1020,720)
        root.grid_rowconfigure(0,weight=1);root.grid_columnconfigure(1,weight=1)
        self.nav=self.frame(root,"nav");self.nav.grid(row=0,column=0,sticky="ns");self.nav.config(width=204);self.nav.grid_propagate(False)
        self.main=self.frame(root);self.main.grid(row=0,column=1,sticky="nsew");self.main.grid_columnconfigure(0,weight=1);self.main.grid_rowconfigure(0,weight=1)
        brand=self.frame(self.nav,"nav");brand.pack(fill="x",padx=20,pady=(28,36))
        self.logo(brand,46).pack(anchor="w")
        self.label(brand,"CHROMA","fg",17,True,"nav").pack(anchor="w",pady=(8,0))
        self.label(brand,"NEURAL NETWORK","muted",8,False,"nav").pack(anchor="w",pady=(1,0))
        for page,text in (("overview",(self.locale.msg('nav.overview'))),("resources",(self.locale.msg('nav.resources'))),("activity",(self.locale.msg('nav.activity'))),("connection",(self.locale.msg('nav.connection')))):
            b=self.button(self.nav,text,lambda p=page:self.show_page(p),"nav","muted",anchor="w")
            b.pack(fill="x",padx=12,pady=3);self.navbuttons[page]=b
        bottom=self.frame(self.nav,"nav");bottom.pack(side="bottom",fill="x",padx=14,pady=20)
        self.label(bottom,(self.locale.msg('nav.extra')),"muted",8,False,"nav").pack(anchor="w",padx=8,pady=(0,8))
        self.button(bottom,(self.locale.msg('nav.studio')),self.open_studio,"nav","muted",anchor="w").pack(fill="x")
        self.button(bottom,(self.locale.msg('nav.theme')),self.toggle_theme,"nav","muted",anchor="w").pack(fill="x",pady=(10,0))
        self.button(bottom,(self.locale.msg('nav.exit')),self.quit,"nav","muted",anchor="w").pack(fill="x")
        self.label(bottom,self.locale.msg("nav.version",version=packaged_version()),"muted",8,False,"nav").pack(anchor="w",padx=8,pady=(20,0))
        self.label(bottom,self.locale.msg("language"),"muted",9,False,"nav").pack(anchor="w",padx=8,pady=(12,4))
        self.language_name=tk.StringVar(root,value=NAMES[LOCALES.index(self.locale.locale)])
        self.language_select=ttk.Combobox(bottom,textvariable=self.language_name,values=NAMES,state="readonly",width=15,style="Chroma.TCombobox")
        self.language_select.pack(fill="x")
        self.language_select.bind("<<ComboboxSelected>>",self.select_language)
        self.make_overview();self.make_resources();self.make_activity()
        from .connection_ui import ConnectionPanel
        self.connection_panel=ConnectionPanel(self)
        self.tray=Tray(root,self.show,on_pause=self.toggle_participation,on_resources=lambda:self.show_page("resources"),on_quit=self.quit,locale=self.locale)
        root.protocol("WM_DELETE_WINDOW",self.close)
        root.bind("<Control-Shift-D>",lambda e:self.open_studio())
        self.locale.listen(root,self.language_changed)
        self.service.start();self.apply_theme();self.refresh()
        self.show_page("overview" if self.settings.value["onboarded"] else "resources")
        if self.settings.value["start_hidden"] and self.settings.value["onboarded"] and self.tray.available:root.after(200,self.hide)
        self.after_id=root.after(250,self.tick)

    def frame(self,parent,role="bg",**kw):
        w=tk.Frame(parent,**kw);self.skinned.append((w,role,None));return w
    def label(self,parent,text="",fg="fg",size=10,bold=False,bg="card",variable=None,**kw):
        w=self.locale.widget(tk.Label,parent,text=text,textvariable=variable,font=("Segoe UI",size,"bold" if bold else "normal"),anchor="w",**kw)
        self.skinned.append((w,bg,fg));return w
    def button(self,parent,text,command,bg="raised",fg="fg",**kw):
        w=self.locale.widget(tk.Button,parent,text=text,command=lambda:self.safe(command),font=("Segoe UI",10),relief="flat",bd=0,padx=14,pady=11,cursor="hand2",takefocus=True,**kw)
        self.skinned.append((w,bg,fg));return w
    def card(self,parent):
        return self.frame(parent,"card",highlightthickness=1)
    def safe(self,fn):
        try:return fn()
        except Exception as e:self.dialogs.showerror("ChromaNeural",diagnostic(self.locale,e),parent=self.root)
    def logo(self,parent,size):
        c=tk.Canvas(parent,width=size,height=size,highlightthickness=0,bd=0)
        def draw(e=None):
            t=PALETTES[self.theme_name];c.configure(bg=t["nav"] if size==46 else t["card"]);c.delete("all")
            s=size/100
            def poly(points,color):c.create_polygon(*[v*s for v in points],fill=color,outline="")
            poly([50,5,94,30,50,53,6,30],t["accent"])
            poly([6,35,46,58,46,96,6,72],t["cyan"])
            poly([54,58,94,35,94,72,54,96],"#6479C8" if self.theme_name=="dark" else "#6677B8")
            c.create_line(50*s,17*s,50*s,43*s,fill=t["card"],width=2)
        c.redraw=draw;draw();return c
    def page(self,name,title,subtitle):
        page=self.frame(self.main);page.grid(row=0,column=0,sticky="nsew",padx=30,pady=14);page.grid_columnconfigure(0,weight=1)
        self.pages[name]=page
        self.label(page,title,"fg",23,True,"bg").grid(row=0,column=0,sticky="w")
        self.label(page,subtitle,"muted",10,False,"bg").grid(row=1,column=0,sticky="w",pady=(5,16))
        return page
    def make_overview(self):
        p=self.page("overview",(self.locale.msg('overview.title')),(self.locale.msg('overview.subtitle')))
        hero=self.card(p);hero.grid(row=2,column=0,sticky="ew");hero.grid_columnconfigure(0,weight=1)
        self.label(hero,variable=self.vars["pill"],fg="cyan",size=10,bold=True).grid(row=0,column=0,sticky="w",padx=22,pady=(14,6))
        self.label(hero,variable=self.vars["title"],size=18,bold=True,wraplength=580,justify="left").grid(row=1,column=0,sticky="w",padx=22)
        self.label(hero,variable=self.vars["subtitle"],fg="muted",wraplength=570,justify="left").grid(row=2,column=0,sticky="w",padx=22,pady=(6,10))
        self.hero_logo=self.logo(hero,88);self.hero_logo.grid(row=0,column=1,rowspan=3,padx=22)
        actions=self.frame(hero,"card");actions.grid(row=3,column=0,columnspan=2,sticky="w",padx=22,pady=(0,14))
        self.primary=self.button(actions,(self.locale.msg('action.start')),self.toggle_participation,"accent","on_accent");self.primary.pack(side="left")
        self.button(actions,(self.locale.msg('action.resources')),lambda:self.show_page("resources")).pack(side="left",padx=10)
        self.button(actions,(self.locale.msg('action.tray')),self.hide,"card","muted").pack(side="left")
        metrics=self.frame(p);metrics.grid(row=3,column=0,sticky="ew",pady=12)
        for i,(key,title,caption) in enumerate((("points","ChromaPoints",(self.locale.msg('metric.earned'))),("balance",(self.locale.msg('metric.balance')),(self.locale.msg('metric.available'))),("spent",(self.locale.msg('metric.spent')),(self.locale.msg('metric.spent.caption'))))):
            metrics.grid_columnconfigure(i,weight=1,uniform="metric")
            card=self.card(metrics);card.grid(row=0,column=i,sticky="nsew",padx=(0,12) if i<2 else 0)
            self.label(card,title,"muted",10).pack(anchor="w",padx=18,pady=(14,6))
            self.label(card,variable=self.vars[key],size=26,bold=True).pack(anchor="w",padx=18)
            self.label(card,caption,"muted",9).pack(anchor="w",padx=18,pady=(5,12))
        lower=self.frame(p);lower.grid(row=4,column=0,sticky="nsew");lower.grid_columnconfigure(0,weight=1,uniform="lower");lower.grid_columnconfigure(1,weight=1,uniform="lower")
        left=self.card(lower);left.grid(row=0,column=0,sticky="nsew",padx=(0,12))
        self.label(left,(self.locale.msg('overview.resources')),size=12,bold=True).pack(anchor="w",padx=18,pady=(14,8))
        self.label(left,variable=self.vars["cpu"]).pack(anchor="w",padx=18,pady=4)
        self.label(left,variable=self.vars["ram"]).pack(anchor="w",padx=18,pady=4)
        self.label(left,(self.locale.msg('overview.private')),"muted",9).pack(anchor="w",padx=18,pady=(10,4))
        self.label(left,variable=self.vars["resources_note"],fg="muted",size=9,wraplength=310,justify="left").pack(anchor="w",padx=18,pady=(0,12))
        right=self.card(lower);right.grid(row=0,column=1,sticky="nsew")
        self.label(right,(self.locale.msg('overview.ai')),size=12,bold=True).pack(anchor="w",padx=18,pady=(14,8))
        self.label(right,variable=self.vars["ai"],fg="cyan",bold=True,wraplength=310,justify="left").pack(anchor="w",padx=18,pady=4)
        self.label(right,variable=self.vars["ratio"],wraplength=310,justify="left").pack(anchor="w",padx=18,pady=4)
        self.label(right,variable=self.vars["contribution"],fg="muted",size=9,wraplength=310,justify="left").pack(anchor="w",padx=18,pady=(8,4))
        self.label(right,variable=self.vars["consumed"],fg="muted",size=9).pack(anchor="w",padx=18,pady=(0,12))
        self.label(p,variable=self.vars["fresh"],fg="muted",size=9,bg="bg",wraplength=810,justify="left").grid(row=5,column=0,sticky="w",pady=(14,0))
        foot=self.frame(p);foot.grid(row=6,column=0,sticky="ew",pady=(10,0))
        self.label(foot,variable=self.vars["footer"],fg="muted",size=9,bg="bg").pack(side="left")
        self.button(foot,self.locale.msg("tools_setup.title"),self.open_setup,"bg","cyan").pack(side="right")
        self.details_button=self.button(foot,(self.locale.msg('overview.ledger')),self.details,"bg","cyan");self.details_button.pack(side="right")

    def make_resources(self):
        first=not self.settings.value["onboarded"]
        p=self.page("resources",(self.locale.msg('resources.welcome')) if first else (self.locale.msg('resources.title')),
          (self.locale.msg('resources.subtitle')))
        self.resource_title=p.winfo_children()[0]
        card=self.card(p);card.grid(row=2,column=0,sticky="ew")
        self.label(card,(self.locale.msg('resources.voluntary')),size=14,bold=True).grid(row=0,column=0,columnspan=3,sticky="w",padx=22,pady=(19,8))
        r=self.settings.value["resources"]
        self.form_cpu=tk.BooleanVar(value=r["cpu"]);self.form_threads=tk.IntVar(value=r["threads"]);self.form_ram=tk.StringVar(value=str(r["ram_mib"]//1024) if r["ram_mib"]>=1024 else "0.5")
        self.form_idle=tk.BooleanVar(value=r["idle_only"]);self.form_battery=tk.BooleanVar(value=r["pause_on_battery"])
        self.form_tray=tk.BooleanVar(value=self.settings.value["close_to_tray"]);self.form_hidden=tk.BooleanVar(value=self.settings.value["start_hidden"])
        def check(parent,text,var,row):
            c=self.locale.widget(tk.Checkbutton,parent,text=text,variable=var,anchor="w",font=("Segoe UI",11),padx=0,pady=8,bd=0,highlightthickness=0,takefocus=True)
            self.skinned.append((c,"card","fg"));c.grid(row=row,column=0,columnspan=3,sticky="w",padx=22);return c
        self.cpu_check=check(card,(self.locale.msg('resources.consent')),self.form_cpu,1)
        self.label(card,(self.locale.msg('resources.threads')),"muted").grid(row=2,column=0,sticky="w",padx=22,pady=12)
        self.cpu_select=ttk.Combobox(card,textvariable=self.form_threads,style="Chroma.TCombobox",state="readonly",values=tuple(range(1,min(8,os.cpu_count() or 1)+1)),width=9);self.cpu_select.grid(row=2,column=1,sticky="w",padx=12)
        self.label(card,(self.locale.msg('resources.ram')),"muted").grid(row=3,column=0,sticky="w",padx=22,pady=12)
        self.ram_select=ttk.Combobox(card,textvariable=self.form_ram,style="Chroma.TCombobox",state="readonly",values=("0.5","1","2","4","8"),width=9);self.ram_select.grid(row=3,column=1,sticky="w",padx=12)
        check(card,(self.locale.msg('resources.idle')),self.form_idle,4)
        check(card,(self.locale.msg('resources.battery')),self.form_battery,5)
        self.label(card,(self.locale.msg('resources.limits')),"muted",9,wraplength=710,justify="left").grid(row=6,column=0,columnspan=3,sticky="w",padx=22,pady=(10,8))
        self.label(card,(self.locale.msg('resources.gpu')),"muted",9).grid(row=7,column=0,columnspan=3,sticky="w",padx=22,pady=(0,18))
        bg=self.card(p);bg.grid(row=3,column=0,sticky="ew",pady=14)
        self.label(bg,(self.locale.msg('resources.closing')),size=12,bold=True).grid(row=0,column=0,columnspan=3,sticky="w",padx=22,pady=(14,4))
        check(bg,(self.locale.msg('resources.tray')),self.form_tray,1)
        check(bg,(self.locale.msg('resources.hidden')),self.form_hidden,2)
        self.label(bg,(self.locale.msg('resources.private')),"muted",9).grid(row=3,column=0,columnspan=3,sticky="w",padx=22,pady=(5,14))
        actions=self.frame(p);actions.grid(row=4,column=0,sticky="ew")
        self.save_settings_button=self.button(actions,(self.locale.msg('resources.save.first')) if first else (self.locale.msg('resources.save')),self.save_preferences,"accent","on_accent");self.save_settings_button.pack(side="left")
        self.button(actions,(self.locale.msg('resources.stop')),self.stop,"bg","muted").pack(side="left",padx=10)
        self.button(actions,(self.locale.msg('resources.advanced')),self.connection_settings,"bg","cyan").pack(side="right")
        self.label(p,((self.locale.msg('resources.invalid')) if self.settings.error else (self.locale.msg('resources.local'))),"muted",9,bg="bg",wraplength=790).grid(row=5,column=0,sticky="w",pady=14)

    def make_activity(self):
        p=self.page("activity",(self.locale.msg('nav.activity')),(self.locale.msg('activity.subtitle')))
        card=self.card(p);card.grid(row=2,column=0,sticky="nsew");p.grid_rowconfigure(2,weight=1)
        self.activity=tk.Text(card,font=("Segoe UI",11),wrap="word",bd=0,padx=20,pady=20,state="disabled",takefocus=True)
        self.activity.pack(fill="both",expand=True);self.skinned.append((self.activity,"card","fg"))
    def show_page(self,name):
        for key,page in self.pages.items():page.grid_remove()
        self.pages[name].grid();self.current_page=name
        t=PALETTES[self.theme_name]
        for key,button in self.navbuttons.items():button.config(bg=t["raised"] if key==name else t["nav"],fg=t["fg"] if key==name else t["muted"])
        if self.root.state()=="withdrawn":self.show()
    def save_preferences(self):
        v=copy.deepcopy(self.settings.value);v["onboarded"]=True
        first=not self.settings.value["onboarded"]
        if first:v["participation"]=bool(self.form_cpu.get());v["paused"]=False
        v["resources"].update(cpu=bool(self.form_cpu.get()),threads=int(self.form_threads.get()),
          ram_mib=int(float(self.form_ram.get().replace(",","."))*1024),idle_only=bool(self.form_idle.get()),pause_on_battery=bool(self.form_battery.get()))
        v["close_to_tray"]=bool(self.form_tray.get());v["start_hidden"]=bool(self.form_hidden.get())
        self.service.configure(v);self.locale.option(self.resource_title,self.locale.msg("resources.title"));self.locale.option(self.save_settings_button,self.locale.msg("resources.save"))
        self.show_page("overview");self.refresh()
    def toggle_participation(self):
        if not self.settings.value["onboarded"]:self.show_page("resources");return
        if self.service.status() in ("PAUSED","STOPPED"):self.service.resume()
        else:self.service.pause()
        self.refresh()
    def stop(self):self.service.stop();self.refresh()
    def connection_settings(self):
        path=filedialog.askopenfilename(parent=self.root,title=(self.locale.msg('connection.choose')),filetypes=[("JSON","*.json")])
        if not path:return
        v=copy.deepcopy(self.settings.value);v["connection"]=path;self.service.configure(v,reset_connection=True)
        self.service.event("Godkendt forbindelsesfil valgt");self.refresh()
    def details(self):
        win=tk.Toplevel(self.root);self.locale.title(win,self.locale.msg("ledger.title"));win.geometry("800x340")
        t=PALETTES[self.theme_name];win.config(bg=t["card"])
        self.locale.widget(tk.Label,win,text=ledger(self.locale,self.service.state),bg=t["card"],fg=t["fg"],font=("Segoe UI",11),wraplength=750,justify="left",padx=24,pady=24).pack(fill="both",expand=True)
        self.locale.widget(tk.Label,win,text=(self.locale.msg('ledger.authority')),bg=t["card"],fg=t["muted"],wraplength=740,pady=15).pack()
    def open_setup(self):
        from .onboarding_ui import Wizard
        existing=getattr(self,"setup_wizard",None)
        if existing and existing.window.winfo_exists():existing.window.lift();return
        self.setup_wizard=Wizard(self.root,self.locale,self.settings.directory,self.mcp_secrets)
    def open_studio(self):
        if self.studio and self.studio.root.winfo_exists():self.studio.show();return
        from .ui import App as Studio
        win=tk.Toplevel(self.root)
        self.studio=Studio(win,self.workspace_arg,standalone=False,on_network=self.details,on_stop=self.stop,locale=self.locale,settings_dir=self.settings.directory,mcp_secrets=self.mcp_secrets)
        self.locale.title(win,self.locale.msg("studio.title"))
        if self.studio.theme_name!=self.theme_name:self.studio.toggle_theme()
    def select_language(self,event=None):
        selected=LOCALES[NAMES.index(self.language_name.get())]
        try:self.language_preference.save(selected)
        except (OSError,ValueError):
            self.language_name.set(NAMES[LOCALES.index(self.locale.locale)])
            self.dialogs.showerror("ChromaNeural",self.locale.msg("language.error"))
            return
        self.locale.set(selected)
    def language_changed(self):
        self.language_name.set(NAMES[LOCALES.index(self.locale.locale)])
        self.refresh()
    def refresh(self):
        v=self.service.view();status=v["status"];c=self.locale;t=c.text
        self.vars["title"].set(t(status.lower()+".title"));self.vars["subtitle"].set(t(status.lower()+".subtitle"))
        summary=t("network.summary",points=c.number(v["points"]),status=t("status."+status.lower()))
        self.vars["pill"].set("●  "+summary)
        for key in ("points","balance","spent"):self.vars[key].set(c.number(v[key]))
        self.vars["ratio"].set(t("ratio.label")+"   "+(t("waiting") if v["ratio"] is None else "1 : "+c.number(v["ratio"])))
        self.vars["contribution"].set(t("metric.contribution",data=c.bytes(v["data_bytes"]),cpu=c.number(v["cpu_seconds"])))
        self.vars["consumed"].set(t("consumed.label")+"   "+c.bytes(v["consumed_bytes"]))
        r=self.settings.value["resources"]
        self.vars["cpu"].set(t("metric.cpu",count=c.number(r["threads"],0)) if r["cpu"] else "CPU     "+t("not.enrolled"))
        self.vars["ram"].set(t("metric.ram",amount=c.number(r["ram_mib"]/1024)) if r["cpu"] else "RAM    "+t("not.enrolled"))
        self.vars["resources_note"].set(t("resources.waiting" if r["cpu"] else "resources.hint"))
        self.vars["ai"].set(t("ai."+status.lower() if status in ("DORMANT","PAUSED","STOPPED","READY") else "ai.waiting"))
        suffix=t("metric.allowance",amount=c.number(v["bootstrap"])) if v["bootstrap"] is not None else ""
        self.vars["fresh"].set((t("fresh.at")+" "+str(v["last_refresh"]) if v["fresh"] else t("fresh.stale" if v["points"] is not None else "fresh.none"))+suffix)
        self.vars["footer"].set(t("footer.private"))
        self.primary.config(text=t({"SETUP":"action.choose","PAUSED":"action.resume","STOPPED":"action.start"}.get(status,"action.pause")))
        text="\n\n".join(clock+"   "+activity(c,event) for clock,event in reversed(self.service.events))
        if self.activity.get("1.0","end-1c")!=text:
            self.activity.config(state="normal");self.activity.delete("1.0","end");self.activity.insert("1.0",text);self.activity.config(state="disabled")
        if hasattr(self,"tray"):self.tray.update("ChromaNeural · "+summary,paused=status in ("PAUSED","STOPPED"))
    def tick(self):
        if self.closed:return
        self.connection_panel.poll();self.refresh();self.after_id=self.root.after(500,self.tick)
    def hide(self):
        if not self.tray.available:
            self.dialogs.showinfo((self.locale.msg('tray.unavailable')),(self.locale.msg('tray.kept')),parent=self.root);return
        if self.studio and self.studio.root.winfo_exists():self.studio.root.withdraw()
        self.root.withdraw()
    def show(self):self.root.deiconify();self.root.lift()
    def close(self):
        if self.settings.value["onboarded"] and self.settings.value["close_to_tray"] and self.tray.available:self.hide()
        else:self.quit()
    def quit(self):
        if self.studio and self.studio.root.winfo_exists():
            if not self.studio.discard_ok():return
            self.studio.shutdown()
        self.closed=True;self.service.close()
        if hasattr(self,"after_id"):self.root.after_cancel(self.after_id)
        self.tray.close();self.root.destroy()
    def toggle_theme(self):
        self.theme_name="light" if self.theme_name=="dark" else "dark"
        v=copy.deepcopy(self.settings.value);v["theme"]=self.theme_name;self.settings.save(v);self.service.value["theme"]=self.theme_name
        self.apply_theme()
    def apply_theme(self):
        t=PALETTES[self.theme_name];self.root.config(bg=t["bg"])
        if os.name=="nt":
            import ctypes
            from ctypes import wintypes
            user=ctypes.WinDLL("user32");user.GetAncestor.argtypes=[wintypes.HWND,wintypes.UINT];user.GetAncestor.restype=wintypes.HWND
            self.root.update_idletasks();hwnd=user.GetAncestor(self.root.winfo_id(),2)
            dark=ctypes.c_int(self.theme_name=="dark")
            dwm=ctypes.WinDLL("dwmapi");dwm.DwmSetWindowAttribute.argtypes=[wintypes.HWND,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD]
            dwm.DwmSetWindowAttribute(hwnd,20,ctypes.byref(dark),ctypes.sizeof(dark))
        for w,bg,fg in self.skinned:
            if not w.winfo_exists():continue
            kw={"bg":t[bg]}
            if fg:kw["fg"]=t[fg]
            if isinstance(w,tk.Frame) and int(w.cget("highlightthickness")):kw.update(highlightbackground=t["line"],highlightcolor=t["line"])
            if isinstance(w,tk.Button):kw.update(activebackground=t["raised"],activeforeground=t["fg"],highlightbackground=t["line"],highlightcolor=t["cyan"],highlightthickness=1)
            if isinstance(w,tk.Checkbutton):kw.update(activebackground=t[bg],activeforeground=t["fg"],selectcolor=t["raised"])
            if isinstance(w,tk.Text):kw.update(insertbackground=t["fg"],selectbackground=t["accent"],selectforeground=t["on_accent"])
            w.config(**kw)
        style=ttk.Style();style.theme_use("clam")
        style.configure("Chroma.TCombobox",fieldbackground=t["raised"],background=t["raised"],foreground=t["fg"],arrowcolor=t["fg"],padding=6)
        style.map("Chroma.TCombobox",fieldbackground=[("readonly",t["raised"])],foreground=[("readonly",t["fg"])],selectbackground=[("readonly",t["accent"])],selectforeground=[("readonly",t["on_accent"])])
        def draw(w):
            if isinstance(w,tk.Canvas) and hasattr(w,"redraw"):w.redraw()
            for child in w.winfo_children():draw(child)
        draw(self.root)
        if hasattr(self,"current_page"):self.show_page(self.current_page)
