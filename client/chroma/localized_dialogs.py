"""Small app-owned modal adapter. OS file picker chrome remains OS-owned."""
import tkinter as tk
from .i18n import Message

class OwnedDialog:
    def __init__(self, parent, locale, title, message, kind="info", initialvalue=""):
        self.locale = locale
        self.kind = kind
        self.result = None if kind == "string" else False
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.transient(parent)
        locale.title(self.window, title)
        self.label = locale.widget(tk.Label, self.window, text=message, justify="left",
                                   wraplength=640, padx=20, pady=18)
        self.label.pack(fill="both", expand=True)
        self.entry = None
        if kind == "string":
            self.entry = tk.Entry(self.window, width=60)
            self.entry.insert(0, initialvalue)
            self.entry.pack(fill="x", padx=20, pady=6)
        bar = tk.Frame(self.window)
        bar.pack(fill="x", padx=20, pady=12)
        self.buttons = {}
        choices = (("common.yes", True), ("common.no", False)) if kind == "yesno" else (("common.ok", True),)
        if kind == "string":
            choices += (("common.cancel", False),)
        for key, answer in choices:
            button = locale.widget(tk.Button, bar, text=locale.msg(key),
                                   command=lambda answer=answer: self.finish(answer),
                                   padx=18, pady=8)
            button.pack(side="right", padx=4)
            self.buttons[key] = button
        self.window.protocol("WM_DELETE_WINDOW", lambda: self.finish(False))
        self.window.bind("<Escape>", lambda event: self.finish(False))
        self.window.bind("<Return>", lambda event: self.finish(True))

    def finish(self, answer):
        self.result = self.entry.get() if self.kind == "string" and answer else (None if self.kind == "string" else bool(answer))
        self.window.destroy()

    def show(self):
        self.window.deiconify()
        self.window.wait_visibility()
        previous = self.window.grab_current()
        self.window.grab_set()
        (self.entry or next(iter(self.buttons.values()))).focus_set()
        self.window.wait_window()
        if previous is not None and previous.winfo_exists():
            previous.grab_set()
        return self.result

class Dialogs:
    def __init__(self, parent, locale):
        self.parent, self.locale = parent, locale
    def showinfo(self, title, message, **kwargs):
        return OwnedDialog(kwargs.get("parent", self.parent), self.locale, title, message).show()
    showerror = showinfo
    def askyesno(self, title, message, **kwargs):
        return OwnedDialog(kwargs.get("parent", self.parent), self.locale, title, message, "yesno").show()
    def askstring(self, title, prompt, initialvalue="", **kwargs):
        return OwnedDialog(kwargs.get("parent", self.parent), self.locale, title, prompt, "string", initialvalue).show()
