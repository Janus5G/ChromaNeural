"""Background status controller reusing the authoritative v0.2 ledger client."""
import threading,time,copy,queue
from collections import deque
from .network_state import NetworkState
from . import icp_client
class Participation:
    def __init__(self,settings,provider=None,interval=30):
        self.settings=settings;self.provider=provider or icp_client.call;self.interval=max(1,interval)
        self.state=NetworkState(settings.directory/"balance-cache.json")
        self.events=deque(maxlen=80);self.results=queue.Queue();self.wake=threading.Event();self.closed=threading.Event()
        self.publication_results=queue.Queue()
        self.worker_results=queue.Queue(maxsize=32);self.worker_wake=threading.Event()
        self.worker_thread=None;self.worker_busy=False;self.worker_status="IDLE"
        self.generation=0;self.busy=False;self.failures=0;self.thread=None;self.last_refresh=None
        self.configure(settings.value,persist=False)
    def event(self,text):
        if self.events and self.events[-1][1]==text:return
        self.events.append((time.strftime("%H:%M:%S"),text))
    def configure(self,value,persist=True,reset_connection=False):
        previous=getattr(self,"value",{}).get("connection")
        if persist:self.settings.save(value)
        if reset_connection or (previous is not None and previous!=value["connection"]):
            self.state=NetworkState(self.settings.directory/"balance-cache.json");self.last_refresh=None
        self.value=copy.deepcopy(self.settings.value if persist else value)
        self.generation+=1;self.failures=0
        self.state.network_enabled=self.value["participation"] and not self.value["paused"]
        # Saved resource preferences never grant execution; aggregate quota backend is still gated.
        self.state.sharing_enabled=False
        self.state.unavailable("Afventer en bekræftet forbindelse")
        self.event("Deltagelse sat på pause" if self.value["paused"] else "Indstillinger opdateret")
        self.wake.set();self.worker_wake.set()
    def start(self):
        if self.thread or self.closed.is_set():return
        self.thread=threading.Thread(target=self._loop,name="chroma-status",daemon=True);self.thread.start()
        self.worker_thread=threading.Thread(target=self._worker_loop,name="chroma-ai-worker",daemon=True);self.worker_thread.start()
    def _worker_event(self,item):
        if item==getattr(self,'_last_worker_event',None):return
        self._last_worker_event=item
        try:self.worker_results.put_nowait(item)
        except queue.Full:
            try:self.worker_results.get_nowait()
            except queue.Empty:pass
            self.worker_results.put_nowait(item)
    def _worker_loop(self):
        # Separate from status/publication: fixed local inference never blocks the UI.
        from .work_queue import WorkQueue
        from .worker_resources import WorkerResources
        while not self.closed.is_set():
            self.worker_wake.clear()
            generation=self.generation;selected=copy.deepcopy(self.value);state=self.state
            active=lambda: (not self.closed.is_set() and generation==self.generation
                            and self.value['participation'] and not self.value['paused'])
            db=self.settings.directory/'work-queue.db'
            if active() and selected['connection'] and db.is_file():
                work=None
                try:
                    execution=WorkerResources(selected['resources'],active);execution.check()
                    work=WorkQueue(db);self.worker_busy=True
                    result=work.step(selected['connection'],state,execution=execution)
                    self.worker_status=result['status'] if result else 'IDLE'
                    if result:self._worker_event((generation,result['id'],result['status'],result['error']))
                except Exception as error:
                    self.worker_status='BLOCKED'
                    self._worker_event((generation,'','BLOCKED',str(error)[:300]))
                finally:
                    self.worker_busy=False
                    if work is not None:work.close()
            self.worker_wake.wait(1)
    def _loop(self):
        while not self.closed.is_set():
            self.wake.clear()
            generation=self.generation;selected=self.value;path=selected["connection"]
            enabled=selected["participation"] and not selected["paused"]
            if enabled and path and generation==self.generation and not self.closed.is_set():
                self.busy=True
                try:
                    self.results.put((generation,True,self.provider(path,"balance")))
                    self.publication_tick(path,generation)
                except Exception as e:self.results.put((generation,False,str(e)))
                finally:self.busy=False
            delay=min(300,self.interval*(2**min(self.failures,3)))
            self.wake.wait(delay)
    def publication_tick(self,path,generation):
        """Only explicitly approved local queue entries; never automatic private upload."""
        db=self.settings.directory/"work-queue.db"
        if not db.exists():return
        from .publication import PublicationQueue
        queue=PublicationQueue(db)
        try:
            active=lambda: (not self.closed.is_set() and generation==self.generation
                            and self.value["participation"] and not self.value["paused"])
            result=queue.step(path,self.state,allowed=active,provider=self.provider)
            if result:self.publication_results.put((generation,result["status"]))
        except (ValueError,PermissionError,OSError):
            self.publication_results.put((generation,"BLOCKED"))
        finally:queue.close()
    def drain(self):
        while True:
            try:generation,jid,status,error=self.worker_results.get_nowait()
            except queue.Empty:break
            if generation==self.generation and not self.closed.is_set():
                self.event("AI worker · "+status+(" · "+error if error else ""))
        while True:
            try:generation,status=self.publication_results.get_nowait()
            except queue.Empty:break
            if generation==self.generation and not self.closed.is_set():
                labels={"COMPLETE":"Handling bekræftet","WAITING":"Afventer godkendelse/forbindelse","PENDING":"Godkendt handling afventer","REJECTED":"Afvist","REVOKED":"Delingssamtykke tilbagekaldt","BLOCKED":"Afventer gyldig lokal publiceringskonfiguration"}
                self.event("ChromaNeuroAI · Publicering: "+labels.get(status,status))
        while True:
            try:generation,ok,data=self.results.get_nowait()
            except queue.Empty:break
            if self.closed.is_set() or generation!=self.generation or not self.state.network_enabled:continue
            try:
                if not ok:raise RuntimeError(data)
                self.state.update(data);self.failures=0;self.last_refresh=time.strftime("%H:%M:%S")
                self.event({"READY":"Netværksbalance bekræftet","DORMANT":"AI-netværksarbejde i dvale","UNKNOWN":"Afventer opdateret netværkspolitik"}[self.state.status()])
            except Exception as e:
                self.failures+=1;self.state.unavailable(str(e));self.event("Forbindelsen kunne ikke bekræftes. Prøver igen.")
    def pause(self):
        v=copy.deepcopy(self.value);v["paused"]=True;self.configure(v)
    def resume(self):
        v=copy.deepcopy(self.value);v["participation"]=True;v["paused"]=False;self.configure(v)
    def stop(self):
        v=copy.deepcopy(self.value);v["participation"]=False;v["paused"]=False;self.configure(v);self.event("Deltagelse stoppet")
    def close(self):
        self.closed.set();self.generation+=1;self.state.network_enabled=False;self.state.sharing_enabled=False;self.wake.set();self.worker_wake.set()
        if self.worker_thread and threading.current_thread() is not self.worker_thread:self.worker_thread.join(timeout=5)
    def status(self):
        if not self.value["onboarded"]:return "SETUP"
        if self.value["paused"]:return "PAUSED"
        if not self.value["participation"]:return "STOPPED"
        if not self.value["connection"]:return "UNCONNECTED"
        return self.state.status()
    def view(self):
        self.drain();snapshot=self.state.snapshot
        result={"status":self.status(),"points":None,"spent":None,"balance":None,"ratio":None,
                "data_bytes":None,"cpu_seconds":None,"ram_byte_seconds":None,"gpu_seconds":None,
                "consumed_bytes":None,"bootstrap":None,"fresh":self.state.status() in ("READY","DORMANT"),
                "sharing_active":False,"active_jobs":int(self.worker_busy),"worker_status":self.worker_status,"last_refresh":self.last_refresh}
        if snapshot:
            a=snapshot["account"];m=a["contribution"]
            result.update(points=int(a["earned"])/1e6,spent=int(a["spent"])/1e6,balance=int(snapshot["available"])/1e6,
              ratio=int(snapshot["policy"]["ratioBps"])/10000,data_bytes=int(m["dataBytes"]),cpu_seconds=int(m["cpuMicros"])/1e6,
              ram_byte_seconds=int(m["ramByteMicros"])/1e6,gpu_seconds=int(m["gpuMicros"])/1e6,
              consumed_bytes=int(a["consumedBytes"]),bootstrap=int(a["bootstrap"])/1e6)
        return result
