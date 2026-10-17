"""Local-only MCP fair-use enforcement. No authoritative ledger mutation."""
import contextlib, hashlib, hmac, json, os, re, sqlite3, stat, time, uuid
from pathlib import Path
from dataclasses import dataclass, asdict
from .resource_policy import (POLICY_VERSION, POLICY_ID, Resources, natural, TICKS_PER_POINT)

MCP_USAGE_POLICY_VERSION = POLICY_VERSION
POINT = 1_000_000
MAX_CALLS = 4
MAX_ROWS = 10000
MAX_BYTES = 16 * 1024 * 1024
MAX_OUTSTANDING_TICKS = 100 * TICKS_PER_POINT  # Admission limit, never a price clamp.
HEX = re.compile(r"[0-9a-f]{64}")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")

class UsageBlocked(RuntimeError):
    """Safe public error: never include connection paths or journal content."""

def require_resource_policy():
    """Legacy live bridge has no V2 allowance/measurement contract. Fail closed."""
    raise UsageBlocked("Resource normalization V2 activation unavailable; MCP execution is paused")


@dataclass(frozen=True)
class ResourceBudget:
    """Trusted authority-adapter output, NOT MCP metadata or a new balance.

    The authority must exclusively allocate this allowance to this journal and
    exclude bootstrap/legacy earnings. No live adapter supplies it yet. Test
    fixtures inject it explicitly; configuration files cannot enable it.
    """
    account: str
    epoch: int
    allowance: str
    contribution_ticks: int
    available_ticks: int
    revision: int
    observed_at: float
    expires_at: float

    def validate(self):
        if not HEX.fullmatch(self.account) or not ID.fullmatch(self.allowance):
            raise UsageBlocked('Invalid resource allowance binding')
        for value in (self.epoch,self.contribution_ticks,self.available_ticks,self.revision):
            natural(value)
        now=time.monotonic()
        if (self.epoch == 0 or not 0 <= now-self.observed_at <= 60
                or not now < self.expires_at <= self.observed_at+300):
            raise UsageBlocked('Resource allowance unavailable or stale')
        return min(self.contribution_ticks,self.available_ticks)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()

def task_digest(source, instruction, model, identifiers):
    return digest([MCP_USAGE_POLICY_VERSION, source, instruction, model, identifiers])

def fresh_balance(directory):
    """Read the existing balance query only, using existing opt-in/freshness rules."""
    from .settings import Settings
    from .network_state import NetworkState
    from .icp_client import call
    settings = Settings(directory)
    v = settings.value
    if settings.error or not v["participation"] or v["paused"] or not v["connection"]:
        raise UsageBlocked("MCP balance unavailable")
    path = Path(v["connection"])
    if path.is_symlink() or path.stat().st_size > 32768:
        raise UsageBlocked("MCP balance unavailable")
    def account_binding():
        raw = path.read_bytes()
        if len(raw) > 32768:
            raise UsageBlocked("MCP account binding unavailable")
        config = json.loads(raw)
        # The existing bridge verifies this public metadata against the actual
        # node identity. Hash it without storing or displaying identity values.
        public = Path(config["identityDirectory"]) / "public_key.json"
        _safe(public)
        if public.stat().st_size > 16384:
            raise UsageBlocked("MCP account binding unavailable")
        return hashlib.sha256(raw + b"\x00" + public.read_bytes()).hexdigest()
    binding = account_binding()
    snapshot = call(path, "balance")
    # Recheck configuration after the bounded read-only request.
    after = Settings(directory)
    if after.error or after.value != v or account_binding() != binding:
        raise UsageBlocked("MCP balance changed")
    state = NetworkState(Path(directory) / "balance-cache.json")
    state.network_enabled = True
    state.update(snapshot, persist=False)
    return state, binding

# Exact decimal TEXT ticks exceed SQLite int64. No floating-point SQL arithmetic.
# Strict canonical values, all arithmetic and integrity checks happen under lock.
# Existing journals are never migrated/reset automatically.
SCHEMA = (
    "CREATE TABLE meta (version INTEGER PRIMARY KEY CHECK(version=2), anchor TEXT NOT NULL, mac TEXT NOT NULL)",
    """CREATE TABLE task (id TEXT PRIMARY KEY, request TEXT NOT NULL, connections TEXT NOT NULL,
    reserved_units TEXT NOT NULL, remaining_units TEXT NOT NULL,
    envelope TEXT NOT NULL, call_count INTEGER NOT NULL CHECK(call_count BETWEEN 0 AND 4),
    state TEXT NOT NULL CHECK(state IN ('RESERVED','RECONCILIATION','RELEASED')), created REAL NOT NULL,
    deadline REAL NOT NULL, boot TEXT NOT NULL)""",
    """CREATE TABLE operation (id TEXT PRIMARY KEY, task TEXT NOT NULL REFERENCES task(id),
    connection TEXT NOT NULL, tool TEXT NOT NULL, fingerprint TEXT NOT NULL, request TEXT NOT NULL,
    reserved_units TEXT NOT NULL, amount TEXT, envelope TEXT NOT NULL, resources TEXT,
    state TEXT NOT NULL CHECK(state IN ('DISPATCHING','RECONCILIATION','SPENT','RELEASED')),
    reserved REAL NOT NULL, dispatched REAL, outcome TEXT NOT NULL
    CHECK(outcome IN ('PENDING','SUCCESS','ERROR','UNCERTAIN')))""",
)

def _safe(path):
    for parent in (path, *path.parents):
        if parent.exists() or parent.is_symlink():
            st = parent.lstat()
            if stat.S_ISLNK(st.st_mode) or getattr(st, "st_file_attributes", 0) & 0x400:
                raise UsageBlocked("MCP journal unavailable")
    if path.exists() and (not path.is_file() or path.stat().st_size > MAX_BYTES):
        raise UsageBlocked("MCP journal unavailable")

def _boot():
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()

class Usage:
    def __init__(self, directory=None, *, balance_reader=None):
        from .settings import state_directory
        self.directory = Path(directory) if directory is not None else state_directory()
        self.path = self.directory / "mcp-usage.sqlite3"
        self.keypath = self.directory / ".mcp-usage-v2.key"
        self.sealpath = self.directory / ".mcp-usage-v2.seal"
        self.balance_reader = balance_reader or fresh_balance

    def _seal(self, db, key):
        rows = [db.execute("SELECT version,anchor FROM meta").fetchall()]
        rows += [db.execute("SELECT * FROM " + table + " ORDER BY id").fetchall() for table in ("task", "operation")]
        return hmac.new(key, json.dumps(rows, separators=(",", ":"), ensure_ascii=True).encode(), hashlib.sha256).hexdigest()

    @contextlib.contextmanager
    def _transaction(self):
        self._resource_budget()  # No legacy/live allowance => no journal mutation.
        db = None
        fd = None
        try:
            if os.name != "posix":
                raise UsageBlocked("MCP accounting requires the supported Linux host")
            import fcntl
            _safe(self.directory / ".check")
            self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            lock = self.directory / ".mcp-usage.lock"
            _safe(lock)
            fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
            until = time.monotonic() + 2
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= until:
                        raise UsageBlocked("MCP journal busy")
                    time.sleep(.02)
            for p in (self.path, self.keypath, self.sealpath, Path(str(self.path)+"-journal"),
                      Path(str(self.path)+"-wal"), Path(str(self.path)+"-shm")):
                _safe(p)
            new = not any(p.exists() for p in (self.path,self.keypath,self.sealpath))
            if not new and not all(p.exists() for p in (self.path,self.keypath,self.sealpath)):
                raise UsageBlocked("MCP journal requires reconciliation")
            if new:
                key = os.urandom(32)
                keyfd = os.open(self.keypath, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(keyfd, "wb") as stream:
                    stream.write(key); stream.flush(); os.fsync(stream.fileno())
            key = self.keypath.read_bytes()
            if len(key) != 32:
                raise UsageBlocked("MCP journal integrity failure")
            db = sqlite3.connect(self.path, timeout=2, isolation_level=None)
            os.chmod(self.path, 0o600)
            db.execute("PRAGMA trusted_schema=OFF")
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("PRAGMA max_page_count=4096")
            if db.execute("PRAGMA page_size").fetchone()[0] != 4096:
                raise UsageBlocked("MCP journal page size")
            db.execute("BEGIN IMMEDIATE")
            if new:
                for sql in SCHEMA: db.execute(sql)
                db.execute("INSERT INTO meta VALUES(2,'{}','')")
                db.execute("UPDATE meta SET mac=?", (self._seal(db,key),))
                db.commit()
                with self.sealpath.open("x",encoding="ascii") as stream:
                    stream.write(self._seal(db,key));stream.flush();os.fsync(stream.fileno())
                db.execute("BEGIN IMMEDIATE")
            actual = {r[0]:r[1] for r in db.execute("SELECT name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
            expected = {sql.split()[2]:sql for sql in SCHEMA}
            if actual != expected or db.execute("PRAGMA quick_check").fetchone() != ("ok",):
                raise UsageBlocked("MCP journal schema failure")
            if any(db.execute("SELECT count(*) FROM "+t).fetchone()[0] > MAX_ROWS for t in ("task","operation")):
                raise UsageBlocked("MCP journal capacity reached")
            meta = db.execute("SELECT version,anchor,mac FROM meta").fetchall()
            if len(meta)!=1 or meta[0][0]!=2 or not hmac.compare_digest(meta[0][2],self._seal(db,key)):
                raise UsageBlocked("MCP journal integrity failure")
            if not new and self.sealpath.read_text(encoding="ascii") != meta[0][2]:
                raise UsageBlocked("MCP journal rollback or interrupted commit")
            # No time-based refund or assumed debit. Ambiguous execution must
            # remain reserved for reconciliation using trusted measurements.
            yield db
            if any(db.execute("SELECT count(*) FROM "+t).fetchone()[0] > MAX_ROWS for t in ("task","operation")):
                raise UsageBlocked("MCP journal capacity reached")
            seal = self._seal(db,key)
            db.execute("UPDATE meta SET mac=?", (seal,))
            db.commit()
            # A crash between database commit and seal replacement fails closed.
            # Never repair a mismatch by silently forgetting local debits.
            import tempfile
            seal_fd, temporary = tempfile.mkstemp(prefix=".mcp-seal-",dir=self.directory)
            try:
                with os.fdopen(seal_fd,"w",encoding="ascii") as stream:
                    stream.write(seal);stream.flush();os.fsync(stream.fileno())
                os.replace(temporary,self.sealpath)
                directory_fd=os.open(self.directory,os.O_DIRECTORY)
                try:os.fsync(directory_fd)
                finally:os.close(directory_fd)
            finally:
                if os.path.exists(temporary):os.unlink(temporary)
        except UsageBlocked:
            if db: db.rollback()
            raise
        except Exception:
            if db: db.rollback()
            raise UsageBlocked("MCP accounting unavailable; local features remain available") from None
        finally:
            if db: db.close()
            if fd is not None: os.close(fd)

    def quote(self):
        with self._transaction() as db:
            budget=self._resource_budget()
            return self._totals(db,budget)

    def advance_epoch(self, expected_epoch):
        """Accept an explicit prospective epoch from the trusted allowance reader.

        Same policy, account and exclusive allowance; cumulative tick amounts and
        revisions MUST continue, never reset. This is not a balance conversion or
        an authority to allocate credit. Unresolved work blocks the transition.
        The default live reader still cannot supply a V2 allowance.
        """
        if type(expected_epoch) is not int or expected_epoch < 1:
            raise UsageBlocked('Expected resource epoch required')
        with self._transaction() as db:
            budget=self._resource_budget()
            anchor=json.loads(db.execute('SELECT anchor FROM meta').fetchone()[0])
            if (anchor.get('epoch') != expected_epoch or budget.epoch <= expected_epoch
                    or anchor.get('policy') != POLICY_ID or anchor.get('account') != budget.account
                    or anchor.get('allowance') != budget.allowance
                    or budget.revision <= anchor.get('revision',-1)
                    or budget.contribution_ticks < int(anchor.get('contribution','0'))):
                raise UsageBlocked('Resource epoch continuity not established')
            if (db.execute("SELECT 1 FROM task WHERE state!='RELEASED'").fetchone()
                    or db.execute("SELECT 1 FROM operation WHERE state IN ('DISPATCHING','RECONCILIATION')").fetchone()):
                raise UsageBlocked('Unresolved execution prevents resource epoch transition')
            history=anchor.get('closed_epochs',[])
            if len(history)>=128:
                raise UsageBlocked('Resource epoch history capacity reached')
            prior_tasks={task for epoch in history for task in epoch['tasks']}
            history.append({'epoch':expected_epoch,'revision':anchor['revision'],
                            'contribution':anchor['contribution'],'available':anchor['available'],
                            'tasks':[row[0] for row in db.execute('SELECT id FROM task ORDER BY id')
                                     if row[0] not in prior_tasks]})
            anchor.update(epoch=budget.epoch, revision=budget.revision,
                          contribution=str(budget.contribution_ticks),
                          available=str(budget.available_ticks),closed_epochs=history)
            db.execute('UPDATE meta SET anchor=?',(json.dumps(anchor,sort_keys=True),))
            # Cumulative finalized debits, exact fractional ticks, duplicate IDs
            # and the old epoch evidence remain intact in the same journal.
            return self._totals(db,budget)

    def reserve(self, request, identifiers, maximum, *, approved=False):
        self._resource_budget()
        if (approved is not True or not HEX.fullmatch(request) or type(maximum) is not Resources
                or not maximum.ticks or not isinstance(identifiers,list) or not 1 <= len(identifiers) <= 4
                or len(set(identifiers)) != len(identifiers) or any(not ID.fullmatch(x) for x in identifiers)):
            raise UsageBlocked('Explicit bounded resource consent required')
        with self._transaction() as db:
            budget=self._resource_budget();totals=self._totals(db,budget)
            if db.execute('SELECT 1 FROM task WHERE request=?',(request,)).fetchone():
                raise UsageBlocked('Task identity already used; no automatic retry')
            if maximum.ticks > totals['available_ticks']:
                raise UsageBlocked('Insufficient contribution-funded resources')
            if maximum.ticks+totals['reserved_ticks'] > MAX_OUTSTANDING_TICKS:
                raise UsageBlocked('Aggregate resource admission ceiling exceeded')
            task=uuid.uuid4().hex
            db.execute('INSERT INTO task VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                (task,request,json.dumps(identifiers),str(maximum.ticks),str(maximum.ticks),
                 json.dumps(asdict(maximum),sort_keys=True),0,'RESERVED',time.time(),budget.expires_at,_boot()))
            return task,maximum.ticks

    def validate_task(self, task, request, identifiers):
        with self._transaction() as db:
            self._totals(db,self._resource_budget())
            row=db.execute('SELECT request,connections,state,deadline,boot FROM task WHERE id=?',(task,)).fetchone()
            if (not row or row[0]!=request or json.loads(row[1])!=identifiers or row[2]!='RESERVED'
                    or row[3]<=time.monotonic() or row[4]!=_boot()):
                raise UsageBlocked('Resource task approval unavailable')
            return MAX_CALLS  # Protocol/security cap only, NEVER a price.

    def dispatch(self, task, operation, connection, tool, fingerprint, request, authority, *, balance=None, envelope=None):
        self._resource_budget()
        if (type(envelope) is not Resources or not envelope.ticks or not ID.fullmatch(operation or '')
                or not ID.fullmatch(connection) or not ID.fullmatch(tool)
                or not HEX.fullmatch(fingerprint) or not HEX.fullmatch(request)):
            raise UsageBlocked('Trusted resource envelope required')
        with self._transaction() as db:
            totals=self._totals(db,self._resource_budget())
            if totals['overdrawn']:
                raise UsageBlocked('Resource allowance requires reconciliation')
            row=db.execute('SELECT connections,remaining_units,state,deadline,boot,call_count,envelope FROM task WHERE id=?',(task,)).fetchone()
            if (not row or connection not in json.loads(row[0]) or row[2]!='RESERVED'
                    or row[3]<=time.monotonic() or row[4]!=_boot() or row[5]>=MAX_CALLS):
                raise UsageBlocked('Resource task unavailable')
            if db.execute('SELECT 1 FROM operation WHERE id=?',(operation,)).fetchone():
                raise UsageBlocked('Operation already dispatched; no retry')
            if envelope.ticks > self._ticks(row[1]):
                raise UsageBlocked('Task resource reservation exhausted')
            consumed_data=consumed_cpu=0
            for prior_envelope,prior_resources,prior_state in db.execute(
                    'SELECT envelope,resources,state FROM operation WHERE task=?',(task,)):
                prior=Resources(**json.loads(prior_resources if prior_state=='SPENT' else prior_envelope))
                consumed_data+=prior.data_bytes;consumed_cpu+=prior.cpu_micros
            if not Resources(**json.loads(row[6])).contains(Resources(
                    consumed_data+envelope.data_bytes,consumed_cpu+envelope.cpu_micros)):
                raise UsageBlocked('Task technical resource envelope exhausted')
            authority()  # Same connection/tool authority immediately before durable dispatch.
            db.execute('INSERT INTO operation VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (operation,task,connection,tool,fingerprint,request,str(envelope.ticks),None,
                 json.dumps(asdict(envelope),sort_keys=True),None,'DISPATCHING',time.time(),time.time(),'PENDING'))
            db.execute('UPDATE task SET remaining_units=?,call_count=call_count+1 WHERE id=?',
                (str(self._ticks(row[1])-envelope.ticks),task))

    def completed(self, operation, outcome, *, measured=None):
        self._resource_budget()
        if outcome not in ('SUCCESS','ERROR','UNCERTAIN'):
            raise UsageBlocked('Invalid execution outcome')
        with self._transaction() as db:
            self._totals(db,self._resource_budget())
            row=db.execute('SELECT task,reserved_units,amount,envelope,resources,state,outcome FROM operation WHERE id=?',(operation,)).fetchone()
            if not row:raise UsageBlocked('Unknown operation')
            encoded=json.dumps(asdict(measured),sort_keys=True) if type(measured) is Resources else None
            if row[5]=='SPENT':
                if row[4]!=encoded or row[6]!=outcome:raise UsageBlocked('Conflicting settlement')
                return self._ticks(row[2])
            if row[5] not in ('DISPATCHING','RECONCILIATION'):raise UsageBlocked('Invalid operation state')
            envelope=Resources(**json.loads(row[3]))
            if outcome=='UNCERTAIN' or measured is None:
                db.execute("UPDATE operation SET state='RECONCILIATION',outcome='UNCERTAIN' WHERE id=?",(operation,))
                db.execute("UPDATE task SET state='RECONCILIATION' WHERE id=?",(row[0],))
                return None
            if not envelope.contains(measured):
                raise UsageBlocked('Measured usage exceeds approved envelope; reconciliation required')
            # Only a trusted host meter may call this API. MCP-reported metrics
            # are never routed here. Missing evidence preserves the full hold.
            amount=measured.ticks;release=self._ticks(row[1])-amount
            db.execute("UPDATE operation SET amount=?,resources=?,state='SPENT',outcome=? WHERE id=?",
                       (str(amount),encoded,outcome,operation))
            remaining=db.execute('SELECT remaining_units FROM task WHERE id=?',(row[0],)).fetchone()[0]
            db.execute('UPDATE task SET remaining_units=? WHERE id=?',(str(self._ticks(remaining)+release),row[0]))
            return amount

    def finish(self, task):
        if task is None:return
        with self._transaction() as db:
            self._totals(db,self._resource_budget())
            row=db.execute('SELECT state,remaining_units FROM task WHERE id=?',(task,)).fetchone()
            if not row:raise UsageBlocked('Unknown task')
            if row[0]=='RELEASED':return 0
            pending=db.execute("SELECT 1 FROM operation WHERE task=? AND state IN ('DISPATCHING','RECONCILIATION')",(task,)).fetchone()
            if pending:
                db.execute("UPDATE task SET state='RECONCILIATION' WHERE id=?",(task,))
                return None  # No automatic refund after an ambiguous execution.
            release=self._ticks(row[1])
            db.execute("UPDATE task SET state='RELEASED',remaining_units='0' WHERE id=?",(task,))
            return release

    def _resource_budget(self):
        # Default bridge returns legacy NetworkState; it cannot mint a V2 budget.
        if self.balance_reader is fresh_balance:
            require_resource_policy()
        try:
            budget=self.balance_reader(self.directory)
            if type(budget) is not ResourceBudget:raise ValueError()
            budget.validate()
            return budget
        except UsageBlocked:raise
        except Exception:
            raise UsageBlocked('Trusted V2 resource allowance unavailable') from None

    @staticmethod
    def _ticks(value):
        if not isinstance(value,str) or not value.isascii() or not value.isdigit() or str(int(value))!=value:
            raise UsageBlocked('Noncanonical journal resource amount')
        return natural(int(value))

    def _totals(self,db,budget):
        ceiling=budget.validate()
        anchor=json.loads(db.execute('SELECT anchor FROM meta').fetchone()[0])
        binding={'policy':POLICY_ID,'account':budget.account,'epoch':budget.epoch,'allowance':budget.allowance}
        if anchor:
            if (any(anchor.get(k)!=v for k,v in binding.items())
                    or budget.revision<anchor['revision'] or budget.contribution_ticks<int(anchor['contribution'])):
                raise UsageBlocked('Resource epoch/account rollback; explicit reconciliation required')
            if budget.revision==anchor['revision'] and (budget.contribution_ticks!=int(anchor['contribution'])
                    or budget.available_ticks!=int(anchor['available'])):
                raise UsageBlocked('Resource authority revision conflict')
        binding.update(revision=budget.revision,contribution=str(budget.contribution_ticks),available=str(budget.available_ticks))
        if 'closed_epochs' in anchor:
            binding['closed_epochs']=anchor['closed_epochs']
        db.execute('UPDATE meta SET anchor=?',(json.dumps(binding,sort_keys=True),))
        spent=held=0
        for amount,maximum,state in db.execute('SELECT amount,reserved_units,state FROM operation'):
            maximum=self._ticks(maximum)
            if state=='SPENT':
                debit=self._ticks(amount)
                if debit>maximum:raise UsageBlocked('Journal amount exceeds reservation')
                spent+=debit
            elif state in ('DISPATCHING','RECONCILIATION'):held+=maximum
        for reserved,remaining,state in db.execute('SELECT reserved_units,remaining_units,state FROM task'):
            reserved=self._ticks(reserved);remaining=self._ticks(remaining)
            if remaining>reserved:raise UsageBlocked('Invalid task reservation')
            if state!='RELEASED':held+=remaining
        return {'available_ticks':max(0,ceiling-spent-held),'reserved_ticks':held,
                'used_ticks':spent,'overdrawn':spent+held>ceiling,'policy':POLICY_ID}
