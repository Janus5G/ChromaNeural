"""Consent-bound, durable publication of inert peer results. No remote execution."""
from pathlib import Path
import hashlib,json,time,uuid,sqlite3,base64
from .work_queue import WorkQueue
from .speech import Inbox,MAX_BYTES
from . import icp_client

def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True)
def strict_json(text):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError("Duplicate JSON key")
            out[k]=v
        return out
    return json.loads(text,object_pairs_hook=pairs)
FIELDS={"schema","taskId","namespace","logicalKey","version","payloadHash","payloadBytes",
        "payloadLocator","mediaType","criteria","evidence","complete","contributorNodeId","finalizerNodeId"}
def validate(spec):
    if not isinstance(spec,dict) or set(spec)!=FIELDS:raise ValueError("Publication manifest fields")
    if type(spec["schema"]) is not int or spec["schema"]!=1 or spec["complete"] is not True:
        raise ValueError("Only complete reviewed results")
    for k in ("taskId","namespace","logicalKey","payloadLocator","mediaType"):
        if not isinstance(spec[k],str) or not 0<len(spec[k].encode())<=128:raise ValueError("Manifest text bounds: "+k)
    for k in ("criteria","evidence"):
        if not isinstance(spec[k],str) or not 0<len(spec[k].strip()) or len(spec[k].encode())>4096:
            raise ValueError("Documented criteria and evidence required")
    for k in ("payloadHash","contributorNodeId","finalizerNodeId"):
        if not isinstance(spec[k],str) or len(spec[k])!=64 or any(c not in "0123456789abcdef" for c in spec[k]):raise ValueError("Manifest hash")
    if spec["finalizerNodeId"]==spec["contributorNodeId"]:raise ValueError("Independent finalizer required")
    if type(spec["payloadBytes"]) is not int or not 1<=spec["payloadBytes"]<=MAX_BYTES:raise ValueError("Payload size")
    if spec["version"]!="1":raise ValueError("This first-publication adapter supports version 1 only")
    return json.loads(canonical(spec))
def binding(config):
    c=strict_json(Path(config).read_text(encoding="utf-8"))
    from urllib.parse import urlparse
    u=urlparse(c["host"])
    if u.hostname not in ("127.0.0.1","localhost","::1") or u.username or u.password:
        raise PermissionError("Publication candidate is LOCAL ONLY")
    if c.get("networkEnabled") is not True or c.get("allowLocalTestRoot") is not True or c.get("publicationEnabled") is not True:
        raise PermissionError("Explicit local publication opt-in required")
    meta=strict_json((Path(c["identityDirectory"])/"public_key.json").read_text())
    raw=base64.b64decode(meta["publicKeyBase64"],validate=True)
    if len(raw)!=32 or digest(raw)!=meta["nodeId"]:raise ValueError("Node public identity mismatch")
    return digest(canonical({"host":c["host"],"canisterId":c["canisterId"],"nodeId":meta["nodeId"]}).encode())
def operation_id(request,target):
    return digest(canonical({"binding":target,"spec":request["spec"],"action":request["action"],"method":request["method"],"maxReward":request["maxReward"]}).encode())

class PublicationQueue:
    """Uses the existing WorkQueue database; adds no executable work or points store."""
    def __init__(self,path):
        self.queue=WorkQueue(path);self.db=self.queue.db
        self.db.execute("""CREATE TABLE IF NOT EXISTS publication(
          id TEXT PRIMARY KEY, request TEXT NOT NULL, binding TEXT NOT NULL,
          approved INTEGER NOT NULL, status TEXT NOT NULL, phase TEXT NOT NULL,
          claim TEXT NOT NULL DEFAULT '', lease REAL NOT NULL DEFAULT 0,
          result TEXT, error TEXT NOT NULL DEFAULT '', updated REAL NOT NULL)""")
        self.db.commit()
    def close(self):self.queue.close()
    def enqueue(self,config,spec,inbox,peer,message_id,*,action="submit",method="",max_reward=0,approved=False):
        if approved is not True:raise PermissionError("Explicit result/role approval required")
        spec=validate(spec)
        if action not in ("submit","commission","attest"):raise ValueError("Publication action")
        if action=="attest" and (not isinstance(method,str) or not 1<=len(method)<=80):
            raise ValueError("Independent verification method required")
        if action=="commission" and (type(max_reward) is not int or not 1<=max_reward<=100000000):
            raise ValueError("Administrator must approve reward cap")
        if Path(inbox).is_symlink():raise ValueError("Inbox symlink")
        inbox=Path(inbox).resolve(strict=True)
        request={"spec":spec,"inbox":str(inbox),"peer":peer,"messageId":message_id,
                 "action":action,"method":method,"maxReward":max_reward}
        self._payload(request)
        target=binding(config)
        # Same target/action/manifest has one durable operation, even when delivered again.
        key=operation_id(request,target)
        encoded=canonical(request)
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            old=self.db.execute("SELECT request,approved FROM publication WHERE id=?",(key,)).fetchone()
            if old:
                if canonical(strict_json(old[0])["spec"])!=canonical(spec):raise ValueError("Operation conflict")
                if not old[1]:raise PermissionError("Consent revoked; explicit approve operation required")
                return key
            if self.db.execute("SELECT COUNT(*) FROM publication").fetchone()[0]>=128:raise ValueError("Publication queue capacity")
            self.db.execute("INSERT INTO publication(id,request,binding,approved,status,phase,updated) VALUES(?,?,?,?,?,?,?)",
                            (key,encoded,target,1,"PENDING",action,time.time()))
        return key
    def _payload(self,r):
        # Read only the explicitly selected completed message; never scan projects.
        p=Path(r["inbox"])
        if p.is_symlink() or not p.is_file():raise ValueError("Existing regular inbox required")
        db=sqlite3.connect(p.as_uri()+"?mode=ro",uri=True,timeout=2)
        try:row=db.execute("SELECT body FROM message WHERE peer=? AND id=?",(r["peer"],r["messageId"])).fetchone()
        finally:db.close()
        if not row or not isinstance(row[0],bytes):raise ValueError("Completed peer message missing")
        body=row[0];s=r["spec"]
        if len(body)!=s["payloadBytes"] or digest(body)!=s["payloadHash"]:raise ValueError("Approved payload changed")
        return body
    def read(self,key):
        row=self.db.execute("SELECT id,status,phase,approved,result,error FROM publication WHERE id=?",(key,)).fetchone()
        if not row:raise KeyError("Unknown publication")
        return dict(zip(("id","status","phase","approved","result","error"),row))|{"result":json.loads(row[4]) if row[4] else None}
    def consent(self,key,approved,config=None):
        if type(approved) is not bool:raise ValueError("Consent boolean")
        if approved:
            row=self.db.execute("SELECT request,binding FROM publication WHERE id=?",(key,)).fetchone()
            if not row or config is None or binding(config)!=row[1]:raise PermissionError("Reapprove exact target")
            self._payload(strict_json(row[0]))
        with self.db:
            self.db.execute("UPDATE publication SET approved=?,status=?,updated=? WHERE id=?",
                            (int(approved),"PENDING" if approved else "REVOKED",time.time(),key))
    def summary(self):
        return dict(self.db.execute("SELECT status,COUNT(*) FROM publication GROUP BY status").fetchall())
    def step(self,config,state,*,allowed=lambda:True,provider=None):
        provider=provider or icp_client.call
        if not allowed() or not state.network_enabled:return None
        if not self.db.execute("SELECT 1 FROM publication WHERE approved=1 AND status NOT IN ('COMPLETE','REJECTED','REVOKED') LIMIT 1").fetchone():return None
        target=binding(config)
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            row=self.db.execute("""SELECT id,request,phase,status FROM publication
                WHERE approved=1 AND binding=? AND status NOT IN ('COMPLETE','REJECTED','REVOKED')
                AND lease<? ORDER BY updated LIMIT 1""",(target,time.time())).fetchone()
            if not row:return None
            key,raw,phase,status=row;claim=str(uuid.uuid4())
            self.db.execute("UPDATE publication SET claim=?,lease=? WHERE id=?",(claim,time.time()+90,key))
        def permitted():
            current=self.db.execute("SELECT approved,claim FROM publication WHERE id=?",(key,)).fetchone()
            return allowed() and state.network_enabled and current and current[0] and current[1]==claim
        def finish(status,next_phase=phase,result=None,error=""):
            with self.db:
                self.db.execute("""UPDATE publication SET status=CASE WHEN approved=0 THEN 'REVOKED' ELSE ? END,
                    phase=?,result=?,error=?,lease=0,updated=? WHERE id=? AND claim=?""",
                    (status,next_phase,canonical(result) if result is not None else None,error[:800],time.time(),key,claim))
        try:
            req=strict_json(raw)
            if operation_id(req,target)!=key:raise ValueError("Approved request changed; new consent required")
            validate(req["spec"]);self._payload(req)
            if not permitted():finish("WAITING");return self.read(key)
            snap=provider(config,"balance");state.update(snap)
            # Already approved contributions may recover balance in DORMANT; UNKNOWN stops.
            if state.status() not in ("READY","DORMANT") or not permitted():
                finish("WAITING",error="Paused or balance unavailable");return self.read(key)
            if phase in ("await_verified","verify_unknown"):
                result=provider(config,"publication_status",spec=req["spec"])
                if result["verified"]:finish("COMPLETE",result=result)
                else:finish("WAITING",error="Awaiting authorized external verification")
                return self.read(key)
            if not permitted():finish("WAITING");return self.read(key)
            # Persist ambiguity BEFORE sending. A lost verification response must not
            # blindly append another event or re-verify a later contested record.
            if phase=="verify":
                with self.db:self.db.execute("UPDATE publication SET phase='verify_unknown' WHERE id=? AND claim=?",(key,claim))
            result=provider(config,"publication_"+phase,spec=req["spec"],method=req["method"],maxReward=req["maxReward"],approved=True)
            if result.get("error"):finish("REJECTED",result=result,error=result["error"])
            elif phase=="submit":finish("COMPLETE" if result.get("verified") else "WAITING","await_verified",result)
            elif phase=="commission":finish("COMPLETE",result=result)
            elif phase=="attest":
                if int(result["credited"])>0:
                    finish("PENDING" if result["finalizeAllowed"] else "COMPLETE","verify" if result["finalizeAllowed"] else "attest",result)
                else:finish("WAITING","attest",result)
            else:finish("COMPLETE",result=result)
        except Exception as e:
            state.unavailable(str(e))
            latest=self.db.execute("SELECT phase FROM publication WHERE id=?",(key,)).fetchone()[0]
            finish("WAITING",latest,error=str(e))
        return self.read(key)
