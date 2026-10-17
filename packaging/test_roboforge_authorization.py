"""Exact local contract vectors and central host routing; no live account."""
import asyncio
import base64
import contextlib
import hashlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_resource_execution as host_fixture
from chroma.mcp_client import Host
from chroma.mcp_config import Config, fingerprint
from chroma.mcp_usage import UsageBlocked
from chroma.roboforge_authorization import (
    RoboForgeAuthorization, canonical_arguments, DOMAIN, GRANT_META, RECEIPT_META, CONTROLLED_TOOL)
from chroma.resource_policy import Resources
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


class Grants(unittest.TestCase):
    def setUp(self):
        self.server={'id':'fixture','transport':'http','endpoint':'http://127.0.0.1:3219/mcp',
                     'command':'','args':[]}
        self.key=Ed25519PrivateKey.generate()
        self.issuer=RoboForgeAuthorization(self.key,self.server,'synthetic-session')

    def grant(self,args=None):
        return self.issuer.prepare(self.server,CONTROLLED_TOOL,args or {'source':'var x = 1'},'operation')

    def test_exact_upstream_unicode_vectors(self):
        vectors=[({},'44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'),
            ({'source':'Hej København — æøå 😀'},'5b8bf5d0137e6b1d13d54561cd5a184873ede0bc10fe19f09e0f9a01e6606ae7'),
            ({'z':[True,3,{'k':'værdi'}],'a':False},'a4532b493ebc67117718d2483224a78acdf058abf89fd805286513a660dcb21e')]
        for value,expected in vectors:
            self.assertEqual(hashlib.sha256(canonical_arguments(value)).hexdigest(),expected)

    def test_signature_and_no_economic_fields(self):
        grant=self.grant();payload=grant['payload']
        self.key.public_key().verify(base64.urlsafe_b64decode(grant['signature']+'=='),
                                     DOMAIN+canonical_arguments(payload))
        self.assertEqual(set(payload),{'schemaVersion','issuer','audience','sessionId','authorizationId',
            'reservationId','tool','argumentsSha256','issuedAtMs','expiresAtMs','nonce','resourceEnvelope'})
        self.assertEqual(payload['expiresAtMs']-payload['issuedAtMs'],15000)
        self.assertEqual(payload['reservationId'],'operation')

    def test_target_and_tool_binding(self):
        with self.assertRaises(UsageBlocked):self.issuer.prepare(dict(self.server,endpoint='http://127.0.0.1:9999/mcp'),CONTROLLED_TOOL,{},'op')
        with self.assertRaises(UsageBlocked):self.issuer.prepare(self.server,'arbitrary_tool',{},'op')

    def test_unsafe_json_and_ceilings_rejected(self):
        for value in (1.5, float('nan'), -0.0, 9007199254740992, '\ud800', {3:'key'}):
            with self.assertRaises(UsageBlocked):canonical_arguments(value)
        with self.assertRaises(UsageBlocked):RoboForgeAuthorization(self.key,self.server,'session',wall_millis=5501)
        with self.assertRaises(UsageBlocked):self.grant({'source':'x'*8200})

    def test_receipt_exact_and_telemetry_ignored(self):
        grant=self.grant()
        receipt={k:grant['payload'][k] for k in ('authorizationId','reservationId','tool')}
        receipt['authorizationAccepted']=True
        meta={RECEIPT_META:receipt,'net.aagii.chromaneural/execution-telemetry':{'points':999999,'cpuMicros':0}}
        self.assertEqual(self.issuer.correlate(grant,meta),receipt)
        for field,value in [('authorizationAccepted',1),('reservationId','other'),('tool','other')]:
            with self.assertRaises(UsageBlocked):self.issuer.correlate(grant,{RECEIPT_META:dict(receipt,**{field:value})})

    def test_nonce_and_authorization_unique(self):
        a=self.grant()['payload'];b=self.grant()['payload']
        self.assertNotEqual(a['authorizationId'],b['authorizationId'])
        self.assertNotEqual(a['nonce'],b['nonce'])


class HostGrant(unittest.TestCase):
    def setUp(self):
        host_fixture.CentralExecution.setUp(self)
        config=Config(self.root)
        config.put({'id':'fixture','name':'Local RoboForge','transport':'http',
                    'endpoint':'http://127.0.0.1:3219/mcp','command':'','args':[]})
        self.tool['name']=CONTROLLED_TOOL
        config.update('fixture',approved=True,enabled=True,tools={CONTROLLED_TOOL:fingerprint(self.tool)})
        self.entry=('fixture',config.server('fixture',enabled=True),self.tool)
        self.issuer=RoboForgeAuthorization(Ed25519PrivateKey.generate(),self.entry[1],'synthetic-session')
        self.bad_receipt=False
    tearDown=host_fixture.CentralExecution.tearDown

    def invoke(self, with_issuer=True):
        owner=self
        async def forbidden(*args,**kwargs):raise AssertionError('Retrying SDK facade must not be called')
        async def call_tool(name,args,*,meta):
            owner.called+=1
            self.assertEqual(args,{})
            self.assertEqual(set(meta),{GRANT_META})
            grant=meta[GRANT_META]['payload']
            receipt={k:grant[k] for k in ('authorizationId','reservationId','tool')}
            receipt['authorizationAccepted']=True
            if owner.bad_receipt:receipt['reservationId']='wrong'
            return SimpleNamespace(is_error=False,content=[SimpleNamespace(type='text',text='untrusted')],
                meta={RECEIPT_META:receipt,'net.aagii.chromaneural/execution-telemetry':{'points':1000000,'cpuMicros':0}})
        client=SimpleNamespace(protocol_version='2025-11-25',call_tool=forbidden,
                               session=SimpleNamespace(call_tool=call_tool))
        @contextlib.asynccontextmanager
        async def connect(*args):yield client
        async def tools(*args):return [owner.tool]
        with patch('chroma.mcp_client.connect',connect),patch('chroma.mcp_client.tools',tools):
            return asyncio.run(Host(self.root,usage_task=self.task,resource_execution=self.execution,
                roboforge_authorization=self.issuer if with_issuer else None).call(self.entry,{},'op'))

    def test_metadata_separate_and_host_meter_authoritative(self):
        self.assertEqual(self.invoke(),{'is_error':False,'text':'untrusted'})
        self.assertEqual(self.called,1)
        self.assertEqual(self.usage.quote()['used_ticks'],Resources(2,100).ticks)

    def test_receipt_mismatch_preserves_full_hold(self):
        self.bad_receipt=True
        with self.assertRaises(UsageBlocked):self.invoke()
        self.assertEqual(self.called,1)
        self.assertEqual(self.usage.quote()['used_ticks'],0)
        self.assertEqual(self.usage.quote()['reserved_ticks'],self.envelope.ticks)

    def test_revoked_tool_never_receives_grant(self):
        Config(self.root).update('fixture',tools={})
        with self.assertRaises(PermissionError):self.invoke()
        self.assertEqual(self.called,0)
        self.assertEqual(self.usage.finish(self.task),self.envelope.ticks)

    def test_insufficient_allowance_never_dispatches(self):
        from dataclasses import replace
        reader=self.usage.balance_reader
        self.usage.balance_reader=lambda p:replace(reader(p),revision=2,available_ticks=0)
        with self.assertRaises(UsageBlocked):self.invoke()
        self.assertEqual(self.called,0)

    def test_missing_issuer_cannot_use_standalone_fallback(self):
        with self.assertRaises(PermissionError):self.invoke(with_issuer=False)
        self.assertEqual(self.called,0)
        self.assertEqual(self.usage.finish(self.task),self.envelope.ticks)

if __name__=='__main__':unittest.main(verbosity=2)
