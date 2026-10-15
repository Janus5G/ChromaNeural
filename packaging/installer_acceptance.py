"""Installer-only acceptance: installed bytes/imports, never behavioral MCP or GUI suites."""
import hashlib,importlib,importlib.metadata,json,os,platform,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def source():
    sys.path.insert(0,str(ROOT/'packaging'))
    from check_release import verify_source
    verify_source(ROOT)
    assert (ROOT/'VERSION').read_text().strip()=='0.2.21-rc.4'
    assert shutil.disk_usage(ROOT).free>8*1024**3,'Insufficient native build space'
    print('Exact accepted application source binding PASS; behavioral suites reused')
def installed(client,out):
    client=Path(client).resolve();deps=client/'mcp-deps'
    assert deps.is_dir(),'MCP payload omitted from installer'
    sys.path.insert(0,str(client))
    from chroma.mcp_client import sdk_path
    sdk_path()
    expected={}
    for line in (ROOT/'packaging/requirements-mcp.txt').read_text().splitlines():
        spec=line.split(' --hash=')[0]
        if not spec.strip():continue
        if ';' in spec:
            spec,marker=spec.split(';',1)
            assert marker.strip()=='sys_platform == "win32"'
            if sys.platform!='win32':continue
        name,version=spec.split('==')
        expected[name.lower().replace('_','-')]=version
    actual={d.metadata['Name'].lower().replace('_','-'):d.version
            for d in importlib.metadata.distributions(path=[str(deps)])}
    assert actual==expected,{'missing_or_wrong':{k:v for k,v in expected.items() if actual.get(k)!=v},
                             'unexpected':sorted(set(actual)-set(expected))}
    imports={}
    for name in ('mcp','mcp.client.stdio','mcp.client.streamable_http',
                 'cryptography.hazmat.bindings._rust','pydantic_core','rpds','httpx2'):
        module=importlib.import_module(name)
        location=Path(module.__file__).resolve()
        assert location.is_relative_to(deps),name+' loaded outside installed payload'
        imports[name]=location.relative_to(client).as_posix()
    assert actual['mcp']=='2.3.0' and actual['cryptography']=='46.0.5'
    payload=client.parent
    shutil.copyfile(payload/'SHA256SUMS.txt',Path(out).parent/'INSTALLED_PAYLOAD_SHA256.txt')
    dump(Path(out),{'status':'PASS','platform':platform.system(),'python':sys.version,
         'distributions':actual,'imports':imports,'payload_manifest_sha256':sha(payload/'SHA256SUMS.txt'),
         'scope':'Actual installed native dependencies/paths; no MCP call, AI inference or GUI suite',
         'remote_execution':'DISABLED'})
def finalize():
    dist=ROOT/'dist'
    smoke=json.loads((dist/'PACKAGE_SMOKE.json').read_text())
    sdk=json.loads((dist/'INSTALLED_MCP.json').read_text())
    assert smoke['status']=='PASS' and sdk['status']=='PASS'
    assert smoke['acceptanceMode']=='installer-only'
    dump(dist/'BUILD_ENVIRONMENT.json',{'platform':platform.platform(),'python':sys.version,
        'runnerImage':os.environ.get('ImageVersion'),'source_commit':os.environ.get('GITHUB_SHA'),
        'scope':'rc.4 installer acceptance; closed behavior/GUI gates reused',
        'sdk_lock_sha256':sha(ROOT/'packaging/requirements-mcp.txt')})
    (dist/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n'
        for p in sorted(dist.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'),encoding='utf-8')
if __name__=='__main__':
    if sys.argv[1:] == ['source']:source()
    elif sys.argv[1:] == ['finalize']:finalize()
    elif len(sys.argv)==4 and sys.argv[1]=='installed':installed(sys.argv[2],sys.argv[3])
    else:raise SystemExit('Expected source, finalize, or installed CLIENT OUTPUT')
