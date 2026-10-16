"""Actual Linux Tk: blocked resource policy, explicit local-only choice, EN/DA."""
import sys,tempfile,time,tkinter as tk,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'client'))
from chroma.mcp_usage import Usage
from chroma.mcp_usage_ui import Consent
from chroma.i18n import LocaleContext,fields,LOCALES
class ConsentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='resource-ui-');self.path=Path(self.temp.name)
        self.root=tk.Tk();self.root.withdraw();self.dialog=None
    def tearDown(self):
        if self.dialog and not self.dialog.closed:self.dialog.close(None)
        self.root.destroy();self.temp.cleanup()
    def show(self,lang):
        self.dialog=Consent(self.root,LocaleContext(lang),self.path,[{'id':'fixture','name':'Fixture'}],'synthetic','keep','fixture:model')
        end=time.monotonic()+4
        while self.dialog.busy and time.monotonic()<end:self.root.update();time.sleep(.02)
        self.assertFalse(self.dialog.busy);self.root.update()
    def test_en_da_blocked_clear_and_not_quoting_calls(self):
        for lang in ('en','da'):
            self.show(lang)
            self.assertEqual(str(self.dialog.approve.cget('state')),'disabled')
            self.assertEqual(self.dialog.summary.get(),self.dialog.locale.text('usage.unavailable'))
            self.dialog.accept();self.assertIsNone(self.dialog.result)
            self.assertFalse(Usage(self.path).path.exists())
            self.dialog.queue.put(("reserve",True,("obsolete-v1-task",4)))
            self.dialog.poll();self.assertIsNone(self.dialog.result)
            self.dialog.local.invoke();self.assertEqual(self.dialog.result,([],None))
    def test_cancel_no_silent_fallback(self):
        self.show('en');self.dialog.cancel.invoke();self.assertIsNone(self.dialog.result)
    def test_locale_keys_and_fallback(self):
        en=LocaleContext('en');da=LocaleContext('da');keys={k for k in en.english if k.startswith('usage.')}
        self.assertEqual(len(keys),11);self.assertTrue(keys<=set(da.messages))
        for key in keys:
            self.assertEqual(fields(en.english[key]),fields(da.messages[key]))
            self.assertNotIn('?',da.messages[key])
        for lang in LOCALES:
            ctx=LocaleContext(lang)
            for key in keys:self.assertNotEqual(ctx.text(key),key)
if __name__=='__main__':unittest.main(verbosity=2)
