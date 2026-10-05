"""Bounded native CPU inference; no network, file tools or model code execution."""
from pathlib import Path
from dataclasses import dataclass
import hashlib,json,os,platform,re,subprocess,tempfile,time

BASE=Path(__file__).resolve().parents[2]
MODEL_SHA="1d9614638d18024d0fbb36575a15f1302a3adf044df10345688ec4f6e1c4ff32"
@dataclass(frozen=True)
class Inference:
    source: bytes
    seconds: float
    provider: str
    diagnostics: str

def clean_completion(text):
    text=text.strip()
    if text.endswith("[end of text]"): text=text[:-13].rstrip()
    fence=chr(96)*3
    match=re.fullmatch(fence+r"[^\n]*\n(.*?)\n"+fence,text,re.S)
    if match: text=match[1]
    if not text or len(text.encode())>65536 or "\x00" in text:
        raise ValueError("Invalid or oversized local model proposal")
    return (text.rstrip()+"\n").encode()

def runtime(base=BASE):
    arch=platform.machine().lower()
    if arch not in ("amd64","x86_64"): raise RuntimeError("No bundled runtime for this CPU; configure another local provider")
    if os.name=="nt": rel="runtime/windows-x64/llama-completion.exe"
    elif platform.system()=="Linux": rel="runtime/linux-x64/llama-b10964/llama-completion"
    else: raise RuntimeError("No bundled runtime for this OS; local editor remains available")
    exe=base/rel
    model=base/"models/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf"
    if not exe.is_file() or not model.is_file(): raise RuntimeError("Install the verified optional CPU AI runtime/model")
    with model.open("rb") as stream:
        if hashlib.file_digest(stream,"sha256").hexdigest()!=MODEL_SHA:
            raise RuntimeError("Local model SHA-256 mismatch")
    return exe,model

def infer(source,instruction,*,timeout=90,threads=4,max_tokens=256,base=BASE,execution=None):
    if not isinstance(source,str) or len(source.encode())>8192: raise ValueError("CPU AI source limit is 8 KiB")
    if not isinstance(instruction,str) or not instruction or len(instruction)>2000: raise ValueError("Instruction limit")
    if not 1<=threads<=8 or not 1<=max_tokens<=512 or not 1<=timeout<=120: raise ValueError("Inference budget")
    if execution is not None:execution.check()
    exe,model=runtime(base)
    prompt=("<|im_start|>system\nYou are a code assistant. Return only complete replacement source. "
            "Do not call tools or execute code. Do not include explanations or markdown.<|im_end|>\n"
            "<|im_start|>user\nTask: "+instruction+"\nSource:\n"+source+
            "<|im_end|>\n<|im_start|>assistant\n")
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix="chroma-local-ai-") as tmp:
        folder=Path(tmp); promptfile=folder/"prompt.txt"; promptfile.write_text(prompt,encoding="utf-8")
        cmd=[str(exe),"-m",str(model),"-t",str(threads),"-c","4096","-n",str(max_tokens),
             "--temp","0","--seed","1","--no-conversation","--no-display-prompt",
             "--simple-io","--no-warmup","-f",str(promptfile)]
        if execution is not None:
            cmd += ["-tb",str(threads),"--load-mode","none","--lazy-mode","off","-ngl","0"]
        opts={"creationflags":subprocess.CREATE_NO_WINDOW} if os.name=="nt" else {"start_new_session":True}
        env={k:v for k,v in os.environ.items() if not k.startswith(("LLAMA_","GGML_"))}
        with (folder/"out").open("wb") as out,(folder/"err").open("wb") as err:
            launcher=subprocess.Popen if execution is None else execution.spawn
            proc=launcher(cmd,stdin=subprocess.DEVNULL,stdout=out,stderr=err,env=env,**opts)
            try:
                while proc.poll() is None:
                    if execution is not None:execution.check()
                    if time.monotonic()-started>timeout: raise TimeoutError("Local inference deadline exceeded")
                    if out.tell()>262144 or err.tell()>262144: raise RuntimeError("Local inference output limit")
                    time.sleep(0.05)
            finally:
                if proc.poll() is None: proc.kill()
                proc.wait(timeout=5)
        raw=(folder/"out").read_bytes(); diag=(folder/"err").read_bytes()
        if len(raw)>262144 or len(diag)>262144: raise RuntimeError("Local inference output limit")
        if proc.returncode: raise RuntimeError("Local CPU inference failed rc="+str(proc.returncode)+": "+diag.decode(errors="replace")[-1500:])
        return Inference(clean_completion(raw.decode("utf-8")),time.monotonic()-started,
                         "llama.cpp b10964 / Qwen2.5-Coder-0.5B-Instruct Q4_K_M",diag.decode(errors="replace"))
