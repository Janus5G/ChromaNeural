"""Bounded adapters. Source bytes remain separate from compiled output."""
import struct
from .storage import MAX_FILE
def optical(content):
    if not isinstance(content,bytes) or len(content)>MAX_FILE or len(content)<42: raise ValueError("OPTB size")
    # Reference decoder checks version, indices, CRC and exact framing.
    from reference_core.optical_bridge import decode_optb
    if content[:4]!=b"OPTB" or content[4]!=1 or content[5]!=3: raise ValueError("Unsupported OPTB profile")
    symbol_count=struct.unpack_from("<Q",content,16)[0]
    if symbol_count>65536: raise ValueError("Symbol allocation budget")
    return decode_optb(content)
