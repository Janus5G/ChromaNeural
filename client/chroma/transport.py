"""CNRB v1: bounded raw-byte container; peer-channel HMAC, never an II credential.
No compression, automatic extraction, execution, or filename-based routing.
"""
import hashlib,hmac,json,struct
MAX=1024*1024
CHUNK=32768
HEADER=struct.Struct(">4sBII")
def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")
def keycheck(key):
    if not isinstance(key,bytes) or len(key)!=32: raise ValueError("A separately provisioned 32-byte peer-channel key is required")
def pack(data,key,kind="raw"):
    keycheck(key)
    if not isinstance(data,bytes) or len(data)>MAX: raise ValueError("Oversize")
    if kind not in ("raw","cpl","cpa","prisme-asm","optb"): raise ValueError("Unknown format")
    meta=canonical({"format":kind,"length":len(data),"sha256":hashlib.sha256(data).hexdigest()})
    body=HEADER.pack(b"CNRB",1,len(meta),len(data))+meta+data
    return body+hmac.digest(key,body,"sha256")
def unpack(blob,key):
    keycheck(key)
    if len(blob)>MAX+4096 or len(blob)<HEADER.size+32: raise ValueError("Size")
    magic,version,mlen,dlen=HEADER.unpack_from(blob)
    if magic!=b"CNRB" or version!=1 or not 1<=mlen<=1024 or dlen>MAX: raise ValueError("Header")
    if len(blob)!=HEADER.size+mlen+dlen+32: raise ValueError("Length or trailing bytes")
    body=blob[:-32]
    if not hmac.compare_digest(hmac.digest(key,body,"sha256"),blob[-32:]): raise ValueError("Authentication")
    raw=blob[HEADER.size:HEADER.size+mlen]
    meta=json.loads(raw)
    if canonical(meta)!=raw or set(meta)!={"format","length","sha256"}: raise ValueError("Noncanonical metadata")
    data=blob[HEADER.size+mlen:-32]
    if type(meta["length"]) is not int or meta["length"]!=len(data) or meta["sha256"]!=hashlib.sha256(data).hexdigest(): raise ValueError("Integrity")
    if meta["format"] not in ("raw","cpl","cpa","prisme-asm","optb"): raise ValueError("Format")
    return data,meta
class Receiver:
    """In-memory resumable quarantine. Restart persistence is explicit through snapshot."""
    def __init__(self,size,digest):
        if type(size) is not int or not 0<size<=MAX+4096: raise ValueError("Size")
        if len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest): raise ValueError("Digest")
        self.size=size;self.digest=digest;self.data=bytearray()
    @property
    def cursor(self): return len(self.data)
    def append(self,offset,data):
        if type(offset) is not int or offset<0 or not isinstance(data,bytes) or not 0<len(data)<=CHUNK: raise ValueError("Chunk")
        if offset<len(self.data) and bytes(self.data[offset:offset+len(data)])==data: return self.cursor
        if offset!=len(self.data) or offset+len(data)>self.size: raise ValueError("Cursor")
        self.data.extend(data);return self.cursor
    def finish(self,key):
        if len(self.data)!=self.size or hashlib.sha256(self.data).hexdigest()!=self.digest: raise ValueError("Incomplete/corrupt")
        return unpack(bytes(self.data),key)
    def snapshot(self): return {"size":self.size,"digest":self.digest,"data":bytes(self.data).hex()}
    @classmethod
    def resume(cls,snapshot):
        obj=cls(snapshot["size"],snapshot["digest"])
        raw=snapshot["data"]
        if len(raw)>obj.size*2: raise ValueError("Oversize snapshot")
        obj.data=bytearray.fromhex(raw)
        return obj
