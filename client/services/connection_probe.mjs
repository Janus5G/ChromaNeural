// Public, anonymous, read-only endpoint check. Never creates a private session.
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const require=createRequire(import.meta.url);
const {HttpAgent,Actor,AnonymousIdentity,Cbor}=require('@icp-sdk/core/agent');
const {Principal}=require('@icp-sdk/core/principal');
const FIELDS=['version','app_id','network','host','connection_target','backend_canister_id','frontend_canister_id','identity_provider','ii_derivation_origin','principal'].sort();
export function validateProfile(p){
 if(!p||Array.isArray(p)||JSON.stringify(Object.keys(p).sort())!==JSON.stringify(FIELDS))throw Error('Unsupported public API metadata');
 if(p.version!==1||p.app_id!=='01a09729-ea2b-731d-9190-cb11a7778be4'||p.network!=='mainnet'||p.connection_target!=='backend_canister')throw Error('Unsupported application target');
 if(!['https://icp0.io','https://icp-api.io'].includes(p.host)||p.identity_provider!=='https://id.ai/authorize'||p.ii_derivation_origin!=='https://chroma-neural-wl9.caffeine.xyz')throw Error('Unapproved endpoint or origin');
 for(const key of ['backend_canister_id','frontend_canister_id','principal']){
  if(typeof p[key]!=='string'||['aaaaa-aa','2vxsx-fae'].includes(p[key])||Principal.fromText(p[key]).toText()!==p[key])throw Error('Invalid principal');
 }
 if(p.backend_canister_id===p.frontend_canister_id)throw Error('Backend/frontend mismatch');
 return p;
}
export function readOnlyFetch(profile,fetcher=fetch){
 const p=validateProfile(profile),deadline=Date.now()+22000;let requests=0;const audit=[];
 const guarded=async(input,init={})=>{
  if(Date.now()>deadline||++requests>8)throw Error('Read-only request budget');
  const u=new URL(typeof input==='string'||input instanceof URL?input:input.url);
  if(u.origin!==p.host||u.search||u.hash||u.username||u.password||init.method!=='POST'||!/^\/api\/v[23]\/(canister|subnet)\/[a-z0-9-]+\/(query|read_state)$/.test(u.pathname))throw Error('Only ICP query/read_state allowed');
  if(u.pathname.includes('/canister/')&&!u.pathname.includes('/'+p.backend_canister_id+'/'))throw Error('Wrong canister');
  const e=Cbor.decode(new Uint8Array(init.body)),c=e.content;
  if(e.sender_sig||e.sender_pubkey||e.sender_delegation||!c||Principal.fromUint8Array(c.sender).toText()!=='2vxsx-fae')throw Error('Credentials forbidden in public check');
  if(!['query','read_state'].includes(c.request_type)||!u.pathname.endsWith('/'+c.request_type))throw Error('Non-read request');
  if(c.request_type==='query'&&(c.method_name!=='getApiDoc'||Principal.fromUint8Array(c.canister_id).toText()!==p.backend_canister_id))throw Error('Query not allowlisted');
  const entry={requestType:c.request_type,method:c.method_name??null};audit.push(entry);
  const r=await fetcher(u,{...init,redirect:'error',signal:AbortSignal.timeout(Math.min(10000,deadline-Date.now()))});
  const chunks=[];let n=0;
  if(r.body)for await(const part of r.body){n+=part.length;if(n>2097152)throw Error('Response size bound');chunks.push(part);}
  const headers=new Headers(r.headers);headers.delete('content-encoding');headers.delete('content-length');
  return new Response(n?Buffer.concat(chunks):null,{status:r.status,statusText:r.statusText,headers});
 };
 return {fetch:guarded,audit};
}
export async function probe(profile){
 const p=validateProfile(profile),guard=readOnlyFetch(p);
 const agent=await HttpAgent.create({host:p.host,identity:new AnonymousIdentity(),fetch:guard.fetch,retryTimes:0,
  verifyQuerySignatures:true,shouldFetchRootKey:false,shouldSyncTime:false});
 agent.call=async()=>{throw Error('Updates forbidden')};
 const actor=Actor.createActor(({IDL})=>IDL.Service({getApiDoc:IDL.Func([],[IDL.Text],['query'])}),{agent,canisterId:p.backend_canister_id});
 const doc=await actor.getApiDoc();
 if(typeof doc!=='string'||!doc.length||Buffer.byteLength(doc)>1048576)throw Error('Unexpected public API response');
 return {backendReachable:true,backendCanisterId:p.backend_canister_id,host:p.host,caller:'anonymous',
  privateAccess:'NOT_VERIFIED',nodeAdmission:'NOT_VERIFIED',querySignatureVerification:true,platform:process.platform,nodeVersion:process.version,checkedAt:new Date().toISOString(),requests:guard.audit};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const timer=setTimeout(()=>{console.error('Read-only probe deadline');process.exit(124)},25000);
 try{let raw='';for await(const chunk of process.stdin){raw+=chunk;if(Buffer.byteLength(raw)>8192)throw Error('Input size bound');}
  console.log(JSON.stringify({ok:true,result:await probe(JSON.parse(raw))}));
 }catch(e){console.log(JSON.stringify({ok:false,error:String(e)}));process.exitCode=1;}
 finally{clearTimeout(timer)}
}
