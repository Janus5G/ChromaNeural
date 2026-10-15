"""Release-only checks. Never log private values."""
import base64,binascii,json,re
from pathlib import PurePosixPath
PRIVATE_NAMES={'api-connection-v1.json','preferences.json','ui-language.json',
 'identity.json','credentials.json','mcp-connections.json','mcp.json',
 'ai-tools.json','service-state.json','.env'}
BAD_SUFFIX={'.db','.sqlite','.sqlite3','.log','.partial','.pem','.key','.pfx','.p12'}
PROFILE={'principal','backend_canister_id','frontend_canister_id',
 'identity_provider','ii_derivation_origin'}
PRINCIPAL=re.compile(rb'(?<![a-z2-7])(?:[a-z2-7]{5}-){2,11}[a-z2-7]{1,5}(?![a-z2-7])')
def fail(path,category):raise ValueError(category+': '+path)
def check_name(path):
 p=PurePosixPath(path)
 if p.is_absolute() or '..' in p.parts or ':' in path or '\\' in path:fail(path,'UNSAFE_PATH')
 if p.name.lower() in PRIVATE_NAMES or p.suffix.lower() in BAD_SUFFIX:fail(path,'PRIVATE_STATE_FILENAME')
 if p.name.lower().startswith(('api-connection.','preferences.invalid.')):fail(path,'PRIVATE_STATE_FILENAME')
 if any(x.lower() in {'diagnostics','evidence','logs','private-state'} for x in p.parts):fail(path,'PRIVATE_DIRECTORY')
def check_object(path,value):
 if isinstance(value,dict):
  populated={str(k).lower() for k,v in value.items() if v not in (None,'',False,[],{})}
  if len(PROFILE & populated)>=2:fail(path,'SAVED_CONNECTION_PROFILE')
  for k,v in value.items():
   if str(k).lower() in {'access_token','refresh_token','client_secret','private_key','session_token'} and isinstance(v,str) and v:
    fail(path,'PRIVATE_CREDENTIAL')
   check_object(path,v)
 elif isinstance(value,list):
  for v in value:check_object(path,v)
def inspect(path,data,allow_sdk_literals=False):
 check_name(path)
 # UTF-16/32 ASCII fields must not bypass byte-pattern checks.
 streams=[data]
 if b'\x00' in data[:4096]:streams.append(data.replace(b'\x00',b''))
 for raw in streams:
  if re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----[ \t]*(?:\r?\n|\\n)[A-Za-z0-9+/]{32,}',raw):fail(path,'PRIVATE_KEY')
  if re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|AKIA[A-Z0-9]{16})',raw):fail(path,'CREDENTIAL_PATTERN')
  if not allow_sdk_literals and re.search(rb'(?i)(?:[A-Z]:\\Users\\[^\\\s]+\\|[/]Users[/][^/\s]+[/]|[/]home[/][^/\s]+[/])',raw):fail(path,'PRIVATE_MACHINE_PATH')
  if not allow_sdk_literals:
   for m in PRINCIPAL.finditer(raw):
    compact=m.group().replace(b'-',b'')
    try:decoded=base64.b32decode(compact.upper()+b'='*(-len(compact)%8))
    except binascii.Error:continue
    if 4<len(decoded)<=33 and decoded[:4]==binascii.crc32(decoded[4:]).to_bytes(4,'big'):fail(path,'UNCLASSIFIED_PRINCIPAL')
  # Detect serialized profiles embedded in any text/binary file.
  text=raw.decode('utf-8',errors='ignore')
  for match in re.finditer(r'\{[^{}]{0,16384}\}',text):
   try:value=json.loads(match.group())
   except (ValueError,RecursionError):continue
   check_object(path,value)
 if path.lower().endswith('.json'):
  try:value=json.loads(data.decode('utf-8-sig'))
  except (ValueError,UnicodeError):fail(path,'INVALID_JSON')
  check_object(path,value)
