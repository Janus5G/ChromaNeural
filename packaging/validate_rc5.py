"""Focused RC5 input/documentation checks; does not rerun closed product gates."""
from pathlib import Path
import ast,hashlib,json,re,struct,sys
from urllib.parse import unquote,urlsplit
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'packaging'))
from release_guard import source_files

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 files=source_files(ROOT)
 binding=json.loads((ROOT/'packaging/rc4-application.json').read_text())
 hashes=dict(binding['files'])
 delta=json.loads((ROOT/'packaging/rc5-wizard-acceptance.json').read_text())
 assert set(delta['changes'])=={'client/chroma/onboarding_ui.py','client/chroma/mcp_catalog.py','client/locales/en.json','client/locales/da.json'}
 for p,item in delta['changes'].items():
  assert hashes.get(p)==item['previous_sha256'],'Unexpected wizard baseline'
  hashes[p]=item['sha256']
 assert sha(ROOT/delta['test_file']['path'])==delta['test_file']['sha256']
 assert all(sha(ROOT/p)==h for p,h in hashes.items()),'RC4 application correlation failed'
 current={p.relative_to(ROOT).as_posix() for parent in ('client','scripts') for p in (ROOT/parent).rglob('*') if p.is_file()}
 assert current==set(hashes),'Unexpected application source file'
 for p in files:
  if p.suffix=='.py' and p.parent==ROOT/'packaging':ast.parse(p.read_text(encoding='utf-8-sig'),filename=p.name)
 links=0
 for p in files:
  if p.suffix.lower()!='.md':continue
  text=p.read_text(encoding='utf-8-sig')
  refs=re.findall(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)',text)
  refs+=re.findall(r'(?:src|href)=["\']([^"\']+)["\']',text)
  for ref in refs:
   u=urlsplit(ref.strip('<>'))
   if u.scheme or u.netloc or not u.path:continue
   dest=(p.parent/unquote(u.path)).resolve()
   assert dest.is_relative_to(ROOT) and dest.exists(),f'Broken local link: {p.relative_to(ROOT)} -> {ref}'
   links+=1
 for locale in ('en','da'):
  guide=(ROOT/'docs'/locale/'guide.md').read_text(encoding='utf-8')
  assert all('images/'+v+'.png' in guide for v in ('overview','resources','activity','connection','ai-setup','mcp'))
  assert not any(x in guide for x in ('rc.1','rc.2','preserved','Unreleased candidate'))
  if locale=='en':assert not any(x in guide for x in ('Oversigt','Ressourcer','Gem og','forbindelse'))
 manifest=json.loads((ROOT/'docs/SCREENSHOT_MANIFEST.json').read_text())
 assert manifest['status']=='PASS' and len(manifest['captures'])==12
 assert manifest['version']==(ROOT/'VERSION').read_text().strip()
 # Capture provenance remains historical; accepted additive wizard/locale changes
 # do not relabel old captures as newly generated Linux/package evidence.
 for p,h in manifest['source_hashes'].items():
  if p in delta['changes']:
   assert h==delta['changes'][p]['previous_sha256']
  else:assert sha(ROOT/p)==h
 for item in manifest['captures']:
  p=ROOT/item['filename'];assert sha(p)==item['sha256'] and item['verification']=='PASS'
  assert p.parts[-3]==item['locale'] and item['locale'] in ('en','da')
  data=p.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n'
  assert list(struct.unpack('>II',data[16:24]))==item['size']
 workflow=(ROOT/'.github/workflows/native-packages.yml').read_text()
 assert all(re.fullmatch(r'[a-zA-Z0-9_./-]+@[a-f0-9]{40}',x) for x in re.findall(r'uses:\s+(\S+)',workflow))
 assert 'contents: read' in workflow and 'persist-credentials: false' in workflow
 assert 'workflow_dispatch:' in workflow and 'schedule:' not in workflow
 assert 'runs-on: ubuntu-24.04' in workflow
 assert not any(x in workflow.lower() for x in ('windows-','signpath','inno','test-sign:'))
 assert 'packaging/source_archive.py' in workflow
 assert not any(x in p.relative_to(ROOT).as_posix() for p in files for x in ('docs/images/rc2/','docs/pdf/rc2/'))
 assert 'gh release' not in workflow and 'contents: write' not in workflow
 assert not list((ROOT/'docs').rglob('*.pdf')),'Withdrawn PDFs must not be RC5 inputs'
 print(json.dumps({'status':'PASS','scope':'RC5 source guard, application baseline plus owner-accepted wizard binding, docs/local links, screenshot manifest, pinned manual workflow','sourceFiles':len(files),'applicationFiles':len(hashes),'localLinks':links,'screenshots':12,'remoteExecution':'DISABLED'}))
if __name__=='__main__':main()
