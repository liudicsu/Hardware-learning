#!/usr/bin/env python3
"""Independent contract tests for batch-16 PR3 MolmoAct trace + HAMSTER hierarchical path toys; stdlib only."""
from __future__ import annotations

import importlib.util
import random
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MO_REL = "examples/month-6/vla-models/molmoact_reasoning_trace_toy.py"
HA_REL = "examples/month-6/behaviour-cloning/hamster_hierarchical_path_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


mo = load("molmoact_reasoning_trace_toy", MO_REL)
ha = load("hamster_hierarchical_path_toy", HA_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((mo, MO_REL), (ha, HA_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertEqual(mod.SEEDS, (0, 1, 2, 3, 4))
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1e-16, -2e-16, 3e-16, 0.0, 1e-16], [0.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertNotIn("seeds", v)
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            src = (ROOT / rel).read_text()
            self.assertIn("Common random numbers", src)
            self.assertIn("本页未运行", src)
            self.assertIn("No integration step", src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))


class Nearest(unittest.TestCase):
    def test_nearest_matches_a_full_sort(self):
        rng = random.Random(7)
        for mod in (mo, ha):
            table = [([rng.uniform(-1, 1) for _ in range(5)], [rng.random(), rng.random(), rng.random()]) for _ in range(300)]
            for _ in range(50):
                f = [rng.uniform(-1, 1) for _ in range(5)]
                full = sorted(range(len(table)), key=lambda i: (sum((x - y) ** 2 for x, y in zip(table[i][0], f)), i))[:mod.K_NN]
                self.assertEqual(mod.nearest(table, f), [table[i][1] for i in full])


class MolmoAct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(MO_REL)

    def test_step_and_wall_check(self):
        self.assertLess(mo.V / mo.SUB, mo.WALL_T)
        g = mo.step_to([0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
        self.assertAlmostEqual(g[0], mo.V, places=12)
        self.assertTrue(mo.hits_wall([0.47, 0.3, 0.5], [0.53, 0.3, 0.5], 0.5))
        self.assertFalse(mo.hits_wall([0.47, mo.WALL_H + 0.01, 0.5], [0.53, mo.WALL_H + 0.01, 0.5], 0.5))

    def test_trace_and_depth_tokens(self):
        rng = random.Random(3)
        for wall in (True, False):
            sc = mo.scene(rng, wall, None)
            tr = mo.trace(sc, [0.2, 0.3, 0.5], 0, False)
            self.assertLessEqual(len(tr), 5)
            self.assertTrue(all(len(p) == 2 for p in tr))
            mir = mo.trace(sc, [0.2, 0.3, 0.5], 0, True)
            self.assertEqual(mir[0], tr[0])
            self.assertAlmostEqual(mir[-1][0], 1.0 - tr[-1][0], places=12)
        for i in range(101):
            z = i / 100 * 0.999
            self.assertLessEqual(abs(mo.depth_token(z) - z), 0.5 / mo.N_DEPTH + 1e-12)

    def test_depth_edit_cannot_choose(self):
        rng = random.Random(5)
        sc = mo.scene(rng, False, "depth")
        self.assertEqual(mo.trace(sc, [0.2, 0.3, 0.5], 0, False), mo.trace(sc, [0.2, 0.3, 0.5], 1, False))

    def test_common_random_numbers(self):
        a, b = mo.shared_draws("single_step", 1), mo.shared_draws("single_step", 1)
        self.assertEqual(a[0], b[0])
        self.assertEqual([t[2] for t in a[1]], [t[2] for t in b[1]])

    def test_output(self):
        self.assertEqual(self.out, (ROOT / "examples/month-6/expected/molmoact_reasoning_trace_toy.txt").read_text())
        self.assertIn("paired B-A succ: 72.0000+-8.5513: clear gap", self.out)
        self.assertIn("paired B-A succ: -4.5000+-4.8088: near-tie", self.out)
        self.assertIn("paired C-B succ: -0.5000+-1.1180: near-tie", self.out)


class Hamster(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(HA_REL)

    def test_features(self):
        rng = random.Random(2)
        sc = ha.scene(rng, 0.5)
        f = ha.mono_features([0.2, 0.3, 0.5], 0, sc)
        self.assertEqual(f[-ha.APP:], sc["bg"])
        self.assertEqual(len(ha.low_features([0.2, 0.3, 0.5], 0, [0.4, 0.1], 0.6)), 4)
        sc0 = ha.scene(rng, 0.0, 0.0)
        self.assertEqual(sc0["bg"], [0.0] * ha.APP)

    def test_paths(self):
        rng = random.Random(4)
        sc = ha.scene(rng, 0.0)
        p = ha.make_path("B_hier", sc, [0.2, 0.3, 0.5], [[0.0, 0.0], [0.0, 0.0]])
        q = ha.make_path("C_wrong", sc, [0.2, 0.3, 0.5], [[0.0, 0.0], [0.0, 0.0]])
        self.assertEqual([x[2] for x in p], [1, 0, 1])
        self.assertEqual(p[1][:2], sc["obj"][:2])
        self.assertEqual(q[1][:2], sc["dis"][:2])
        self.assertEqual(p[2], q[2])
        self.assertAlmostEqual(ha.seg_dist([0.5, 1.0], [0.0, 0.0], [1.0, 0.0]), 1.0, places=12)

    def test_streams_kept_for_declared_regimes(self):
        self.assertEqual({k: ha.STREAM[k] for k in ("coarse_path", "matched_easy", "visual_shift")},
                         {k: i for i, k in enumerate(sorted(("coarse_path", "matched_easy", "visual_shift")))})
        self.assertIn("added after the first run", (ROOT / HA_REL).read_text())

    def test_output(self):
        self.assertEqual(self.out, (ROOT / "examples/month-6/expected/hamster_hierarchical_path_toy.txt").read_text())
        self.assertIn("paired B-A succ: 76.5000+-7.4162: clear gap", self.out)
        self.assertIn("paired B-A succ: -2.5000+-4.3301: near-tie", self.out)


if __name__ == "__main__":
    unittest.main()
