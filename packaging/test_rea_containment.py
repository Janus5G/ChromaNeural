"""Controlled Linux containment acceptance; maximum 64 MiB/8 tasks/25% CPU."""
import json,os,sys,time,subprocess,tempfile,uuid,errno
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'client'))
from chroma.rea_isolation import Limits,service_command,verify_cgroup,control_environment,stop
from chroma.ai_provider import selected_inference
LIMIT=Limits(memory=64*1024*1024,cpu_percent=25,tasks=8,wall_seconds=4)

def fixture(mode):
    limits=verify_cgroup(LIMIT)
    group=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip()[3:].lstrip('/')
    if mode=='memory':
        child=os.fork()
        if child==0:
            time.sleep(30);os._exit(0)
        print(json.dumps({'limits':limits,'child':child}),flush=True)
        data=bytearray(96*1024*1024) # OOM group kills BOTH processes, budget 64 MiB.
        raise AssertionError('memory budget not enforced')
    if mode=='cpu':
        start=time.monotonic()
        children=[]
        for _ in range(2):
            child=os.fork()
            if child==0:
                until=time.monotonic()+2
                while time.monotonic()<until: pass
                os._exit(0)
            children.append(child)
        for child in children:os.waitpid(child,0)
        stat=dict(line.split() for line in (group/'cpu.stat').read_text().splitlines())
        print(json.dumps({'limits':limits,'throttled':int(stat['nr_throttled']),
                         'cpu_usec':int(stat['usage_usec']),'wall':time.monotonic()-start}))
    if mode=='tasks':
        children=[];blocked=False
        try:
            for _ in range(10):
                try:child=os.fork()
                except OSError as e:
                    assert e.errno==errno.EAGAIN;blocked=True;break
                if child==0:time.sleep(20);os._exit(0)
                children.append(child)
            assert blocked
            print(json.dumps({'limits':limits,'fork_blocked':blocked,'children':len(children),
                              'events':(group/'pids.events').read_text()}))
        finally:
            for child in children:
                os.kill(child,9);os.waitpid(child,0)
    if mode=='wall':
        child=os.fork()
        if child==0:time.sleep(30);os._exit(0)
        print(json.dumps({'limits':limits,'child':child}),flush=True)
        time.sleep(30)

def run():
    results={}
    for mode in ('memory','cpu','tasks','wall'):
        unit='chromaneural-rea-'+uuid.uuid4().hex+'.service'
        with tempfile.TemporaryDirectory(prefix='chroma-rea-resource-') as tmp:
            cmd=service_command(unit,tmp,[sys.executable,'-B',str(Path(__file__).resolve()),'--fixture',mode],LIMIT)
            cmd.remove('--collect') # Retain failure result for observation, then clear only this unit.
            started=time.monotonic()
            try:
                p=subprocess.run(cmd,capture_output=True,text=True,env=control_environment(),timeout=10)
                state=subprocess.run(['/usr/bin/systemctl','--user','show',unit,'-p','Result','-p','MemoryPeak','-p','TasksCurrent'],
                     capture_output=True,text=True,env=control_environment(),timeout=3).stdout
                data=json.loads(p.stdout)
                if mode=='memory':assert p.returncode and 'Result=oom-kill' in state,state
                if mode=='cpu':assert p.returncode==0 and data['throttled']>0
                if mode=='tasks':assert p.returncode==0 and data['fork_blocked']
                if mode=='wall':assert p.returncode and 'Result=timeout' in state,state
                if mode in ('memory','wall'):
                    deadline=time.monotonic()+2
                    while Path('/proc',str(data['child'])).exists() and time.monotonic()<deadline:time.sleep(.05)
                    assert not Path('/proc',str(data['child'])).exists(),'child process survived'
                results[mode]={'status':'PASS','details':data,'unit_result':state.strip(),'elapsed':round(time.monotonic()-started,2)}
            finally:
                stop(unit)
                subprocess.run(['/usr/bin/systemctl','--user','reset-failed',unit],env=control_environment(),
                               stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3)
            assert selected_inference('fixture','unchanged',None,bundled=lambda *a,**k:'core-ok')=='core-ok'
    results['core_after_exhaustion']='PASS'
    print(json.dumps(results,indent=2))

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--fixture':fixture(sys.argv[2])
    else:run()