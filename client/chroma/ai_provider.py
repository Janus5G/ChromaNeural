"""Owner-selected fixed AI adapters. No plugin loading, endpoint choice or fallback."""
import hashlib,json,math,os,re,subprocess,sys,time
from pathlib import Path
from .native_ai import Inference


def selection(provider="bundled-cpu",model=None):
    if provider=="bundled-cpu":
        if model is not None:raise ValueError("The bundled provider uses its existing pinned model")
        return None
    if provider!="ollama":raise ValueError("Unsupported AI provider")
    if not isinstance(model,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,119}",model):
        raise ValueError("Choose an explicitly approved Ollama model name")
    return {"version":1,"provider":"ollama","model":model}


def validate_selection(value):
    if value is None:return None
    if not isinstance(value,dict) or set(value)!={"version","provider","model"} or type(value["version"]) is not int or value["version"]!=1:
        raise ValueError("Invalid stored AI provider selection")
    expected=selection(value["provider"],value["model"])
    if expected is None or value!=expected:raise ValueError("Invalid stored AI provider selection")
    return expected


def request_digest(request):
    # Same SHA-256 mechanism as existing queues; detects changed approved job data.
    return hashlib.sha256(json.dumps(request,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()


def selected_inference(source,instruction,choice,*,bundled,timeout=90,mcp_servers=None,mcp_directory=None,mcp_secrets=None):
    choice=validate_selection(choice)
    if mcp_servers and choice is None:raise ValueError("MCP tool use requires an explicitly selected Ollama model")
    if choice is None:return bundled(source,instruction,timeout=timeout)
    if not isinstance(source,str) or len(source.encode())>8192:raise ValueError("AI source limit is 8 KiB")
    if not isinstance(instruction,str) or not 0<len(instruction)<=2000:raise ValueError("Instruction limit")
    if isinstance(timeout,bool) or not isinstance(timeout,(int,float)) or not math.isfinite(timeout) or not 0<timeout<=120:
        raise ValueError("Inference deadline")
    if mcp_servers:
        from .onboarding import worker
        started=time.monotonic()
        response=worker({"operation":"infer","directory":str(mcp_directory) if mcp_directory is not None else None,
                         "identifiers":mcp_servers,"secrets":dict(mcp_secrets or {}),"model":choice["model"],
                         "source":source,"instruction":instruction},timeout=timeout)
        text=response.get("proposal")
        if not isinstance(text,str) or not text.strip() or "\x00" in text or len(text.encode())>65536:
            raise ValueError("Invalid or oversized provider proposal")
        return Inference(text.encode(),time.monotonic()-started,"ollama / "+choice["model"],"")
    # Isolated child bounds the whole existing HTTP adapter, including slow headers.
    # No browser identity, node key, project path or arbitrary command crosses here.
    worker=Path(__file__).with_name("ai_provider_worker.py")
    body=json.dumps({"model":choice["model"],"source":source,"instruction":instruction}).encode()
    opts={"creationflags":subprocess.CREATE_NO_WINDOW} if os.name=="nt" else {}
    started=time.monotonic()
    try:
        result=subprocess.run([sys.executable,"-I","-B",str(worker)],input=body,
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,**opts)
    except subprocess.TimeoutExpired:
        raise TimeoutError("Selected AI provider deadline exceeded") from None
    if result.returncode:raise RuntimeError("Selected AI provider failed; no fallback attempted")
    if len(result.stdout)>524288:raise ValueError("Provider response limit")
    response=json.loads(result.stdout)
    if not isinstance(response,dict) or set(response)!={"proposal"}:raise ValueError("Invalid provider response")
    text=response["proposal"]
    if not isinstance(text,str) or not text.strip() or "\x00" in text or len(text.encode())>65536:
        raise ValueError("Invalid or oversized provider proposal")
    return Inference(text.encode(),time.monotonic()-started,"ollama / "+choice["model"],"")
