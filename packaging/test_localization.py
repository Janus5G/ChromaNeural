"""Bounded Phase B/C checks. No external service, inference or live identity."""
from pathlib import Path
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "client"))
from chroma.i18n import (LOCALES, LocaleContext, LanguagePreference, catalog, fields,
                         language_from_argv, NEUTRAL)
from chroma.localized_views import activity, diagnostic, target_description, ledger
from chroma.settings import Settings, validate
from chroma.targets import load_catalog
from chroma.network_state import NetworkState

class LocalizationTests(unittest.TestCase):
    def test_resource_parity_unicode_and_format_safety(self):
        canonical = catalog("en")
        self.assertGreaterEqual(len(canonical), 292)
        for locale in LOCALES:
            values = catalog(locale)
            self.assertEqual(set(values), set(canonical), locale)
            self.assertEqual(values, json.loads(json.dumps(values, ensure_ascii=False).encode("utf-8")), locale)
            for key, text in values.items():
                self.assertEqual(fields(text), fields(canonical[key]), (locale,key))
            if locale != "en":
                # Brand/unit/OK values can be identical; prose must be translated.
                for key in ("setup.subtitle","resources.limits","studio.consent","target.note","launch.help"):
                    self.assertNotEqual(values[key], canonical[key], (locale,key))
        for bad in ("{x.__class__}", "{x[0]}", "{x!r}", "{x:>9}", "{}", "{0}", "{x:{y}}"):
            with self.assertRaises(ValueError):fields(bad)

    def test_fallback_and_data_is_literal(self):
        c = LocaleContext("da")
        c.messages = dict(c.messages)
        del c.messages["setup.title"]
        self.assertEqual(c.text("setup.title"), c.english["setup.title"])
        self.assertEqual(c.text("not.a.message"), NEUTRAL)
        self.assertIn("missing:not.a.message", c.findings)
        value = r"C:\{name}\日本語\$HOME"
        self.assertIn(value, c.text("studio.saved.message", name=value))
        c.messages["studio.saved.message"] = "{name.__class__}"
        self.assertEqual(c.text("studio.saved.message", name=value), NEUTRAL)
        self.assertEqual(LocaleContext("xx").locale, "en")

    def test_preference_compatibility_and_explicit_save(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            old = Settings(directory)
            old.save(old.value)
            original = old.path.read_bytes()
            for name in ("identity.json","connection-profile.json","queue.sqlite","source.cpl"):
                (directory/name).write_bytes(b"untouched\x00\r\n")
            before = {p.name:p.read_bytes() for p in directory.iterdir()}
            preference = LanguagePreference(directory)
            self.assertEqual(preference.locale,"en")
            self.assertFalse(preference.path.exists())
            override = LocaleContext(language_from_argv(["--language","ja","--workspace","x"]))
            self.assertEqual(override.locale,"ja")
            self.assertFalse(preference.path.exists())
            for locale in LOCALES:
                preference.save(locale)
                self.assertEqual(LanguagePreference(directory).locale,locale)
            for name, raw in before.items():
                self.assertEqual((directory/name).read_bytes(),raw)
            self.assertEqual(old.path.read_bytes(),original)
            self.assertEqual(validate(Settings(directory).value),old.value)
            invalids = [b"invalid\xff", b" "*1025, b'{"version":true,"locale":"da"}',
                        b'{"version":1,"locale":"xx"}', b'{"version":1,"locale":"da","extra":0}',
                        b'{"version":1,"locale":[]}', b'{"version":1,"locale":null}']
            for raw in invalids:
                preference.path.write_bytes(raw)
                self.assertEqual(LanguagePreference(directory).locale,"en")
                self.assertEqual(preference.path.read_bytes(),raw)
            preference.save("fr")
            backups=list(directory.glob("ui-language.invalid.*.json"))
            self.assertTrue(any(p.read_bytes()==invalids[-1] for p in backups))
            saved=preference.path.read_bytes()
            with patch("chroma.i18n.os.replace", side_effect=OSError("test save failure")):
                with self.assertRaises(OSError):preference.save("ja")
            self.assertEqual(preference.locale,"fr")
            self.assertEqual(preference.path.read_bytes(),saved)
            self.assertFalse(list(directory.glob(".ui-language-*")))

    def test_display_boundaries_and_accounting(self):
        c=LocaleContext("ja")
        unknown="External {payload} Netværksbalance bekræftet"
        self.assertEqual(activity(c,unknown),unknown)
        self.assertEqual(activity(c,"Netværksbalance bekræftet"),c.text("event.balance"))
        self.assertIn(unknown,str(diagnostic(c,unknown)))
        self.assertEqual(str(diagnostic(c,"Ugyldigt Principal-format")),c.text("error.principal"))
        event="ChromaNeuroAI · Publicering: Handling bekræftet"
        self.assertIn("ChromaNeural",activity(c,event))
        self.assertNotIn("ChromaNeuroAI",activity(c,event))
        self.assertIn("ID{raw}",activity(c,"AI worker · FAILED · ID{raw}"))
        with tempfile.TemporaryDirectory() as temp:
            state=NetworkState(Path(temp)/"cache.json")
            state.snapshot={"status":"READY","account":{"earned":"2000000","spent":"1000000",
                "bootstrap":"500000","consumedBytes":"71","contribution":{"dataBytes":"31","cpuMicros":"9000000",
                "ramByteMicros":"5000000","gpuMicros":"0"}},"policy":{"epoch":"epoch-37","ratioBps":"20000"},
                "available":"1500000","adjustment":"0","debt":"0"}
            before=copy.deepcopy(state.snapshot)
            for locale in LOCALES:
                c.set(locale);text=str(ledger(c,state))
                self.assertIn("epoch-37",text)
                self.assertIn("31 B",text)
            self.assertEqual(state.snapshot,before)
            self.assertFalse(state.cache.exists())

    def test_catalogue_exact_bytes_and_ids(self):
        raw=(ROOT/"client/docs/TARGETS.json").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),"e4b10c19a38a642461e98cecea4653033013ca9188604759b3d34c399efbe628")
        targets=load_catalog()
        original=copy.deepcopy(targets)
        for locale in LOCALES:
            c=LocaleContext(locale)
            for target in targets:
                text=target_description(c,target)
                self.assertTrue(text.startswith(target["id"]+"\n\n"))
                self.assertIn(c.text("target.arch"),text)
                self.assertFalse(c.findings)
        self.assertEqual(targets,original)

    def test_numbers_and_no_global_locale(self):
        c=LocaleContext()
        self.assertEqual(c.number(1234567.5),"1,234,567.5")
        c.set("da");self.assertEqual(c.number(1234567.5),"1.234.567,5")
        c.set("fr");self.assertEqual(c.number(1234.5),"1\u202f234,5")
        c.set("hi-IN");self.assertEqual(c.number(1234567.5),"12,34,567.5")
        self.assertEqual(c.number(None),"—")
        self.assertEqual(c.bytes(1048576),"1 MiB")

    def test_help_is_local_and_json_contract_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            state=Path(temp)/"state-that-must-not-exist"
            env={**os.environ,"CHROMA_STATE_DIR":str(state),"PYTHONDONTWRITEBYTECODE":"1","PYTHONUTF8":"1"}
            for script in ("client/launch.py","scripts/network_client.py"):
                for locale in LOCALES:
                    result=subprocess.run([sys.executable,"-B",str(ROOT/script),"--language",locale,"--help"],
                        env=env,capture_output=True,encoding="utf-8",timeout=15)
                    self.assertEqual(result.returncode,0,result.stderr)
                    key="launch.help" if script.startswith("client") else "cli.description"
                    self.assertIn(LocaleContext(locale).text(key),result.stdout)
                    self.assertIn("--language",result.stdout)
                    self.assertFalse(state.exists())
            # A bounded validation failure, before any connection or network call.
            results=[]
            for locale in ("en","ja"):
                result=subprocess.run([sys.executable,"-B",str(ROOT/"scripts/network_client.py"),
                    "--language",locale,"plan","--namespace","n","--key","k","--question-file","unused","--output","unused"],
                    env=env,capture_output=True,encoding="utf-8",timeout=15)
                self.assertEqual(result.returncode,1)
                results.append(json.loads(result.stderr))
            self.assertEqual(results[0],results[1])
            self.assertFalse(state.exists())

if __name__=="__main__":
    unittest.main(verbosity=2)
