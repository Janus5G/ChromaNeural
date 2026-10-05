"""Only executed inside the local sandbox, never loads source as Python."""
import contextlib,io,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"reference_core"))
sys.path.insert(0,str(ROOT))
def execute(req):
    if set(req)!={"profile","action","source"}: raise ValueError("Request fields")
    source=req["source"];profile=req["profile"];action=req["action"]
    if not isinstance(source,str) or len(source.encode())>65536: raise ValueError("Source limit")
    if action not in ("compile","simulate"): raise ValueError("Action")
    import cpl_adapter
    if profile in ("cpl-legacy","cpl-spec"):
        fn=cpl_adapter._compile_original_cpl if profile=="cpl-legacy" else cpl_adapter._compile_specification_cpl
        cpa,dialect=fn(source)
        result={"profile":profile,"dialect":dialect,"output":cpa}
        if action=="simulate":
            runner=cpl_adapter._run_original_cpa if profile=="cpl-legacy" else cpl_adapter._run_specification_cpa
            output,state=runner(cpa);result.update(output="\n".join(map(str,output)),state=state,cpa=cpa)
        return result
    if profile in ("cpa-legacy","cpa-spec"):
        if action=="compile":
            if profile=="cpa-legacy":
                from chromaplex_os.assembler import assemble
                obj=assemble(cpl_adapter._normalize_original_cpa(source))
            else:
                from chromaplex.cpa_assembler import assemble
                obj=assemble(source)
            return {"profile":profile,"output":repr(obj)}
        fn=cpl_adapter._run_original_cpa if profile=="cpa-legacy" else cpl_adapter._run_specification_cpa
        output,state=fn(source);return {"profile":profile,"output":"\n".join(map(str,output)),"state":state}
    if profile=="prisme-asm":
        import prisme_isa,prisme_runner
        program=prisme_isa.assemble(source)
        if len(program)>256: raise ValueError("PRISME program exceeds 256 bytes")
        result={"profile":profile,"hex":program.hex(),"output":program.hex()}
        if action=="simulate":
            out=io.StringIO()
            with contextlib.redirect_stdout(out): rc=prisme_runner.run(program,max_steps=10000)
            if rc: raise RuntimeError("PRISME instruction budget exceeded")
            result["output"]=out.getvalue()
        return result
    raise ValueError("Unsupported profile")
def main():
    try:
        raw=sys.stdin.buffer.read(70001)
        if len(raw)>70000: raise ValueError("Request limit")
        result=execute(json.loads(raw)); encoded=json.dumps({"ok":True,**result},ensure_ascii=True)
        if len(encoded)>131072: raise ValueError("Result size limit")
        print(encoded);return 0
    except Exception as e:
        print(json.dumps({"ok":False,"error":str(e)},ensure_ascii=True));return 1
if __name__=="__main__":raise SystemExit(main())
