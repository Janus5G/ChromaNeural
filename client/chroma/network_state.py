"""Network-only scheduling state. Local editing and private inference are never gated."""
from pathlib import Path
import json,time,threading
class NetworkState:
    def __init__(self,cache):
        self.cache=Path(cache);self.snapshot=None;self.error="Not connected";self.confirmed_at=0
        self.sharing_enabled=False;self.network_enabled=False
        self._lock=threading.Lock()
    def update(self,snapshot):
        if not isinstance(snapshot,dict) or snapshot.get("status") not in ("READY","DORMANT","UNKNOWN"):raise ValueError("Balance status")
        snapshot=dict(snapshot)
        # Candid optional fields preserve interoperability with the original ledger.
        for key in ("adjustment","debt","journalLength","journalTip"):
            value=snapshot.get(key)
            if isinstance(value,list):
                if len(value)==0:snapshot.pop(key,None)
                elif len(value)==1:snapshot[key]=value[0]
                else:raise ValueError("Invalid optional ledger field")
        account=snapshot["account"];policy=snapshot["policy"]
        for k in ("earned","spent","bootstrap","consumedBytes"):
            value=account[k]
            if isinstance(value,bool) or not str(value).isdigit():raise ValueError("Invalid ledger amount")
        earned=int(account["earned"]);spent=int(account["spent"]);bootstrap=int(account["bootstrap"])
        adjustment=snapshot.get("adjustment",0);debt=snapshot.get("debt",0)
        if isinstance(adjustment,bool) or not str(adjustment).removeprefix("-").isdigit():raise ValueError("Invalid ledger adjustment")
        if isinstance(debt,bool) or not str(debt).isdigit():raise ValueError("Invalid ledger debt")
        net=earned+bootstrap-spent+int(adjustment)
        if int(snapshot["available"])!=max(0,net) or int(debt)!=max(0,-net):raise ValueError("Ledger invariant")
        if self.snapshot and "journalLength" in self.snapshot:
            if "journalLength" not in snapshot or int(snapshot["journalLength"])<int(self.snapshot["journalLength"]):raise ValueError("Journal rollback")
            if snapshot["journalLength"]==self.snapshot["journalLength"] and snapshot.get("journalTip")!=self.snapshot.get("journalTip"):raise ValueError("Journal fork")
        if not 15000<=int(policy["ratioBps"])<=50000 or int(policy["version"])!=1:raise ValueError("Unsupported policy")
        with self._lock:
            if self.snapshot and (earned<int(self.snapshot["account"]["earned"]) or spent<int(self.snapshot["account"]["spent"]) or int(policy["epoch"])<int(self.snapshot["policy"]["epoch"])):
                raise ValueError("Ledger rollback; reconciliation required")
            self.snapshot=snapshot;self.confirmed_at=time.monotonic();self.error=""
            self.cache.parent.mkdir(parents=True,exist_ok=True)
            temp=self.cache.with_suffix(".tmp");temp.write_text(json.dumps(snapshot),encoding="utf-8");temp.replace(self.cache)
    def unavailable(self,error):
        with self._lock:self.error=str(error);self.confirmed_at=0
    def status(self):
        if not self.network_enabled:return "STOPPED"
        if self.error or not self.snapshot or time.monotonic()-self.confirmed_at>60:return "UNKNOWN"
        return self.snapshot["status"]
    def can_run(self,scope):
        if scope=="private-local":return True
        if scope=="owner-approved-contribution":return self.sharing_enabled
        if scope=="network-dependent":return self.status()=="READY"
        return False
    def display(self):
        s=self.snapshot
        if not s:return "ChromaPoints: — | Contribution: — | Consumption: — | Balance: — | Ratio: — | "+self.status()
        a=s["account"];m=a["contribution"];p=s["policy"]
        return (f"ChromaPoints earned: {int(a['earned'])/1e6:.6f} | Spent: {int(a['spent'])/1e6:.6f} | "
                f"Adjustments: {int(s.get('adjustment',0))/1e6:+.6f} | Debt: {int(s.get('debt',0))/1e6:.6f} | "
                f"Balance: {int(s['available'])/1e6:.6f} (includes {int(a['bootstrap'])/1e6:g} start allowance)\n"
                f"Verified data: {int(m['dataBytes'])} B | CPU: {int(m['cpuMicros'])/1e6:.3f} s | "
                f"RAM: {int(m['ramByteMicros'])/1e6:.0f} byte-seconds | GPU: {int(m['gpuMicros'])/1e6:.3f} s\n"
                f"Shared metadata consumed: {a['consumedBytes']} B | Current data ratio: 1:{int(p['ratioBps'])/10000:.4f} | "
                f"Policy epoch {p['epoch']} | {self.status()}"+("\n"+self.error if self.error else ""))
class NetworkQueue:
    """Only locally queued, explicitly approved callbacks; no received code becomes a job."""
    def __init__(self,state):self.state=state;self.pending=[]
    def enqueue(self,operation,*,approved=False):
        if approved is not True:raise PermissionError("User approval required")
        self.pending.append(operation)
    def step(self):
        if self.state.can_run("network-dependent") and self.pending:
            operation=self.pending[0]
            result=operation() # On failure keep the request for explicit retry/reconciliation.
            self.pending.pop(0);return result
        return None
