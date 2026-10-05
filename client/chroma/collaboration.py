"""User-approved knowledge-first planning over the existing node bridge and PRSM transport."""
import hashlib,json,uuid,sqlite3
from pathlib import Path
from .speech import Credentials,canonical,strict_json,validate,MAX_BYTES
from .speech_identity import certificate_identity
from . import icp_client
from .speech import send
class Collaboration:
    def __init__(self,connection,state):
        self.connection=connection;self.state=state
    def refresh(self):
        try:
            snapshot=icp_client.call(self.connection,"balance");self.state.update(snapshot)
            return self.state.status()
        except Exception as error:
            self.state.unavailable(str(error));raise
    def prepare(self,namespace,key,question,*,approved=False):
        if approved is not True or not self.state.network_enabled:raise PermissionError("Explicit network work consent required")
        if not isinstance(question,str) or len(question.encode())>8192:raise ValueError("Question limit")
        self.refresh()
        if not self.state.can_run("network-dependent"):
            return {"status":self.state.status(),"question":question,"namespace":namespace,"key":key}
        matches=icp_client.call(self.connection,"search",namespace=namespace,key=key)
        if matches:
            selected=max(matches,key=lambda row:int(row["version"]))
            return {"status":"REUSE_AVAILABLE","reference":selected,"policyEpoch":str(self.state.snapshot["policy"]["epoch"])}
        return {"status":"COLLABORATION_REQUIRED","namespace":namespace,"key":key,"question":question}
    def acquire_reference(self,plan,*,approved=False):
        if approved is not True or plan.get("status")!="REUSE_AVAILABLE":raise PermissionError("Approve this record acquisition")
        result=icp_client.call(self.connection,"acquire",recordId=plan["reference"]["recordId"],epoch=plan["policyEpoch"])
        if isinstance(result,dict) and "err" in result:
            raise RuntimeError("Knowledge acquisition rejected: "+json.dumps(result["err"],sort_keys=True))
        self.refresh()
        return result
    def send_question(self,plan,host,port,credentials,*,approved=False,message_id=None):
        if approved is not True or plan.get("status")!="COLLABORATION_REQUIRED":raise PermissionError("Approve this peer data disclosure")
        self.refresh()
        if not self.state.can_run("network-dependent"):raise PermissionError("Network work is dormant or balance unknown")
        payload=json.dumps({"schema":"chroma-question-v1","namespace":plan["namespace"],"key":plan["key"],"question":plan["question"]},sort_keys=True,separators=(",",":")).encode()
        return send(host,port,credentials,message_id or str(uuid.uuid4()),"question",payload)
    @staticmethod
    def reviewed_payload(reference,payload,*,approved=False):
        if approved is not True:raise PermissionError("Approve use of received data")
        if not isinstance(payload,bytes) or len(payload)>1048576:raise ValueError("Payload bounds")
        if hashlib.sha256(payload).hexdigest()!=reference["payloadHash"]:raise ValueError("Shared payload digest mismatch")
        return payload # Inert bytes only; never an executable or a model tool call.


    def send_job_question(self,queue,job_id,host,port,credentials,peer,*,approved=False):
        """Explicit disclosure of an existing local code task, pinned to one peer."""
        if approved is not True:raise PermissionError('Approve task/source disclosure')
        pinned=_pinned(credentials,peer);origin=certificate_identity(credentials.certificate)[0]
        if peer==origin:raise PermissionError('Choose a different approved node')
        self.refresh()
        if not self.state.can_run('network-dependent'):raise PermissionError('Network work unavailable')
        with queue.db:
            queue.db.execute('BEGIN IMMEDIATE')
            request,result=_local_result(queue,job_id)
            mid=str(uuid.uuid5(uuid.UUID(job_id),'question:'+peer))
            question={'schema':'chroma-job-question-v1','taskId':job_id,'requestId':mid,'requesterNode':origin,'recipientNode':peer,
                      **{k:request[k] for k in ('namespace','key','source','instruction','sourceHash')}}
            payload=canonical(question);_question(question,origin,peer,mid)
            link={'peer':peer,'requestHash':_hash(payload)}
            work=_work(result);old=work['requests'].get(mid)
            if old is not None and old!=link:raise ValueError('Conflicting task disclosure')
            if old is None and len(work['requests'])>=8:raise ValueError('Task peer limit 8')
            work['requests'][mid]=link
            queue.db.execute('UPDATE job SET result=? WHERE id=?',(json.dumps(result),job_id))
        # Binding is durable before send; retry uses identical message ID and bytes.
        return send(host,port,pinned,mid,'question',payload)

    @staticmethod
    def accept_job_question(queue,inbox,peer,message_id,credentials,*,network_approved=False,ai_approved=False,ai_provider='bundled-cpu',ai_model=None):
        """An inbound message is inert until the local owner approves this exact task."""
        if network_approved is not True or ai_approved is not True:raise PermissionError('Approve network and fixed local AI separately')
        _pinned(credentials,peer)
        meta,body=_message(inbox,peer,message_id)
        if meta['kind']!='question':raise ValueError('Expected question')
        question=strict_json(body);_question(question,peer,certificate_identity(credentials.certificate)[0],message_id)
        jid=_accepted_id(peer,message_id)
        # No request/job from the wire is executed. Enqueue only the existing fixed
        # code-proposal operation, using local provider selection and local consent.
        queue.enqueue(question['namespace'],question['key'],question['source'],question['instruction'],
                      network_approved=True,ai_approved=True,ai_provider=ai_provider,ai_model=ai_model,job_id=jid)
        return {'id':jid,'taskId':question['taskId'],'requestId':message_id,'requestHash':_hash(body),
                'originPeer':peer,'status':queue.read(jid)['status']}

    def send_job_reply(self,queue,inbox,peer,question_id,credentials,host,port,*,kind='answer',approved=False):
        if approved is not True:raise PermissionError('Approve reply disclosure')
        if kind not in ('partial','answer'):raise ValueError('Reply kind')
        pinned=_pinned(credentials,peer)
        meta,body=_message(inbox,peer,question_id)
        if meta['kind']!='question':raise ValueError('Expected question')
        question=strict_json(body);_question(question,peer,certificate_identity(credentials.certificate)[0],question_id)
        local_id=_accepted_id(peer,question_id);request,result=_local_result(queue,local_id)
        if any(request[k]!=question[k] for k in ('namespace','key','source','instruction','sourceHash')):
            raise ValueError('Local work does not match approved question')
        reply={'schema':'chroma-job-reply-v1','taskId':question['taskId'],'requestId':question_id,
               'requestHash':_hash(body),'localJobId':local_id,'kind':kind,'proposal':result['proposal'],
               'provider':result['provider'],'scientificallyVerified':False}
        mid=_reply_id(question_id,kind);_reply(reply,mid,kind)
        self.refresh()
        if not self.state.can_run('network-dependent'):raise PermissionError('Network work unavailable')
        return send(host,port,pinned,mid,kind,canonical(reply))

    @staticmethod
    def collect_job_reply(queue,job_id,inbox,peer,message_id,credentials,*,approved=False):
        if approved is not True:raise PermissionError('Approve attaching this inert reply')
        _pinned(credentials,peer)
        meta,body=_message(inbox,peer,message_id);reply=strict_json(body);_reply(reply,message_id,meta['kind'])
        if reply['taskId']!=job_id:raise ValueError('Reply task mismatch')
        with queue.db:
            queue.db.execute('BEGIN IMMEDIATE');request,result=_local_result(queue,job_id);work=_work(result)
            link=work['requests'].get(reply['requestId'])
            if link!={'peer':peer,'requestHash':reply['requestHash']}:raise PermissionError('No matching locally approved peer/question binding')
            if reply['localJobId']!=_accepted_id(certificate_identity(credentials.certificate)[0],reply['requestId']):
                raise ValueError('Reply local job correlation')
            reference={'peer':peer,'messageId':message_id,'inbox':str(Path(inbox).resolve()),'sha256':meta['sha256'],
                       'bytes':meta['total'],'kind':meta['kind'],'requestId':reply['requestId'],'localJobId':reply['localJobId'],
                       'scientificallyVerified':False}
            old=work['replies'].get(message_id)
            if old is not None and old!=reference:raise ValueError('Conflicting correlated result')
            if old is None and len(work['replies'])>=16:raise ValueError('Task reply limit 16')
            work['replies'][message_id]=reference
            queue.db.execute('UPDATE job SET result=? WHERE id=?',(json.dumps(result),job_id))
        return queue.read(job_id)

    @staticmethod
    def inspect_job(queue,job_id):
        """References and inert proposals; neither receipt nor SHA-256 means verified."""
        job=queue.read(job_id);responses=[]
        result=job['result']
        if result and 'peerWork' in result:
            work=_work(result)
            for mid,ref in sorted(work['replies'].items()):
                meta,body=_message(ref['inbox'],ref['peer'],mid)
                if meta['sha256']!=ref['sha256'] or meta['total']!=ref['bytes']:raise ValueError('Referenced reply integrity failure')
                reply=strict_json(body);_reply(reply,mid,meta['kind'])
                if reply['taskId']!=job_id or work['requests'].get(reply['requestId'])!={'peer':ref['peer'],'requestHash':reply['requestHash']}:
                    raise ValueError('Referenced reply binding changed')
                responses.append({**ref,'proposal':reply['proposal'],'providerClaim':reply['provider'],'origin':'peer','reviewStatus':'AWAITING_REVIEW'})
        return {**job,'localOrigin':'local','peerResponses':responses}

def _hash(body):return hashlib.sha256(body).hexdigest()
def _accepted_id(peer,mid):return str(uuid.uuid5(uuid.UUID(mid),'local-approved-code:'+peer))
def _reply_id(mid,kind):return str(uuid.uuid5(uuid.UUID(mid),'reply:'+kind))
def _uuid(value):
    if not isinstance(value,str) or str(uuid.UUID(value))!=value:raise ValueError('Canonical UUID required')
def _digest(value):
    if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('SHA-256/node ID required')
def _pinned(credentials,peer):
    _digest(peer)
    if peer not in credentials.peers or certificate_identity(credentials.peers[peer])[0]!=peer:
        raise PermissionError('Explicitly approved peer certificate required')
    # Narrow trust BEFORE connection, not after disclosing bytes to another admitted peer.
    return Credentials(credentials.certificate,credentials.private_key,{peer:credentials.peers[peer]})
def _message(inbox,peer,mid):
    _digest(peer);_uuid(mid);path=Path(inbox)
    if path.is_symlink() or not path.is_file():raise ValueError('Existing regular inbox required')
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=3)
    try:row=db.execute('SELECT substr(meta,1,513),substr(body,1,?),length(body) FROM message WHERE peer=? AND id=?',(MAX_BYTES+1,peer,mid)).fetchone()
    finally:db.close()
    if not row or not isinstance(row[0],bytes) or len(row[0])>512 or not isinstance(row[1],bytes) or row[2]>MAX_BYTES:raise ValueError('Completed bounded peer message required')
    meta=strict_json(row[0]);validate(meta)
    if canonical(meta)!=row[0] or meta['id']!=mid or meta['total']!=len(row[1]) or meta['sha256']!=_hash(row[1]):raise ValueError('Inbox message integrity failure')
    return meta,row[1]
def _question(q,peer,recipient,mid):
    if not isinstance(q,dict) or set(q)!={'schema','taskId','requestId','requesterNode','recipientNode','namespace','key','source','instruction','sourceHash'}:raise ValueError('Question fields')
    if q['schema']!='chroma-job-question-v1':raise ValueError('Question schema')
    _uuid(q['taskId']);_uuid(q['requestId']);_digest(q['sourceHash'])
    if q['requesterNode']!=peer or q['recipientNode']!=recipient or peer==recipient:raise PermissionError('Question peer binding')
    if q['requestId']!=mid or mid!=str(uuid.uuid5(uuid.UUID(q['taskId']),'question:'+recipient)):raise ValueError('Question message correlation')
    if not all(isinstance(q[k],str) and 0<len(q[k])<=128 for k in ('namespace','key')):raise ValueError('Lookup bounds')
    if not isinstance(q['source'],str) or len(q['source'].encode())>8192 or _hash(q['source'].encode())!=q['sourceHash']:raise ValueError('Question source bounds/hash')
    if not isinstance(q['instruction'],str) or not 0<len(q['instruction'])<=2000:raise ValueError('Question instruction bounds')
def _reply(r,mid,kind):
    if not isinstance(r,dict) or set(r)!={'schema','taskId','requestId','requestHash','localJobId','kind','proposal','provider','scientificallyVerified'}:raise ValueError('Reply fields')
    if r['schema']!='chroma-job-reply-v1' or kind not in ('partial','answer') or r['kind']!=kind:raise ValueError('Reply schema/kind')
    for k in ('taskId','requestId','localJobId'):_uuid(r[k])
    _digest(r['requestHash'])
    if mid!=_reply_id(r['requestId'],kind):raise ValueError('Reply message correlation')
    if r['scientificallyVerified'] is not False:raise PermissionError('Peer cannot self-verify')
    if not isinstance(r['proposal'],str) or not 0<len(r['proposal'].encode())<=65536 or '\x00' in r['proposal']:raise ValueError('Proposal bounds')
    if not isinstance(r['provider'],str) or not 0<len(r['provider'])<=200:raise ValueError('Provider claim bounds')
def _local_result(queue,jid):
    _uuid(jid)
    row=queue.db.execute('SELECT request,status,result FROM job WHERE id=?',(jid,)).fetchone()
    if not row or row[1]!='AWAITING_REVIEW':raise ValueError('Existing completed local proposal required')
    req=strict_json(row[0]);r=strict_json(row[2])
    if req.get('networkApproved') is not True or req.get('aiApproved') is not True:raise PermissionError('Local consent missing')
    if r.get('kind')!='LOCAL_AI_PROPOSAL' or r.get('scientificallyVerified') is not False or r.get('applied') is not False:raise ValueError('Unverified unapplied code proposal required')
    if _hash(req['source'].encode())!=req['sourceHash'] or r['sourceHash']!=req['sourceHash']:raise ValueError('Local source changed')
    if any(r['plan'].get(k)!=req[v] for k,v in (('namespace','namespace'),('key','key'),('question','instruction'))):raise ValueError('Local approved plan changed')
    return req,r

def _work(result):
    work=result.setdefault('peerWork',{'version':1,'requests':{},'replies':{}})
    if not isinstance(work,dict) or set(work)!={'version','requests','replies'} or type(work['version']) is not int or work['version']!=1 or not isinstance(work['requests'],dict) or not isinstance(work['replies'],dict):raise ValueError('Task link format')
    if len(work['requests'])>8 or len(work['replies'])>16:raise ValueError('Task link capacity')
    return work
