"""Synthetic Resource V2 checks; no network, accounts, GUI or live points."""
import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'client'))
from chroma.resource_policy import (Resources, DataBroker, accumulate,
    TICKS_PER_POINT as K, TICKS_PER_MICROPOINT as Q, display)


class ResourceMath(unittest.TestCase):
    def test_units(self):
        self.assertEqual(Resources(1048576, 0).ticks, K)
        self.assertEqual(Resources(0, 1000000).ticks, K)
        self.assertGreater(Resources(1, 0).ticks, 0)

    def test_partition_invariance_and_monotonicity(self):
        rng=random.Random(921)
        for _ in range(3000):
            a,b,c,d=(rng.randrange(10000000) for _ in range(4))
            self.assertEqual(Resources(a+b,c+d).ticks, Resources(a,c).ticks+Resources(b,d).ticks)
            self.assertGreaterEqual(Resources(a+b,c+d).ticks,Resources(a,c).ticks)

    def test_micro_work_carry(self):
        credited=carry=0
        byte=Resources(1,0)
        for _ in range(1048576):
            amount,carry=accumulate(carry,byte)
            credited+=amount
        self.assertEqual((credited,carry),(1000000,0))

    def test_identical_contribution_consumption(self):
        workloads=[Resources(3,7),Resources(1048576,1),Resources(0,7000000)]
        earned=consumed=0
        earning_carry=spending_carry=0
        for measured in workloads:
            e,earning_carry=accumulate(earning_carry,measured)
            s,spending_carry=accumulate(spending_carry,measured)
            earned+=e;consumed+=s
        self.assertEqual((earned,earning_carry),(consumed,spending_carry))
        self.assertEqual(earned*Q+earning_carry,sum(r.ticks for r in workloads))

    def test_no_call_price_and_fractional_values(self):
        self.assertEqual(Resources().ticks,0)
        self.assertLess(Resources(1,1).ticks,K)
        self.assertGreater(Resources(0,2000000).ticks,K)
        self.assertNotEqual(Resources(1,1).ticks,Resources(2,2).ticks)

    def test_unsupported_dimensions_rejected(self):
        for kwargs in ({'gpu_micros':1},{'ram_byte_micros':1},{'cpu_micros':True},
                       {'data_bytes':-1},{'cpu_micros':1.5},{'data_bytes':2**128}):
            with self.assertRaises(ValueError):Resources(**kwargs)

    def test_bounds_are_dimensionwise_not_only_price(self):
        envelope=Resources(1048576,1000000)
        self.assertTrue(envelope.contains(Resources(1024,900000)))
        self.assertFalse(envelope.contains(Resources(2097152,0)))
        actual=Resources(1024,900000)
        self.assertEqual(actual.ticks+(envelope.ticks-actual.ticks),envelope.ticks)

    def test_display_does_not_change_ticks(self):
        resource=Resources(1,0)
        before=resource.ticks
        self.assertEqual(display(K),'1.000000000000')
        display(before)
        self.assertEqual(resource.ticks,before)


class PayloadBroker(unittest.TestCase):
    def test_actual_utf8_and_binary_bytes(self):
        broker=DataBroker(100)
        incoming='æ日本'.encode('utf-8');outgoing=b'\x00\xffanswer'
        broker.cross('in','input',incoming)
        broker.cross('out','output',outgoing)
        self.assertEqual(broker.total,len(incoming)+len(outgoing))

    def test_repeated_event_not_double_counted(self):
        broker=DataBroker(3)
        broker.cross('a','input',b'abc');broker.cross('a','input',b'abc')
        self.assertEqual(broker.total,3)
        with self.assertRaises(ValueError):broker.cross('a','input',b'abd')

    def test_output_bound_rejects_before_crossing(self):
        broker=DataBroker(3);broker.cross('a','input',b'ab')
        with self.assertRaises(ValueError):broker.cross('b','output',b'cd')
        self.assertEqual(broker.total,2)

    def test_no_implicit_control_plane_charge(self):
        broker=DataBroker(10)
        self.assertEqual(broker.total,0)
        with self.assertRaises(ValueError):broker.cross('list','tools/list',b'{}')
        self.assertEqual(broker.total,0)

if __name__=='__main__':unittest.main(verbosity=2)
