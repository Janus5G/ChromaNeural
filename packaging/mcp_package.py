"""Stage fresh locked libraries; generated console launchers never enter payloads."""
from pathlib import Path
import os,platform,shutil,subprocess,sys

def libraries(root,target,lock,label):
    scratch=root/'build'/('dependency-install-'+label)
    if scratch.exists() or target.exists():raise ValueError('Preserve existing dependency output')
    python='/usr/bin/python3' if platform.system()=='Linux' else sys.executable
    subprocess.run([python,'-B','-m','pip','install','--disable-pip-version-check',
        '--no-cache-dir','--no-compile','--only-binary=:all:','--require-hashes',
        '--target',str(scratch),'-r',str(root/'packaging'/lock)],
        check=True,timeout=300,env=dict(os.environ,PIP_NO_INPUT='1',PYTHONDONTWRITEBYTECODE='1'))
    target.mkdir(parents=True)
    # pip creates absolute-interpreter console launchers under bin. The client
    # imports libraries; it never executes these dependency entry points.
    for p in sorted(scratch.iterdir()):
        if p.name in {'bin','Scripts','__pycache__'}:continue
        if p.is_symlink():raise ValueError('Dependency link rejected')
        if p.is_dir():shutil.copytree(p,target/p.name)
        else:shutil.copyfile(p,target/p.name)

def stage(root,payload):
    if shutil.disk_usage(payload).free<512*1024*1024:raise OSError('Insufficient MCP staging space')
    libraries(root,payload/'client/mcp-deps','requirements-mcp.txt','mcp')
    if platform.system()=='Windows':
        libraries(root,payload/'client/optional-deps','requirements-runtime.txt','runtime')
    python='/usr/bin/python3' if platform.system()=='Linux' else sys.executable
    code="import sys;sys.path.insert(0,sys.argv[1]);from chroma.mcp_client import sdk_path;sdk_path();from mcp import Client;import importlib.metadata;assert importlib.metadata.version('mcp')=='2.3.0';assert importlib.metadata.version('cryptography')=='46.0.5'"
    subprocess.run([python,'-I','-B','-c',code,str(payload/'client')],check=True,timeout=30)
