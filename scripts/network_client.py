"""Explicit, bounded collaboration commands; no remote execution."""
from pathlib import Path
import sys,argparse,json,os,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"client"))
from chroma.collaboration import Collaboration
from chroma.network_state import NetworkState
from chroma.speech import Credentials
from chroma.speech_identity import certificate

def bounded_json(path):
    with Path(path).open("rb") as stream: raw=stream.read(32769)
    if len(raw)>32768: raise ValueError("Configuration/plan limit is 32 KiB")
    return json.loads(raw)

def main(argv=None):
    from chroma.i18n import LocaleContext,LOCALES,language_from_argv,argument_parser
    locale=LocaleContext(language_from_argv(sys.argv[1:] if argv is None else argv) or "en")
    p=argument_parser(locale,description=locale.text("cli.description"))
    p.add_argument("--language",choices=LOCALES,help=locale.text("launch.language"))
    p.add_argument("--config");p.add_argument("--cache")
    sub=p.add_subparsers(dest="operation",required=True)
    setup=sub.add_parser('node-prepare')
    source=setup.add_mutually_exclusive_group(required=True)
    source.add_argument('--profile');source.add_argument('--local-host')
    setup.add_argument('--canister-id');setup.add_argument('--identity-directory',required=True)
    setup.add_argument('--output',required=True);setup.add_argument('--approve-node-network',action='store_true')
    setup.add_argument('--allow-local-test',action='store_true')
    sub.add_parser('node-status')
    setup=sub.add_parser('node-register-local');setup.add_argument('--approve-registration',action='store_true')
    setup.add_argument('--approve-node-owner',action='store_true')
    setup=sub.add_parser('node-use');setup.add_argument('--state-directory',required=True)
    setup.add_argument('--approve-selection',action='store_true')
    sub.add_parser("balance")
    q=sub.add_parser("plan");q.add_argument("--namespace",required=True);q.add_argument("--key",required=True)
    q.add_argument("--question-file",required=True);q.add_argument("--output",required=True)
    q.add_argument("--approve-network",action="store_true")
    a=sub.add_parser("acquire");a.add_argument("--plan",required=True);a.add_argument("--approve-cost",action="store_true")
    s=sub.add_parser("send-question");s.add_argument("--plan",required=True);s.add_argument("--peer-config",required=True)
    s.add_argument("--host",required=True);s.add_argument("--port",type=int,default=7443)
    s.add_argument("--id",required=True);s.add_argument("--approve-disclosure",action="store_true")
    c=sub.add_parser("certificate");c.add_argument("--identity-directory",required=True);c.add_argument("--output",required=True)
    q=sub.add_parser("queue-ai");q.add_argument("--queue",required=True);q.add_argument("--namespace",required=True);q.add_argument("--key",required=True)
    q.add_argument("--source-file",required=True);q.add_argument("--instruction",required=True)
    q.add_argument("--approve-network",action="store_true");q.add_argument("--approve-local-ai",action="store_true")
    q.add_argument("--ai-provider",choices=("bundled-cpu","ollama"),default="bundled-cpu")
    q.add_argument("--ai-model",help=locale.text("cli.model"))
    w=sub.add_parser("work");w.add_argument("--queue",required=True);w.add_argument("--duration",type=int,default=60);w.add_argument("--poll",type=float,default=30)
    r=sub.add_parser("result");r.add_argument("--queue",required=True);r.add_argument("--id",required=True)
    pub=sub.add_parser("publication-enqueue")
    pub.add_argument("--queue",required=True);pub.add_argument("--manifest",required=True)
    pub.add_argument("--inbox",required=True);pub.add_argument("--peer",required=True);pub.add_argument("--message-id",required=True)
    pub.add_argument("--action",choices=("submit","commission","attest"),default="submit")
    pub.add_argument("--method",default="");pub.add_argument("--max-reward",type=int,default=0)
    pub.add_argument("--approve-result",action="store_true")
    for name in ("publication-status","publication-revoke","publication-approve"):
        command=sub.add_parser(name);command.add_argument("--queue",required=True);command.add_argument("--id",required=True)
    command=sub.add_parser("publication-work");command.add_argument("--queue",required=True)
    command.add_argument("--duration",type=int,default=60);command.add_argument("--poll",type=float,default=30)
    for name in ('task-question','task-accept','task-reply','task-collect','task-status'):
        command=sub.add_parser(name);command.add_argument('--queue',required=True)
        if name in ('task-question','task-collect','task-status'):command.add_argument('--id',required=True)
        if name!='task-status':
            command.add_argument('--peer-config',required=True);command.add_argument('--peer',required=True)
        if name in ('task-accept','task-reply','task-collect'):
            command.add_argument('--inbox',required=True);command.add_argument('--message-id',required=True)
        if name in ('task-question','task-reply'):
            command.add_argument('--host',required=True);command.add_argument('--port',type=int,default=7443)
            command.add_argument('--approve-disclosure',action='store_true')
        if name=='task-reply':command.add_argument('--kind',choices=('partial','answer'),default='answer')
        if name=='task-accept':
            command.add_argument('--approve-network',action='store_true');command.add_argument('--approve-local-ai',action='store_true')
            command.add_argument('--ai-provider',choices=('bundled-cpu','ollama'),default='bundled-cpu');command.add_argument('--ai-model')
        if name=='task-collect':command.add_argument('--approve-reply',action='store_true')
    args=p.parse_args(argv)
    if args.operation.startswith('node-'):
        from chroma import node_setup
        if args.operation=='node-prepare':
            result=node_setup.prepare(args.identity_directory,args.output,profile=args.profile,
                local_host=args.local_host,canister_id=args.canister_id,
                approve_network=args.approve_node_network,allow_local_test=args.allow_local_test)
        else:
            if not args.config:raise ValueError('Choose explicit --config')
            if args.operation=='node-status':result=node_setup.observe(args.config)
            elif args.operation=='node-register-local':result=node_setup.register_local(args.config,
                approve_registration=args.approve_registration,approve_node_owner=args.approve_node_owner)
            else:result=node_setup.select_connection(args.config,args.state_directory,approved=args.approve_selection)
        print(json.dumps(result,ensure_ascii=True));return
    if args.operation.startswith('task-'):
        from chroma.work_queue import WorkQueue
        # Check consent before reading inbox/source/credentials or creating a queue.
        if args.operation in ('task-question','task-reply') and not args.approve_disclosure:raise PermissionError('Approve disclosure')
        if args.operation=='task-accept' and not (args.approve_network and args.approve_local_ai):raise PermissionError('Approve network and local AI')
        if args.operation=='task-collect' and not args.approve_reply:raise PermissionError('Approve inert reply attachment')
        if args.operation!='task-status':
            peer=bounded_json(args.peer_config)
            if peer.get('sharingConsent') is not True:raise PermissionError('Peer sharing opt-in required')
            credentials=Credentials(Path(peer['certificate']),Path(peer['privateKey']),peer['approvedPeerCertificates'])
        if args.operation in ('task-question','task-reply'):
            if not args.config or not args.cache or bounded_json(args.config).get('networkEnabled') is not True:raise PermissionError('Explicit network configuration required')
            state=NetworkState(args.cache);state.network_enabled=True;client=Collaboration(args.config,state)
        queue=WorkQueue(args.queue)
        try:
            if args.operation=='task-status':result=Collaboration.inspect_job(queue,args.id)
            elif args.operation=='task-question':result=client.send_job_question(queue,args.id,args.host,args.port,credentials,args.peer,approved=True)
            elif args.operation=='task-accept':result=Collaboration.accept_job_question(queue,args.inbox,args.peer,args.message_id,credentials,network_approved=True,ai_approved=True,ai_provider=args.ai_provider,ai_model=args.ai_model)
            elif args.operation=='task-reply':result=client.send_job_reply(queue,args.inbox,args.peer,args.message_id,credentials,args.host,args.port,kind=args.kind,approved=True)
            else:result=Collaboration.collect_job_reply(queue,args.id,args.inbox,args.peer,args.message_id,credentials,approved=True)
            print(json.dumps(result,ensure_ascii=True));return
        finally:queue.close()

    if args.operation.startswith("publication-"):
        from chroma.publication import PublicationQueue,strict_json
        queue=PublicationQueue(args.queue)
        try:
            if args.operation=="publication-status":result=queue.read(args.id)
            elif args.operation=="publication-revoke":
                queue.consent(args.id,False);result=queue.read(args.id)
            elif args.operation=="publication-approve":
                queue.consent(args.id,True,args.config);result=queue.read(args.id)
            elif args.operation=="publication-enqueue":
                if not args.approve_result:raise PermissionError("Explicit --approve-result required")
                with Path(args.manifest).open("rb") as stream:raw=stream.read(32769)
                if len(raw)>32768:raise ValueError("Manifest limit")
                result={"id":queue.enqueue(args.config,strict_json(raw.decode("utf-8")),args.inbox,args.peer,args.message_id,
                    action=args.action,method=args.method,max_reward=args.max_reward,approved=True),"status":"PENDING"}
            else:
                if not args.config or not args.cache:raise ValueError("Choose config and cache")
                if not 1<=args.duration<=600 or not 1<=args.poll<=60:raise ValueError("Worker duration/poll bounds")
                state=NetworkState(args.cache);state.network_enabled=True
                deadline=time.monotonic()+args.duration
                while time.monotonic()<deadline:
                    result=queue.step(args.config,state)
                    print(json.dumps({"status":"IDLE"} if result is None else result),flush=True)
                    if result is None:break
                    time.sleep(min(args.poll,max(0,deadline-time.monotonic())))
                return
            print(json.dumps(result));return
        finally:queue.close()

    if args.operation in {"queue-ai","result"}:
        from chroma.work_queue import WorkQueue
        if args.operation=="queue-ai" and not (args.approve_network and args.approve_local_ai):
            raise PermissionError("Approve network and local AI separately")
        queue=WorkQueue(args.queue)
        try:
            if args.operation=="result":result=queue.read(args.id)
            else:
                with Path(args.source_file).open("rb") as f:source=f.read(8193)
                if len(source)>8192:raise ValueError("Source limit")
                result={"id":queue.enqueue(args.namespace,args.key,source.decode("utf-8"),args.instruction,
                         network_approved=True,ai_approved=True,ai_provider=args.ai_provider,ai_model=args.ai_model),"status":"WAITING" if args.ai_provider=="bundled-cpu" else "PROVIDER_WAITING"}
            print(json.dumps(result));return
        finally:queue.close()
    if args.operation=="certificate":
        folder=Path(args.identity_directory)
        print(json.dumps({"nodeId":certificate(folder/"private_key.pem",folder/"public_key.json",args.output),
                          "publicCertificate":args.output}));return
    if not args.config or not args.cache: raise ValueError("Choose --config and a private --cache path")
    config=bounded_json(args.config)
    if config.get("networkEnabled") is not True: raise PermissionError("Network opt-in required")
    state=NetworkState(args.cache);state.network_enabled=True
    client=Collaboration(args.config,state)
    if args.operation=="work":
        from chroma.work_queue import WorkQueue
        if not 1<=args.duration<=600 or not 1<=args.poll<=60:raise ValueError("Worker budget: duration 1..600s; poll 1..60s")
        queue=WorkQueue(args.queue);deadline=time.monotonic()+args.duration
        try:
            while time.monotonic()<deadline:
                result=queue.step(args.config,state)
                # Progress contains no private source/proposal. Inspect result separately.
                print(json.dumps({"status":"IDLE"} if result is None else {"id":result["id"],"status":result["status"],"error":result["error"]}),flush=True)
                if result is None:break
                time.sleep(min(args.poll,max(0,deadline-time.monotonic())))
        finally:queue.close()
        return
    if args.operation=="balance":
        client.refresh();result={"status":state.status(),"display":state.display(),"snapshot":state.snapshot}
    elif args.operation=="plan":
        # Consent must precede even reading the selected private question.
        if not args.approve_network: raise PermissionError("Approve network lookup and this question with --approve-network")
        with Path(args.question_file).open("rb") as f:raw=f.read(8193)
        if len(raw)>8192:raise ValueError("Question limit is 8 KiB")
        result=client.prepare(args.namespace,args.key,raw.decode("utf-8"),approved=True)
        # Never replace an existing plan or source file.
        fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as f:json.dump(result,f,indent=2)
    elif args.operation=="acquire":
        result=client.acquire_reference(bounded_json(args.plan),approved=args.approve_cost)
    else:
        if not args.approve_disclosure:raise PermissionError("Approve peer disclosure with --approve-disclosure")
        peer=bounded_json(args.peer_config)
        if peer.get("sharingConsent") is not True:raise PermissionError("Peer sharing opt-in required")
        credentials=Credentials(Path(peer["certificate"]),Path(peer["privateKey"]),peer["approvedPeerCertificates"])
        result=client.send_question(bounded_json(args.plan),args.host,args.port,credentials,
                                   approved=True,message_id=args.id)
    print(json.dumps(result,ensure_ascii=True))

if __name__=="__main__":
    try:main()
    except Exception as error:
        print(json.dumps({"status":"FAIL","error":str(error)}),file=sys.stderr);raise SystemExit(1)
