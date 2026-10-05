"""Offline native package check; never calls the production backend."""
from pathlib import Path
import hashlib,json,os,platform,subprocess,sys,tempfile,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'packaging'))
from build import validate,VERSION
def run(args,**kw):return subprocess.run([str(a) for a in args],check=True,timeout=180,**kw)
def main():
 if platform.system() not in ('Windows','Linux'):raise SystemExit('RC4 supports Windows x64 and Linux amd64 only')
 installer_only=sys.argv[1:]==["--installer-only"]
 assert installer_only or not sys.argv[1:],"Unknown smoke arguments"
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');env.pop('NODE_PATH',None);env.pop('NODE_OPTIONS',None)
 with tempfile.TemporaryDirectory(prefix='chroma-package-test-') as tmp:
  tmp=Path(tmp);env['CHROMA_STATE_DIR']=str(tmp/'state');kind=platform.system()
  sentinel=tmp/'state'/'owner-sentinel.txt';sentinel.parent.mkdir();sentinel.write_bytes(b'SYNTHETIC STATE MUST SURVIVE')
  if kind=='Windows':
   target=tmp/'Installed Client';env['CHROMANEURAL_INSTALL_DESTINATION']=str(target)
   extraction_root=Path(env.get('TEMP',tempfile.gettempdir())).resolve()
   before=set(extraction_root.glob('ChromaNeural-extract-*'))
   run([ROOT/'dist'/('ChromaNeural-'+VERSION+'-windows-x64.exe'),'/Q'],env=env)
   leftovers=set(extraction_root.glob('ChromaNeural-extract-*'))-before
   if not target.exists() or leftovers:
    log=Path(env.get('TEMP',tempfile.gettempdir()))/'ChromaNeural-install.log'
    if log.is_file():print(log.read_text(encoding='utf-8-sig',errors='replace'),flush=True)
    raise AssertionError('EXE installation or extraction cleanup failed; installer transcript printed above')
  elif kind=='Linux':
   run(['dpkg-deb','--extract',next((ROOT/'dist').glob('*.deb')),tmp/'deb']);target=tmp/'deb/opt/chromaneural'
  validate(target)
  assert sentinel.read_bytes()==b'SYNTHETIC STATE MUST SURVIVE','Existing state changed'
  if kind=='Windows':
   refusal=subprocess.run(['powershell.exe','-NoProfile','-File',str(ROOT/'build/payload/Install-ChromaNeural.ps1'),'-Destination',str(target)],capture_output=True,timeout=30)
   assert refusal.returncode!=0 and b'NEW destination' in refusal.stderr,'Existing installation overwrite was not refused'
  required=['LICENSE','NOTICE','THIRD_PARTY_LICENSES.md','docs/LICENSING.md','client/reference_core/LICENSE','client/reference_core/NOTICE','docs/licenses/icp-sdk-core-5.4.0-LICENSE']
  required+=['VERSION','client/locale-registry.json']
  required+=[p.relative_to(ROOT).as_posix() for p in ROOT.glob('README*.md')]
  required+=[p.relative_to(ROOT).as_posix() for p in (ROOT/'client/locales').glob('*.json')]
  required+=[p.relative_to(ROOT).as_posix() for p in (ROOT/'docs').rglob('*') if p.is_file()]
  assert all((target/p).is_file() for p in required),'Installed documentation/localization/license payload incomplete'
  assert all((target/p).read_bytes()==(ROOT/p).read_bytes() for p in required),'Installed documentation/localization/license bytes changed'
  assert all((target/'installer'/p.name).read_bytes()==p.read_bytes() for p in (ROOT/'packaging/installer').iterdir() if p.is_file()),'Installer localization payload changed'
  run([sys.executable,'-B',target/'client/launch.py','--help'],env=env)
  run([sys.executable,'-B',target/'scripts/network_client.py','--help'],env=env)
  code="const {createRequire}=require('node:module');const path=require('node:path');const r=createRequire(path.join(process.cwd(),'connection_probe.mjs'));const p=r.resolve('@icp-sdk/core/agent');if(!p.startsWith(path.join(process.cwd(),'node_modules')))throw Error('external dependency');r('@icp-sdk/core/agent');"
  run(['node','-e',code],cwd=target/'client/services',env=env)
  if installer_only:
   run([sys.executable,'-I','-B',ROOT/'packaging/installer_acceptance.py','installed',
        target/'client',ROOT/'dist/INSTALLED_MCP.json'],env=env)
  else:
   # Launch actual Tk with isolated state; never start participation or a network probe.
   code="import sys,tkinter as tk;sys.path.insert(0,sys.argv[1]);from chroma.dashboard import App;r=tk.Tk();a=App(r,state_dir=sys.argv[2]);r.update();assert not a.service.value['participation'];a.show_page('connection');r.update();assert str(a.connection_panel.probe_button['state'])=='disabled';a.quit()"
   run([sys.executable,'-B','-c',code,target/'client',tmp/'gui-state'],env=env)
   mcp_env=dict(env,CHROMA_MCP_CLIENT=str(target/'client'),CHROMA_FROZEN_SOURCE=str(ROOT/'NOT_A_FROZEN_TREE'))
   run([sys.executable,'-I','-B',ROOT/'packaging/test_mcp.py'],env=mcp_env)
  report={'status':'PASS','platform':kind,'architecture':platform.machine(),'scope':'native package extraction/install, manifest, CLI, bundled ICP resolution, actual offline Tk','licensePayload':'PASS','documentationLocalizationPayload':'PASS','existingStatePreserved':True,'existingDestinationRefused':kind=='Windows','manualGUI':'NOT VERIFIED','liveII':'NOT VERIFIED','remoteExecution':'DISABLED'}
  report['acceptanceMode']='installer-only' if installer_only else 'full'
  if installer_only:
   report['scope']='native installer extraction/install, exact payload, CLI, bundled dependencies; closed GUI/MCP behavior suites reused'
   report['guiStartup']='REUSED prior native acceptance; not rerun'
  (ROOT/'dist/PACKAGE_SMOKE.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
