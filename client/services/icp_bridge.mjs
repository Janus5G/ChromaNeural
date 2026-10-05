import {publicationOperation} from './publication.mjs';
import {nodeConnection,validateNodeBinding} from './node_connection.mjs';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
let sdk;
try{sdk=require('@icp-sdk/core/agent')}catch{throw new Error('Install the pinned optional services dependencies; private editor and CPU AI remain available')}
const {HttpAgent,Actor}=sdk;
const {Ed25519KeyIdentity}=require('@icp-sdk/core/identity');
const {IDL}=require('@icp-sdk/core/candid');
const timer=setTimeout(()=>{console.error('ICP bridge deadline');process.exit(124)},25000);
let raw='';
try{
 for await(const chunk of process.stdin){raw+=chunk;if(Buffer.byteLength(raw)>32768)throw new Error('Request limit')}
 const request=JSON.parse(raw),config=JSON.parse(fs.readFileSync(request.config,'utf8'));
 if(config.networkEnabled!==true)throw new Error('Network opt-in required');
 const endpoint=new URL(config.host);
 if(!['https:','http:'].includes(endpoint.protocol))throw new Error('Unsupported ICP endpoint');
 const local=['127.0.0.1','localhost','[::1]'].includes(endpoint.hostname);
 if(request.operation==='node_register_local'&&(!local||endpoint.hostname!=='127.0.0.1'||config.allowLocalTestRoot!==true||request.approveRegistration!==true||request.approveNodeOwner!==true))throw Error('LOCAL ONLY registration with separate explicit approvals required');
 if(endpoint.protocol!=='https:'&&!local)throw new Error('HTTPS required');
 if(typeof request.operation==='string'&&request.operation.startsWith('publication_')&&(!local||config.allowLocalTestRoot!==true||config.publicationEnabled!==true))throw Error('Publication candidate is LOCAL ONLY with explicit opt-in');
 const home=path.resolve(config.identityDirectory);
 const key=crypto.createPrivateKey(fs.readFileSync(path.join(home,'private_key.pem')));
 const pub=crypto.createPublicKey(key).export({format:'jwk'});
 if(pub.crv!=='Ed25519'||pub.kty!=='OKP')throw new Error('Existing Ed25519 identity required');
 const rawKey=Buffer.from(pub.x,'base64url'),nodeId=crypto.createHash('sha256').update(rawKey).digest('hex');
 const metadata=JSON.parse(fs.readFileSync(path.join(home,'public_key.json'),'utf8'));
 if(metadata.nodeId!==nodeId||metadata.publicKeyBase64!==rawKey.toString('base64'))throw new Error('Node metadata mismatch');
 if(config.nodeConnectionV1||['node_status','node_register_local'].includes(request.operation))validateNodeBinding(config,nodeId);
 const secret=key.export({format:'jwk'});
 const identity=Ed25519KeyIdentity.fromSecretKey(Buffer.from(secret.d,'base64url'));
 const agent=await HttpAgent.create({host:config.host,identity});
 if(local){
  if(config.allowLocalTestRoot!==true)throw new Error('Explicit local replica trust required');
  await agent.fetchRootKey();
 }else if(config.allowLocalTestRoot)throw new Error('Never fetch mainnet trust roots');
 const declarations=fs.readFileSync(path.join(import.meta.dirname,'backend.did.js'),'utf8').replace(/^import .*candid.*;$/m,'').replaceAll('export const ','const ');
 const {idlFactory}=new Function('IDL',declarations+';return {idlFactory};')(IDL);
 const actor=Actor.createActor(idlFactory,{agent,canisterId:config.canisterId});
 let result;
 if(['node_status','node_register_local'].includes(request.operation))result=await nodeConnection({actor,identity,nodeId,rawKey,request,config,local});
 else if(request.operation==='balance')result=await actor.getNetworkBalanceV1(nodeId);
 else if(request.operation==='search'){
  if(typeof request.namespace!=='string'||request.namespace.length>128||typeof request.key!=='string'||request.key.length>128)throw new Error('Search bounds');
  result=await actor.searchVerifiedKnowledgeV1(nodeId,request.namespace,request.key);
 }else if(request.operation==='acquire'){
  if(!/^[0-9a-f]{64}$/.test(request.recordId)||!/^[0-9]{1,12}$/.test(request.epoch))throw new Error('Read request bounds');
  result=await actor.acquireVerifiedKnowledgeV1(nodeId,request.recordId,BigInt(request.epoch));
 }else if(typeof request.operation==='string'&&request.operation.startsWith('publication_')){
  result=await publicationOperation({actor,identity,nodeId,request,config,local});
 }else throw new Error('Unsupported bridge operation');
 console.log(JSON.stringify({ok:true,nodeId,result},(_,v)=>typeof v==='bigint'?v.toString():v));
}catch(e){console.log(JSON.stringify({ok:false,error:String(e)}));process.exitCode=1}
finally{clearTimeout(timer)}
