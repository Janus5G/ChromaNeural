"""Actual Tk, isolated state, synthetic stopped controller, no live probes."""
from pathlib import Path
import copy
import json
import os
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import tkinter as tk

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"client"))
from chroma.dashboard import App
from chroma.i18n import LOCALES,NAMES,LocaleContext
from chroma.settings import Settings
from chroma.network_state import NetworkState
from chroma.localized_dialogs import OwnedDialog

def capture_view(window):
    """Capture the requested client window, independent of desktop occlusion."""
    from PIL import ImageGrab
    window.update_idletasks()
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        user = ctypes.WinDLL("user32")
        user.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        user.GetAncestor.restype = wintypes.HWND
        hwnd = user.GetAncestor(window.winfo_id(), 2)
        if not hwnd:
            raise OSError("Cannot resolve capture window")
        return ImageGrab.grab(window=int(hwnd))
    x, y = window.winfo_rootx(), window.winfo_rooty()
    return ImageGrab.grab(bbox=(x, y, x + window.winfo_width(), y + window.winfo_height()))

class Controller:
    def __init__(self,settings):
        self.settings=settings
        self.value=settings.value
        self.state=NetworkState(settings.directory/"balance-cache.json")
        self.events=[("12:00:00","Deltagelse stoppet"),("12:00:01","AI worker · IDLE")]
        self.starts=0;self.pauses=0;self.resumes=0;self.stops=0;self.closes=0
    def start(self):self.starts+=1
    def close(self):self.closes+=1
    def status(self):
        return "PAUSED" if self.value["paused"] else ("UNCONNECTED" if self.value["participation"] else "STOPPED")
    def view(self):
        return dict(status=self.status(),points=None,spent=None,balance=None,ratio=None,
            data_bytes=None,cpu_seconds=None,consumed_bytes=None,bootstrap=None,fresh=False,last_refresh=None)
    def event(self,text):self.events.append(("12:00:02",text))
    def configure(self,value,**kwargs):self.settings.save(value);self.value=self.settings.value
    def pause(self):self.pauses+=1;self.value["paused"]=True
    def resume(self):self.resumes+=1;self.value["paused"]=False;self.value["participation"]=True
    def stop(self):self.stops+=1;self.value["paused"]=False;self.value["participation"]=False

class GuiLocalizationTests(unittest.TestCase):
    def test_all_locales_views_probe_dialogs_and_preservation(self):
        from chroma import connection_ui
        with tempfile.TemporaryDirectory() as temp:
            state=Path(temp)
            settings=Settings(state)
            value=copy.deepcopy(settings.value)
            value.update(onboarded=True,close_to_tray=False)
            settings.save(value)
            original=settings.path.read_bytes()
            for name in ("identity.json","job-queue.sqlite","source.cpl"):
                (state/name).write_bytes(b"private-test-fixture\x00\r\n")
            protected={p.name:p.read_bytes() for p in state.iterdir()}
            service=Controller(settings)
            root=tk.Tk()
            callback_errors=[]
            root.report_callback_exception=lambda *args:callback_errors.append(str(args[1]))
            app=None
            release=threading.Event()
            try:
                app=App(root,state_dir=state,controller=service)
                # The controller uses the App's Settings object as in production.
                service.settings=app.settings;service.value=app.settings.value
                if hasattr(app,"after_id"):root.after_cancel(app.after_id);del app.after_id
                root.geometry("1280x900+20+20")
                root.update()
                self.assertEqual(app.locale.locale,"en")
                self.assertEqual(service.starts,1)
                app.form_threads.set(3);app.form_ram.set("0.5")
                app.form_idle.set(False)
                panel=app.connection_panel
                pasted='{"unaltered":"日本語 {x} C:\\\\source","number":7}\n'
                panel.editor.insert("1.0",pasted)
                # Synthetic in-memory metadata: never saved or sent to a real probe.
                panel.profile.value={"backend_canister_id":"synthetic-canister"}
                app.open_studio()
                studio=app.studio
                studio.root.withdraw()
                source="raw source 日本語 {x}\n  spaces\n"
                studio.editor.insert("1.0",source)
                studio.show_output("compiler {literal} output")
                studio.profile.set("cpl-spec")
                studio.target_platforms()
                target=studio.target_dialog
                target.selected.set("esp32");target.show_selected()
                target.window.withdraw()
                events=copy.deepcopy(service.events)
                calls=[]
                def probe(profile):
                    calls.append(copy.deepcopy(profile));release.wait(10)
                    return {"public":True}
                with patch.object(connection_ui,"probe_profile",side_effect=probe):
                    panel.check_connection()
                    generation=panel.generation
                    for locale in LOCALES:
                        app.language_name.set(NAMES[LOCALES.index(locale)])
                        app.select_language()
                        root.update()
                        self.assertEqual(app.locale.locale,locale)
                        self.assertEqual(panel.generation,generation)
                        self.assertTrue(panel.busy)
                        self.assertIn(app.locale.text("connection.checking"),panel.status.get())
                        self.assertEqual(app.form_threads.get(),3)
                        self.assertEqual(app.form_ram.get(),"0.5")
                        self.assertFalse(app.form_idle.get())
                        self.assertEqual(panel.editor.get("1.0","end-1c"),pasted)
                        self.assertEqual(studio.editor.get("1.0","end-1c"),source)
                        self.assertEqual(studio.output.get("1.0","end-1c"),"compiler {literal} output")
                        self.assertEqual(studio.profile.get(),"cpl-spec")
                        self.assertEqual(target.selected.get(),"esp32")
                        self.assertIn(app.locale.text("target.arch"),target.details.get("1.0","end-1c"))
                        for page in ("overview","resources","activity","connection"):
                            app.show_page(page);root.update()
                            self.assertEqual(app.navbuttons[page].cget("text"),app.locale.text("nav."+page))
                            self.assertFalse(app.locale.findings)
                        for name,raw in protected.items():self.assertEqual((state/name).read_bytes(),raw)
                        self.assertEqual(service.events,events)
                        self.assertEqual(service.starts,1)
                        self.assertEqual((service.pauses,service.resumes,service.stops),(0,0,0))
                    release.set()
                    # Wait on the bounded synthetic queue, not the network.
                    item=panel.results.get(timeout=5);panel.results.put(item);panel.poll()
                self.assertEqual(len(calls),1)
                result=panel.last_probe
                for locale in LOCALES:
                    app.locale.set(locale)
                    self.assertEqual(panel.status.get(),app.locale.text("connection.success"))
                    self.assertIs(panel.last_probe,result)
                # Failure/unknown text and stale reply are kept separate from locale.
                panel.results.put((panel.generation,False,"external {x} diagnostic"));panel.poll()
                app.locale.set("fr")
                self.assertIn("external {x} diagnostic",panel.error.get())
                self.assertEqual(panel.status.get(),app.locale.text("connection.failed"))
                panel.results.put((panel.generation-1,True,{"stale":True}));panel.poll()
                self.assertIsNone(panel.last_probe)
                self.assertNotEqual(panel.status.get(),app.locale.text("connection.success"))
                # Failed explicit language save keeps prior locale and choice.
                app.language_name.set("日本語")
                with patch.object(app.language_preference,"save",side_effect=OSError("failure")),patch.object(app.dialogs,"showerror") as error:
                    app.select_language();error.assert_called_once()
                self.assertEqual(app.locale.locale,"fr")
                self.assertEqual(app.language_name.get(),"Français")
                # Owned modal controls update without losing entered data; Escape/close is cancel.
                for locale in LOCALES:
                    app.locale.set(locale)
                    dialog=OwnedDialog(root,app.locale,app.locale.msg("studio.ai"),app.locale.msg("studio.instruction"),"string","user 日本語 {x}")
                    app.locale.set("en" if locale!="en" else "da")
                    self.assertEqual(dialog.entry.get(),"user 日本語 {x}")
                    self.assertEqual(dialog.buttons["common.cancel"].cget("text"),app.locale.text("common.cancel"))
                    dialog.finish(False);self.assertIsNone(dialog.result)
                    confirm=OwnedDialog(root,app.locale,app.locale.msg("studio.unsaved"),app.locale.msg("studio.discard"),"yesno")
                    confirm.finish(False);self.assertFalse(confirm.result)
                # Resource save and participation controls keep original callback effects.
                app.save_preferences()
                self.assertEqual(service.value["resources"]["threads"],3)
                self.assertEqual(service.value["resources"]["ram_mib"],512)
                app.toggle_participation();app.toggle_participation();app.stop()
                self.assertEqual((service.resumes,service.pauses,service.stops),(1,1,1))
                self.assertEqual(service.starts,1)
                # Capture real representative rendered surfaces on an isolated stopped controller.
                destination=os.environ.get("CHROMA_LOCALIZATION_EVIDENCE")
                if destination:
                    out=Path(destination);out.mkdir(parents=True,exist_ok=True)
                    for locale in LOCALES:
                        app.locale.set(locale)
                        for page in ("overview","resources","activity","connection"):
                            app.show_page(page);root.update()
                            capture_view(root).save(out/(locale+"-"+page+".png"))
                        studio.root.deiconify();studio.root.lift();studio.root.update()
                        capture_view(studio.root).save(out/(locale+"-studio.png"))
                        studio.root.withdraw()
                        target.window.deiconify();target.window.lift();target.window.update()
                        capture_view(target.window).save(out/(locale+"-targets.png"))
                        target.window.withdraw()
                self.assertFalse(callback_errors,callback_errors)
                self.assertEqual(app.settings.path.read_bytes(),service.settings.path.read_bytes())
                self.assertNotEqual(original,app.settings.path.read_bytes()) # Only explicit resource save.
                studio.load(b"") # Explicit cleanup; no discard dialog for test-owned unsaved input.
                app.quit();app=None
                self.assertEqual(service.closes,1)
            finally:
                release.set()
                if app:
                    if app.studio and app.studio.root.winfo_exists():app.studio.load(b"")
                    app.quit()
                else:
                    try:root.destroy()
                    except tk.TclError:pass

if __name__=="__main__":
    unittest.main(verbosity=2)
