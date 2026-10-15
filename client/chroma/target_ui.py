"""Informational target chooser. No state writes, installation or execution."""
import tkinter as tk
from tkinter import ttk
from .targets import load_catalog
from .i18n import LocaleContext
from .localized_views import target_description

class TargetDialog:
    def __init__(self, parent, profile, theme, locale=None):
        self.locale = locale or LocaleContext()
        self.targets = load_catalog()  # Validate before creating a window.
        self.window = tk.Toplevel(parent)
        self.locale.title(self.window,(self.locale.msg('target.title')))
        self.window.geometry("720x640")
        self.window.minsize(560,420)
        self.window.grid_columnconfigure(0,weight=1)
        self.window.grid_rowconfigure(2,weight=1)
        self.heading = self.locale.widget(tk.Label,self.window,text=(self.locale.msg('target.heading')),font=("Segoe UI",16,"bold"),anchor="w")
        self.heading.grid(row=0,column=0,columnspan=2,sticky="ew",padx=16,pady=(14,8))
        self.selected = tk.StringVar(self.window)
        self.select = ttk.Combobox(self.window,textvariable=self.selected,state="readonly",values=tuple(t["id"] for t in self.targets))
        self.select.grid(row=1,column=0,columnspan=2,sticky="ew",padx=16,pady=(0,10))
        self.details = tk.Text(self.window,wrap="word",font=("Segoe UI",11),padx=12,pady=10,state="disabled",takefocus=True)
        self.details.grid(row=2,column=0,sticky="nsew",padx=(16,0))
        self.scroll = ttk.Scrollbar(self.window,command=self.details.yview)
        self.scroll.grid(row=2,column=1,sticky="ns",padx=(0,16))
        self.details.configure(yscrollcommand=self.scroll.set)
        self.note = self.locale.widget(tk.Label,self.window,text=(self.locale.msg('target.note')),justify="left",anchor="w")
        self.note.grid(row=3,column=0,columnspan=2,sticky="ew",padx=16,pady=10)
        self.note.bind("<Configure>",lambda event:self.note.configure(wraplength=max(100,event.width)))
        self.close = self.locale.widget(tk.Button,self.window,text=(self.locale.msg('common.close')),command=self.window.destroy,font=("Segoe UI",10),relief="flat",padx=18,pady=7)
        self.close.grid(row=4,column=0,columnspan=2,sticky="e",padx=16,pady=(0,14))
        self.window.bind("<Escape>",lambda event:self.window.destroy())
        self.select.bind("<<ComboboxSelected>>",self.show_selected)
        initial = {"cpa-legacy":"cpl-legacy","cpa-spec":"cpl-spec"}.get(profile,profile)
        self.selected.set(initial if initial in tuple(t["id"] for t in self.targets) else self.targets[0]["id"])
        self.show_selected()
        self.locale.listen(self.window,self.retranslate)
        self.apply_theme(theme)

    def show_selected(self, event=None):
        target = next(t for t in self.targets if t["id"] == self.selected.get())
        self.details.configure(state="normal")
        self.details.delete("1.0","end")
        self.details.insert("1.0",target_description(self.locale,target))
        self.details.configure(state="disabled")
        self.details.yview_moveto(0)

    def retranslate(self):
        position=self.details.yview()
        self.show_selected()
        if position:self.details.yview_moveto(position[0])

    def apply_theme(self, theme):
        self.window.configure(bg=theme["bg"])
        for label in (self.heading,self.note):
            label.configure(bg=theme["bg"],fg=theme["fg"])
        self.details.configure(bg=theme["panel"],fg=theme["fg"],insertbackground=theme["fg"],selectbackground=theme["accent"],selectforeground=theme["on_accent"])
        self.close.configure(bg=theme["accent"],fg=theme["on_accent"],activebackground=theme["accent"],activeforeground=theme["on_accent"])
