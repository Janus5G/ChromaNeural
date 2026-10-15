// Adapter for the existing v0.2.8 contracts. No new backend/state/token.
import crypto from 'node:crypto';
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const hash=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
const fields=['schema','taskId','namespace','logicalKey','version','payloadHash','payloadBytes','payloadLocator','mediaType','criteria','evidence','complete','contributorNodeId','finalizerNodeId'];
export function contract(s){
 if(!s||typeof s!=='object'||Object.keys(s).sort().join()!=fields.slice().sort().join())throw Error('Publication manifest fields');
 if(s.schema!==1||s.complete!==true||s.version!=='1')throw Error('Complete version-1 result required');
 for(const k of ['taskId','namespace','logicalKey','payloadLocator','mediaType'])
  if(typeof s[k]!=='string'||!s[k].length||Buffer.byteLength(s[k])>128)throw Error('Manifest text bounds');
 for(const k of ['criteria','evidence'])
  if(typeof s[k]!=='string'||!s[k].trim()||Buffer.byteLength(s[k])>4096)throw Error('Acceptance evidence required');
 if(!hash(s.payloadHash)||!hash(s.contributorNodeId)||!hash(s.finalizerNodeId)||s.finalizerNodeId===s.contributorNodeId||!Number.isSafeInteger(s.payloadBytes)||s.payloadBytes<1||s.payloadBytes>1048576)throw Error('Payload bounds');
 const acceptanceHash=sha(s.criteria),evidenceHash=sha(s.evidence);
 const input={schemaVersion:1,nodeId:s.contributorNodeId,namespace:s.namespace,logicalKey:s.logicalKey,version:1n,
  payloadHash:s.payloadHash,payloadLocator:s.payloadLocator,mediaType:s.mediaType,provenanceHash:evidenceHash,
  provenance:[{kind:'acceptance',reference:s.taskId,hash:acceptanceHash},{kind:'verification',reference:s.taskId,hash:evidenceHash}],
  supersedes:[],metadata:[['taskId',s.taskId],['payloadBytes',String(s.payloadBytes)],['finalizerNodeId',s.finalizerNodeId]],signature:new Uint8Array()};
 const f=t=>Buffer.byteLength(t)+':'+t;
 const canonical='CHROMA-NETWORK-KNOWLEDGE-v1'+f(input.nodeId)+f(input.namespace)+f(input.logicalKey)+f('1')+
  f(input.payloadHash)+f(input.payloadLocator)+f(input.mediaType)+f(input.provenanceHash)+input.provenance.length+':'+
  input.provenance.map(p=>f(p.kind)+f(p.reference)+f(p.hash)).join('')+'0:'+input.metadata.length+':'+input.metadata.map(([k,v])=>f(k)+f(v)).join('');
 return {input,recordId:sha(canonical),acceptanceHash,evidenceHash};
}
export async function publicationOperation({actor,identity,nodeId,request,config,local}){
 if(!local||config.allowLocalTestRoot!==true||config.publicationEnabled!==true)throw Error('Publication candidate is LOCAL ONLY with explicit opt-in');
 const {input,recordId,acceptanceHash,evidenceHash}=contract(request.spec);
 const found=async()=> (await actor.searchVerifiedKnowledgeV1(nodeId,input.namespace,input.logicalKey)).some(r=>r.recordId===recordId&&r.payloadHash===input.payloadHash);
 if(request.operation==='publication_status')return {recordId,verified:await found()};
 if(request.approved!==true)throw Error('Explicit publication/role approval required');
 if(request.operation==='publication_submit'){
  if(nodeId!==input.nodeId)throw Error('Contributor identity mismatch');
  input.signature=new Uint8Array(await identity.sign(Buffer.from('CHROMA-PUBLICATION-v1:'+recordId)));
  const r=await actor.submitNetworkKnowledge(input);
  if(r.err)return {recordId,error:JSON.stringify(r.err,(_,v)=>typeof v==='bigint'?String(v):v)};
  if(r.ok.record.recordId!==recordId||r.ok.record.payloadHash!==input.payloadHash)throw Error('Publication acknowledgement mismatch');
  return {recordId,verified:'verified' in r.ok.status,status:Object.keys(r.ok.status)[0]};
 }
 if(request.operation==='publication_commission'){
  if(!Number.isSafeInteger(request.maxReward)||request.maxReward<1||request.maxReward>100000000)throw Error('Explicit administrator reward cap');
  await actor.commissionNetworkWorkV1({id:recordId,nodeId:input.nodeId,kind:'data',contentHash:input.payloadHash,acceptanceHash,maxReward:BigInt(request.maxReward)});
  return {recordId,commissioned:true};
 }
 if(request.operation==='publication_attest'){
  if(nodeId===input.nodeId)throw Error('Self attestation forbidden');
  if(typeof request.method!=='string'||!request.method.length||[...request.method].length>80)throw Error('Verification method bounds');
  const credited=await actor.attestNetworkWorkV1({workId:recordId,evidenceHash,method:request.method,
    metrics:{dataBytes:BigInt(request.spec.payloadBytes),cpuMicros:0n,ramByteMicros:0n,gpuMicros:0n}});
  return {recordId,credited:String(credited),finalizeAllowed:nodeId===request.spec.finalizerNodeId};
 }
 if(request.operation==='publication_verify'){
  if(nodeId!==request.spec.finalizerNodeId)throw Error('Only designated independent finalizer');
  if(nodeId===input.nodeId)throw Error('Self verification forbidden');
  if(await found())return {recordId,verified:true};
  const r=await actor.verifyNetworkKnowledge({nodeId,recordId,evidenceHash,
    signature:new Uint8Array(await identity.sign(Buffer.from('CHROMA-VERIFY-v1:'+recordId+':'+evidenceHash)))});
  if(r.err)return {recordId,error:JSON.stringify(r.err,(_,v)=>typeof v==='bigint'?String(v):v)};
  return {recordId,verified:'verified' in r.ok.status};
 }
 throw Error('Unsupported publication operation');
}
