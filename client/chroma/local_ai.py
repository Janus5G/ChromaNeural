"""Optional loopback-only Ollama adapter. The caller obtains explicit prompt consent."""
import http.client,json
def suggest(source,model,instruction):
    if model=="bundled-cpu":
        from .native_ai import infer
        return infer(source,instruction).source
    return suggest_ollama(source,model,instruction)

def suggest_ollama(source,model,instruction):
    """Explicit Ollama selection: a model name can never switch providers."""
    if not isinstance(model,str) or not model or len(model)>120: raise ValueError("Choose an installed local model")
    if len(source.encode())>65536 or len(instruction)>2000: raise ValueError("Prompt too large")
    conn=http.client.HTTPConnection("127.0.0.1",11434,timeout=20)
    try:
        body=json.dumps({"model":model,"stream":False,"prompt":"Return only the complete replacement source, without markdown fences.\nTask: "+instruction+"\nSource:\n"+source})
        conn.request("POST","/api/generate",body,{"Content-Type":"application/json"})
        response=conn.getresponse()
        if response.status!=200: raise RuntimeError("Local model service returned "+str(response.status))
        raw=response.read(262145)
        if len(raw)>262144: raise ValueError("Model response too large")
        obj=json.loads(raw);text=obj.get("response")
        if not isinstance(text,str) or len(text.encode())>65536: raise ValueError("Invalid proposal")
        return text.encode()
    finally:conn.close()
