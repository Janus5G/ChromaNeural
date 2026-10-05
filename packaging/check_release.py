"""Offline release checks. No publication or application network calls."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,os,platform,re,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
def h(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify_source(root):
 from release_guard import source_files,entries
 source_files(root)
 return entries(root),[]

def check():
 checks=[]
 def ok(name,condition):
  if not condition:raise AssertionError(name)
  checks.append(name)
 version=(ROOT/'VERSION').read_text(encoding='utf-8').strip();ok('RC version',version=='0.2.21-rc.4')
 required=['README.md','LICENSE','NOTICE','CHANGELOG.md','SECURITY.md','CONTRIBUTING.md','INSTALLATION.md','VERIFICATION.md','KNOWN_LIMITATIONS.md','RELEASE_NOTES.md','THIRD_PARTY_NOTICES.md','THIRD_PARTY_LICENSES.md','docs/LICENSING.md','docs/LICENSE_SCOPE.json']
 ok('public documentation complete',all((ROOT/p).is_file() for p in required))
 ok('Apache text',(ROOT/'LICENSE').read_text().find('Apache License')>=0)
 mapping,additions=verify_source(ROOT)
 ok('accepted source, reviewed overrides and added-file inventory exact',True)
 registry=json.loads((ROOT/'client/locale-registry.json').read_text(encoding='utf-8'))
 ok('registered locale resources packaged',all((ROOT/'client/locales'/(x['id']+'.json')).is_file() for x in registry['locales']))
 ok('translated root READMEs available',all((ROOT/p).is_file() for p in required) and bool(list(ROOT.glob('README-*.md'))))
 ok('Windows installer version',("$version = '"+version+"'") in (ROOT/'packaging/windows/install.ps1').read_text(encoding='utf-8'))
 scope=json.loads((ROOT/'docs/LICENSE_SCOPE.json').read_text(encoding='utf-8'))
 ok('Refract first MIT license documented',scope['publicDistributionCleared'] is True and all(x['license']=='MIT' for x in scope['files'] if x['path'].startswith('client/reference_core/') and x['path'].endswith('.py') and not x['path'].endswith('__init__.py')) and 'Copyright (c) 2026 Janus Rokkjær' in (ROOT/'client/reference_core/LICENSE').read_text(encoding='utf-8'))
 ok('mobile deferral wording','Official Android and iOS support is deferred to a later time.' in (ROOT/'KNOWN_LIMITATIONS.md').read_text())
 workflow=(ROOT/'.github/workflows/native-packages.yml').read_text()
 ok('CI artifact version','name: ChromaNeural-'+version+'-${{ matrix.platform }}' in workflow)
 ok('native runner matrix',all(x in workflow for x in ['windows-2025','ubuntu-24.04','macos-15-intel']))
 ok('manual workflow only','workflow_dispatch:' in workflow and not re.search(r'^  (push|pull_request|release):',workflow,re.M))
 ok('no publication permission','contents: read' in workflow and 'write' not in workflow and 'persist-credentials: false' in workflow)
 uses=re.findall(r'uses: (\S+)',workflow)
 ok('local MCP workflow fixed',uses.count('./.github/workflows/mcp-acceptance.yml')==1)
 uses=[x for x in uses if x!='./.github/workflows/mcp-acceptance.yml']
 ok('immutable Action pins',len(uses)==4 and all(re.fullmatch(r'actions/[a-z-]+@[0-9a-f]{40}',x) for x in uses))
 mcp_workflow=(ROOT/'.github/workflows/mcp-acceptance.yml').read_text()
 mcp_uses=re.findall(r'uses: (\S+)',mcp_workflow)
 ok('MCP native workflow pins/permissions',len(mcp_uses)==3 and all(re.fullmatch(r'actions/[a-z-]+@[0-9a-f]{40}',x) for x in mcp_uses) and 'contents: read' in mcp_workflow and 'persist-credentials: false' in mcp_workflow and not re.search(r'^  (push|pull_request|release):',mcp_workflow,re.M))
 ok('no continue-on-error','continue-on-error' not in workflow)
 ok('no production command','caffeine' not in workflow.lower() and 'gh release' not in workflow and 'dfx' not in workflow)
 forbidden=[];syntax=0;large=[]
 for p in ROOT.rglob('*'):
  rel=p.relative_to(ROOT)
  if any(x in rel.parts for x in ['.git','build','dist','__pycache__','node_modules']):continue
  if not p.is_file():continue
  if p.stat().st_size>95*1024*1024:large.append(str(rel))
  if p.suffix in ['.pem','.key','.p12','.pfx'] or p.name in ['.env','identity.json','credentials.json']:forbidden.append(str(rel))
  if p.stat().st_size<4*1024*1024:
   b=p.read_bytes()
   if re.search(rb'(?m)^-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----\r?$',b):forbidden.append(str(rel))
   if p.suffix=='.py':compile(b,str(rel),'exec');syntax+=1
 ok('no known credential files/private-key blocks',not forbidden)
 ok('GitHub source file-size limit',not large)
 ok('Python syntax',syntax>0)
 assets=json.loads((ROOT/'packaging/assets.lock.json').read_text())
 ok('hash-bound fixed asset inputs',len(assets)==3 and all(re.fullmatch('[0-9a-f]{64}',x['sha256']) and x['url'].startswith('https://') and x['size']>0 for x in assets))
 # Test the actual packaging manifest verifier against a deliberately corrupt byte.
 import tempfile
 sys.path.insert(0,str(ROOT/'packaging'));from build import manifest,validate
 with tempfile.TemporaryDirectory() as temp:
  t=Path(temp);(t/'file').write_bytes(b'INERT');manifest(t);validate(t);(t/'file').write_bytes(b'CHANGED')
  try:validate(t)
  except ValueError:ok('packaging manifest rejects corruption',True)
  else:raise AssertionError('Corruption accepted')
 result={'status':'PASS','checks':checks,'count':len(checks),'applicationSourceFiles':len(mapping),'pythonFilesParsed':syntax,'scope':'local release source/contract and package-manifest tests; not native CI acceptance'}
 print(json.dumps(result,indent=2));return result
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--artifacts',action='store_true');args=parser.parse_args()
 result=check()
 if args.artifacts:
  dist=ROOT/'dist';smoke=json.loads((dist/'PACKAGE_SMOKE.json').read_text());assert smoke['status']=='PASS'
  (dist/'BUILD_ENVIRONMENT.json').write_text(json.dumps({'platform':platform.platform(),'python':sys.version,'runnerImage':os.environ.get('ImageVersion'),'checks':result},indent=2))
  (dist/'SHA256SUMS.txt').write_text(''.join(h(p)+'  '+p.name+'\n' for p in sorted(dist.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'),encoding='utf-8')
