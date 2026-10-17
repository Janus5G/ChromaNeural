"""Focused guided-onboarding UI/security tests. No vendor/network connections.
Run directly with Python -I -B. Uses real Tk widgets and Config persistence;
provider discovery and service responses use bounded fixtures, not vendor PASS.
"""
import ast
import copy
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
import tkinter as tk
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "client"))
from chroma import onboarding_ui as ui
from chroma import onboarding
from chroma.ai_provider import selection
from chroma.i18n import LocaleContext, LOCALES, fields
from chroma.mcp_catalog import PROFILES, candidates, checked_connection, installed_program, local_path, needs_extra_consent
from chroma.mcp_config import Config, connection_key, fingerprint
from chroma.mcp_client import Host


def children(widget):
    result = []
    for child in widget.winfo_children():
        result.append(child)
        result.extend(children(child))
    return result


class WizardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chroma-wizard-test-")
        self.directory = Path(self.tmp.name)
        self.discovery = patch.object(ui, "discover", return_value=[])
        self.discovery.start()
        self.w = ui.Wizard(self.root, LocaleContext("en"), self.directory, {})
        self.w.dialogs.askyesno = lambda *a, **k: True
        self.w.dialogs.showinfo = lambda *a, **k: None
        self.providers = [dict(provider="bundled-cpu", model=None, endpoint="", status="discovered"),
                          dict(provider="ollama", model="qwen3:4b-instruct", endpoint="http://127.0.0.1:11434", status="discovered")]
        self.w.found_providers(self.providers)

    def tearDown(self):
        if not self.w.closed:
            self.w.close()
        self.root.update()
        self.discovery.stop()
        self.tmp.cleanup()

    def choose(self, ident="siemens"):
        self.w.choose_profile(next(p for p in PROFILES if p.id == ident))

    def connect(self, tools=None):
        self.choose()
        self.w.review_connection()
        tool = {"name": "askDeveloperPortal", "description": "Search documentation", "input_schema": {"type": "object"}, "output_schema": None, "annotations": None}
        value = {"tools": [tool] if tools is None else tools, "resources": [], "protocol": "fixture"}
        with patch.object(ui, "discover_mcp", return_value=value):
            self.w.approve_and_test()
            deadline = time.monotonic() + 3
            while self.w.busy and time.monotonic() < deadline:
                self.root.update(); time.sleep(.01)
        self.assertFalse(self.w.busy)
        return tool

    def test_real_tk_wizard_not_notebook_and_initial_read_only(self):
        self.assertFalse(any(isinstance(c, ui.ttk.Notebook) for c in children(self.w.window)))
        self.assertFalse(self.w.config.path.exists())
        self.assertIn("Step 1 of 7", self.w.progress.get())

    def test_builtin_and_skip_complete_without_mcp_config(self):
        self.w.provider_list.selection_clear(0, "end")
        self.w.provider_list.selection_set(0)
        self.w.continue_ai()
        self.assertEqual(self.w.page, "optional")
        self.w.skip()
        self.assertEqual(self.w.page, "finish")
        self.w.finish()
        self.assertTrue(self.w.closed)
        self.assertEqual(self.w.config.load()["servers"], [])
        self.assertIsNone(self.w.config.load()["provider"])

    def test_ollama_recommendation_only_when_exact_model_present(self):
        self.assertIn("verified", " ".join(self.w.provider_list.get(0, "end")))
        self.w.provider_list.selection_clear(0, "end")
        self.w.provider_list.selection_set(1)
        self.w.continue_ai()
        self.assertEqual(self.w.config.load()["provider"], selection("ollama", "qwen3:4b-instruct"))
        self.w.show("ai")
        self.w.found_providers([dict(self.providers[1], model="other:1b")])
        self.assertNotIn("verified", " ".join(self.w.provider_list.get(0, "end")))
        self.w.continue_ai()
        self.assertEqual(self.w.page, "ai")
        self.assertEqual(self.w.config.load()["provider"]["model"], "qwen3:4b-instruct")

    def test_provider_test_consent_can_be_declined(self):
        self.w.dialogs.askyesno = lambda *a, **k: False
        with patch.object(ui, "test_provider") as test:
            self.w.test_ai()
            test.assert_not_called()

    def test_catalog_has_eight_profiles_no_network_or_custom(self):
        with patch.object(socket.socket, "connect", side_effect=AssertionError("network")), patch.object(ui, "discover_mcp") as discover:
            self.w.show("catalog")
            discover.assert_not_called()
        self.assertEqual(len(self.w.catalog_cards), 8)
        self.assertTrue(all(not p.enabled for p in PROFILES))
        self.assertTrue(all(p.maturity != "SUPPORTED" for p in PROFILES if p.id != "rea"))
        self.assertFalse(any("Custom" in str(c.cget("text")) for c in children(self.w.body) if isinstance(c, tk.Button)))

    def test_experimental_profiles_do_not_expose_guessed_connection(self):
        for ident in ("ros2", "emqx", "arduino"):
            self.choose(ident)
            self.assertIsNone(self.w.profile.transport)
            self.assertFalse(any(isinstance(c, tk.Entry) for c in children(self.w.body)))
        self.assertFalse(self.w.config.path.exists())

    def test_online_fields_help_and_fixed_vendor_prefill(self):
        self.choose()
        self.assertEqual(self.w.target.get(), "https://mcp.developer.xcelerator.rocks/mcp")
        self.assertEqual(self.w.profile.transport, "http")
        self.assertEqual(self.w.token_entry.cget("show"), "*")
        self.assertFalse(any(isinstance(c, tk.Button) and c.cget("text") == "Choose application…" for c in children(self.w.body)))
        for key in ("wizard.profile.siemens.help", "wizard.token.help", "wizard.address.hint"):
            self.assertNotEqual(self.w.text(key), "Message unavailable.")
        self.w.target.set("https://other.example/mcp")
        self.assertFalse(self.w.validate_fields())

    def test_local_fields_and_advanced_hidden_browse(self):
        self.choose("opcua")
        self.assertEqual(self.w.profile.transport, "stdio")
        self.assertEqual(self.w.advanced.winfo_manager(), "")
        self.assertFalse(any(isinstance(c, tk.Entry) and c.cget("show") == "*" for c in children(self.w.body)))
        program = self.directory / "opcua-mcp.exe"; program.write_bytes(b"fixture-not-executed")
        with patch.object(ui.filedialog, "askopenfilename", return_value=str(program)):
            self.w.browse()
        self.assertEqual(self.w.target.get(), str(program))
        self.w.toggle_advanced(); self.w.add_argument()
        self.w.args[0].set("--profile")
        self.w.add_argument(); self.w.args[1].set("core")
        self.assertEqual(self.w.current_draft()["args"], ["--profile", "core"])
        self.assertNotIn("JSON", " ".join(c.cget("text") for c in children(self.w.body) if isinstance(c, tk.Label)))

    def test_address_validation_no_connection(self):
        self.choose("homeassistant")
        for address in ("http://host.example/mcp", "https://user:secret@example.com/mcp", "https://x/mcp?key=x", "https://x/mcp#x", "https://x:bad/mcp", "website"):
            self.w.target.set(address)
            self.assertFalse(self.w.validate_fields(), address)
        self.w.target.set(" https://home.example/api/mcp ")
        self.assertTrue(self.w.validate_fields())
        self.assertEqual(self.w.current_draft()["endpoint"], "https://home.example/api/mcp")
        self.assertFalse(self.w.config.path.exists())

    def test_connection_approval_then_no_auto_tool_or_enable(self):
        self.choose()
        with patch.object(ui, "discover_mcp") as discover:
            self.w.review_connection(); discover.assert_not_called()
        self.assertFalse(self.w.config.path.exists())
        self.connect()
        saved = self.w.config.server(self.w.identifier)
        self.assertTrue(saved["approved"])
        self.assertFalse(saved["enabled"])
        self.assertEqual(saved["tools"], {})
        self.assertFalse(any(v.get() for v in self.w.tool_vars.values()))

    def test_tool_consent_and_finish_enable_are_explicit(self):
        tool = self.connect()
        self.w.config.select(selection("ollama", "qwen3:4b-instruct"))
        self.w.tool_vars[tool["name"]].set(True)
        self.w.dialogs.askyesno = lambda *a, **k: False
        self.w.approve_tools()
        self.assertEqual(self.w.config.server(self.w.identifier)["tools"], {})
        self.w.dialogs.askyesno = lambda *a, **k: True
        self.w.approve_tools()
        self.assertEqual(self.w.config.server(self.w.identifier)["tools"], {tool["name"]: fingerprint(tool)})
        self.assertFalse(self.w.config.server(self.w.identifier)["enabled"])
        self.assertFalse(self.w.enable_at_finish.get())
        self.w.enable_at_finish.set(True)
        self.w.finish()
        self.assertTrue(self.w.config.server(self.w.identifier)["enabled"])

    def test_unknown_tools_need_separate_approval_even_with_readonly_hint(self):
        tool = {"name": "move_robot", "description": "test", "input_schema": {"type": "object"}, "output_schema": None, "annotations": {"readOnlyHint": True}}
        self.connect([tool])
        self.assertTrue(needs_extra_consent(self.w.profile, tool))
        self.w.tool_vars[tool["name"]].set(True)
        self.w.approve_tools()
        self.assertEqual(self.w.config.server(self.w.identifier)["tools"], {})
        self.w.allow_changes.set(True)
        self.w.dialogs.askyesno = lambda *a, **k: False
        self.w.change_permission()
        self.assertFalse(self.w.allow_changes.get())
        self.assertFalse(self.w.tool_vars[tool["name"]].get())

    def test_target_edit_revokes_authority_and_session(self):
        tool = self.connect()
        self.w.tool_vars[tool["name"]].set(True); self.w.approve_tools()
        self.w.secrets[self.w.identifier] = {"target": connection_key(self.w.tested), "token": "synthetic-only"}
        self.w.show("configure")
        self.w.target_edited()
        s = self.w.config.load()["servers"][0]
        self.assertFalse(s["approved"]); self.assertFalse(s["enabled"]); self.assertEqual(s["tools"], {})
        self.assertNotIn(s["id"], self.w.secrets)

    def test_token_memory_only_and_target_binding(self):
        self.choose("homeassistant")
        self.w.target.set("https://home.example/api/mcp")
        self.w.token.set("SYNTHETIC_TEST_TOKEN")
        self.w.review_connection()
        with patch.object(ui, "discover_mcp", return_value={"tools": []}):
            self.w.approve_and_test()
            end = time.monotonic() + 3
            while self.w.busy and time.monotonic() < end:
                self.root.update(); time.sleep(.01)
        self.assertNotIn("SYNTHETIC_TEST_TOKEN", self.w.config.path.read_text())
        s = self.w.config.server(self.w.identifier)
        self.assertEqual(Host(self.directory, self.w.secrets).credential(s), "SYNTHETIC_TEST_TOKEN")
        changed = dict(s, endpoint="https://different.example/mcp")
        with self.assertRaises(PermissionError):
            Host(self.directory, self.w.secrets).credential(changed)
        self.assertNotIn("SYNTHETIC_TEST_TOKEN", " ".join(str(c.cget("text")) for c in children(self.w.body) if isinstance(c, tk.Label)))

    def test_stale_async_discovery_cannot_approve_tools(self):
        self.choose()
        def run(work, done, error_key):
            self.w.config.update(self.w.identifier, approved=False)
            with self.assertRaises(PermissionError): done({"tools": []})
        self.w.run = run
        self.w.approve_and_test()
        self.assertIsNone(self.w.tested)
        self.assertFalse(self.w.config.load()["servers"][0]["approved"])

    def test_failed_test_edit_still_revokes_and_no_secret_error_output(self):
        self.choose()
        self.w.token.set("SYNTHETIC_TEST_TOKEN")
        self.w.review_connection()
        with patch.object(ui, "discover_mcp", side_effect=RuntimeError("SYNTHETIC_TEST_TOKEN")):
            self.w.approve_and_test()
            end = time.monotonic() + 3
            while self.w.busy and time.monotonic() < end:
                self.root.update(); time.sleep(.01)
        self.assertFalse(self.w.busy)
        self.assertNotIn("SYNTHETIC_TEST_TOKEN", self.w.status.get())
        self.assertEqual(self.w.error_kind, "RuntimeError")
        self.assertIsNone(self.w.tested)
        self.w.show("configure"); self.w.target_edited()
        self.assertFalse(self.w.config.load()["servers"][0]["approved"])
        self.assertFalse(self.w.secrets)

    def test_back_preserves_form_and_invalid_next_is_disabled(self):
        self.choose("homeassistant")
        self.assertEqual(self.w.next_button.cget("state"), "disabled")
        self.w.name.set("My service"); self.w.target.set("https://home.example/api/mcp")
        self.w.token.set("SYNTHETIC_TEST_TOKEN")
        self.w.review_connection(); self.w.show("configure")
        self.assertEqual(self.w.name.get(), "My service")
        self.assertEqual(self.w.target.get(), "https://home.example/api/mcp")
        self.assertEqual(self.w.token.get(), "SYNTHETIC_TEST_TOKEN")
        self.w.target.set("http://unsafe.example/mcp"); self.w.target_edited()
        self.assertEqual(self.w.next_button.cget("state"), "disabled")
        self.assertEqual(self.w.token.get(), "")
    def test_existing_config_unchanged_by_open_and_skip(self):
        c = self.w.config
        c.put(checked_connection("existing", "Existing", "http", "https://example.test/mcp"))
        c.update("existing", approved=True, enabled=True)
        original = c.path.read_bytes()
        self.w.show("catalog"); self.w.show("optional"); self.w.skip()
        self.assertEqual(original, c.path.read_bytes())

    def test_advanced_management_loads_existing_backend_config(self):
        manager = ui.ConnectionManager(self.w.window, self.w.locale, self.directory, self.w.secrets)
        self.assertTrue(any(isinstance(c, ui.ttk.Notebook) for c in children(manager.window)))
        self.assertEqual(manager.config.load(), self.w.config.load())
        manager.window.destroy()

    def test_en_da_complete_all_pages_and_fallback_other_locales(self):
        en = LocaleContext("en"); da = LocaleContext("da")
        keys = {k for k in en.english if k.startswith("wizard.")}
        self.assertGreater(len(keys), 100)
        for k in keys:
            self.assertIn(k, da.messages)
            self.assertEqual(fields(en.english[k]), fields(da.messages[k]))
        for lang in ("en", "da"):
            self.w.locale.set(lang)
            for page in ("ai", "optional", "catalog"):
                self.w.show(page)
            for profile in PROFILES:
                self.w.choose_profile(profile)
            self.choose(); self.w.review_connection()
            self.connect(); self.w.approve_tools()
            self.assertFalse(self.w.locale.findings)
        for lang in LOCALES:
            context = LocaleContext(lang)
            self.assertNotEqual(context.text("wizard.heading.ai"), "Message unavailable.")


class DiscoveryTests(unittest.TestCase):
    def test_existing_discovery_contract_and_no_mutation(self):
        class Response:
            status = 200
            def read(self, limit): return b'{"models":[{"name":"qwen3:4b-instruct"}]}'
        class Connection:
            def __init__(self, *a, **k): self.calls=[]
            def request(self, method, path): self.calls.append((method, path))
            def getresponse(self): return Response()
            def close(self): pass
        with patch("chroma.native_ai.runtime", return_value=(Path("unused"), Path("unused"))), patch.object(onboarding.http.client, "HTTPConnection", Connection):
            result = onboarding.discover()
        self.assertEqual([p["provider"] for p in result], ["bundled-cpu", "ollama"])
        self.assertEqual(result[1]["model"], "qwen3:4b-instruct")

    def test_discovery_bounded_and_never_runs_program(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / ("opcua-mcp.exe" if os.name == "nt" else "opcua-mcp")
            path.write_bytes(b"not-executed"); path.chmod(0o700)
            with patch.object(os, "get_exec_path", return_value=[temp]), patch("subprocess.Popen", side_effect=AssertionError("must not execute")), patch.object(socket.socket, "connect", side_effect=AssertionError("must not connect")):
                found = candidates(PROFILES[0], [])
            self.assertEqual(found, [{"command": str(path.resolve()), "args": [], "name": "opcua-mcp"}])
        with patch.object(os, "get_exec_path", return_value=["", ".", str(Path.cwd())]):
            self.assertIsNone(installed_program("opcua-mcp"))

    def test_network_paths_excluded_without_file_probe(self):
        with patch.object(Path, "is_file", side_effect=AssertionError("must not probe")):
            self.assertFalse(local_path("//server/share/opcua-mcp.exe"))
            server = {"transport": "stdio", "command": "//server/share/opcua-mcp.exe"}
            with patch.object(os, "get_exec_path", return_value=[]):
                self.assertEqual(candidates(PROFILES[0], [server]), [])

    def test_profile_routes_and_limits(self):
        routes = {p.id: p.transport for p in PROFILES}
        self.assertEqual(routes, dict(opcua="stdio", ros2=None, isaac="http", emqx=None, homeassistant="http", siemens="http", arduino=None, rea="stdio"))
        for p in PROFILES:
            self.assertEqual(p.concurrent_calls, 1)
            self.assertEqual(p.task_calls, 4)
            self.assertLessEqual(p.discovery_seconds, 20)


if __name__ == "__main__":
    unittest.main(verbosity=2)