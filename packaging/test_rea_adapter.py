"""REA adapter bounds and generic MCP regressions; no external connections."""
import asyncio,copy,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'client'))
from chroma import mcp_rea,rea_isolation
from chroma.mcp_client import definition,tools,Host,connect
from chroma.mcp_config import fingerprint
from mcp_types import Tool

def tool(name='safe_static'):
    return Tool(name=name,description='Synthetic static tool',inputSchema={'type':'object'},annotations={'readOnlyHint':True})

class Client:
    server_capabilities=SimpleNamespace(tools={})
    def __init__(self,items,rea=True,next_cursor=None):
        self.items=items;self.chroma_rea=rea;self.next_cursor=next_cursor
    async def list_tools(self,cursor=None):
        return SimpleNamespace(tools=self.items,next_cursor=self.next_cursor)

class Adapter(unittest.TestCase):
    def setUp(self):
        self.safe=tool()
        self.audit=patch.object(mcp_rea,'AUDITED_TOOLS',{'safe_static':fingerprint(definition(self.safe))})
        self.audit.start()
    def tearDown(self):self.audit.stop()
    def test_only_audited_subset_exposed_without_assuming_207(self):
        for count in (1,33,209):
            client=Client([self.safe]+[tool('unknown_'+str(i)) for i in range(count)])
            result=asyncio.run(tools(client))
            self.assertEqual([v['name'] for v in result],['safe_static'])
            self.assertEqual(client.chroma_rea_catalog_count,count+1)
    def test_changed_or_missing_contract_fails_closed(self):
        changed=tool();changed.description='Unreviewed change'
        for items in ([changed],[tool('missing')]):
            with self.assertRaises(ValueError):asyncio.run(tools(Client(items)))
    def test_duplicate_pagination_and_full_catalog_limits(self):
        for client in (Client([self.safe,self.safe]),Client([self.safe],next_cursor='loop'),
                       Client([self.safe]+[tool('unknown_'+str(i)) for i in range(512)])):
            with self.assertRaises(ValueError):asyncio.run(tools(client))
    def test_generic_limits_unchanged(self):
        with self.assertRaisesRegex(ValueError,'MCP discovery limit'):
            asyncio.run(tools(Client([tool('generic_'+str(i)) for i in range(33)],rea=False)))
        oversized=tool();oversized.description='x'*17000
        with self.assertRaisesRegex(ValueError,'MCP tool definition limit'):definition(oversized)
    def test_selected_definition_still_uses_generic_size_limit(self):
        oversized=tool();oversized.description='x'*17000
        with self.assertRaisesRegex(ValueError,'MCP tool definition limit'):
            asyncio.run(tools(Client([oversized])))
    def test_broken_rea_target_cannot_fall_back(self):
        server={'id':'rea-missing','transport':'stdio','command':'/missing/node','args':['/missing/rea.mjs','mcp']}
        self.assertTrue(mcp_rea.is_rea_target(server))
        self.assertFalse(mcp_rea.valid_launch(server['command'],server['args']))
        async def check():
            with patch.object(rea_isolation,'available',return_value=False):
                async with rea_isolation.transport(server):self.fail('uncontained process')
        with self.assertRaisesRegex(RuntimeError,'isolation unavailable'):asyncio.run(check())
    @unittest.skipUnless(sys.platform == 'linux', 'Linux isolation')
    def test_one_session_budget_and_lock_release_after_failure(self):
        with self.assertRaisesRegex(ValueError, 'synthetic failure'):
            with rea_isolation.exclusive_slot():
                with self.assertRaisesRegex(RuntimeError, 'already busy'):
                    with rea_isolation.exclusive_slot():
                        self.fail('second resource budget')
                raise ValueError('synthetic failure')
        with rea_isolation.exclusive_slot():
            pass

    def test_curated_profile_and_audit_match(self):
        from chroma.mcp_catalog import PROFILES
        # Restore the real audit for this identity check.
        self.audit.stop()
        rea=next(p for p in PROFILES if p.id=='rea')
        self.assertEqual(set(rea.read_tools),set(mcp_rea.AUDITED_TOOLS))
        self.assertEqual(len(rea.read_tools),8)
        self.assertFalse(rea.enabled)

if __name__=='__main__':unittest.main(verbosity=2)