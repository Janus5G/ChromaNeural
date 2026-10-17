"""Focused REA catalog/discovery/failure-isolation checks; no REA dependency.
Synthetic local npm layouts, real Tk/Config and simulated worker failures.
The actual upstream integration result is recorded separately, never inferred.
"""
import asyncio
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import tkinter as tk
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "client"))
sys.path.insert(0, str(ROOT / "packaging"))
from chroma import mcp_rea, onboarding_ui as ui
from chroma.mcp_catalog import PROFILES, candidates, checked_connection, needs_extra_consent
from chroma.mcp_config import Config, fingerprint
from chroma.mcp_client import Host
from chroma.i18n import LocaleContext, LOCALES, fields
import test_onboarding_wizard as existing

REA = next(p for p in PROFILES if p.id == "rea")


def installation(folder):
    package = folder / "node_modules/rea-agents"
    (package / "scripts").mkdir(parents=True)
    (package / "dist/mcp").mkdir(parents=True)
    (package / "scripts/rea.mjs").write_text("// fixture: never executed", encoding="utf-8")
    (package / "dist/mcp/main.js").write_text("// fixture", encoding="utf-8")
    (package / "package.json").write_text(json.dumps({"name": "rea-agents", "version": "6.5.0",
        "bin": {"rea": "scripts/rea.mjs", "rea-agents": "scripts/rea.mjs"}}), encoding="utf-8")
    node = folder / ("node.exe" if os.name == "nt" else "node")
    node.write_text("fixture: never executed", encoding="utf-8"); node.chmod(0o700)
    for name in mcp_rea.NAMES:
        (folder / (name + (".cmd" if os.name == "nt" else ""))).write_text("fixture", encoding="utf-8")
    return node, package / "scripts/rea.mjs"


class Discovery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chroma-rea-test-")
        self.folder = Path(self.tmp.name)
        self.node, self.script = installation(self.folder)
    def tearDown(self): self.tmp.cleanup()

    def test_official_entry_and_aliases_no_execution_or_network(self):
        with patch.object(mcp_rea, "installed_program", return_value=str(self.node)), \
             patch.object(os, "get_exec_path", return_value=[str(self.folder)]), \
             patch.object(subprocess, "Popen", side_effect=AssertionError("no execution")), \
             patch.object(socket.socket, "connect", side_effect=AssertionError("no network")):
            found = candidates(REA, [])
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["args"], [str(self.script), "mcp"])
        self.assertEqual(found[0]["version"], "6.5.0")
        self.assertTrue(mcp_rea.valid_launch(found[0]["command"], found[0]["args"]))

    def test_existing_config_precedes_path_and_never_preserves_trust(self):
        other = self.folder / "other"; other.mkdir()
        other_node, other_script = installation(other)
        saved = checked_connection("saved", "Existing REA", "stdio", str(other_node), [str(other_script), "mcp"])
        with patch.object(mcp_rea, "installed_program", return_value=str(self.node)), patch.object(os, "get_exec_path", return_value=[str(self.folder)]):
            found = candidates(REA, [dict(saved, approved=True, enabled=True)])
        self.assertEqual(len(found), 2)
        self.assertEqual(found[0]["name"], "Existing REA")
        self.assertFalse(any("approved" in item or "enabled" in item or "tools" in item for item in found))

    def test_missing_invalid_and_network_installations_fail_locally(self):
        with patch.object(os, "get_exec_path", return_value=[]):
            self.assertEqual(candidates(REA, []), [])
        with patch.object(Path, "is_file", side_effect=AssertionError("network probe")):
            self.assertIsNone(mcp_rea.package_entry("//server/share/rea.cmd"))
        package = self.script.parent.parent
        for bad in ('{"name":"unrelated"}', '{"name":', '[' * 2000):
            (package / "package.json").write_text(bad, encoding="utf-8")
            self.assertIsNone(mcp_rea.candidate(self.script, str(self.node)))

    def test_no_setup_download_shell_or_argument_injection(self):
        for args in ([str(self.script), "setup"], [str(self.script), "mcp", "extra"], [str(self.script), "--mcp"], ["mcp"]):
            self.assertFalse(mcp_rea.valid_launch(str(self.node), args))
        self.assertFalse(mcp_rea.valid_launch(str(self.folder / "npx"), [str(self.script), "mcp"]))

    def test_node_ranges_and_safe_version_probe(self):
        for v in ("22.19.0", "22.20.1", "24.11.0", "24.13.0", "26.0.0", "27.0.0"):
            self.assertTrue(mcp_rea.compatible_node(v), v)
        for v in ("22.18.9", "24.10.9", "23.0.0", "25.0.0", "26.0.0-rc.1", "garbage"):
            self.assertFalse(mcp_rea.compatible_node(v), v)
        with patch.dict(os.environ, {"NODE_OPTIONS": "unsafe", "SECRET_TOKEN": "do-not-inherit"}), \
             patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"v24.13.0\n")) as run:
            result = mcp_rea.runtime_status(str(self.node))
        self.assertTrue(result["compatible"])
        self.assertEqual(run.call_args.args[0], [str(self.node), "--version"])
        self.assertNotIn("NODE_OPTIONS", run.call_args.kwargs["env"])
        self.assertNotIn("SECRET_TOKEN", run.call_args.kwargs["env"])
        with patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired("node", 2)):
            self.assertFalse(mcp_rea.runtime_status(str(self.node))["compatible"])

    @unittest.skipIf(os.name == "nt", "npm POSIX symlink layout")
    def test_posix_npm_symlink_only_to_local_official_package(self):
        launcher = self.folder / "rea"; launcher.unlink(); launcher.symlink_to(self.script)
        self.assertEqual(mcp_rea.package_entry(launcher)[0], str(self.script))
        launcher.unlink(); launcher.symlink_to("//server/share/rea.mjs")
        self.assertIsNone(mcp_rea.package_entry(launcher))

    def test_permissions_are_opt_in_and_backend_revocation_unchanged(self):
        self.assertFalse(REA.enabled)
        self.assertEqual(REA.maturity, "SUPPORTED")
        static = {"name": "analyze_javascript_application"}
        self.assertFalse(needs_extra_consent(REA, static))
        for name in ("execute", "capture_process_scenario", "write_file", "unknown"):
            self.assertTrue(needs_extra_consent(REA, {"name": name, "annotations": {"readOnlyHint": True}}))
        config = Config(self.folder / "state")
        config.put(checked_connection("rea", "REA", "stdio", str(self.node), [str(self.script), "mcp"]))
        host = Host(config.directory)
        with self.assertRaises(PermissionError): host.check("rea")
        config.update("rea", approved=True, enabled=True)
        snapshot = config.server("rea")
        with self.assertRaises(PermissionError):
            asyncio.run(host.call(("rea", snapshot, static), {}))
        config.update("rea", tools={static["name"]: fingerprint(static)})
        config.put(dict(snapshot, args=[str(self.script), "mcp"]))
        revoked=config.load()["servers"][0]
        self.assertFalse(revoked["approved"] or revoked["enabled"] or revoked["tools"])

    def test_en_da_complete_and_other_locales_fallback(self):
        en, da = LocaleContext("en"), LocaleContext("da")
        keys = [k for k in en.english if k.startswith(("wizard.rea.", "wizard.profile.rea."))]
        self.assertGreaterEqual(len(keys), 15)
        for k in keys:
            self.assertIn(k, da.messages)
            self.assertEqual(fields(en.english[k]), fields(da.messages[k]))
        for lang in LOCALES:
            context=LocaleContext(lang)
            self.assertNotEqual(context.text("wizard.profile.rea.name"), "Message unavailable.")


class UI(unittest.TestCase):
    setUpClass = classmethod(lambda cls: existing.WizardTests.setUpClass.__func__(cls))
    tearDownClass = classmethod(lambda cls: existing.WizardTests.tearDownClass.__func__(cls))
    setUp = existing.WizardTests.setUp
    tearDown = existing.WizardTests.tearDown

    def configured(self):
        node, script = installation(self.directory / "installed")
        item = mcp_rea.candidate(script, str(node))
        with patch.object(ui, "candidates", return_value=[item]), patch.object(mcp_rea, "runtime_status", return_value={"compatible": True, "node": "v24.13.0", "npm": "11.0.0"}):
            self.w.choose_profile(REA)
        return item

    def test_absent_rea_does_not_block_builtin_ai_skip_or_shutdown(self):
        with patch.object(os, "get_exec_path", return_value=[]), patch.object(subprocess, "Popen", side_effect=AssertionError("no REA process")):
            self.w.show("catalog"); self.w.choose_profile(REA)
        labels=[str(c.cget("text")) for c in existing.children(self.w.body) if isinstance(c, tk.Label)]
        self.assertIn(self.w.text("wizard.rea.absent"), labels)
        self.assertFalse(any(isinstance(c, tk.Entry) for c in existing.children(self.w.body)))
        self.assertFalse(self.w.config.path.exists())
        self.w.show("ai"); self.w.found_providers(self.providers)
        self.assertEqual(len(self.w.providers), 2)
        self.w.config.select(None); self.w.show("optional"); self.w.skip(); self.w.finish()
        self.assertTrue(self.w.closed)

    def test_detected_card_browse_and_hidden_args_in_both_languages(self):
        item = self.configured()
        with patch.object(ui, "candidates", return_value=[item]), patch.object(subprocess, "Popen", side_effect=AssertionError("catalog must not launch")):
            self.w.show("catalog")
        for lang in ("en", "da"):
            self.w.locale.set(lang)
            self.w.show("configure")
            from chroma.rea_isolation import available
            self.assertEqual(self.w.validate_fields(), available())
            self.assertEqual([a.get() for a in self.w.args], item["args"])
            self.assertEqual(self.w.advanced.winfo_manager(), "")
            self.assertFalse(self.w.locale.findings)
        with patch.object(ui.filedialog, "askopenfilename", return_value=item["args"][0]), \
             patch.object(mcp_rea, "installed_program", return_value=item["command"]), \
             patch.object(mcp_rea, "runtime_status", return_value={"compatible": True, "node": "v24.13.0", "npm": "11.0.0"}):
            self.w.browse()
        self.assertEqual([a.get() for a in self.w.args], item["args"])

    def test_worker_failures_are_bounded_and_do_not_change_other_connections(self):
        other=checked_connection("other", "Other integration", "http", "https://example.invalid/mcp")
        self.w.config.put(other);self.w.config.update("other",approved=True,enabled=True)
        before=self.w.config.server("other")
        self.configured()
        for failure in (FileNotFoundError(), PermissionError(), ConnectionError(), RuntimeError(), TimeoutError(), MemoryError(), ValueError("size limit")):
            with patch.object(ui, "discover_mcp", side_effect=failure) as call:
                self.w.run(lambda: ui.discover_mcp(self.w.config.directory, "rea-fixture"),
                           lambda result: self.fail("failed worker must not succeed"), "wizard.rea.test_failed")
                deadline=time.monotonic()+3
                while self.w.busy and time.monotonic()<deadline:
                    self.root.update(); time.sleep(.01)
            self.assertFalse(self.w.busy)
            self.assertEqual(call.call_count, 1)
            self.assertEqual(self.w.config.server("other"), before)
            self.assertEqual(self.w.config.load()["servers"], [before])
            self.assertIsNone(self.w.tested)
            self.assertLess(len(self.w.status.get()), 500)
            self.w.show("ai");self.w.found_providers(self.providers)
            self.assertEqual(len(self.w.providers),2)
            self.w.show("configure")
        self.w.show("catalog")
        self.w.choose_profile(next(p for p in PROFILES if p.id=="siemens"))
        self.assertTrue(self.w.validate_fields())

    def test_resource_gate_blocks_before_any_execution_or_trust_change(self):
        self.configured()
        before = self.w.config.load()
        with patch("chroma.rea_isolation.available", return_value=False), patch.object(ui, "discover_mcp", side_effect=AssertionError("must not launch")):
            self.w.approve_and_test()
            self.w.review_connection()
        self.assertEqual(before, self.w.config.load())
        with patch("chroma.rea_isolation.available", return_value=False):
            self.assertFalse(self.w.validate_fields())
        self.assertEqual(self.w.next_button.cget("state"), "disabled")
        self.assertEqual(self.w.page, "configure")
        self.assertFalse(REA.connection_blocker)
        self.assertTrue(all(not p.connection_blocker for p in PROFILES if p.id != "rea"))


if __name__ == "__main__":
    unittest.main(verbosity=2)