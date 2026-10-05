// Existing registry + signed node access. No II session, admission grant or publication.
export function validateNodeBinding(config,nodeId){
 const b=config.nodeConnectionV1;
 if(!b||Object.keys(b).sort().join(',')!=='canisterId,host,nodeId'||
    !/^[0-9a-f]{64}$/.test(b.nodeId)||b.nodeId!==nodeId||b.host!==config.host||b.canisterId!==config.canisterId)
  throw Error('Node setup identity/target binding mismatch');
}
export async function nodeConnection({actor,identity,nodeId,rawKey,request,config,local}){
 validateNodeBinding(config,nodeId);
 const principal=identity.getPrincipal().toText();
 const base={nodeId,nodePrincipal:principal,host:config.host,canisterId:config.canisterId,
  checkedAt:new Date().toISOString(),privateLogin:'BROWSER_ONLY',resourceSharing:false};
 const records=await actor.getNode(nodeId);
 if(!Array.isArray(records)||records.length>1)throw Error('Invalid registry response');
 let record=records[0];
 function validateRecord(r){
  if(r.nodeId!==nodeId||!Buffer.from(r.publicKey).equals(rawKey))throw Error('Registry identity mismatch');
  const status=Object.keys(r.status);
  if(status.length!==1||!['registered','active','degraded','offline','revoked'].includes(status[0]))throw Error('Unknown registry status');
  return {...base,registryStatus:status[0],registryOwner:r.owner.toText(),
    registryOwnerIsNode:r.owner.toText()===principal};
 }
 if(request.operation==='node_register_local'){
  if(!local||config.allowLocalTestRoot!==true||new URL(config.host).hostname!=='127.0.0.1')throw Error('Registration is LOCAL ONLY');
  if(request.approveRegistration!==true||request.approveNodeOwner!==true)throw Error('Explicit registration and node-owner consent required');
  if(record){
   const current=validateRecord(record);
   return {...current,status:current.registryStatus==='revoked'?'REVOKED':'ALREADY_REGISTERED',nodeAdmission:'NOT_VERIFIED',registrationSubmitted:false};
  }
  const result=await actor.registerNode({schemaVersion:1,protocolVersion:'chroma-node/0.1',publicKey:rawKey,publicMetadata:[]});
  if(!result.ok)throw Error('Registration rejected: '+JSON.stringify(result.err,(_,v)=>typeof v==='bigint'?String(v):v));
  const registered=validateRecord(result.ok);
  if(!registered.registryOwnerIsNode)throw Error('Unexpected registration owner');
  return {...registered,status:'REGISTERED',nodeAdmission:'NOT_VERIFIED',registrationSubmitted:true};
 }
 if(request.operation!=='node_status')throw Error('Unsupported node setup operation');
 if(!record)return {...base,status:'UNREGISTERED',nodeAdmission:'NOT_VERIFIED'};
 const current=validateRecord(record);
 if(current.registryStatus==='revoked')return {...current,status:'REVOKED',nodeAdmission:'DENIED'};
 try{
  const balance=await actor.getNetworkBalanceV1(nodeId);
  if(!['READY','DORMANT','UNKNOWN'].includes(balance.status))throw Error('Invalid balance response');
  return {...current,status:'AUTHORIZED',nodeAdmission:'CONFIRMED',balanceStatus:balance.status,balance};
 }catch(error){
  // A failed query cannot distinguish admission denial from a transport failure.
  return {...current,status:'REGISTERED_ACCESS_NOT_CONFIRMED',nodeAdmission:'NOT_VERIFIED',error:String(error).slice(0,1000)};
 }
}
