#!/usr/bin/env python3
"""Independent exhaustive table/job tests; no ROS, network or third-party packages."""
import importlib.util
from itertools import product
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, slug):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'examples/month-4' / slug / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


acl = load('sros_enclave_acl_toy', 'ros2-setup')
composition = load('composition_container_toy', 'ros2-graph')


class Contracts(unittest.TestCase):
    def test_exhaustive_acl(self):
        allowed = {('listener', '/scan'), ('operator', '/scan'), ('operator', '/cmd_vel')}
        cases = list(product((7, 8), ('listener', 'operator', 'visitor', 'unknown'),
                             ('/scan', '/cmd_vel', '/debug')))
        self.assertEqual(set(cases), set(acl.REQUESTS))
        for arm in acl.ARMS:
            received = unauthorized = legitimate_denied = 0
            for domain, principal, topic in cases:
                truth = domain == 7 and (principal, topic) in allowed
                want = domain == 7 and (arm == 'domain_only' or
                       (arm == 'enclave_ACL_Enforce' and (principal, topic) in allowed))
                got, reason = acl.decision(arm, domain, principal, topic)
                self.assertEqual(got, want, (arm, domain, principal, topic))
                if domain != 7:
                    self.assertEqual(reason, 'other_domain')
                elif arm != 'domain_only':
                    if arm == 'missing_enclave_Enforce' or principal == 'unknown':
                        self.assertEqual(reason, 'missing_materials')
                    elif not truth:
                        self.assertEqual(reason, 'policy_deny')
                received += want
                unauthorized += want and not truth
                legitimate_denied += truth and not want
            result = acl.evaluate(arm)
            self.assertEqual((result['received'], result['unauthorized_receive'], result['legitimate_denied']),
                             (received, unauthorized, legitimate_denied))
            # Reordering the SHARED stream must not change counts.
            self.assertEqual(result, acl.evaluate(arm, tuple(reversed(cases))))
        with self.assertRaises(ValueError):
            acl.decision('invalid_arm', 7, 'listener', '/scan')

    def test_grant_and_material_negative_cases(self):
        # Check the policy is used, not hard-coded successful output.
        acl.GRANTS['visitor'].add('/debug')
        try:
            self.assertTrue(acl.decision('enclave_ACL_Enforce', 7, 'visitor', '/debug')[0])
            self.assertFalse(acl.decision('missing_enclave_Enforce', 7, 'visitor', '/debug')[0])
        finally:
            acl.GRANTS['visitor'].remove('/debug')
        acl.MATERIALS.remove('listener')
        try:
            self.assertEqual(acl.decision('enclave_ACL_Enforce', 7, 'listener', '/scan'),
                             (False, 'missing_materials'))
        finally:
            acl.MATERIALS.add('listener')

    def test_shared_work_and_fault_enumeration(self):
        for n in range(2, 13):
            jobs = [(t, i, (t+1)*(i+1)) for t in range(12) for i in range(n) if (t+i) % 3 == 0]
            for composed in (False, True):
                healthy = composition.run(n, composed)
                self.assertEqual(healthy.callbacks, len(jobs))
                self.assertEqual(healthy.checksum, sum(p for _, _, p in jobs))
                self.assertEqual(healthy.polls, 12 * (1 if composed else n))
                for crash_tick in (0, 5, 11, 12):
                    old = composition.CRASH_TICK
                    composition.CRASH_TICK = crash_tick
                    try:
                        fault = composition.run(n, composed, fault=True)
                    finally:
                        composition.CRASH_TICK = old
                    kept = [(t, i, p) for t, i, p in jobs if t < crash_tick or (not composed and i != 1)]
                    self.assertEqual(fault.callbacks, len(kept))
                    self.assertEqual(fault.checksum, sum(p for _, _, p in kept))
                    self.assertEqual(fault.callbacks + fault.lost_callbacks, healthy.callbacks)
                    self.assertEqual(fault.polls, crash_tick if composed else 12*(n-1) + crash_tick)
                    self.assertEqual(fault.blast_radius, (n if composed else 1) if crash_tick < 12 else 0)
                    self.assertEqual(fault.processes, 1 if composed else n)
        with self.assertRaises(ValueError):
            composition.run(1, True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
