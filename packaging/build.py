"""Native package builder. No publication, credentials or backend access."""
from pathlib import Path, PurePosixPath
import argparse,hashlib,json,os,platform,shutil,subprocess,sys,tarfile,urllib.request,zipfile
ROOT=Path(__file__).resolve().parents[1]
VERSION=(ROOT/'VERSION').read_text().strip()
BUILD=ROOT/'build';DIST=ROOT/'dist'
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(args,**kw):
 return subprocess.run([str(a) for a in args],check=True,timeout=kw.pop('timeout',180),**kw)
def files(root):return sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
def manifest(root):
 (root/'SHA256SUMS.txt').write_text(''.join(digest(p)+'  '+p.relative_to(root).as_posix()+'\n' for p in files(root) if p!=root/'SHA256SUMS.txt'),encoding='utf-8',newline='\n')
def validate(root):
 for line in (root/'SHA256SUMS.txt').read_text().splitlines():
  h,rel=line.split('  ',1);p=root/rel
  if not p.resolve().is_relative_to(root.resolve()) or not p.is_file() or digest(p)!=h:raise ValueError('Payload mismatch: '+rel)
def archive(root,out):
 with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
  for p in files(root):
   i=zipfile.ZipInfo(p.relative_to(root).as_posix(),(2026,10,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=((0o100755 if os.access(p,os.X_OK) and os.name!='nt' else 0o100644)<<16);z.writestr(i,p.read_bytes())
 with zipfile.ZipFile(out) as z:
  assert z.testzip() is None
  for p in files(root):
   with z.open(p.relative_to(root).as_posix()) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest(p)
def assets(target,cache):
 cache.mkdir(parents=True,exist_ok=True)
 for item in json.loads((ROOT/'packaging/assets.lock.json').read_text()):
  p=cache/item['name']
  if not p.exists():
   req=urllib.request.Request(item['url'],headers={'User-Agent':'ChromaNeural-release-builder'})
   with urllib.request.urlopen(req,timeout=60) as inp,p.open('xb') as out:shutil.copyfileobj(inp,out)
  if p.stat().st_size!=item['size'] or digest(p)!=item['sha256']:raise ValueError('Asset mismatch: '+p.name)
  if p.suffix=='.gguf':
   dest=target/'models'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest)
  elif p.suffix=='.zip':
   with zipfile.ZipFile(p) as z:
    for name in z.namelist():
     rel=PurePosixPath(name)
     if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe asset path')
     if name.endswith('/'):continue
     dest=target/'runtime/windows-x64'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
  else:
   with tarfile.open(p) as t:
    for member in t.getmembers():
     rel=PurePosixPath(member.name)
     if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe asset path')
     if member.isdir():continue
     # Archive already hash-bound. Materialize in-archive links as ordinary bytes.
     stream=t.extractfile(member)
     if stream is None:raise ValueError('Unsupported tar member')
     dest=target/'runtime/linux-x64'/member.name;dest.parent.mkdir(parents=True,exist_ok=True)
     with stream,dest.open('wb') as out:shutil.copyfileobj(stream,out)
     dest.chmod(member.mode & 0o777)
def stage(kind,cache):
 if kind not in ('windows','linux'):raise SystemExit('This release supports Windows x64 and Linux amd64 only')
 target=BUILD/'payload';target.mkdir(parents=True)
 from release_guard import stage_source
 stage_source(ROOT,target,kind)
 # Lock-driven, release time only. No user state or live endpoint involved.
 run([sys.executable,'-B',target/'scripts/prepare_node_runtime.py','--prepare','--cache',BUILD/'npm-cache'])
 assets(target,cache)
 for name,dest in [('Qwen.txt','models/QWEN_LICENSE'),('llama.cpp.txt','runtime/windows-x64/LICENSE-llama.cpp'),('LLVM-OpenMP.txt','runtime/windows-x64/LICENSE-LLVM-OpenMP')]:
  p=target/dest;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'docs/licenses'/name,p)
 # Verify every accepted model/runtime byte, not merely compressed archives.
 expected=json.loads((ROOT/'packaging/binaries.lock.json').read_text())
 for rel,h in expected.items():
  if not (target/rel).is_file() or digest(target/rel)!=h:raise ValueError('Extracted runtime mismatch: '+rel)
 if kind=='linux':shutil.rmtree(target/'runtime/windows-x64')
 from mcp_package import stage as stage_mcp
 stage_mcp(ROOT,target)
 from release_guard import inspect_payload
 policy=json.loads((ROOT/'packaging/release-policy.json').read_text())
 inspect_payload(target,policy['jsonPaths'],policy['publicDependencyFiles'],json.loads((ROOT/'packaging/binaries.lock.json').read_text()))
 manifest(target);validate(target);return target
def windows(payload):
 from inno import compile_installer
 compile_installer(ROOT,payload,BUILD,DIST,VERSION)

def linux(payload):
 deb=BUILD/'deb';app=deb/'opt/chromaneural';app.parent.mkdir(parents=True);shutil.copytree(payload,app)
 control=deb/'DEBIAN';control.mkdir()
 version=VERSION.replace('-rc.','~rc.')
 (control/'control').write_text('Package: chromaneural\nVersion: '+version+'\nArchitecture: amd64\nMaintainer: ChromaNeural maintainers\nDepends: python3 (>= 3.11), python3-tk, python3-cryptography, nodejs (>= 20), libgomp1\nSection: science\nPriority: optional\nDescription: ChromaNeural local client release candidate\n Explicitly approved local AI work and authenticated peer transport.\n',encoding='utf-8')
 script=deb/'usr/bin/chromaneural';script.parent.mkdir(parents=True)
 script.write_text('#!/bin/sh\nset -eu\nexec /usr/bin/python3 -B /opt/chromaneural/client/launch.py "$@"\n');script.chmod(0o755)
 desktop=deb/'usr/share/applications/chromaneural.desktop';desktop.parent.mkdir(parents=True)
 desktop.write_text('[Desktop Entry]\nType=Application\nName=ChromaNeural\nExec=chromaneural\nIcon=chromaneural\nTerminal=false\nCategories=Science;Development;\n')
 for directory,name in [('512x512/apps','chromaneural.png'),('scalable/apps','chromaneural.svg')]:
  icon=deb/'usr/share/icons/hicolor'/directory/name;icon.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'packaging/branding'/name,icon)
 run(['dpkg-deb','--root-owner-group','--build',deb,DIST/('chromaneural_'+VERSION.replace('-rc.','.rc.')+'_amd64.deb')])
def require_license_clearance():
 scope=json.loads((ROOT/'docs/LICENSE_SCOPE.json').read_text(encoding='utf-8'))
 if scope.get('publicDistributionCleared') is not True:
  raise SystemExit('LICENSE BLOCKED: documented source-license clearance is required before packaging')

def main():
 if platform.system() not in ('Windows','Linux'):raise SystemExit('This release supports Windows x64 and Linux amd64 only')
 require_license_clearance()
 parser=argparse.ArgumentParser();parser.add_argument('--asset-cache',type=Path,default=BUILD/'asset-cache');args=parser.parse_args()
 kind={'Windows':'windows','Linux':'linux'}[platform.system()]
 if platform.machine().lower() not in ('amd64','x86_64'):raise SystemExit('This RC package profile is x86_64 only; source remains portable')
 if (BUILD/'payload').exists() or DIST.exists():raise SystemExit('Preserve existing output; use a fresh checkout/build directory')
 from release_guard import source_files
 source_files(ROOT)
 DIST.mkdir();payload=stage(kind,args.asset_cache)
 {'windows':windows,'linux':linux}[kind](payload)
 (DIST/'SHA256SUMS.txt').write_text(''.join(digest(p)+'  '+p.name+'\n' for p in sorted(DIST.iterdir()) if p.is_file()),encoding='utf-8')
 (DIST/'BUILD_INFO.json').write_text(json.dumps({'version':VERSION,'platform':kind,'architecture':platform.machine(),'python':sys.version,'signing':'UNSIGNED','productSource':'accepted-source.json plus exact reviewed source-overrides.json and source-additions.json','status':'BUILT; package smoke still required'},indent=2))
if __name__=='__main__':main()
