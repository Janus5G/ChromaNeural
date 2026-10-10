"""Finalize unsigned candidate metadata only; no publication or signing."""
from pathlib import Path
import hashlib,shutil,json
ROOT=Path(__file__).resolve().parents[1]
def main():
 dist=ROOT/'dist'
 for name in ('README.md','RELEASE_NOTES.md'):shutil.copyfile(ROOT/name,dist/name)
 files=sorted(p for p in dist.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt')
 lines=[]
 for p in files:
  with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
  lines.append(h+'  '+p.name+'\n')
 (dist/'SHA256SUMS.txt').write_text(''.join(lines),encoding='utf-8',newline='\n')
 print(json.dumps({'status':'PASS','scope':'final unsigned candidate checksums','files':len(files)}))
if __name__=='__main__':main()
