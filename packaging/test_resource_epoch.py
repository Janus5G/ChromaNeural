"""Only the newly added local epoch transition; all balances are synthetic."""
import json
import sqlite3
import sys
import subprocess
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_resource_journal as journal_fixture
from chroma.mcp_usage import Usage, UsageBlocked
from chroma.resource_policy import Resources


class Epoch(unittest.TestCase):
    setUp=journal_fixture.Journal.setUp
    tearDown=journal_fixture.Journal.tearDown
    reserve=journal_fixture.Journal.reserve
    dispatch=journal_fixture.Journal.dispatch

    def settle(self):
        envelope=Resources(1,1000000)
        task=self.reserve(envelope);self.dispatch(task,envelope=envelope)
        self.usage.completed('op','SUCCESS',measured=Resources(1,1))
        self.usage.finish(task)
        return task

    def test_fractional_debit_survives_reopen_and_epoch(self):
        task=self.settle();before=self.usage.quote()
        self.epoch=2;self.rev=2
        self.usage.advance_epoch(1)
        reopened=Usage(self.root,balance_reader=self.usage.balance_reader)
        self.assertEqual(reopened.quote(),before)
        with sqlite3.connect(reopened.path) as db:
            anchor=json.loads(db.execute('SELECT anchor FROM meta').fetchone()[0])
        self.assertEqual(anchor['epoch'],2)
        self.assertEqual(anchor['closed_epochs'][0]['tasks'],[task])
        self.assertEqual(anchor['policy'],'chromaneural-resource-v2-data-cpu')

    def test_pending_reservation_blocks_epoch(self):
        self.reserve();self.epoch=2;self.rev=2
        with self.assertRaises(UsageBlocked):self.usage.advance_epoch(1)

    def test_ambiguous_execution_blocks_epoch(self):
        task=self.reserve();self.dispatch(task);self.usage.finish(task)
        self.epoch=2;self.rev=2
        with self.assertRaises(UsageBlocked):self.usage.advance_epoch(1)

    def test_epoch_cannot_reset_contribution_or_revision(self):
        self.settle();self.epoch=2
        with self.assertRaises(UsageBlocked):self.usage.advance_epoch(1)
        self.rev=2;self.earned=0
        with self.assertRaises(UsageBlocked):self.usage.advance_epoch(1)

    def test_duplicate_execution_remains_rejected_after_epoch(self):
        task=self.settle();self.epoch=2;self.rev=2;self.usage.advance_epoch(1)
        with self.assertRaises(UsageBlocked):self.reserve()
        with self.assertRaises(UsageBlocked):self.dispatch(task)
        with self.assertRaises(UsageBlocked):self.usage.advance_epoch(1)

    def test_transition_never_uses_legacy_live_balance(self):
        with self.assertRaises(UsageBlocked):Usage(self.root).advance_epoch(1)
        self.assertFalse(self.usage.path.exists())

    def test_fractional_carry_survives_process_restart(self):
        self.settle();before=self.usage.quote()
        script = '''
import sys,time,json
sys.path.insert(0,sys.argv[1])
from chroma.mcp_usage import Usage,ResourceBudget
from chroma.resource_policy import TICKS_PER_POINT as K
now=time.monotonic()
usage=Usage(sys.argv[2],balance_reader=lambda _:ResourceBudget(
    'a'*64,1,'synthetic-exclusive-allowance',4*K,4*K,1,now,now+60))
print(json.dumps(usage.quote()))
'''
        process=subprocess.run([sys.executable,'-B','-c',script,
            str(Path(__file__).resolve().parents[1]/'client'),str(self.root)],
            capture_output=True,text=True,timeout=5,check=True)
        self.assertEqual(json.loads(process.stdout),before)

    def test_epoch_cannot_change_account_or_allowance(self):
        from dataclasses import replace
        self.settle();self.epoch=2;self.rev=2
        reader=self.usage.balance_reader
        for change in ({'account':'b'*64},{'allowance':'different-allowance'}):
            self.usage.balance_reader=lambda p,change=change:replace(reader(p),**change)
            with self.assertRaises(UsageBlocked):self.usage.advance_epoch(1)

if __name__=='__main__':unittest.main(verbosity=2)
