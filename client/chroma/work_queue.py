"""Durable queue of OWNER-created fixed AI operations; never a remote code queue."""
from pathlib import Path
import sqlite3,json,time,uuid,hashlib,os
from .collaboration import Collaboration
from .native_ai import infer
from .ai_provider import selection,validate_selection,request_digest,selected_inference

class WorkQueue:
    def __init__(self,path):
        path=Path(path)
        self.path=path
        if path.is_symlink():raise ValueError("Queue cannot be a symlink")
        if not path.exists():
            fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
        self.db=sqlite3.connect(path,timeout=2)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS job(id TEXT PRIMARY KEY,created REAL NOT NULL,request TEXT NOT NULL,status TEXT NOT NULL,lease REAL NOT NULL DEFAULT 0,claim TEXT NOT NULL DEFAULT '',result TEXT,error TEXT NOT NULL DEFAULT '')")
        self.db.commit()
    def close(self):self.db.close()
    def enqueue(self,namespace,key,source,instruction,*,network_approved=False,ai_approved=False,ai_provider="bundled-cpu",ai_model=None,job_id=None):
        if network_approved is not True or ai_approved is not True:raise PermissionError("Separate network and local AI consent required")
        if not all(isinstance(x,str) and 0<len(x)<=128 for x in (namespace,key)):raise ValueError("Lookup bounds")
        if not isinstance(source,str) or len(source.encode())>8192:raise ValueError("Source limit 8 KiB")
        if not isinstance(instruction,str) or not 0<len(instruction)<=2000:raise ValueError("Instruction bounds")
        request={"namespace":namespace,"key":key,"source":source,"instruction":instruction,
                 "sourceHash":hashlib.sha256(source.encode()).hexdigest(),"networkApproved":True,"aiApproved":True}
        choice=selection(ai_provider,ai_model)
        if choice is not None:
            request["aiProvider"]=choice
            request["approvedRequestHash"]=request_digest(request)
        jid=str(uuid.uuid4()) if job_id is None else str(uuid.UUID(job_id))
        if job_id is not None and jid!=job_id:raise ValueError("Canonical local job ID required")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            existing=self.db.execute("SELECT request FROM job WHERE id=?",(jid,)).fetchone()
            if existing:
                if existing[0]!=json.dumps(request):raise ValueError("Conflicting local job identity")
                return jid
            if self.db.execute("SELECT COUNT(*) FROM job").fetchone()[0]>=32:raise ValueError("Queue capacity 32; archive reviewed results explicitly")
            self.db.execute("INSERT INTO job(id,created,request,status) VALUES(?,?,?,?)",(jid,time.time(),json.dumps(request),"PROVIDER_WAITING" if choice else "WAITING"))
        return jid
    def read(self,jid):
        row=self.db.execute("SELECT id,status,result,error FROM job WHERE id=?",(jid,)).fetchone()
        if not row:raise KeyError("Unknown local job")
        return {"id":row[0],"status":row[1],"result":json.loads(row[2]) if row[2] else None,"error":row[3]}
    def cancel(self,jid):
        """Cancel pending/controlled work; legacy manual running workers are unchanged."""
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            row=self.db.execute("SELECT status FROM job WHERE id=?",(jid,)).fetchone()
            if not row:raise KeyError("Unknown local job")
            if row[0] in ('RUNNING','PROVIDER_RUNNING'):
                raise PermissionError('Stop the legacy manual worker before cancelling its job')
            if row[0] in ('WAITING','PROVIDER_WAITING') or row[0].startswith('CONTROLLED_'):
                self.db.execute("UPDATE job SET status='FAILED',error='Cancelled by owner',lease=0,claim=? WHERE id=?",(str(uuid.uuid4()),jid))
        return self.read(jid)
    def step(self,connection,state,*,execution=None):
        if execution is None:return self._step(connection,state)
        from .worker_resources import queue_lock
        with queue_lock(self.path) as locked:
            if not locked:return None
            # The OS lock is held through process termination and durable completion.
            # Expiry alone is never authority to repeat controlled inference.
            with self.db:
                self.db.execute("BEGIN IMMEDIATE")
                for jid,raw,status in self.db.execute("SELECT id,request,status FROM job WHERE status LIKE 'CONTROLLED_%'").fetchall():
                    if status not in ('CONTROLLED_STARTING','CONTROLLED_PROVIDER_STARTING'):
                        self.db.execute("UPDATE job SET status='FAILED',lease=0,error='Interrupted inference; outcome uncertain, automatic retry disabled' WHERE id=?",(jid,))
                    else:
                        pending='PROVIDER_WAITING' if status=='CONTROLLED_PROVIDER_STARTING' else 'WAITING'
                        self.db.execute("UPDATE job SET status=?,lease=0,error='Recovered before inference' WHERE id=?",(pending,jid))
            execution.check()
            return self._step(connection,state,execution=execution)
    def _step(self,connection,state,execution=None):
        now=time.time()
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if execution is None:
                row=self.db.execute("SELECT id,request,status FROM job WHERE status IN ('WAITING','PROVIDER_WAITING') OR (status IN ('RUNNING','PROVIDER_RUNNING') AND lease<?) ORDER BY created LIMIT 1",(now,)).fetchone()
            else:
                # Explicit external providers remain queued for their manual path;
                # do not let one unsupported provider starve approved bundled jobs.
                self.db.execute("UPDATE job SET error='Controlled Ollama resource profile unsupported; manual path unchanged' WHERE status='PROVIDER_WAITING' AND error<>'Controlled Ollama resource profile unsupported; manual path unchanged'")
                row=self.db.execute("SELECT id,request,status FROM job WHERE status='WAITING' ORDER BY created LIMIT 1").fetchone()
            if not row:return None
            jid,raw,old_status=row;provider_job=old_status.startswith("PROVIDER_");claim=str(uuid.uuid4())
            pending="PROVIDER_WAITING" if provider_job else "WAITING"
            running=("PROVIDER_RUNNING" if provider_job else "RUNNING") if execution is None else "CONTROLLED_STARTING"
            self.db.execute("UPDATE job SET status=?,lease=?,claim=? WHERE id=?",(running,now+240,claim,jid))
        waiting_for_network=False;inference_started=False
        if execution is not None:
            execution.check_claim=lambda: self.db.execute("SELECT 1 FROM job WHERE id=? AND claim=? AND status LIKE 'CONTROLLED_%'",(jid,claim)).fetchone() is not None
        try:
            request=json.loads(raw)
            if request.get("networkApproved") is not True or request.get("aiApproved") is not True:raise PermissionError("Stored consent missing")
            if hashlib.sha256(request["source"].encode()).hexdigest()!=request["sourceHash"]:raise ValueError("Stored input changed")
            choice=None
            if "aiProvider" in request or "approvedRequestHash" in request:
                if "aiProvider" not in request or request["aiProvider"] is None:raise ValueError("Stored AI provider missing")
                choice=validate_selection(request["aiProvider"])
                approved=request.get("approvedRequestHash")
                if approved!=request_digest({k:v for k,v in request.items() if k!="approvedRequestHash"}):
                    raise ValueError("Approved AI request changed")
            if (choice is not None)!=provider_job:raise ValueError("Provider job status mismatch")
            if execution is not None:execution.supports(choice)
            collab=Collaboration(connection,state)
            waiting_for_network=True
            plan=collab.prepare(request["namespace"],request["key"],request["instruction"],approved=True)
            waiting_for_network=False
            if execution is not None:execution.check()
            if plan["status"] in {"UNKNOWN","DORMANT","STOPPED"}:
                self._finish(jid,claim,pending,None,plan["status"]);return self.read(jid)
            if plan["status"]=="REUSE_AVAILABLE":
                result={"kind":"VERIFIED_REFERENCE_AVAILABLE","plan":plan,"applied":False}
            else:
                if not state.can_run("network-dependent"):
                    self._finish(jid,claim,pending,None,"Balance expired before local work");return self.read(jid)
                # Fixed bounded provider adapters; no tools, auto-apply or publication.
                if execution is None:
                    proposal=selected_inference(request["source"],request["instruction"],choice,bundled=infer,timeout=90)
                else:
                    execution.check()
                    with self.db:
                        self.db.execute("UPDATE job SET status='CONTROLLED_INFERENCE' WHERE id=? AND claim=?",(jid,claim))
                    execution.check();inference_started=True
                    proposal=execution.inference(request["source"],request["instruction"],infer)
                    execution.check()
                result={"kind":"LOCAL_AI_PROPOSAL","plan":plan,"sourceHash":request["sourceHash"],
                        "proposal":proposal.source.decode("utf-8"),"provider":proposal.provider,
                        "seconds":proposal.seconds,"applied":False,"scientificallyVerified":False}
            if choice is not None:result["aiProvider"]=choice
            self._finish(jid,claim,"AWAITING_REVIEW",result,"")
        except Exception as error:
            # Connection uncertainty preserves the request for automatic later reconciliation.
            from .worker_resources import WorkerBlocked,WorkerCancelled
            if execution is not None and not inference_started and isinstance(error,(WorkerBlocked,WorkerCancelled)):
                self._finish(jid,claim,pending,None,str(error)[:1000])
            elif waiting_for_network:
                state.unavailable(str(error))
                self._finish(jid,claim,pending,None,str(error)[:1000])
            else:self._finish(jid,claim,"FAILED",None,str(error)[:1000])
        return self.read(jid)
    def _finish(self,jid,claim,status,result,error):
        with self.db:self.db.execute("UPDATE job SET status=?,lease=0,result=?,error=? WHERE id=? AND claim=?",
                                    (status,json.dumps(result) if result is not None else None,error,jid,claim))
