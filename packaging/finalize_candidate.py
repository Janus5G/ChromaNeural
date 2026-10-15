"""Finalize the Linux-only candidate; no publication or signing."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 dist=ROOT/'dist';version=(ROOT/'VERSION').read_text().strip()
 names=['chromaneural_'+version.replace('-rc.','.rc.')+'_amd64.deb','ChromaNeural-'+version+'-source.zip']
 assert not list(dist.glob('*.exe')),'Windows executable is outside official release scope'
 hashes={}
 for name in names:
  with (dist/name).open('rb') as f:hashes[name]=hashlib.file_digest(f,'sha256').hexdigest()
 (dist/'SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for n,h in hashes.items()),encoding='utf-8',newline='\n')
 result={'status':'PASS','commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'run':os.environ.get('GITHUB_RUN_ID'),'officialPlatform':'Linux amd64','artifacts':hashes,'scope':'source validation, extracted payload privacy/hash/inclusion and offline Tk startup'}
 (dist/'LINUX_RELEASE.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(result),flush=True)
 if os.environ.get('GITHUB_STEP_SUMMARY'):
  with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:f.write('## Accepted Linux candidate\n\n'+''.join('`'+h+'`  '+n+'\n\n' for n,h in hashes.items()))
if __name__=='__main__':main()
