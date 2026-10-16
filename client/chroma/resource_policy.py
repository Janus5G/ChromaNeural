"""Prospective Resource Fair Use V2. Integer ticks, never a call price.

This module grants no credit or execution authority. Both ledger contribution
and trusted execution consumption must use these units. Legacy credit is not
converted by importing or calling this module.
"""
from dataclasses import dataclass

POLICY_VERSION = 2
POLICY_ID = 'chromaneural-resource-v2-data-cpu'
TICKS_PER_POINT = 107374182400000000
TICKS_PER_MICROPOINT = 107374182400
DATA_TICKS = 102400000000
CPU_TICKS = 107374182400
MAX_VALUE = 2**127 - 1


def natural(value):
    if type(value) is not int or not 0 <= value <= MAX_VALUE:
        raise ValueError('Invalid resource quantity')
    return value


@dataclass(frozen=True)
class Resources:
    data_bytes: int = 0
    cpu_micros: int = 0
    ram_byte_micros: int = 0
    gpu_micros: int = 0

    def __post_init__(self):
        for value in (self.data_bytes, self.cpu_micros, self.ram_byte_micros, self.gpu_micros):
            natural(value)
        if self.ram_byte_micros or self.gpu_micros:
            raise ValueError('RAM-time and GPU settlement are disabled')
        natural(self.data_bytes * DATA_TICKS + self.cpu_micros * CPU_TICKS)

    @property
    def ticks(self):
        return self.data_bytes * DATA_TICKS + self.cpu_micros * CPU_TICKS

    def contains(self, actual):
        return (type(actual) is Resources and actual.data_bytes <= self.data_bytes
                and actual.cpu_micros <= self.cpu_micros)


def accumulate(remainder, resources):
    """Project whole micro-points for a ledger while retaining EVERY tick."""
    natural(remainder)
    if remainder >= TICKS_PER_MICROPOINT or type(resources) is not Resources:
        raise ValueError('Invalid carry or resources')
    return divmod(remainder + resources.ticks, TICKS_PER_MICROPOINT)


def display(ticks):
    """Display only; accounting always retains ticks, including hidden digits."""
    natural(ticks)
    whole, fraction = divmod(ticks, TICKS_PER_POINT)
    return f'{whole}.{fraction * 10**12 // TICKS_PER_POINT:012d}'


class DataBroker:
    """Count bytes at the explicit workload-payload boundary, not MCP frames.

    The trusted caller supplies immutable payload bytes before transport wrapping
    or after unwrapping. It must not feed control-plane traffic or internal copies.
    A boundary event ID is duplicate-safe; IDs are host assigned, never model IDs.
    This primitive alone does not attest a remote server's CPU or disk/network IO.
    """
    def __init__(self, maximum):
        self.maximum = natural(maximum)
        self.total = 0
        self._events = {}

    def cross(self, event, direction, payload):
        import hashlib
        if direction not in ('input', 'output') or type(payload) is not bytes:
            raise ValueError('Workload payload bytes required')
        if not isinstance(event, str) or not 1 <= len(event) <= 128:
            raise ValueError('Invalid boundary event')
        signature = (direction, len(payload), hashlib.sha256(payload).digest())
        if event in self._events:
            if self._events[event] != signature:
                raise ValueError('Conflicting boundary event')
            return
        if len(self._events) >= 1024 or self.total + len(payload) > self.maximum:
            raise ValueError('Workload data ceiling exceeded')
        self._events[event] = signature
        self.total += len(payload)
