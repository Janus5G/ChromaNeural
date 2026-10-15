"""Create a curated source archive; never include build output or runtime state."""
from pathlib import Path
import hashlib,stat,zipfile,json
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={'.git','build','dist','__pycache__','node_modules','.venv'}
def main():
 version=(ROOT/'VERSION').read_text(encoding='utf-8').strip()
 dist=ROOT/'dist';dist.mkdir(exist_ok=True)
 out=dist/('ChromaNeural-'+version+'-source.zip')
 prefix='ChromaNeural-'+version+'/'
 from release_guard import source_files
 files=[(p,p.relative_to(ROOT).as_posix()) for p in source_files(ROOT)]
 hashes={rel:hashlib.sha256(p.read_bytes()).hexdigest() for p,rel in files}
 with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
  for p,rel in files:
   info=zipfile.ZipInfo(prefix+rel,(2026,10,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
   info.external_attr=((stat.S_IFREG|(0o755 if p.suffix=='.sh' else 0o644))<<16)
   z.writestr(info,p.read_bytes())
  info=zipfile.ZipInfo(prefix+'SOURCE_SHA256SUMS.txt',(2026,10,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=((stat.S_IFREG|0o644)<<16)
  z.writestr(info,''.join(value+'  '+rel+'\n' for rel,value in hashes.items()).encode('utf-8'))
 with zipfile.ZipFile(out) as z:
  assert z.testzip() is None
  assert all(hashlib.sha256(z.read(prefix+rel)).hexdigest()==value for rel,value in hashes.items())
  assert all(prefix+rel in z.namelist() for rel in ['LICENSE','NOTICE','THIRD_PARTY_LICENSES.md','docs/LICENSING.md','client/reference_core/LICENSE','client/reference_core/NOTICE','.github/workflows/native-packages.yml'])
 print(json.dumps({'status':'PASS','artifact':out.name,'sourceFiles':len(files),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'scope':'curated source bytes and notices; not platform build acceptance'}))
if __name__=='__main__':main()
