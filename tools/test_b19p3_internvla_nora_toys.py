#!/usr/bin/env python3
"""Independent contract tests for batch-19 PR3 InternVLA-M1 where-then-how + NORA FAST-style toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IV_REL = "examples/month-6/vla-models/internvla_m1_spatial_prompt_toy.py"
NR_REL = "examples/month-8/async-deployment/nora_fastplus_small_vla_toy.py"
IV_EXP = "examples/month-6/expected/internvla_m1_spatial_prompt_toy.txt"
NR_EXP = "examples/month-8/expected/nora_fastplus_small_vla_toy.txt"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


iv = load("internvla_m1_spatial_prompt_toy", IV_REL)
nr = load("nora_fastplus_small_vla_toy", NR_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def section(out: str, start: str, end: str) -> str:
    return out.split(start)[1].split(end)[0]


CLEAR = "clear gap, not a tie (|m| > sd); same sign on all 5 seeds"
SMALL = "small but consistent gap, not a tie (|m| > sd); same sign on all 5 seeds"
TIE = "0.0000+-0.0000: tie: identical on every seed"


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((iv, IV_REL), (nr, NR_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertEqual(mod.SEEDS, (0, 1, 2, 3, 4))
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1e-16, -2e-16, 3e-16, 0.0, 1e-16], [0.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertNotIn("seeds", v)
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("small but consistent", mod.verdict([10.5, 10.6, 10.4, 10.5, 10.5], [10.0] * 5))
            self.assertIn("1 of 5 seeds has the opposite sign", mod.verdict([5.0, 5.0, 5.0, 5.0, -0.5], [0.0] * 5))
            src = (ROOT / rel).read_text()
            for marker in ("Common random numbers", "本页未运行", "以论文为准", "No integration step", "written before the first run"):
                self.assertIn(marker, src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))


class InternVLA(unittest.TestCase):
    def test_declared(self):
        self.assertEqual(iv.ARMS, ("A_direct", "B_where_how", "C_shuffled"))
        self.assertEqual(list(iv.REGIMES), ["cluttered", "single_object", "many_demos", "camera_shift"])
        self.assertEqual((iv.N_COLOR, iv.N_SHAPE, iv.N_TEST, iv.G_ITEMS), (6, 5, 200, 600))
        self.assertEqual((iv.SIGMA_EXEC, iv.TOL), (0.02, 0.05))

    def test_crn_shared_world(self):
        a = iv.shared_world("cluttered", 2)
        self.assertEqual(a, iv.shared_world("cluttered", 2))
        # The grounding corpus is the same in every regime for a seed.
        self.assertEqual(a["corpus"], iv.shared_world("camera_shift", 2)["corpus"])

    def test_knowledge_superset_and_swap(self):
        w = iv.shared_world("cluttered", 0)
        ka, kb = iv.knowledge("A_direct", w, "cluttered"), iv.knowledge("B_where_how", w, "cluttered")
        self.assertTrue(set(ka) <= set(kb))
        self.assertTrue(all(kb[p] == p for p in kb))
        ws = iv.shared_world("camera_shift", 0)
        kbs = iv.knowledge("B_where_how", ws, "camera_shift")
        self.assertTrue(any(kbs[p] != p for p in kbs))
        self.assertEqual(iv.swap_colour((0, 3)), (1, 3))
        self.assertEqual(iv.swap_colour((1, 2)), (0, 2))
        self.assertEqual(iv.swap_colour((4, 2)), (4, 2))

    def test_single_object_cannot_misground(self):
        w = iv.shared_world("single_object", 1)
        for sc in w["tests"][:20]:
            self.assertEqual(iv.ground({}, sc, (5, 4)), 0)

    def test_strict_success(self):
        self.assertFalse(iv.TOL < iv.TOL)
        self.assertTrue(iv.TOL - 1e-4 < iv.TOL)

    def test_expected(self):
        out = run(IV_REL)
        self.assertEqual((ROOT / IV_EXP).read_text(), out)
        self.assertIn("P(radius < TOL) = 1-exp(-(TOL/SIGMA_EXEC)^2/2) = 95.6063 %", out)
        self.assertAlmostEqual(100.0 * (1.0 - math.exp(-(0.05 / 0.02) ** 2 / 2.0)), 95.6063, places=4)
        self.assertIn("1/8 = 12.5000 %", out)
        cl = section(out, "cluttered (", "single_object (")
        self.assertIn(f"paired B-A success_pct: 14.6000+-7.3263: {SMALL}", cl)
        self.assertIn(f"paired C-B success_pct: -94.2000+-1.7176: {CLEAR}", cl)
        so = section(out, "single_object (", "many_demos (")
        self.assertIn(f"paired B-A success_pct: {TIE}", so)
        md = section(out, "many_demos (", "camera_shift (")
        self.assertIn(f"paired B-A success_pct: {TIE}", md)
        cs = section(out, "camera_shift (", "alternative ")
        self.assertIn(f"paired B-A success_pct: -23.8000+-4.4385: {CLEAR}", cs)
        self.assertIn(f"paired C-B success_pct: -70.4000+-3.9592: {CLEAR}", cs)
        self.assertIn(f"paired B-A success_pct@alt: 12.1000+-7.0480: {SMALL}", out)
        self.assertIn(f"paired B-A success_pct@alt: -21.1000+-3.6125: {CLEAR}", out)


class Nora(unittest.TestCase):
    def test_declared(self):
        self.assertEqual(nr.ARMS, ("A_large_bins", "B_small_fast", "C_shuffled"))
        self.assertEqual(list(nr.REGIMES), ["short_in_dist", "long_horizon"])
        self.assertEqual((nr.D, nr.N_EP, nr.BINS, nr.GAMMA, nr.P_LARGE, nr.P_SMALL, nr.TOL), (7, 200, 256, 10.0, 7.0, 3.0, 0.06))
        self.assertEqual(nr.REGIMES["short_in_dist"]["SIG_LARGE"], nr.REGIMES["short_in_dist"]["SIG_SMALL"])
        self.assertGreater(nr.REGIMES["long_horizon"]["SIG_SMALL"], nr.REGIMES["long_horizon"]["SIG_LARGE"])

    def test_dct_roundtrip_and_bins(self):
        x = [math.sin(0.3 * t) for t in range(10)]
        y = nr.idct(nr.dct(x))
        self.assertLess(max(abs(a - b) for a, b in zip(x, y)), 1e-12)
        r = nr.bins_roundtrip([0.123, -0.9, 0.999, -1.0, 1.0])
        self.assertLessEqual(max(abs(a - b) for a, b in zip([0.123, -0.9, 0.999, -1.0, 1.0], r)), 1.0 / nr.BINS + 1e-12)

    def test_crn(self):
        a = nr.shared_chunks("short_in_dist", 3)
        self.assertEqual(a, nr.shared_chunks("short_in_dist", 3))

    def test_expected(self):
        out = run(NR_REL)
        self.assertEqual((ROOT / NR_EXP).read_text(), out)
        self.assertIn("D*H = 7*10 = 70 (H=10) and 7*30 = 210 (H=30)", out)
        self.assertIn("at most half a bin = 0.003906", out)
        self.assertIn("1/(GAMMA*sqrt(12)) = 0.028868", out)
        sh = section(out, "short_in_dist (", "long_horizon (")
        self.assertIn(f"paired B-A success_pct: {TIE}", sh)
        self.assertIn(f"paired B-A cost: -399.2110+-0.6314: {CLEAR}", sh)
        self.assertIn(f"paired C-B success_pct: -100.0000+-0.0000: {CLEAR}", sh)
        lh = section(out, "long_horizon (", "alternative ")
        self.assertIn(f"paired B-A success_pct: -72.9000+-1.7819: {CLEAR}", lh)
        self.assertIn(f"paired B-A cost: -1184.3520+-2.1307: {CLEAR}", lh)
        self.assertIn(f"paired B-A success_pct@alt: -10.2000+-2.1966: {SMALL}", out)


if __name__ == "__main__":
    unittest.main()
