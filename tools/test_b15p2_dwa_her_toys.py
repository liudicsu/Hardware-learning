#!/usr/bin/env python3
"""Independent contract tests for batch-15 PR2 DWA-vs-RPP and HER toys; stdlib only.

The DWA toy takes about 45 s to print its tables, so these tests call its functions directly and
leave the full-output comparison to check.sh / check_diagrams; the HER toy is run end to end.
"""
from __future__ import annotations

import importlib.util
import math
import random
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DW_REL = "examples/month-4/slam-nav/dwa_vs_pure_pursuit_toy.py"
HE_REL = "examples/month-7/rl-manipulation-sim/her_sparse_grasp_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dw = load("dwa_vs_pure_pursuit_toy", DW_REL)
he = load("her_sparse_grasp_toy", HE_REL)


class Labels(unittest.TestCase):
    """Both toys share one labelling rule; check it on hand-made paired data."""

    def test_order_and_thresholds(self):
        for mod, rel in ((dw, DW_REL), (he, HE_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1.0 + 1e-12, 1.0, 1.0 - 1e-12, 1.0, 1.0], [1.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertNotIn("seeds", v)
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("same sign on all 5 seeds", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("small but consistent", mod.verdict([10.5, 10.6, 10.4, 10.5, 10.5], [10.0] * 5))
            src = (ROOT / rel).read_text()
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))

    def test_no_signed_zero(self):
        for mod in (dw, he):
            self.assertEqual(mod.num(-1e-5), "-1.000e-05")
            self.assertEqual(mod.num(0.0), "0.0000")
            self.assertNotEqual(mod.num(-4e-5), "-0.0000")


class DwaToy(unittest.TestCase):
    def test_scope(self):
        self.assertEqual(dw.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / DW_REL).read_text()
        for s in ("本页未运行", "Common random numbers", "以原文为准", "chosen after the first run", "added after"):
            self.assertIn(s, text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
        self.assertEqual(dw.ARMS, ("A_rpp", "B_dwa", "C_window", "D_dwa_dt"))
        self.assertEqual((dw.W_HEAD, dw.W_DIST, dw.W_VEL), (2.0, 0.2, 0.2))  # Fox et al. weights
        self.assertEqual(dw.DT_CTRL, 0.25)
        self.assertEqual(dw.ALT_PADS, (0.0, 0.1))

    def test_admissibility_boundary(self):
        # Fox eq. 14: v <= sqrt(2 dist B_V) stops before the obstacle; 0.98x stops short, 1.02x overshoots.
        for dist in (0.5, 1.0, 2.0):
            lim = math.sqrt(2.0 * dist * dw.B_V)
            self.assertLess(dw.brake_stop(0.98 * lim), dist)
            self.assertGreater(dw.brake_stop(1.02 * lim), dist)
            self.assertAlmostEqual(dw.brake_stop(lim), dist, places=9)

    def test_control_period_criterion(self):
        # D: v <= sqrt(2 B_V (dist - v DT)); closed form for dist = 1.0 is v = (-0.25 + sqrt(4.0625)) / 2.
        v_star = (-0.25 + math.sqrt(0.0625 + 4.0)) / 2.0
        self.assertAlmostEqual(v_star, 0.8828, places=4)
        for dist in (0.5, 1.0, 2.0):
            a, b, c = 1.0, 2.0 * dw.B_V * dw.DT_CTRL, -2.0 * dw.B_V * dist
            v_lim = (-b + math.sqrt(b * b - 4 * a * c)) / 2.0
            ok = lambda v: v <= math.sqrt(2.0 * max(0.0, dist - v * dw.DT_CTRL) * dw.B_V)
            self.assertTrue(ok(0.98 * v_lim))
            self.assertFalse(ok(1.02 * v_lim))
            # held one period, then braking: covers v*DT + v^2/(2 B_V), which equals dist at the limit
            self.assertAlmostEqual(v_lim * dw.DT_CTRL + v_lim ** 2 / (2 * dw.B_V), dist, places=9)
            # Fox's literal limit, held one period, overshoots
            fox = math.sqrt(2.0 * dist * dw.B_V)
            self.assertGreater(fox * dw.DT_CTRL + fox ** 2 / (2 * dw.B_V), dist)

    def test_arc_hit_matches_brute_force(self):
        rng = random.Random(15)
        for _ in range(400):
            v = rng.uniform(0.05, 1.2)
            w = rng.choice((0.0, rng.uniform(-1.5, 1.5)))
            obs = [(rng.uniform(-1.0, 3.0), rng.uniform(-2.0, 2.0), rng.uniform(0.1, 0.35)) for _ in range(4)]
            got = dw.arc_hit(0.0, 0.0, 0.0, v, w, obs)
            # brute force: walk the arc in 1 mm steps until the robot disc touches an obstacle
            s, ds, brute = 0.0, 0.001, dw.D_CAP
            while s <= dw.D_CAP:
                x, y, _ = dw.arc_pose(0.0, 0.0, 0.0, 1.0, w / v, s)
                if any(math.hypot(ox - x, oy - y) <= r + dw.R_ROBOT for ox, oy, r in obs):
                    brute = s
                    break
                s += ds
            self.assertLessEqual(abs(got - brute), 0.0011 if brute < dw.D_CAP else 1e-9, (v, w, obs, got, brute))

    def test_common_random_numbers(self):
        self.assertEqual(dw.world("clutter", 2, 3), dw.world("clutter", 2, 3))
        self.assertNotEqual(dw.world("clutter", 2, 3), dw.world("clutter", 3, 3))
        # clutter_slow and clutter_fast share the same obstacle field
        self.assertEqual(dw.REGIMES["clutter_slow"][1], dw.REGIMES["clutter_fast"][1])

    def test_step_check_and_one_trial(self):
        a = dw.open_loop(dw.SUBSTEPS)
        b = dw.open_loop(2 * dw.SUBSTEPS)
        self.assertLess(math.hypot(a[0] - b[0], a[1] - b[1]), 5e-3)
        r = dw.run("A_rpp", "winding", 0, 0)
        self.assertEqual(r["success"], 1.0)
        self.assertEqual(r["time"], 25.25)
        r = dw.run("B_dwa", "winding", 0, 0)
        self.assertEqual(r["collision"], 1.0)
        r = dw.run("D_dwa_dt", "winding", 0, 0)
        self.assertEqual(r["collision"], 0.0)

    def test_expected_regime_lines(self):
        out = (ROOT / "examples/month-4/expected/dwa_vs_pure_pursuit_toy.txt").read_text()
        self.assertIn("  paired B-A collision: -0.6667+-0.2041: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("  paired C-B collision: 0.1333+-0.1394: near-tie / small gap, within seed noise (|m| <= sd); no seed has the opposite sign, 2 of 5 equal", out)
        self.assertIn("  B_dwa 0.0000+-0.0000 1.0000+-0.0000 60.0000+-0.0000", out)
        self.assertIn("  A_rpp 1.0000+-0.0000 0.0000+-0.0000 25.3333+-0.0510", out)
        self.assertIn("1.02x stops at 1.0404 m (hits)", out)


class HerToy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = subprocess.run([sys.executable, str(ROOT / HE_REL)], check=True, capture_output=True, text=True).stdout

    def test_expected_byte_identical(self):
        self.assertEqual(self.out, (ROOT / "examples/month-7/expected/her_sparse_grasp_toy.txt").read_text())

    def test_scope(self):
        self.assertEqual(he.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / HE_REL).read_text()
        for s in ("本页未运行", "以原文为准", "Common random numbers", "No integration step"):
            self.assertIn(s, text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
        # No integration step: discrete grid, nothing is stepped in continuous time.
        self.assertNotRegex(text, r"\bDT\b|\bdt\b|rk4|euler")
        self.assertIn("no integration step (discrete grid)", self.out)
        self.assertEqual(he.K_FUTURE, 4)
        self.assertEqual(he.REPR, "relative")
        self.assertEqual(he.ALT_REPR, "absolute")

    def test_reward_and_dense_match_reward_shaping(self):
        self.assertEqual(he.reward((4, 3), 1, (4, 3), False), (1.0, True))
        self.assertEqual(he.reward((4, 3), 0, (4, 3), False), (0.0, False))
        r, done = he.reward((4, 3), 1, (4, 3), True)
        self.assertAlmostEqual(r, 5.5)
        self.assertTrue(done)
        r, _ = he.reward((1, 1), 0, (4, 3), True)
        self.assertAlmostEqual(r, -0.5)

    def test_relabel_only_with_gripper_closed(self):
        src = (ROOT / HE_REL).read_text()
        self.assertIn("if tr[j][4] == 1:  # a goal is achieved only with the gripper closed", src)
        self.assertIn("j = replay_rng.randrange(i, len(tr))", src)  # future: at or after the replayed step

    def test_relative_key_shares_offsets(self):
        self.assertEqual(he.key((4, 3), (3, 3), 1), he.key((2, 2), (1, 2), 1))
        self.assertNotEqual(he.key((4, 3), (3, 3), 1, "absolute"), he.key((2, 2), (1, 2), 1, "absolute"))

    def test_common_random_numbers(self):
        self.assertEqual(he.shared_draws("far_goals", 2), he.shared_draws("far_goals", 2))
        self.assertNotEqual(he.shared_draws("far_goals", 2), he.shared_draws("far_goals", 3))
        # every arm trains on the same shared draws; K_FUTURE = 0 still runs (exercise 3)
        a = he.train("A_sparse", "near_goal", 0)
        b0 = he.train("B_her", "near_goal", 0, k_future=0)
        self.assertEqual(set(a), {"final", "auc", "train"})
        self.assertEqual(set(b0), {"final", "auc", "train"})

    def test_regime_lines(self):
        self.assertIn("  paired B-A final: 1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", self.out)
        self.assertIn("  paired B-C final: -0.4321+-0.2232: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", self.out)
        self.assertIn("  paired B-A auc: 0.0021+-0.0031: near-tie / small gap, within seed noise (|m| <= sd); no seed has the opposite sign, 3 of 5 equal", self.out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
