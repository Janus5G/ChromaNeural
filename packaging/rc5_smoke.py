"""Install the actual Inno executable; isolate state; never contact a backend."""
from pathlib import Path
import argparse,hashlib,json,os,platform,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'packaging'))
from build import validate,VERSION

def run(args,**kw):return subprocess.run([str(x) for x in args],check=True,timeout=kw.pop('timeout',240),**kw)
def gui(client,state):
 sys.path.insert(0,str(client))
 def deny(event,args):
  if event in ('socket.connect','socket.getaddrinfo'):raise RuntimeError('Offline installer acceptance forbids network')
 sys.addaudithook(deny)
 import tkinter as tk
 from chroma.dashboard import App
 from chroma.i18n import packaged_version
 root=tk.Tk();app=App(root,state_dir=state)
 try:
  root.update();assert packaged_version()==VERSION
  assert not app.service.value['participation']
  app.show_page('connection');root.update()
  assert app.connection_panel.editor.get('1.0','end-1c')==''
  assert app.connection_panel.profile.value is None
  assert not (state/'api-connection-v1.json').exists()
  assert str(app.connection_panel.probe_button['state'])=='disabled'
 finally:
  for callback in root.tk.call('after','info'):root.after_cancel(callback)
  app.quit()
 print('Actual installed Tk startup / empty connection / no network: PASS')
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--resume-installed',action='store_true');parser.add_argument('--gui',type=Path);parser.add_argument('--state',type=Path);args=parser.parse_args()
 if args.gui:return gui(args.gui,args.state)
 test=ROOT/'build/rc5-acceptance';test.mkdir(exist_ok=args.resume_installed)
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CHROMA_STATE_DIR=str(test/'state'))
 env.pop('NODE_PATH',None);env.pop('NODE_OPTIONS',None)
 sentinel=test/'state'/'synthetic-preserved.txt';sentinel.parent.mkdir(exist_ok=args.resume_installed)
 if args.resume_installed:assert sentinel.read_text()=='SYNTHETIC TEST DATA'
 else:sentinel.write_text('SYNTHETIC TEST DATA')
 target=test/'Installed Client';kind=platform.system()
 if kind=='Windows':
  import winreg
  reg=r'Software\Microsoft\Windows\CurrentVersion\Uninstall\{9D0B957A-B430-4AB9-B27E-32B553503F95}_is1'
  try:
   key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,reg)
   location=winreg.QueryValueEx(key,'InstallLocation')[0];key.Close()
  except FileNotFoundError:
   assert not args.resume_installed,'Resume requested but test installation absent'
  else:
   if not args.resume_installed or Path(location).resolve()!=target.resolve():raise RuntimeError('Existing unrelated Inno installation protected')
  group='ChromaNeural'
  shortcut=Path(os.environ['APPDATA'])/'Microsoft/Windows/Start Menu/Programs'/group/'ChromaNeural.lnk'
  assert args.resume_installed or not shortcut.exists(),'Existing Start Menu shortcut protected'
  desktops=[Path(os.environ['USERPROFILE'])/'Desktop',Path(os.environ.get('PUBLIC',os.environ['USERPROFILE']))/'Desktop']
  before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for d in desktops for p in d.glob('*ChromaNeural*') if p.is_file()}
  exe=ROOT/'dist'/('ChromaNeural-'+VERSION+'-windows-x64.exe')
  install=[exe,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/LANG=en','/DIR='+str(target),'/GROUP='+group]
  if not args.resume_installed:run(install+['/LOG='+str(test/'install.log')],env=env)
  assert shortcut.is_file(),'Start Menu shortcut absent'
  with winreg.OpenKey(winreg.HKEY_CURRENT_USER,reg) as key:
   assert winreg.QueryValueEx(key,'DisplayVersion')[0]==VERSION
   assert winreg.QueryValueEx(key,'DisplayName')[0].startswith('ChromaNeural')
  assert not (test/'state/preferences.json').exists(),'Installer auto-launched/imported state'
 else:
  assert kind=='Linux'
  run(['dpkg-deb','--extract',next((ROOT/'dist').glob('*.deb')),test/'deb'])
  target=test/'deb/opt/chromaneural'
 validate(target)
 expected={line.split('  ',1)[1] for line in (target/'SHA256SUMS.txt').read_text().splitlines()}
 actual={p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}
 extra=actual-expected-{'SHA256SUMS.txt'}
 assert extra<=({'unins000.exe','unins000.dat','unins000.msg'} if kind=='Windows' else set()),'Unknown installed payload'
 assert (target/'VERSION').read_text().strip()==VERSION
 run([sys.executable,'-I','-B',Path(__file__).resolve(),'--gui',target/'client','--state',test/'gui-state'],env=env)
 if kind=='Windows':
  # Verify the installed shortcut itself points to the installed, unchanged launcher.
  code=r"param($Link,$Expected) $s=(New-Object -ComObject WScript.Shell).CreateShortcut($Link); if($s.Arguments -notlike ('*'+$Expected+'*')){throw 'Shortcut target mismatch'}; if(-not (Test-Path -LiteralPath $s.TargetPath)){throw 'Launcher executable absent'}"
  script=test/'shortcut-check.ps1';script.write_text(code,encoding='utf-8-sig')
  run(['powershell.exe','-NoProfile','-File',script,shortcut,str(target/'Start-ChromaNeural.ps1')],env=env)
  run(install+['/LOG='+str(test/'reinstall.log')],env=env)
  validate(target)
  run([target/'unins000.exe','/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/LOG='+str(test/'uninstall.log')],env=env)
  for _ in range(100):
   if not (target/'client/launch.py').exists():break
   time.sleep(.1)
  assert not (target/'client/launch.py').exists() and not shortcut.exists(),'Uninstall incomplete'
  try:
   key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,reg);key.Close()
  except FileNotFoundError:pass
  else:raise AssertionError('Uninstall registration remains')
  after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for d in desktops for p in d.glob('*ChromaNeural*') if p.is_file()}
  assert after==before,'Desktop changed'
  # Real prerequisite failure, isolated child environment; no system PATH change.
  failure_env=dict(env,PATH=os.environ['SystemRoot']+';'+os.environ['SystemRoot']+'\\System32')
  rejected=test/'Rejected Client'
  bad=subprocess.run([str(exe),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/LANG=en','/DIR='+str(rejected),'/LOG='+str(test/'rejected.log')],env=failure_env,capture_output=True,timeout=90)
  assert bad.returncode!=0 and (test/'rejected.log').is_file(),'Prerequisite failure not reported'
  assert not (rejected/'client/launch.py').exists(),'Prerequisite failure installed application'

 assert sentinel.read_text()=='SYNTHETIC TEST DATA'
 report={'status':'PASS','platform':kind,'version':VERSION,'scope':'actual package bytes, offline installed Tk startup and empty connection; Inno install/reinstall/uninstall on Windows','manualWizardReview':'NOT VERIFIED','WindowsSearchUI':'NOT VERIFIED','remoteExecution':'DISABLED','statePreserved':True}
 (ROOT/'dist/RC5_PACKAGE_ACCEPTANCE.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report))
if __name__=='__main__':main()
