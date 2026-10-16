"""Resource correction: fail-closed acceptance, not resource-settlement proof."""
import asyncio, contextlib, copy, json, sys, tempfile, threading, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"client"));sys.path.insert(0,str(ROOT/"packaging"))
from chroma.mcp_usage import Usage, UsageBlocked, POINT, MCP_USAGE_POLICY_VERSION, digest, task_digest, require_resource_policy
from chroma.mcp_config import Config, fingerprint
from chroma.mcp_client import Host
from chroma.ai_provider import selected_inference

class ResourceGate(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="resource-gate-");self.root=Path(self.temp.name)
        self.reader_patch=patch('chroma.mcp_usage.fresh_balance',side_effect=AssertionError("No live network query allowed"))
        self.reader=self.reader_patch.start();self.addCleanup(self.reader_patch.stop)
        self.usage=Usage(self.root)
    def tearDown(self):self.temp.cleanup()
    def test_version_boundary(self):
        self.assertEqual(MCP_USAGE_POLICY_VERSION,2)
        self.assertNotEqual(task_digest("s","i","m",[]),digest([1,"s","i","m",[]]))
    def test_no_guessed_quote_reservation_or_settlement(self):
        methods=[lambda:self.usage.quote(),lambda:self.usage.reserve(digest('r'),['fixture'],2400000,approved=True),
            lambda:self.usage.validate_task('legacy','r',['fixture']),
            lambda:self.usage.dispatch('legacy','op','fixture','read',digest('f'),digest('r'),lambda:None),
            lambda:self.usage.completed('op','SUCCESS'),lambda:self.usage.finish('legacy')]
        for method in methods:
            with self.assertRaisesRegex(UsageBlocked,'normalization'):method()
        self.reader.assert_not_called();self.assertEqual(list(self.root.iterdir()),[])
    def test_internal_writer_also_blocked(self):
        with self.assertRaises(UsageBlocked):
            with self.usage._transaction():self.fail('writer must not open')
        self.assertEqual(list(self.root.iterdir()),[])
    def test_legacy_and_corrupt_state_preserved_no_refund(self):
        files={'mcp-usage.sqlite3':b'unknown legacy or corrupt state', '.mcp-usage-v1.key':b'fixture-key',
               '.mcp-usage-v1.seal':b'fixture-seal'}
        for name,data in files.items():(self.root/name).write_bytes(data)
        for fn in (self.usage.quote,lambda:self.usage.finish('ambiguous-task')):
            with self.assertRaises(UsageBlocked):fn()
        self.assertEqual({p.name:p.read_bytes() for p in self.root.iterdir()},files)
    def test_concurrent_tasks_cannot_create_exposure(self):
        results=[]
        def reserve():
            try:self.usage.reserve(digest('r'),['fixture'],500000,approved=True)
            except UsageBlocked:results.append('blocked')
        threads=[threading.Thread(target=reserve) for _ in range(2)]
        for t in threads:t.start()
        for t in threads:t.join(2);self.assertFalse(t.is_alive())
        self.assertEqual(results,['blocked','blocked']);self.assertEqual(list(self.root.iterdir()),[])
    def test_bootstrap_fresh_stale_and_missing_cannot_enable_unpriced_execution(self):
        # A balance, even a valid one, is not normalization authority.
        for state in ('bootstrap-only','fresh-earned','stale','missing'):
            with self.subTest(state=state),self.assertRaises(UsageBlocked):self.usage.quote()
        self.reader.assert_not_called()
    def configure(self,rea=False):
        c=Config(self.root)
        server={'id':'fixture','name':'Fixture','transport':'http','endpoint':'https://example.invalid/mcp','command':'','args':[]}
        if rea:server.update(transport='stdio',endpoint='',command='/missing/node',args=['/missing/rea.mjs','mcp'])
        c.put(server)
        tool={'name':'inspect_fixture','description':'Read fixture','input_schema':{'type':'object','properties':{},'additionalProperties':False},'annotations':{'readOnlyHint':True}}
        c.update('fixture',approved=True,enabled=True,tools={tool['name']:fingerprint(tool)})
        return c,('fixture',c.server('fixture',enabled=True),tool)
    def test_generic_and_rea_execution_block_before_process_or_network(self):
        for rea in (False,True):
            c,entry=self.configure(rea)
            with patch('chroma.mcp_client.connect',side_effect=AssertionError('Must not launch')) as connect:
                with self.assertRaises(UsageBlocked):asyncio.run(Host(self.root).call(entry,{},'op'))
                connect.assert_not_called()
            self.assertFalse(self.usage.path.exists())
    def test_approval_and_validation_still_precede_dispatch(self):
        c,entry=self.configure()
        with self.assertRaises(Exception):asyncio.run(Host(self.root).call(entry,{'invalid':1},'op'))
        c.update('fixture',tools={})
        with self.assertRaises(PermissionError):asyncio.run(Host(self.root).call(entry,{},'op'))
        self.assertFalse(self.usage.path.exists())
    def test_free_discovery_no_journal_or_billing(self):
        c,entry=self.configure()
        client=SimpleNamespace(protocol_version='fixture',server_capabilities=SimpleNamespace(resources=None))
        @contextlib.asynccontextmanager
        async def connect(*a,**kw):yield client
        async def tools(*a):return [entry[2]]
        with patch('chroma.mcp_client.connect',connect),patch('chroma.mcp_client.tools',tools):
            found=asyncio.run(Host(self.root).discover('fixture'))
        self.assertEqual(found['tools'],[entry[2]])
        self.assertFalse(self.usage.path.exists())
    def test_self_reported_metrics_never_price_authority(self):
        for metrics in ({'cpuMicros':1},{'cpuMicros':999999999,'points':0}):
            with self.assertRaises(UsageBlocked):self.usage.completed('op',metrics)
        self.assertFalse(self.usage.path.exists())
    def test_local_ai_independent(self):
        with patch.object(Usage,'_transaction',side_effect=UsageBlocked('unavailable')):
            self.assertEqual(selected_inference('x','keep',None,bundled=lambda *a,**k:'core-ok'),'core-ok')
    def test_workqueue_and_chromaspeech_independent(self):
        from test_mcp import Acceptance
        case=Acceptance('test_08_queue_and_speech_minimal_regression');result=unittest.TestResult()
        with patch.object(Usage,'_transaction',side_effect=UsageBlocked('unavailable')):case.run(result)
        self.assertTrue(result.wasSuccessful(),result.errors+result.failures)
    def test_snapshot_unmodified_and_no_backend_query(self):
        snapshot={'account':{'earned':7000000,'spent':0,'bootstrap':4000000}}
        before=copy.deepcopy(snapshot)
        u=Usage(self.root,balance_reader=lambda _:snapshot)
        with self.assertRaises(UsageBlocked):u.quote()
        self.assertEqual(snapshot,before);self.assertEqual(list(self.root.iterdir()),[])
    def test_no_fixed_cost_or_call_based_reservation_in_production(self):
        source=(ROOT/'client/chroma/mcp_usage.py').read_text()
        for old in ('CHECK(amount=1000000)','remaining-1','available"]//POINT','remaining)*POINT','LEASE_SECONDS'):
            self.assertNotIn(old,source)
        ui=(ROOT/'client/chroma/mcp_usage_ui.py').read_text()
        self.assertNotIn('["calls"]',ui)
    @unittest.skip('LIVE UNTESTED: V2 authority activation and complete trusted execution adapter are not connected')
    def test_real_resource_cost_settlement_and_unused_release(self):
        # No invented weights, fake measurements or successful economic acceptance.
        pass

if __name__=='__main__':unittest.main(verbosity=2)
