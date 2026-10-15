from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"client"))
from chroma.speech_cli import main
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("PEER_TRANSFER_FAILED: "+str(e),file=sys.stderr);raise SystemExit(1)
