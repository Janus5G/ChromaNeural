"""Local proposals never write files until explicit review and acceptance."""
from dataclasses import dataclass
import difflib,hashlib
@dataclass(frozen=True)
class Proposal:
    before_hash:str
    proposed:bytes
    diff:str
def propose(original,proposed):
    if len(proposed)>1024*1024: raise ValueError("Oversize proposal")
    before=original.decode("utf-8");after=proposed.decode("utf-8")
    return Proposal(hashlib.sha256(original).hexdigest(),proposed,"".join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile="current",tofile="proposed")))
def accept(workspace,name,proposal,approved=False):
    if approved is not True: raise PermissionError("Explicit approval required")
    workspace.write(name,proposal.proposed,expected=proposal.before_hash)
