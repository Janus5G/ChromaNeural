"""Targeted real-protocol MCP acceptance; no model or application network service needed."""
import asyncio, copy, hashlib, json, os, socket, subprocess, sys, tempfile, time, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,os.environ.get("CHROMA_MCP_CLIENT",str(ROOT/"client")))
from chroma.mcp_config import Config, DEFAULT, fingerprint, validate
from chroma.mcp_client import Host, sdk_path
sdk_path()
from chroma.ai_provider import selected_inference, selection
from chroma.onboarding import discover_mcp
from chroma.i18n import LOCALES, LocaleContext, fields

class Acceptance(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="mcp-acceptance-")
        self.root=Path(self.temp.name)
        self.config=Config(self.root)
        self.data=self.root/"data.json";self.data.write_text('{"answer":"EXTERNAL_RECORD_7391"}',encoding="utf-8")
        self.calls=self.root/"calls.log"
        self.server={"id":"test","name":"Test service","transport":"stdio","endpoint":"",
                     "command":sys.executable,"args":["-B","-c","import sys,runpy;sys.path.insert(0,sys.argv.pop(2));from chroma.mcp_client import sdk_path;sdk_path();sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')",str(ROOT/"packaging/mcp_test_server.py"),os.environ.get("CHROMA_MCP_CLIENT",str(ROOT/"client")),str(self.data),str(self.calls)]}
        self.process=None
    def tearDown(self):
        if self.process:
            self.process.terminate()
            try:self.process.wait(5)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
        self.temp.cleanup()
    def put(self):
        self.config.put(self.server)
    def approve(self):
        self.config.update("test",approved=True)
        discovery=discover_mcp(self.root,"test")
        tool=next(t for t in discovery["tools"] if t["name"]=="fetch_record")
        self.config.update("test",tools={"fetch_record":fingerprint(tool)},enabled=True)
        return discovery

    def test_01_standalone_and_settings(self):
        self.assertEqual(self.config.load(),DEFAULT)
        self.assertFalse(self.config.path.exists())
        calls=[]
        result=selected_inference("x","keep",None,bundled=lambda *a,**kw:calls.append((a,kw)) or "standalone")
        self.assertEqual(result,"standalone")
        self.assertEqual(calls,[(("x","keep"),{"timeout":90})])
        from chroma.settings import Settings, validate as old_validate
        settings=Settings(self.root)
        settings.save(settings.value);old=settings.path.read_bytes()
        self.config.select(selection("ollama","example:model"))
        self.assertEqual(settings.path.read_bytes(),old)
        old_validate(json.loads(old))
        self.assertEqual(Config(self.root).load()["provider"],selection("ollama","example:model"))

    def test_02_stdio_real_trust_lifecycle(self):
        self.put()
        host=Host(self.root)
        with self.assertRaises(PermissionError):asyncio.run(host.discover("test"))
        self.assertFalse(self.calls.exists())
        discovery=self.approve()
        self.assertIn(discovery["protocol"],["2026-07-28","2025-11-25","2025-06-18","2025-03-26","2024-11-05"])
        self.assertEqual(len(discovery["tools"]),2)
        self.assertEqual(discovery["resources"][0]["uri"],"test://record")
        caps=asyncio.run(host.capabilities(["test"]))
        self.assertEqual(len(caps),1)
        entry=next(iter(caps.values()))
        result=asyncio.run(host.call(entry,{"key":"answer"}))
        self.assertEqual(result,{"is_error":False,"text":"EXTERNAL_RECORD_7391"})
        self.assertEqual(asyncio.run(host.call(entry,{"key":"answer"})),result) # reconnect
        with self.assertRaises(Exception):asyncio.run(host.call(entry,{"key":4}))
        self.config.update("test",enabled=False)
        with self.assertRaises(PermissionError):asyncio.run(host.call(entry,{"key":"answer"}))
        self.config.update("test",enabled=True)
        self.config.update("test",approved=False)
        with self.assertRaises(PermissionError):asyncio.run(host.call(entry,{"key":"answer"}))
        self.approve()
        self.config.put(self.server)
        with self.assertRaises(PermissionError):asyncio.run(host.call(entry,{"key":"answer"}))
        self.approve()
        self.config.remove("test")
        with self.assertRaises(PermissionError):asyncio.run(host.call(entry,{"key":"answer"}))
        self.assertEqual(self.calls.read_text().splitlines(),["fetch_record","fetch_record"])

    def test_03_http_real(self):
        with socket.socket() as sock:sock.bind(("127.0.0.1",0));port=sock.getsockname()[1]
        self.process=subprocess.Popen([sys.executable,"-B",str(ROOT/"packaging/mcp_test_server.py"),
             str(self.data),str(self.calls),str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
             **({"creationflags":subprocess.CREATE_NO_WINDOW} if os.name=="nt" else {}))
        for _ in range(60):
            try:
                with socket.create_connection(("127.0.0.1",port),timeout=.1):break
            except OSError:time.sleep(.1)
        else:self.fail("Controlled HTTP server did not start")
        self.server.update(transport="http",endpoint=f"http://127.0.0.1:{port}/mcp",command="",args=[])
        self.put();self.approve()
        host=Host(self.root);entry=next(iter(asyncio.run(host.capabilities(["test"])).values()))
        self.assertEqual(asyncio.run(host.call(entry,{"key":"answer"}))["text"],"EXTERNAL_RECORD_7391")
        self.process.terminate();self.process.wait(5);self.process=None
        with self.assertRaises(Exception):asyncio.run(host.discover("test"))

    def test_04_malformed_and_credential_boundary(self):
        self.put()
        original=self.config.load()
        for change in [{"enabled":True},{"endpoint":"https://user:secret@example.test/mcp","transport":"http","command":"","args":[]},
                       {"endpoint":"http://example.test/mcp","transport":"http","command":"","args":[]},
                       {"endpoint":"https://example.test/mcp?token=secret","transport":"http","command":"","args":[]},
                       {"tools":{"bad":"fake"}},{"transport":"shell"},{"approved":1}]:
            value=copy.deepcopy(original);value["servers"][0].update(change)
            with self.assertRaises((ValueError,TypeError)):validate(value)
        self.config.path.write_text('{"version":1,"version":1,"provider":null,"servers":[]}')
        with self.assertRaises(ValueError):self.config.load()
        self.assertIn('"version":1,"version":1',self.config.path.read_text())

    def test_05_new_i18n_and_old_messages(self):
        old=Path(os.environ.get("CHROMA_FROZEN_SOURCE",str(ROOT.parent/"ChromaNeural-0.2.21-rc.2")))
        canonical=LocaleContext("en")
        new={k for k in canonical.english if k.startswith("tools_setup.")}
        self.assertEqual(len(new),49)
        for locale in LOCALES:
            ctx=LocaleContext(locale)
            self.assertTrue(new<=set(ctx.messages))
            for key in new:self.assertEqual(fields(ctx.messages[key]),fields(canonical.english[key]))
            raw=(ROOT/"client/locales"/(locale+".json")).read_bytes()
            self.assertEqual(json.loads(raw),json.loads(raw.decode("utf-8").encode("utf-8")))
            if old.is_dir():
                before=json.loads((old/"client/locales"/(locale+".json")).read_bytes())
                self.assertTrue(all(ctx.messages[k]==v for k,v in before.items()))
        ctx=LocaleContext(LOCALES[-1]);ctx.messages=dict(ctx.messages)
        del ctx.messages["tools_setup.title"]
        self.assertEqual(ctx.text("tools_setup.title"),canonical.text("tools_setup.title"))


    def test_06_session_credentials_bind_exact_target(self):
        from chroma.mcp_config import connection_key
        self.server.update(transport="http",endpoint="https://first.invalid/mcp",command="",args=[])
        self.put();self.config.update("test",approved=True)
        original=self.config.server("test")
        token={"target":connection_key(original),"token":"SYNTHETIC-NOT-A-CREDENTIAL"}
        host=Host(self.root,{"test":token})
        self.assertEqual(host.credential(original),"SYNTHETIC-NOT-A-CREDENTIAL")
        for field,value in [("endpoint","https://second.invalid/mcp"),("id","other"),("endpoint","https://first.invalid/other")]:
            changed=dict(original);changed[field]=value
            if field=="id":
                other=Host(self.root,{"other":token})
                with self.assertRaises(PermissionError):other.credential(changed)
            else:
                with self.assertRaises(PermissionError):host.credential(changed)
        self.assertNotIn("SYNTHETIC",self.config.path.read_text())
        invalid=self.config.load()
        invalid["servers"][0]["authorization_server"]="https://other.invalid"
        with self.assertRaises(ValueError):validate(invalid) # OAuth identities are unsupported, never silently ignored.

    def test_07_controlled_provider_real_mcp_task_result_path(self):
        # A deterministic provider contract fixture, explicitly NOT real-model acceptance.
        import threading
        from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
        received=[]
        class Provider(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                request=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                received.append((self.path,request))
                if self.path=="/api/generate":
                    value={"response":"print(1)\n"}
                elif self.path=="/api/chat":
                    messages=request["messages"]
                    if messages[-1]["role"]=="tool":
                        assert "EXTERNAL_RECORD_7391" in messages[-1]["content"]
                        value={"message":{"role":"assistant","content":"print('EXTERNAL_RECORD_7391')\n"}}
                    else:
                        name=request["tools"][0]["function"]["name"]
                        value={"message":{"role":"assistant","content":"","tool_calls":[{"function":{"name":name,"arguments":{"key":"answer"}}}]}}
                else:raise AssertionError(self.path)
                raw=json.dumps(value).encode()
                self.send_response(200);self.send_header("Content-Type","application/json")
                self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw)
        # Do not intercept or replace any existing provider. Binding fails if the port is occupied.
        server=ThreadingHTTPServer(("127.0.0.1",11434),Provider)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            self.put();self.approve()
            choice=selection("ollama","acceptance-fixture")
            no_mcp=selected_inference("print(1)","keep",choice,bundled=lambda *a:None,timeout=20)
            self.assertEqual(no_mcp.source,b"print(1)\n")
            self.assertFalse(self.calls.exists())
            result=selected_inference("print(1)","Use the test record answer.",choice,
                 bundled=lambda *a:None,timeout=30,mcp_servers=["test"],mcp_directory=self.root)
            self.assertEqual(result.source,b"print('EXTERNAL_RECORD_7391')\n")
            self.assertEqual([x[0] for x in received],["/api/generate","/api/chat","/api/chat"])
            self.assertEqual(self.calls.read_text().splitlines(),["fetch_record"])
        finally:
            server.shutdown();server.server_close();thread.join(5)

    def test_08_queue_and_speech_minimal_regression(self):
        from unittest.mock import patch
        from chroma.work_queue import WorkQueue
        from chroma.native_ai import Inference
        from chroma.speech import metadata,pack,unpack
        import uuid
        body="inert peer data".encode()
        meta=metadata(str(uuid.uuid4()),"data",body)
        self.assertEqual(unpack(pack(meta,body)),(meta,body))
        class State:
            def can_run(self,kind):return True
        queue=WorkQueue(self.root/"work.sqlite")
        try:
            jid=queue.enqueue("test","key","print(1)","keep",network_approved=True,ai_approved=True)
            self.assertEqual(queue.read(jid)["status"],"WAITING")
            with patch("chroma.work_queue.Collaboration") as collab,patch("chroma.work_queue.infer",return_value=Inference(b"print(1)",0,"fixture","")):
                collab.return_value.prepare.return_value={"status":"LOCAL_WORK"}
                result=queue.step(None,State())
            self.assertEqual(result["id"],jid)
            self.assertEqual(result["status"],"AWAITING_REVIEW")
            self.assertEqual(result["result"]["proposal"],"print(1)")
            self.assertFalse(result["result"]["applied"])
        finally:queue.close()


    def test_09_deadline_cleans_local_server(self):
        from chroma.onboarding import worker
        marker=self.root/"server-pid.txt"
        code="import os,time;from pathlib import Path;Path("+repr(str(marker))+").write_text(str(os.getpid()));time.sleep(30)"
        self.server["args"]=["-B","-c",code]
        self.put();self.config.update("test",approved=True)
        started=time.monotonic()
        with self.assertRaises(TimeoutError):
            worker({"operation":"discover","directory":str(self.root),"identifier":"test","secrets":{}},timeout=3)
        self.assertLess(time.monotonic()-started,8)
        self.assertTrue(marker.exists(),"Server must have started to exercise process cleanup")
        pid=int(marker.read_text())
        if os.name=="nt":
            import ctypes
            k=ctypes.WinDLL("kernel32",use_last_error=True)
            k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];k.OpenProcess.restype=ctypes.c_void_p
            k.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)]
            k.CloseHandle.argtypes=[ctypes.c_void_p]
            handle=k.OpenProcess(0x1000,False,pid)
            if handle:
                code=ctypes.c_ulong()
                try:
                    self.assertTrue(k.GetExitCodeProcess(handle,ctypes.byref(code)))
                    self.assertNotEqual(code.value,259,"MCP child survived deadline")
                finally:k.CloseHandle(handle)
        else:
            # A short-lived zombie is no longer executing; the OS reaps it.
            try:os.kill(pid,0)
            except ProcessLookupError:pass
            else:
                status=subprocess.check_output(["ps","-o","stat=","-p",str(pid)],text=True).strip()
                self.assertTrue(not status or status.startswith("Z"),"MCP child survived deadline")


    def test_10_redirect_cannot_change_target(self):
        import threading
        from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
        paths=[]
        class Redirect(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                paths.append(self.path)
                self.rfile.read(int(self.headers.get("Content-Length","0")))
                self.send_response(307);self.send_header("Location","/different-server")
                self.send_header("Content-Length","0");self.end_headers()
            do_GET=do_POST
        server=ThreadingHTTPServer(("127.0.0.1",0),Redirect)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            self.server.update(transport="http",endpoint=f"http://127.0.0.1:{server.server_port}/mcp",command="",args=[])
            self.put();self.config.update("test",approved=True)
            with self.assertRaises(Exception):asyncio.run(Host(self.root).discover("test"))
            self.assertTrue(paths)
            self.assertTrue(all(p=="/mcp" for p in paths),"A redirect reached another target")
        finally:
            server.shutdown();server.server_close();thread.join(5)


    def test_11_ready_server_deadline_cleans_local_server(self):
        """Exercise the real worker timeout after a real server startup marker.

        Startup is separately bounded at 15 seconds; the operation timeout
        stays 3 seconds and cleanup must return within 8 seconds of readiness.
        Only the diagnostic pipe writer delays starting communicate's timer.
        No SDK, MCP server, cancellation, or process signal is simulated.
        """
        from chroma import onboarding
        from unittest.mock import patch
        marker=self.root/"ready-server-pid.txt"
        code="import os,time;from pathlib import Path;Path("+repr(str(marker))+").write_text(str(os.getpid()));time.sleep(30)"
        self.server["args"]=["-B","-c",code]
        self.put();self.config.update("test",approved=True)
        ready=[]
        class ReadyProcess(subprocess.Popen):
            def communicate(child,input=None,timeout=None):
                if input is not None and not ready:
                    child.stdin.write(input);child.stdin.close();child.stdin=None
                    deadline=time.monotonic()+15
                    while not marker.exists():
                        if child.poll() is not None or time.monotonic()>=deadline:
                            raise AssertionError("Real MCP server startup did not complete")
                        time.sleep(0.01)
                    ready.append(time.monotonic())
                    input=None
                return super().communicate(input,timeout)
        started=time.monotonic()
        with patch.object(onboarding.subprocess,"Popen",ReadyProcess):
            with self.assertRaises(TimeoutError):
                onboarding.worker({"operation":"discover","directory":str(self.root),"identifier":"test","secrets":{}},timeout=3)
        elapsed=time.monotonic()-ready[0]
        self.assertGreaterEqual(elapsed,3)
        self.assertLess(elapsed,8)
        self.assertLess(ready[0]-started,15)
        pid=int(marker.read_text())
        try:os.kill(pid,0)
        except ProcessLookupError:pass
        else:
            result=subprocess.run(["ps","-o","stat=","-p",str(pid)],capture_output=True,text=True)
            status=result.stdout.strip()
            self.assertTrue(not status or status.startswith("Z"),"MCP child survived deadline")
        print(json.dumps({"startupSeconds":ready[0]-started,"deadlineAndCleanupSeconds":elapsed,"childStopped":True}))

if __name__=="__main__":
    unittest.main(verbosity=2)
