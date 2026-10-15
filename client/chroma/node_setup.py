"""Explicit node setup. Public metadata never authenticates a node or II user."""
from pathlib import Path
import hashlib,json,os
from urllib.parse import urlsplit
from .connection_profile import parse_profile,principal_bytes,_object
from .speech_identity import node_key

def read_json(path):
    with Path(path).open('rb') as stream: raw=stream.read(32769)
    if len(raw)>32768: raise ValueError('Node configuration size limit')
    return json.loads(raw.decode('utf-8-sig'),object_pairs_hook=_object)

def target(host,canister,local):
    principal_bytes(canister)
    if local:
        u=urlsplit(host)
        if (u.scheme!='http' or u.hostname!='127.0.0.1' or not u.port
                or u.username or u.password or u.path or u.query or u.fragment):
            raise ValueError('Local replica must be explicit http://127.0.0.1:port')
    elif host not in ('https://icp0.io','https://icp-api.io'):
        raise ValueError('Unsupported mainnet target')

def checked_config(path):
    value=read_json(path);binding=value.get('nodeConnectionV1')
    if not isinstance(binding,dict) or set(binding)!={'nodeId','host','canisterId'}:
        raise ValueError('Explicit node setup binding required')
    if value.get('networkEnabled') is not True:
        raise PermissionError('Separate node network opt-in required')
    if value.get('runtimeProvider','native')!='native':
        raise ValueError('New setup requires native runtime paths; legacy WSL config remains separate')
    target(value['host'],value['canisterId'],value.get('allowLocalTestRoot') is True)
    if binding['host']!=value['host'] or binding['canisterId']!=value['canisterId']:
        raise ValueError('Node target binding mismatch')
    folder=Path(value['identityDirectory'])
    if not folder.is_absolute(): raise ValueError('Absolute existing identity directory required')
    _,raw=node_key(folder/'private_key.pem',folder/'public_key.json')
    if hashlib.sha256(raw).hexdigest()!=binding['nodeId']: raise ValueError('Node identity binding mismatch')
    return value

def prepare(identity_directory,output,*,profile=None,local_host=None,canister_id=None,
            approve_network=False,allow_local_test=False):
    if approve_network is not True:
        raise PermissionError('Approve node identity use and node network separately from browser login')
    if (profile is None)==(local_host is None): raise ValueError('Choose public profile OR explicit local replica')
    if profile is not None:
        if canister_id is not None or allow_local_test: raise ValueError('Public profile target may not be overridden')
        p=parse_profile(json.dumps(read_json(profile)))
        host,canister,local=p['host'],p['backend_canister_id'],False
    else:
        if allow_local_test is not True: raise PermissionError('Explicit isolated replica trust required')
        host,canister,local=local_host,canister_id,True
    target(host,canister,local)
    folder=Path(identity_directory).resolve(strict=True)
    _,raw=node_key(folder/'private_key.pem',folder/'public_key.json')
    node_id=hashlib.sha256(raw).hexdigest()
    value={'networkEnabled':True,'host':host,'canisterId':canister,'identityDirectory':str(folder),
           'allowLocalTestRoot':local,'nodeConnectionV1':{'nodeId':node_id,'host':host,'canisterId':canister}}
    # Never import principal/session/grants or enable publication/resources.
    destination=Path(output).resolve()
    fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    return {'status':'CONFIGURED_NOT_CHECKED','config':str(destination),'nodeId':node_id,
            'host':host,'canisterId':canister,'nodeAdmission':'NOT_VERIFIED','privateLogin':'BROWSER_ONLY'}

def observe(config,*,provider=None):
    from . import icp_client
    checked_config(config)
    return (provider or icp_client.call)(config,'node_status')

def register_local(config,*,approve_registration=False,approve_node_owner=False,provider=None):
    from . import icp_client
    if approve_registration is not True or approve_node_owner is not True:
        raise PermissionError('Separate registration and node-as-registry-owner approvals required')
    c=checked_config(config)
    if c.get('allowLocalTestRoot') is not True:
        raise PermissionError('New registration is LOCAL ONLY; live admission requires separate authorization')
    return (provider or icp_client.call)(config,'node_register_local',
                                        approveRegistration=True,approveNodeOwner=True)

def select_connection(config,state_directory,*,approved=False):
    from .settings import Settings
    if approved is not True: raise PermissionError('Explicit connection selection required')
    checked_config(config)
    settings=Settings(state_directory)
    if settings.error: raise ValueError('Existing preferences invalid; preserve and resolve separately')
    if settings.value['participation']: raise PermissionError('Stop participation before changing its node connection')
    value=dict(settings.value);value['connection']=str(Path(config).resolve(strict=True))
    settings.save(value)
    return {'status':'SELECTED_NOT_STARTED','connection':value['connection'],
            'restartClientToLoad':True,'nodeAdmission':'NOT_VERIFIED'}
