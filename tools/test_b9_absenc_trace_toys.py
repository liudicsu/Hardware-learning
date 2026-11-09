#!/usr/bin/env python3
"""Independent contract tests for batch-9 PR2 toys; stdlib only."""
import importlib.util
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, month, slug):
    spec = importlib.util.spec_from_file_location(name, ROOT / f'examples/month-{month}' / slug / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


enc = load('abs_vs_incr_power_on_toy', 3, 'so101-arm')
tr = load('visual_trace_prompt_toy', 9, 'visual-servoing')


class Encoder(unittest.TestCase):
    def test_single_turn_map_is_exact_inside_one_turn(self):
        for angle in (-150.0, -90.0, 0.0, 37.5, 149.9):
            counts = round(angle / enc.DEG_PER_COUNT)
            self.assertAlmostEqual(enc.single_turn_map(counts, -150, 150), counts * enc.DEG_PER_COUNT, places=9)

    def test_single_turn_map_loses_whole_turns(self):
        # 1000 deg and 640 deg share counts mod CPR; on a 0..1080 range both map to the middle turn
        a = enc.single_turn_map(round(1000 / enc.DEG_PER_COUNT), 0, 1080)
        b = enc.single_turn_map(round(640 / enc.DEG_PER_COUNT), 0, 1080)
        self.assertAlmostEqual(a, b, places=9)
        r = abs(1000 - a) % 360.0
        self.assertLess(min(r, 360.0 - r), 0.1)
        self.assertGreater(abs(1000 - a), 300.0)

    def test_homing_time_formula(self):
        self.assertAlmostEqual(enc.homing_time(-150.0, -150.0), 360.0 / 90.0 + 0.5)
        self.assertAlmostEqual(enc.homing_time(1080.0, 0.0), (1080.0 + 360.0) / 90.0 + 0.5)

    def test_arms_share_state_and_noise_streams(self):
        truths = []
        for arm in enc.ARMS:
            rs, rn = random.Random(100), random.Random(200)
            rows = [enc.episode(arm, 0, 1080, 60.0, True, rs, rn) for _ in range(enc.EVENTS)]
            truths.append((rs.random(), rn.random()))
            if arm == 'D_multi_batt':
                self.assertTrue(all(r[0] <= enc.TOL_DEG and r[1] == 0.0 for r in rows))
        self.assertEqual(len(set(truths)), 1)

    def test_flat_battery_alarms_never_silent(self):
        rs, rn = random.Random(101), random.Random(201)
        rows = [enc.episode('D_multi_batt', 0, 1080, 60.0, False, rs, rn) for _ in range(enc.EVENTS)]
        self.assertTrue(all(r[3] and not r[2] and r[1] > 0 for r in rows))


class Trace(unittest.TestCase):
    def test_raw_arm_sees_only_current_frame(self):
        rng = random.Random(0)
        self.assertEqual(tr.encode('A_raw', [(1, 3), (2, 3), (3, 3)], None, rng), (3, 3))
        self.assertEqual(tr.encode('A_raw', [(5, 3), (4, 3), (3, 3)], None, rng), (3, 3))

    def test_trace_reveals_direction_from_past_frames_only(self):
        rng = random.Random(0)
        right = tr.encode('B_raw_trace', [(0, 3), (1, 3), (2, 3), (3, 3)], None, rng)
        left = tr.encode('B_raw_trace', [(6, 3), (5, 3), (4, 3), (3, 3)], None, rng)
        self.assertNotEqual(right, left)
        # changing a future/unseen quantity (the hidden sweep direction) cannot change features: encode has no access to it
        self.assertEqual(tr.encode.__code__.co_varnames[:4], ('arm', 'hist', 'goal', 'rng'))

    def test_lagged_trace_excludes_latest_frames(self):
        tr_j, tr.JITTER = tr.JITTER, 0.0
        try:
            hist = [(0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3)]
            c = tr.encode('C_lagged_trace', hist, None, random.Random(0))
            # window ends LAG frames back: oldest (0, 3), newest (3, 3), relative to the current EE (5, 3)
            self.assertEqual(c, (5, 3, -5, 0, -2, 0))
            self.assertNotEqual(c, tr.encode('B_raw_trace', hist, None, random.Random(0)))
        finally:
            tr.JITTER = tr_j

    def test_no_lag_no_jitter_c_equals_b(self):
        lag, jit = tr.LAG, tr.JITTER
        tr.LAG, tr.JITTER = 0, 0.0
        try:
            for task in ('wipe', 'reach'):
                outs = []
                for arm in ('B_raw_trace', 'C_lagged_trace'):
                    data = tr.demos(task, arm, random.Random(10), random.Random(20))
                    outs.append(tr.evaluate(task, arm, data, random.Random(30), random.Random(40)))
                self.assertEqual(outs[0], outs[1])
        finally:
            tr.LAG, tr.JITTER = lag, jit

    def test_reach_expert_reaches_goal(self):
        ee, goal = (0, 6), (5, 1)
        for _ in range(12):
            a = tr.reach_expert(ee, goal)
            ee = (ee[0] + a[0], ee[1] + a[1])
        self.assertEqual(ee, goal)


if __name__ == '__main__':
    unittest.main(verbosity=1)
