"""TLS 1.3 over unchanged ChromaSpeechAI PRSM frames. All received bytes stay inert."""
from dataclasses import dataclass
from pathlib import Path
import hashlib,json,math,socket,sqlite3,ssl,struct,time,uuid
from .speech_wire.frame import Frame,FrameType
from .speech_wire.lan import receive_frame,send_frame
MAX_BYTES=1048576
CHUNK=32768
KINDS={"task","question","answer","status","data","partial","knowledge-reference"}
def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def strict_json(raw):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise ValueError("Duplicate field")
            d[k]=v
        return d
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError("Nonfinite JSON")))
def metadata(message_id,kind,payload):
    return {"v":1,"id":str(uuid.UUID(message_id)),"kind":kind,"total":len(payload),"sha256":hashlib.sha256(payload).hexdigest()}
def validate(meta):
    if not isinstance(meta,dict) or set(meta)!={"v","id","kind","total","sha256"}:raise ValueError("Metadata fields")
    if type(meta["v"]) is not int or meta["v"]!=1 or meta["kind"] not in KINDS:raise ValueError("Unsupported message")
    if type(meta["total"]) is not int or not 0<=meta["total"]<=MAX_BYTES:raise ValueError("Message size")
    if str(uuid.UUID(meta["id"]))!=meta["id"]:raise ValueError("Message ID")
    h=meta["sha256"]
    if not isinstance(h,str) or len(h)!=64 or any(c not in "0123456789abcdef" for c in h):raise ValueError("Digest")
def pack(meta,chunk):
    h=canonical(meta)
    return struct.pack(">H",len(h))+h+chunk
def unpack(raw):
    if len(raw)<2:raise ValueError("Missing metadata")
    n=struct.unpack(">H",raw[:2])[0]
    if n>512 or len(raw)<2+n:raise ValueError("Metadata limit")
    m=strict_json(raw[2:2+n]);validate(m)
    if canonical(m)!=raw[2:2+n]:raise ValueError("Noncanonical metadata")
    return m,raw[2+n:]
class DeadlineIO:
    def __init__(self,sock,deadline):self.sock=sock;self.deadline=deadline
    def remaining(self):
        value=self.deadline-time.monotonic()
        if value<=0:raise TimeoutError("Transfer deadline")
        self.sock.settimeout(value)
    def recv(self,size):self.remaining();return self.sock.recv(size)
    def sendall(self,data):self.remaining();return self.sock.sendall(data)
@dataclass(frozen=True)
class Credentials:
    certificate: Path
    private_key: Path
    # Mapping is supplied only after registry admission / explicit local peer approval.
    peers: dict
    def context(self,server):
        ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER if server else ssl.PROTOCOL_TLS_CLIENT)
        ctx.minimum_version=ssl.TLSVersion.TLSv1_3
        ctx.maximum_version=ssl.TLSVersion.TLSv1_3
        if not server:ctx.check_hostname=False # Peer is identified by an approved public-key/certificate pin.
        ctx.verify_mode=ssl.CERT_REQUIRED
        ctx.load_cert_chain(str(self.certificate),str(self.private_key))
        if not self.peers:raise PermissionError("No approved peers")
        from .speech_identity import certificate_identity
        for node_id,cert in self.peers.items():
            if certificate_identity(cert)[0]!=node_id:raise PermissionError("Peer node ID does not match certificate key")
            ctx.load_verify_locations(cafile=str(cert))
        ctx.set_alpn_protocols(["chromaspeech-prsm-v1"])
        return ctx
    def peer(self,sock):
        if sock.version()!="TLSv1.3" or sock.selected_alpn_protocol()!="chromaspeech-prsm-v1":raise PermissionError("TLS profile")
        actual=hashlib.sha256(sock.getpeercert(binary_form=True)).hexdigest()
        for node_id,path in self.peers.items():
            expected=hashlib.sha256(ssl.PEM_cert_to_DER_cert(Path(path).read_text())).hexdigest()
            if actual==expected:return node_id
        raise PermissionError("Peer certificate is not approved")
class Inbox:
    """SQLite transactions preserve acknowledged chunks and reject conflicting retries."""
    def __init__(self,path):
        self.db=sqlite3.connect(path,timeout=3)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS transfer(peer TEXT,id TEXT,meta BLOB,created REAL,PRIMARY KEY(peer,id));
        CREATE TABLE IF NOT EXISTS chunk(peer TEXT,id TEXT,idx INTEGER,body BLOB,PRIMARY KEY(peer,id,idx));
        CREATE TABLE IF NOT EXISTS message(peer TEXT,id TEXT,meta BLOB,body BLOB,PRIMARY KEY(peer,id));
        """)
    def close(self):self.db.close()
    def start(self,peer,meta):
        validate(meta);encoded=canonical(meta);mid=meta["id"]
        with self.db:
            row=self.db.execute("SELECT meta FROM message WHERE peer=? AND id=?",(peer,mid)).fetchone()
            if row:
                if row[0]!=encoded:raise ValueError("Conflicting completed message")
                return []
            row=self.db.execute("SELECT meta FROM transfer WHERE peer=? AND id=?",(peer,mid)).fetchone()
            if row and row[0]!=encoded:raise ValueError("Conflicting transfer")
            if not row:
                counts=self.db.execute("SELECT count(*) FROM transfer").fetchone()[0]
                used=self.db.execute("SELECT coalesce(sum(length(body)),0) FROM message").fetchone()[0]
                reserved=0
                for (raw,) in self.db.execute("SELECT meta FROM transfer"):reserved+=strict_json(raw)["total"]
                messages=self.db.execute("SELECT count(*) FROM message").fetchone()[0]
                peer_transfers=self.db.execute("SELECT count(*) FROM transfer WHERE peer=?",(peer,)).fetchone()[0]
                if counts>=32 or peer_transfers>=8 or messages>=4096 or used+reserved+meta["total"]>64*MAX_BYTES:raise ValueError("Inbox capacity")
                self.db.execute("INSERT INTO transfer VALUES(?,?,?,?)",(peer,mid,encoded,time.time()))
            got={r[0] for r in self.db.execute("SELECT idx FROM chunk WHERE peer=? AND id=?",(peer,mid))}
            return [i for i in range(max(1,math.ceil(meta["total"]/CHUNK))) if i not in got]
    def add(self,peer,meta,index,body):
        missing=self.start(peer,meta);mid=meta["id"];count=max(1,math.ceil(meta["total"]/CHUNK))
        if not 0<=index<count:raise ValueError("Fragment index")
        required=CHUNK if index<count-1 else meta["total"]-CHUNK*(count-1)
        if len(body)!=required:raise ValueError("Fragment length")
        with self.db:
            done=self.db.execute("SELECT body FROM message WHERE peer=? AND id=?",(peer,mid)).fetchone()
            if done:
                if done[0][index*CHUNK:(index+1)*CHUNK]!=body:raise ValueError("Conflicting completed fragment")
                return True
            row=self.db.execute("SELECT body FROM chunk WHERE peer=? AND id=? AND idx=?",(peer,mid,index)).fetchone()
            if row and row[0]!=body:raise ValueError("Conflicting fragment")
            if not row:self.db.execute("INSERT INTO chunk VALUES(?,?,?,?)",(peer,mid,index,body))
            chunks=self.db.execute("SELECT body FROM chunk WHERE peer=? AND id=? ORDER BY idx",(peer,mid)).fetchall()
            if len(chunks)==count:
                full=b"".join(r[0] for r in chunks)
                if hashlib.sha256(full).hexdigest()!=meta["sha256"]:raise ValueError("Content digest mismatch")
                self.db.execute("INSERT INTO message VALUES(?,?,?,?)",(peer,mid,canonical(meta),full))
                self.db.execute("DELETE FROM chunk WHERE peer=? AND id=?",(peer,mid))
                self.db.execute("DELETE FROM transfer WHERE peer=? AND id=?",(peer,mid))
                return True
        return False
def frame(meta,payload,kind=FrameType.DATA,index=0):
    return Frame(source=0,destination=0,sequence=index,message_id=int(uuid.UUID(meta["id"]))&0xffffffff,
                 payload=payload,frame_type=kind,fragment_index=index,fragment_count=max(1,math.ceil(meta["total"]/CHUNK)))
def send(host,port,credentials,message_id,kind,payload,timeout=10):
    if not isinstance(payload,bytes):raise TypeError("Payload must be bytes")
    meta=metadata(message_id,kind,payload);validate(meta)
    deadline=time.monotonic()+timeout
    ctx=credentials.context(False)
    with socket.create_connection((host,port),timeout=timeout) as raw,ctx.wrap_socket(raw,server_hostname=host) as sock:
        peer=credentials.peer(sock)
        sock=DeadlineIO(sock,deadline)
        send_frame(sock,frame(meta,canonical(meta),FrameType.SYNC))
        response=receive_frame(sock)
        if response is None or response.frame_type!=FrameType.ACK:raise ConnectionError("Missing transfer acknowledgement")
        reply=strict_json(response.payload)
        if set(reply)!={"id","missing"} or reply["id"]!=meta["id"]:raise ValueError("ACK identity")
        missing=reply["missing"];count=max(1,math.ceil(len(payload)/CHUNK))
        if not isinstance(missing,list) or len(missing)>count or any(type(i) is not int or not 0<=i<count for i in missing) or len(set(missing))!=len(missing):raise ValueError("ACK fragment map")
        for i in missing:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError("Transfer deadline")
            sock.sock.settimeout(remaining)
            send_frame(sock,frame(meta,pack(meta,payload[i*CHUNK:(i+1)*CHUNK]),index=i))
            ack=receive_frame(sock)
            if ack is None or ack.frame_type!=FrameType.ACK or strict_json(ack.payload)!={"id":meta["id"],"index":i}:raise ConnectionError("Fragment acknowledgement mismatch")
        return {"peer":peer,"message_id":message_id,"bytes":len(payload),"sent_fragments":len(missing)}
def receive_connection(raw,credentials,inbox,timeout=10):
    deadline=time.monotonic()+timeout
    raw.settimeout(timeout)
    with credentials.context(True).wrap_socket(raw,server_side=True) as sock:
        peer=credentials.peer(sock);sock=DeadlineIO(sock,deadline);first=receive_frame(sock)
        if first is None or first.frame_type!=FrameType.SYNC:raise ValueError("Transfer must start with SYNC")
        if len(first.payload)>512 or first.flags!=0 or first.source!=0 or first.destination!=0:raise ValueError("Unsupported PRSM routing or flags")
        meta=strict_json(first.payload);validate(meta)
        if first.message_id!=int(uuid.UUID(meta["id"]))&0xffffffff or first.fragment_index!=0 or first.sequence!=0 or first.fragment_count!=max(1,math.ceil(meta["total"]/CHUNK)):raise ValueError("SYNC correlation")
        missing=inbox.start(peer,meta)
        send_frame(sock,frame(meta,canonical({"id":meta["id"],"missing":missing}),FrameType.ACK))
        for expected in missing:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError("Transfer deadline")
            sock.sock.settimeout(remaining)
            f=receive_frame(sock)
            if f is None or f.frame_type!=FrameType.DATA:raise ValueError("Expected data fragment")
            m,body=unpack(f.payload)
            if f.flags!=0 or f.source!=0 or f.destination!=0 or m!=meta or f.fragment_index!=expected or f.sequence!=expected or f.fragment_count!=max(1,math.ceil(meta["total"]/CHUNK)) or f.message_id!=int(uuid.UUID(meta["id"]))&0xffffffff:raise ValueError("Fragment correlation")
            inbox.add(peer,meta,expected,body)
            send_frame(sock,frame(meta,canonical({"id":meta["id"],"index":expected}),FrameType.ACK,index=expected))
        return {"peer":peer,"message_id":meta["id"],"status":"RECEIVED_INERT"}
