"""Host-owned RoboForge V1 grants. No balance, pricing or telemetry authority.

The issuer is injected by the trusted application composition layer, never by
model arguments or a saved MCP profile. Importing this module loads no keys and
starts no service. The private key is never sent to RoboForge or persisted here.
"""
import base64
import hashlib
import json
import secrets
import time
from .mcp_config import connection_key
from .mcp_usage import ID, UsageBlocked

GRANT_META = 'net.aagii.chromaneural/execution-grant'
RECEIPT_META = 'net.aagii.chromaneural/authorization-receipt'
DOMAIN = b'RoboForge/ChromaNeural-Grant/v1\n'
CONTROLLED_TOOL = 'roboforge_refract_compile_cpl_v1'


def canonical_arguments(value):
    """The agreed V1 JSON subset, including Unicode and JS safe integers."""
    def check(item, depth=0):
        if depth > 32:
            raise UsageBlocked('RoboForge argument nesting limit')
        if item is None or type(item) is bool:
            return
        if type(item) is int and abs(item) <= 9007199254740991:
            return
        if type(item) is str:
            if any(0xd800 <= ord(c) <= 0xdfff for c in item):
                raise UsageBlocked('RoboForge invalid Unicode')
            return
        if type(item) is list:
            for child in item:
                check(child, depth+1)
            return
        if type(item) is dict and len(item) <= 512 and all(type(k) is str for k in item):
            for key, child in item.items():
                check(key, depth+1)
                check(child, depth+1)
            return
        raise UsageBlocked('RoboForge V1 requires bounded integral JSON values')
    check(value)
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _encoded(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')


class RoboForgeAuthorization:
    """Explicit pinned connection/session; all capabilities remain opt-in.

    Supplying this adapter does not grant permission to use a tool or allocate
    Fair Use credit. Host.call still performs every approval and journal gate.
    Only the current reviewed compiler tool has an executable grant contract.
    """
    def __init__(self, private_key, server, session_id, *, wall_millis=1500,
                 input_bytes=8192, output_bytes=26000):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        if not isinstance(private_key, Ed25519PrivateKey):
            raise UsageBlocked('An Ed25519 signing authority is required')
        if not isinstance(session_id, str) or not ID.fullmatch(session_id):
            raise UsageBlocked('Invalid RoboForge session binding')
        from urllib.parse import urlsplit
        endpoint = urlsplit(server['endpoint'])
        if (server['transport'] != 'http' or endpoint.scheme != 'http'
                or endpoint.hostname not in ('127.0.0.1', '::1')
                or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment):
            raise UsageBlocked('Managed RoboForge requires its pinned local connection')
        ceilings = {'maxWallMillis': (wall_millis, 5500),
                    'maxInputBytes': (input_bytes, 8192),
                    'maxOutputBytes': (output_bytes, 26000)}
        if any(type(v) is not int or not 0 < v <= maximum for v, maximum in ceilings.values()):
            raise UsageBlocked('Invalid RoboForge technical ceiling')
        self._key = private_key
        self.target = connection_key(server)
        self.session_id = session_id
        self.envelope = {k: v for k, (v, _) in ceilings.items()}
        self.key_id = hashlib.sha256(private_key.public_key().public_bytes(
            Encoding.DER, PublicFormat.SubjectPublicKeyInfo)).hexdigest()

    def prepare(self, server, tool, arguments, operation):
        if connection_key(server) != self.target or tool != CONTROLLED_TOOL:
            raise UsageBlocked('RoboForge grant target/tool is not approved for this adapter')
        if not isinstance(operation, str) or not ID.fullmatch(operation):
            raise UsageBlocked('RoboForge operation identity required')
        encoded = canonical_arguments(arguments)
        if len(encoded) > self.envelope['maxInputBytes']:
            raise UsageBlocked('RoboForge input exceeds its approved ceiling')
        now = time.time_ns() // 1_000_000
        payload = {'schemaVersion': 1, 'issuer': 'ChromaNeural', 'audience': 'RoboForge',
                   'sessionId': self.session_id, 'authorizationId': secrets.token_hex(24),
                   'reservationId': operation, 'tool': tool,
                   'argumentsSha256': hashlib.sha256(encoded).hexdigest(),
                   'issuedAtMs': now, 'expiresAtMs': now+15000,
                   'nonce': _encoded(secrets.token_bytes(24)),
                   'resourceEnvelope': dict(self.envelope)}
        # Prepared only in host memory. Host forwards it only after durable
        # reservation/dispatch and a final approval check. No retry is permitted.
        return {'keyId': self.key_id, 'payload': payload,
                'signature': _encoded(self._key.sign(DOMAIN+canonical_arguments(payload)))}

    @staticmethod
    def correlate(grant, metadata):
        """Receipt correlates execution; it never establishes a resource debit."""
        expected = {k: grant['payload'][k] for k in ('authorizationId', 'reservationId', 'tool')}
        expected['authorizationAccepted'] = True
        receipt = metadata.get(RECEIPT_META) if type(metadata) is dict else None
        if (type(receipt) is not dict or receipt != expected
                or receipt.get('authorizationAccepted') is not True):
            raise UsageBlocked('RoboForge receipt unavailable or mismatched; reconciliation required')
        # Do not read execution-telemetry, even if it claims authoritative status.
        return dict(expected)
