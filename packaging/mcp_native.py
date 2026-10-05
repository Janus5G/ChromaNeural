"""Native MCP-only package staging acceptance. Does not rebuild pre-MCP assets."""
from pathlib import Path
import argparse,hashlib,json,os,platform,shutil,subprocess,sys
parser=argparse.ArgumentParser()
parser.add_argument("--delta",action="store_true")
parser.add_argument("--mac-deadline",action="store_true")
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build/mcp-acceptance"
OUT.mkdir(parents=True,exist_ok=False)
payload=OUT/"payload"
client=payload/"client"
client.mkdir(parents=True)
shutil.copytree(ROOT/"client/chroma",client/"chroma",ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
shutil.copytree(ROOT/"client/locales",client/"locales")
shutil.copyfile(ROOT/"client/locale-registry.json",client/"locale-registry.json")
from mcp_package import stage
stage(ROOT,payload)
from build import manifest,validate
manifest(payload);validate(payload)
python="/usr/bin/python3" if platform.system()=="Linux" else sys.executable
temp=OUT/"tmp";temp.mkdir()
env=dict(os.environ,CHROMA_MCP_CLIENT=str(client),TEMP=str(temp),TMP=str(temp),
         PYTHONDONTWRITEBYTECODE="1")
tests=["Acceptance.test_01_standalone_and_settings","Acceptance.test_02_stdio_real_trust_lifecycle",
       "Acceptance.test_03_http_real","Acceptance.test_04_malformed_and_credential_boundary",
       "Acceptance.test_06_session_credentials_bind_exact_target",
       "Acceptance.test_07_controlled_provider_real_mcp_task_result_path",
       "Acceptance.test_08_queue_and_speech_minimal_regression","Acceptance.test_09_deadline_cleans_local_server"]
if args.delta:
 tests=["Acceptance.test_09_deadline_cleans_local_server","Acceptance.test_10_redirect_cannot_change_target"]
if args.mac_deadline:
 args.delta=True
 tests=["Acceptance.test_11_ready_server_deadline_cleans_local_server"]
with (OUT/"acceptance.log").open("wb") as log:
 result=subprocess.run([python,"-I","-B",str(ROOT/"packaging/test_mcp.py"),*tests],
                       env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
print((OUT/"acceptance.log").read_text(encoding="utf-8"),flush=True)
if result.returncode:raise SystemExit(result.returncode)
gui="import sys,tkinter as tk;sys.path.insert(0,sys.argv[1]);from chroma.dashboard import App;r=tk.Tk();a=App(r,state_dir=sys.argv[2]);r.update();assert not a.service.value['participation'];assert 'mcp' not in sys.modules;a.open_setup();r.update();assert a.setup_wizard.window.winfo_ismapped();assert 'mcp' not in sys.modules;a.setup_wizard.window.destroy();a.quit()"
# Windows GUI startup already passed; POSIX runs had stopped at deadline failure.
if not args.delta or platform.system()!="Windows":
 subprocess.run([python,"-I","-B","-c",gui,str(ROOT/"client"),str(OUT/"gui-state")],env=env,check=True,timeout=30)
validate(payload)
receipt={"status":"PASS","scope":"MCP-specific native staging/runtime, real stdio/HTTP tool calls, trust/credentials, controlled provider task fixture, minimal queue/speech/GUI regression",
         "tests":tests,"delta":args.delta,"macDeadlineOnly":args.mac_deadline,"platform":platform.platform(),"python":python,"sdk":"mcp==2.3.0","cryptography":"46.0.5",
         "payloadManifestSha256":hashlib.sha256((payload/"SHA256SUMS.txt").read_bytes()).hexdigest(),
         "sourceCommit":os.environ.get("GITHUB_SHA"),"realModelInference":"NOT VERIFIED",
         "fullReleaseInstallerRebuild":"NOT RUN; frozen native baseline reused; final candidate packages remain a later gate",
         "remoteExecution":"DISABLED"}
(OUT/"RESULT.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
shutil.copyfile(payload/"SHA256SUMS.txt",OUT/"MCP_PAYLOAD_SHA256SUMS.txt")
print(json.dumps(receipt,indent=2))
