"""Central MCP host integration with synthetic meters; no live vendor calls."""
import asyncio, contextlib, sys, tempfile, time, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'client'))
from chroma.mcp_client import Host
from chroma.mcp_config import Config, fingerprint
from chroma.mcp_usage import Usage, ResourceBudget, UsageBlocked, digest
from chroma.resource_policy import Resources, TICKS_PER_POINT as K
from chroma.resource_execution import ControlledExecution


class CentralExecution(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='chroma-v2-host-')
        self.root=Path(self.temp.name);now=time.monotonic()
        self.usage=Usage(self.root,balance_reader=lambda _:ResourceBudget(
            'a'*64,1,'synthetic-allowance',K,K,1,now,now+120))
        self.envelope=Resources(1000,100000)
        self.task=self.usage.reserve(digest('task'),['fixture'],self.envelope,approved=True)[0]
        config=Config(self.root)
        config.put({'id':'fixture','name':'Fixture','transport':'http',
                    'endpoint':'https://example.invalid/mcp','command':'','args':[]})
        self.tool={'name':'read','description':'Read fixture','input_schema':{'type':'object','properties':{},'additionalProperties':False},'annotations':{'readOnlyHint':True}}
        config.update('fixture',approved=True,enabled=True,tools={'read':fingerprint(self.tool)})
        self.entry=('fixture',config.server('fixture',enabled=True),self.tool)
        self.closed=False;self.called=0;self.fail_meter=False;self.tool_error=False
        owner=self
        class Meter:
            def start(self):pass
            def finish(self):
                if owner.fail_meter:raise RuntimeError('Unavailable')
                return Resources(2,100)
            def close(self):owner.closed=True
        self.execution=ControlledExecution(self.usage,self.envelope,lambda _:Meter())
    def tearDown(self):self.temp.cleanup()
    def invoke(self,arguments=None,entry=None,execution=True):
        owner=self
        async def call_tool(name,args):
            owner.called+=1
            return SimpleNamespace(is_error=owner.tool_error,content=[SimpleNamespace(type='text',text='untrusted fixture')],reported_price=0)
        client=SimpleNamespace(session=SimpleNamespace(call_tool=call_tool))
        @contextlib.asynccontextmanager
        async def connect(*args):yield client
        async def tools(*args):return [self.tool]
        with patch('chroma.mcp_client.connect',connect),patch('chroma.mcp_client.tools',tools):
            return asyncio.run(Host(self.root,usage_task=self.task,
                resource_execution=self.execution if execution else None,
                roboforge_authorization=getattr(self,'optional_issuer',None)).call(entry or self.entry,arguments or {},'op'))
    def test_approved_host_call_settles_only_host_measurement(self):
        result=self.invoke()
        self.assertEqual(result,{'is_error':False,'text':'untrusted fixture'})
        self.assertEqual(self.usage.quote()['used_ticks'],Resources(2,100).ticks)
        self.assertTrue(self.closed);self.assertEqual(self.called,1)
    def test_tool_error_still_settles_actual_usage(self):
        self.tool_error=True
        self.assertTrue(self.invoke()['is_error'])
        self.assertEqual(self.usage.quote()['used_ticks'],Resources(2,100).ticks)
    def test_missing_measurement_retains_reservation(self):
        self.fail_meter=True
        with self.assertRaises(UsageBlocked):self.invoke()
        self.assertTrue(self.closed)
        self.assertEqual(self.usage.quote()['reserved_ticks'],self.envelope.ticks)
        self.assertEqual(self.usage.quote()['used_ticks'],0)
    def test_validation_failure_does_not_dispatch(self):
        with self.assertRaises(Exception):self.invoke({'unexpected':1})
        self.assertEqual(self.called,0)
        self.assertEqual(self.usage.finish(self.task),self.envelope.ticks)
    def test_revocation_prevents_execution(self):
        Config(self.root).update('fixture',tools={})
        with self.assertRaises(PermissionError):self.invoke()
        self.assertEqual(self.called,0)
    def test_unmetered_generic_or_future_profile_fails_closed(self):
        with self.assertRaises(UsageBlocked):self.invoke(execution=False)
        self.assertEqual(self.called,0)
        self.assertEqual(self.usage.quote()['used_ticks'],0)

    def test_foreign_configuration_cannot_supply_allowance(self):
        self.execution.usage.directory=self.root/'different-owner-config'
        with self.assertRaises(PermissionError):self.invoke()
        self.assertEqual(self.called,0)

    def test_unrelated_roboforge_authorizer_does_not_block_generic_mcp(self):
        from chroma.roboforge_authorization import RoboForgeAuthorization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        self.optional_issuer=RoboForgeAuthorization(Ed25519PrivateKey.generate(),
            {'id':'other','transport':'http','endpoint':'http://127.0.0.1:3219/mcp','command':'','args':[]},
            'synthetic-session')
        self.assertFalse(self.invoke()['is_error'])
        self.assertEqual(self.called,1)

if __name__=='__main__':unittest.main(verbosity=2)
