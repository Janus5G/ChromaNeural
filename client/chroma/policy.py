"""Truthful capability policy. No scheduler or remote job endpoint."""
from dataclasses import dataclass,field
@dataclass
class Policy:
    contribution:bool=False
    stopped:bool=True
    remote_execution:bool=False
    private_sync:bool=False
    node_metadata_sync:bool=False
    limits:dict=field(default_factory=dict)
    def enable_remote(self): raise PermissionError("REMOTE_EXECUTION=DISABLED")
    def configure(self,limits):
        if limits: raise NotImplementedError("Aggregate CPU/RAM/GPU/disk/network quotas are not yet enforced; contribution remains disabled")
    def stop(self): self.stopped=True;self.contribution=False
    def logout(self): self.private_sync=False
