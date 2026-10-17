"""Trusted-host resource adapter; no MCP telemetry is accepted as evidence.

Meter factories and allowance readers are application-owned dependencies, not
model arguments/configuration. There is deliberately no production factory until
the V2 authority contract and complete execution-envelope enforcement are accepted.
"""
from .mcp_usage import UsageBlocked
from .resource_policy import Resources


class ControlledExecution:
    def __init__(self, usage, envelope, meter_factory):
        if type(envelope) is not Resources or not callable(meter_factory):
            raise UsageBlocked('Trusted bounded execution adapter required')
        self.usage=usage
        self.envelope=envelope
        self.meter_factory=meter_factory
        self.meter=None

    def dispatch(self, task, operation, identifier, tool, fingerprint, request, authority):
        if self.meter is not None:
            raise UsageBlocked('Resource meter already active')
        meter=self.meter_factory(self.envelope)
        try:
            meter.start()
            self.usage.dispatch(task,operation,identifier,tool,fingerprint,request,authority,
                                envelope=self.envelope)
        except BaseException:
            meter.close()
            raise
        self.meter=meter

    def complete(self, operation, outcome):
        meter,self.meter=self.meter,None
        if meter is None:raise UsageBlocked('Resource meter unavailable')
        try:
            try:
                measured=meter.finish()
                if type(measured) is not Resources or not self.envelope.contains(measured):
                    raise UsageBlocked('Resource evidence invalid')
            except Exception:
                self.usage.completed(operation,'UNCERTAIN')
                raise UsageBlocked('Resource evidence unavailable; reservation retained') from None
            self.usage.completed(operation,outcome,measured=measured)
        finally:
            meter.close()
