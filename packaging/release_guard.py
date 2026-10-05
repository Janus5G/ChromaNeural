"""Explicit reviewed inputs are the release boundary, not recursive copy exclusions."""
from pathlib import Path
import hashlib,json,shutil
from release_privacy import inspect,fail
INDEX='packaging/release-inputs.json'
def digest(data):return hashlib.sha256(data).hexdigest()
def entries(root):
 raw=(root/INDEX).read_bytes();inspect(INDEX,raw)
 value=json.loads(raw)
 assert set(value)=={'version','files'}
 assert value['version']==(root/'VERSION').read_text().strip()
 return value['files']
def source_files(root):
 root=Path(root).resolve();mapping=entries(root)
 for rel,item in mapping.items():
  from release_privacy import check_name
  check_name(rel)
  assert set(item)<= {'sha256','classification','payload','platform'}
  p=root/rel
  if p.is_symlink() or not p.resolve().is_relative_to(root):fail(rel,'SOURCE_LINK')
  if not p.is_file() or digest(p.read_bytes())!=item['sha256']:fail(rel,'SOURCE_HASH')
  inspect(rel,p.read_bytes())
  if p.suffix=='.json' and item['classification']!='PUBLIC_PRODUCT_JSON':fail(rel,'UNCLASSIFIED_JSON')
 # Reject unknown source, including private state, before copying even one file.
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
  and p.relative_to(root).parts[0] not in {'.git','build','dist'}}
 expected=set(mapping)|{INDEX}
 # A source archive carries a generated, strictly verified public checksum file.
 checksum=root/'SOURCE_SHA256SUMS.txt'
 if checksum.exists():
  rows=checksum.read_text(encoding='utf-8').splitlines()
  wanted={p:digest((root/p).read_bytes()) for p in expected}
  supplied={}
  for line in rows:
   h,rel=line.split('  ',1)
   if rel in supplied:raise ValueError('Duplicate source checksum')
   supplied[rel]=h
  if supplied!=wanted:raise ValueError('Source archive checksum mismatch')
  expected.add('SOURCE_SHA256SUMS.txt')
 if actual!=expected:raise ValueError('UNAPPROVED_SOURCE_PATH')
 return [root/p for p in sorted(mapping)]+[root/INDEX]
def stage_source(root,target,kind):
 source_files(root)
 for rel,item in entries(root).items():
  dest=item.get('payload')
  if not dest or item.get('platform',kind)!=kind:continue
  from release_privacy import check_name
  check_name(dest)
  p=target/dest;p.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(root/rel,p)
def inspect_payload(root,approved_json,sdk_public=None,public_binaries=None):
 sdk_public=sdk_public or {}
 result=[]
 for p in sorted(root.rglob('*')):
  if p.is_symlink():fail(p.relative_to(root).as_posix(),'PAYLOAD_LINK')
  if not p.is_file():continue
  rel=p.relative_to(root).as_posix();data=p.read_bytes();h=digest(data)
  if (public_binaries or {}).get(rel)!=h:
   approved=sdk_public.get(rel,())
   if isinstance(approved,str):approved=(approved,)
   inspect(rel,data,allow_sdk_literals=h in approved)
  if p.suffix.lower()=='.json':
   if rel not in approved_json:fail(rel,'UNCLASSIFIED_JSON')
   result.append({'path':rel,'sha256':h,'classification':'PUBLIC_PRODUCT_JSON'})
 return result
