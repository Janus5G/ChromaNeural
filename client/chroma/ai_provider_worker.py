"""Fixed subprocess boundary for the existing owner-approved loopback adapter."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from chroma.ai_provider import selection
from chroma.local_ai import suggest_ollama


def main():
    raw=sys.stdin.buffer.read(65537)
    if len(raw)>65536:raise ValueError("Input limit")
    request=json.loads(raw)
    if not isinstance(request,dict) or set(request)!={"source","instruction","model"}:raise ValueError("Request shape")
    selection("ollama",request["model"])
    source=request["source"];instruction=request["instruction"]
    if not isinstance(source,str) or len(source.encode())>8192:raise ValueError("Source limit")
    if not isinstance(instruction,str) or not 0<len(instruction)<=2000:raise ValueError("Instruction limit")
    data=suggest_ollama(source,request["model"],instruction)
    if not isinstance(data,bytes) or len(data)>65536:raise ValueError("Output limit")
    sys.stdout.write(json.dumps({"proposal":data.decode("utf-8")},ensure_ascii=True))


if __name__=="__main__":
    try:main()
    except Exception:
        # Never echo source, prompts or service response bodies into queue error logs.
        sys.stderr.write("Selected AI provider failed\n");raise SystemExit(1)
