"""Explicit local data exchange. No automatic projects scan, model execution or upload."""
import argparse,json,socket
from pathlib import Path
from .speech import Credentials,Inbox,send,receive_connection,MAX_BYTES
def main():
    p=argparse.ArgumentParser();p.add_argument("--config",required=True);sub=p.add_subparsers(dest="op",required=True)
    tx=sub.add_parser("send");tx.add_argument("--host",required=True);tx.add_argument("--port",required=True,type=int);tx.add_argument("--file",required=True);tx.add_argument("--id",required=True);tx.add_argument("--kind",default="data")
    rx=sub.add_parser("receive-once");rx.add_argument("--bind",required=True);rx.add_argument("--port",required=True,type=int);rx.add_argument("--inbox",required=True)
    a=p.parse_args();config=json.loads(Path(a.config).read_text())
    if config.get("sharingConsent") is not True:raise PermissionError("Explicit data-sharing consent required")
    c=Credentials(Path(config["certificate"]),Path(config["privateKey"]),config["approvedPeerCertificates"])
    if a.op=="send":
        path=Path(a.file)
        with path.open("rb") as f:body=f.read(MAX_BYTES+1)
        if len(body)>MAX_BYTES:raise ValueError("Data limit 1 MiB")
        result=send(a.host,a.port,c,a.id,a.kind,body)
    else:
        inbox=Inbox(a.inbox)
        try:
            with socket.socket() as listener:
                listener.bind((a.bind,a.port));listener.listen(1);listener.settimeout(30)
                print(json.dumps({"status":"LISTENING","port":listener.getsockname()[1]}),flush=True)
                raw,_=listener.accept()
                try:result=receive_connection(raw,c,inbox)
                finally:raw.close()
        finally:inbox.close()
    print(json.dumps(result))
if __name__=="__main__":
    try:main()
    except Exception as e:print(json.dumps({"status":"FAIL","error":str(e)}));raise SystemExit(1)
