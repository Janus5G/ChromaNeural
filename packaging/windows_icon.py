"""Resource-only branding of a newly built, unsigned IExpress package.
Abort before replacing the output unless code, non-icon resources, overlay,
and extracted payload are identical. No installer is executed by this check.
"""
from pathlib import Path
import ctypes,hashlib,json,shutil,struct,subprocess

def digest(data):return hashlib.sha256(data).hexdigest()

def inspect_pe(path):
 data=path.read_bytes()
 def u16(p):return struct.unpack_from('<H',data,p)[0]
 def u32(p):return struct.unpack_from('<I',data,p)[0]
 assert data[:2]==b'MZ'
 pe=u32(60);assert data[pe:pe+4]==b'PE\0\0'
 opt=pe+24;magic=u16(opt);assert magic in (0x10b,0x20b)
 directory=opt+(96 if magic==0x10b else 112)
 assert data[directory+32:directory+40]==b'\0'*8,'Signed input is not supported'
 sections=[]
 for i in range(u16(pe+6)):
  p=opt+u16(pe+20)+i*40
  name=data[p:p+8].rstrip(b'\0').decode('ascii')
  sections.append((name,u32(p+12),u32(p+16),u32(p+20)))
 def offset(rva):
  for name,va,size,pos in sections:
   if va<=rva<va+size:return pos+rva-va
  raise ValueError('Unmapped RVA')
 base=offset(u32(directory+16));resources={}
 def walk(pos,keys):
  p=base+pos
  for i in range(u16(p+12)+u16(p+14)):
   key,child=struct.unpack_from('<II',data,p+16+i*8)
   if key&0x80000000:
    n=base+(key&0x7fffffff);key=data[n+2:n+2+u16(n)*2].decode('utf-16-le')
   branch=keys+(key,)
   if child&0x80000000:walk(child&0x7fffffff,branch)
   else:
    rva,size,cp,_=struct.unpack_from('<IIII',data,base+child)
    q=offset(rva);assert q+size<=len(data)
    resources[branch]=(cp,data[q:q+size])
 walk(0,())
 end=max(pos+size for _,_,size,pos in sections)
 code={name:(va,digest(data[pos:pos+size])) for name,va,size,pos in sections if name!='.rsrc'}
 reloc_rva=u32(directory+40)
 if '.reloc' in code:assert reloc_rva==code['.reloc'][0],'Relocation directory mismatch'
 return {'resources':resources,'sections':code,'overlay':digest(data[end:]),'machine':u16(pe+4),'entry':u32(opt+16)}

def icon_entries(path):
 data=path.read_bytes();reserved,kind,count=struct.unpack_from('<HHH',data)
 assert reserved==0 and kind==1 and count>0
 result=[]
 for i in range(count):
  p=6+i*16;size,offset=struct.unpack_from('<II',data,p+8)
  assert offset+size<=len(data)
  result.append((data[p:p+12],data[offset:offset+size]))
 return result

def update_icons(path,before,icons):
 api=ctypes.WinDLL('kernel32',use_last_error=True)
 api.BeginUpdateResourceW.argtypes=[ctypes.c_wchar_p,ctypes.c_int];api.BeginUpdateResourceW.restype=ctypes.c_void_p
 api.UpdateResourceW.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ushort,ctypes.c_void_p,ctypes.c_uint32];api.UpdateResourceW.restype=ctypes.c_int
 api.EndUpdateResourceW.argtypes=[ctypes.c_void_p,ctypes.c_int];api.EndUpdateResourceW.restype=ctypes.c_int
 groups=[key for key in before['resources'] if key[0]==14]
 assert groups and all(len(key)==3 for key in groups)
 # Preserve group identities/languages. Replace only icon resource content.
 ids=[key[1] for key in before['resources'] if key[0]==3 and isinstance(key[1],int)]
 start=max(ids,default=0)+1;assert start+len(icons)<65536
 group=struct.pack('<HHH',0,1,len(icons))+b''.join(header+struct.pack('<H',start+i) for i,(header,_) in enumerate(icons))
 def resource_key(value):
  return ctypes.c_void_p(value) if isinstance(value,int) else ctypes.cast(ctypes.c_wchar_p(value),ctypes.c_void_p)
 handle=api.BeginUpdateResourceW(str(path),False)
 if not handle:raise ctypes.WinError(ctypes.get_last_error())
 try:
  writes={(14,name,lang):group for _,name,lang in groups}
  for lang in {key[2] for key in groups}:
   for i,(_,bits) in enumerate(icons):writes[(3,start+i,lang)]=bits
  for (kind,name,lang),bits in writes.items():
   buf=ctypes.create_string_buffer(bits)
   if not api.UpdateResourceW(handle,resource_key(kind),resource_key(name),lang,buf,len(bits)):raise ctypes.WinError(ctypes.get_last_error())
  if not api.EndUpdateResourceW(handle,False):raise ctypes.WinError(ctypes.get_last_error())
  handle=None
 finally:
  if handle:api.EndUpdateResourceW(handle,True)
 return writes

def inventory(root):
 return {p.relative_to(root).as_posix():digest(p.read_bytes()) for p in root.rglob('*') if p.is_file()}

def brand(exe,ico,evidence):
 evidence.mkdir()
 original=evidence/'unbranded.exe';candidate=evidence/'branded.exe'
 shutil.copyfile(exe,original);shutil.copyfile(exe,candidate)
 before=inspect_pe(original);icons=icon_entries(ico)
 writes=update_icons(candidate,before,icons);after=inspect_pe(candidate)
 for field in ('overlay','machine','entry'):assert before[field]==after[field],field+' changed'
 assert before['sections'].keys()==after['sections'].keys()
 for name,(rva,sha) in before['sections'].items():
  new_rva,new_sha=after['sections'][name]
  assert sha==new_sha,'Non-resource section bytes changed: '+name
  # Windows may move the trailing relocation table when .rsrc grows.
  # Its directory RVA is checked in inspect_pe; all code/data RVAs stay fixed.
  assert rva==new_rva or name=='.reloc','Code/data RVA changed: '+name
 old_other={k:v for k,v in before['resources'].items() if k[0] not in (3,14)}
 new_other={k:v for k,v in after['resources'].items() if k[0] not in (3,14)}
 assert old_other==new_other,'Non-icon resource changed'
 assert set(after['resources'])==set(before['resources'])|set(writes),'Unexpected resource inventory'
 for key,bits in writes.items():assert after['resources'][key][1]==bits,'Icon bytes differ'
 for key,value in before['resources'].items():
  if key not in writes:assert after['resources'][key]==value,'Unrelated resource changed'
 extracted=[]
 for name,path in [('before',original),('after',candidate)]:
  target=evidence/name;target.mkdir()
  result=subprocess.run([str(path),'/Q','/C','/T:'+str(target)],capture_output=True,timeout=180)
  assert result.returncode==0,'Extraction failed: '+str(result.returncode)
  extracted.append(inventory(target))
 assert extracted[0] and extracted[0]==extracted[1],'Extracted payload changed'
 report={'status':'PASS','originalSha256':digest(original.read_bytes()),'brandedSha256':digest(candidate.read_bytes()),'iconSha256':digest(ico.read_bytes()),'iconImages':len(icons),'resourceWrites':len(writes),'nonIconResourcesPreserved':len(old_other),'codeAndOverlayPreserved':True,'sectionLayoutBefore':before['sections'],'sectionLayoutAfter':after['sections'],'extraction':'byte-identical; extract-only /Q /C /T','extracted':extracted[0]}
 (evidence/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 shutil.copyfile(candidate,exe)
 return report
