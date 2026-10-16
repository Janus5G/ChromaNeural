"""Actual Linux SQLite tests with synthetic authority allowances only."""
import json, sys, tempfile, threading, time, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'client'))
from chroma.mcp_usage import Usage, UsageBlocked, ResourceBudget, digest
from chroma.resource_policy import Resources, TICKS_PER_POINT as K


class Journal(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='chroma-v2-synthetic-')
        self.root=Path(self.tmp.name)
        self.available=4*K;self.earned=4*K;self.rev=1;self.epoch=1
        self.now=time.monotonic()
        self.usage=Usage(self.root,balance_reader=lambda _:ResourceBudget(
            'a'*64,self.epoch,'synthetic-exclusive-allowance',self.earned,self.available,
            self.rev,self.now,self.now+120))
    def tearDown(self):self.tmp.cleanup()
    def reserve(self,resource=Resources(0,1000000),request='task'):
        return self.usage.reserve(digest(request),['fixture'],resource,approved=True)[0]
    def dispatch(self,task,op='op',envelope=Resources(0,1000000),authority=lambda:None):
        self.usage.dispatch(task,op,'fixture','read',digest('tool'),digest('request'),authority,envelope=envelope)

    def test_exact_fractional_settlement_release(self):
        ceiling=Resources(100,1000000)
        task=self.reserve(ceiling);self.dispatch(task,envelope=ceiling)
        actual=Resources(1,1000)
        self.assertEqual(self.usage.completed('op','SUCCESS',measured=actual),actual.ticks)
        self.assertEqual(self.usage.finish(task),ceiling.ticks-actual.ticks)
        quote=self.usage.quote()
        self.assertEqual((quote['available_ticks'],quote['reserved_ticks'],quote['used_ticks']),
                         (4*K-actual.ticks,0,actual.ticks))

    def test_concurrent_reservations_do_not_overspend(self):
        self.available=self.earned=K
        gate=threading.Barrier(2);out=[]
        def reserve(i):
            gate.wait()
            try:self.reserve(request=str(i));out.append('reserved')
            except UsageBlocked:out.append('blocked')
        threads=[threading.Thread(target=reserve,args=(i,)) for i in range(2)]
        for thread in threads:thread.start()
        for thread in threads:thread.join(5);self.assertFalse(thread.is_alive())
        self.assertCountEqual(out,['reserved','blocked'])
        self.assertEqual(self.usage.quote()['available_ticks'],0)

    def test_bootstrap_or_legacy_not_eligible(self):
        self.earned=0;self.available=100*K
        with self.assertRaises(UsageBlocked):self.reserve()
        self.assertEqual(self.usage.quote()['available_ticks'],0)

    def test_insufficient_budget_and_no_silent_shrink(self):
        self.available=K-1
        with self.assertRaises(UsageBlocked):self.reserve()
        self.assertEqual(self.usage.quote()['reserved_ticks'],0)

    def test_no_substitution_of_data_for_approved_cpu(self):
        task=self.reserve()
        with self.assertRaises(UsageBlocked):self.dispatch(task,envelope=Resources(1048576,0))
        self.assertEqual(self.usage.finish(task),K)

    def test_multiple_calls_share_resource_envelope(self):
        task=self.reserve()
        self.dispatch(task,envelope=Resources(0,600000))
        self.usage.completed('op','SUCCESS',measured=Resources(0,600000))
        with self.assertRaises(UsageBlocked):self.dispatch(task,'second',Resources(0,500000))
        self.dispatch(task,'second',Resources(0,400000))
        self.usage.completed('second','SUCCESS',measured=Resources(0,400000))
        self.assertEqual(self.usage.finish(task),0)
        self.assertEqual(self.usage.quote()['used_ticks'],K)

    def test_explicit_consent(self):
        with self.assertRaises(UsageBlocked):
            self.usage.reserve(digest('task'),['fixture'],Resources(0,1))
        self.assertFalse(self.usage.path.exists())

    def test_authority_rejection_is_free(self):
        task=self.reserve()
        def denied():raise PermissionError('revoked')
        with self.assertRaises(UsageBlocked):self.dispatch(task,authority=denied)
        self.assertEqual(self.usage.finish(task),K)
        self.assertEqual(self.usage.quote()['used_ticks'],0)

    def test_dispatch_retry_rejected(self):
        task=self.reserve();self.dispatch(task)
        with self.assertRaises(UsageBlocked):self.dispatch(task)

    def test_duplicate_task_rejected(self):
        task=self.reserve();self.usage.finish(task)
        with self.assertRaises(UsageBlocked):self.reserve()

    def test_known_error_settles_measured_resources(self):
        task=self.reserve();self.dispatch(task)
        self.usage.completed('op','ERROR',measured=Resources(0,1))
        self.usage.finish(task)
        self.assertEqual(self.usage.quote()['used_ticks'],Resources(0,1).ticks)

    def test_ambiguous_dispatch_remains_held_after_reopen(self):
        task=self.reserve();self.dispatch(task)
        reopened=Usage(self.root,balance_reader=self.usage.balance_reader)
        self.assertIsNone(reopened.finish(task))
        self.assertEqual(reopened.quote()['reserved_ticks'],K)
        with self.assertRaises(UsageBlocked):self.dispatch(task)

    def test_uncertain_measurement_not_refunded(self):
        task=self.reserve();self.dispatch(task)
        self.assertIsNone(self.usage.completed('op','UNCERTAIN'))
        self.assertIsNone(self.usage.finish(task))
        self.assertEqual(self.usage.quote()['reserved_ticks'],K)

    def test_never_dispatched_reservation_released(self):
        task=self.reserve()
        self.assertEqual(self.usage.finish(task),K)
        self.assertEqual(self.usage.finish(task),0)
        self.assertEqual(self.usage.quote()['available_ticks'],4*K)

    def test_settlement_is_idempotent(self):
        task=self.reserve();self.dispatch(task);actual=Resources(0,100)
        for _ in range(2):self.usage.completed('op','SUCCESS',measured=actual)
        self.assertEqual(self.usage.quote()['used_ticks'],actual.ticks)
        with self.assertRaises(UsageBlocked):self.usage.completed('op','ERROR',measured=actual)

    def test_tool_self_report_cannot_settle(self):
        task=self.reserve();self.dispatch(task)
        with self.assertRaises(UsageBlocked):self.usage.completed('op','SUCCESS',measured={'cpuMicros':0,'points':0})
        self.assertEqual(self.usage.quote()['reserved_ticks'],K)

    def test_over_envelope_retains_hold(self):
        task=self.reserve();self.dispatch(task)
        with self.assertRaises(UsageBlocked):self.usage.completed('op','SUCCESS',measured=Resources(0,1000001))
        self.assertEqual(self.usage.quote()['reserved_ticks'],K)

    def test_stale_budget(self):
        self.now-=61
        with self.assertRaises(UsageBlocked):self.reserve()
        self.assertFalse(self.usage.path.exists())

    def test_epoch_change_requires_reconciliation(self):
        self.reserve();self.epoch=2
        with self.assertRaises(UsageBlocked):self.usage.quote()

    def test_revision_rollback_rejected(self):
        self.reserve();self.rev=0
        with self.assertRaises(UsageBlocked):self.usage.quote()

    def test_same_revision_conflicting_allowance_rejected(self):
        self.reserve();self.available+=1
        with self.assertRaises(UsageBlocked):self.usage.quote()

    def test_aggregate_admission_ceiling(self):
        self.earned=self.available=200*K
        self.reserve(Resources(0,60000000),'first')
        with self.assertRaises(UsageBlocked):self.reserve(Resources(0,60000000),'second')
        self.assertEqual(self.usage.quote()['reserved_ticks'],60*K)

    def test_execution_count_is_only_security_cap(self):
        task=self.reserve()
        for i in range(4):
            self.dispatch(task,str(i),Resources(0,1000))
            self.usage.completed(str(i),'SUCCESS',measured=Resources(0,1))
        with self.assertRaises(UsageBlocked):self.dispatch(task,'fifth',Resources(0,1000))
        self.assertEqual(self.usage.quote()['used_ticks'],Resources(0,4).ticks)

    def test_corruption_is_not_reset(self):
        self.reserve();before=self.usage.path.read_bytes()
        self.usage.sealpath.write_text('corrupt')
        with self.assertRaises(UsageBlocked):self.usage.quote()
        self.assertEqual(self.usage.path.read_bytes(),before)

    def test_existing_state_not_migrated(self):
        self.usage.path.write_bytes(b'legacy state')
        with self.assertRaises(UsageBlocked):self.usage.quote()
        self.assertEqual(self.usage.path.read_bytes(),b'legacy state')

    def test_live_reader_cannot_activate(self):
        with self.assertRaises(UsageBlocked):Usage(self.root).quote()
        self.assertFalse(self.usage.path.exists())

    def test_no_sensitive_content_stored(self):
        task=self.reserve();self.dispatch(task)
        self.usage.completed('op','SUCCESS',measured=Resources(0,10));self.usage.finish(task)
        import sqlite3
        with sqlite3.connect(self.usage.path) as db:
            columns=[r[1] for r in db.execute('PRAGMA table_info(operation)')]
        self.assertFalse({'token','prompt','result','response','source'} & set(columns))

if __name__=='__main__':unittest.main(verbosity=2)
