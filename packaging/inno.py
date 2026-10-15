"""Inno front end over the unchanged, manifest-verified native payload."""
from pathlib import Path
import os,shutil,subprocess

def compile_installer(root,payload,build,dist,version):
 from build import validate
 validate(payload)
 iscc=os.environ.get('CHROMA_ISCC') or shutil.which('ISCC.exe')
 if not iscc:raise RuntimeError('Inno Setup compiler unavailable; set CHROMA_ISCC to verified ISCC.exe')
 iscc=Path(iscc).resolve()
 if not iscc.is_file():raise RuntimeError('Invalid Inno Setup compiler')
 entries=[]
 for line in (payload/'SHA256SUMS.txt').read_text().splitlines():
  _,rel=line.split('  ',1);entries.append(rel)
 entries.append('SHA256SUMS.txt')
 def quote(value):return str(value).replace('"','""')
 rows=[]
 for rel in entries:
  p=(payload/rel).resolve()
  if not p.is_relative_to(payload.resolve()) or not p.is_file():raise RuntimeError('Unsafe payload input')
  dest=Path(rel).parent
  directory='{app}' if str(dest)=='.' else '{app}\\'+str(dest).replace('/','\\')
  rows.append('Source: "'+quote(p)+'"; DestDir: "'+quote(directory)+'"; Flags: ignoreversion')
 include=build/'inno-files.iss';include.write_text('\n'.join(rows)+'\n',encoding='utf-8-sig')
 subprocess.run([str(iscc),'/DAppVersion='+version,'/DPayloadFiles='+str(include.resolve()),'/DOutputPath='+str(dist.resolve()),str(root/'packaging/windows/ChromaNeural.iss')],check=True,timeout=1200)
 target=dist/('ChromaNeural-'+version+'-windows-x64.exe')
 if not target.is_file():raise RuntimeError('Inno Setup output absent')
