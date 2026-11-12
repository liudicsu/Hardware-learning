#!/usr/bin/env python3
"""Independent contract tests for batch-20 PR3 InternVLA-A1 foresight + GraspVLA synthetic-pretrain toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A1_REL = "examples/month-9/world-models-overview/internvla_a1_mot_foresight_toy.py"
GV_REL = "examples/month-7/perception-to-grasp/graspvla_syngrasp_pretrain_toy.py"
A1_EXP = "examples/month-9/expected/internvla_a1_mot_foresight_toy.txt"
GV_EXP = "examples/month-7/expected/graspvla_syngrasp_pretrain_toy.txt"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


a1 = load("internvla_a1_mot_foresight_toy", A1_REL)
gv = load("graspvla_syngrasp_pretrain_toy", GV_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def section(out: str, start: str, end: str) -> str:
    return out.split(start)[1].split(end)[0]


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((a1, A1_REL), (gv, GV_REL)):
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
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|cv2)")
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))

    def test_half_up_rounding(self):
        for mod in (a1, gv):
            self.assertEqual(mod.num(0.00125), "0.0013")      # half-up, not half-even
            self.assertEqual(mod.num(0.12345), "0.1235")
            self.assertEqual(mod.num(2 / 256), "0.0078")
            self.assertEqual(mod.num(-0.00004), "-4.000e-5")  # Decimal exponent form; no such value is printed by either toy
            self.assertEqual(mod.num(-1e-12 * 0), "0.0000")

    def test_byte_identical_rerun(self):
        for rel, exp in ((A1_REL, A1_EXP), (GV_REL, GV_EXP)):
            first, second = run(rel), run(rel)
            self.assertEqual(first, second)
            self.assertEqual(first, (ROOT / exp).read_text())
            self.assertNotRegex(first, r"(?<![+\d.e])-0\.0+(?![\d.e])")


class Foresight(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((a1.N_SCENES, a1.H, a1.V_LO, a1.V_HI, a1.SIGMA_LO, a1.SIGMA_HI), (50, 0.5, 10.0, 30.0, 0.3, 1.2))
        self.assertEqual((a1.P_CORRUPT, a1.CORRUPT_CM, a1.TOL), (0.3, 6.0, 2.0))
        self.assertEqual(a1.ARMS, ("A_action_only", "B_foresight", "C_corrupt"))
        self.assertEqual(list(a1.REGIMES), ["static", "dynamic", "static_noisy"])

    def test_crn_and_shared_understanding(self):
        for seed in a1.SEEDS:
            self.assertEqual(a1.scenes("dynamic", seed), a1.scenes("dynamic", seed))
        pos, target = (3.0, 17.0), 1
        self.assertEqual(a1.understand(pos, target), 17.0)

    def test_noiseless_foresight_is_exact(self):
        # Independent form: with zero noise, constant-velocity extrapolation hits x0 + v*H exactly; A misses by |v|*H.
        scene = ((10.0, 30.0), 0, 20.0, 0.0, 0.0, 0.9, 1.0)
        truth = 10.0 + 20.0 * a1.H
        self.assertAlmostEqual(a1.aim("B_foresight", scene, a1.P_CORRUPT), truth, places=12)
        self.assertAlmostEqual(abs(a1.aim("A_action_only", scene, a1.P_CORRUPT) - truth), 20.0 * a1.H, places=12)
        bad = ((10.0, 30.0), 0, 20.0, 0.0, 0.0, 0.1, -1.0)
        self.assertAlmostEqual(a1.aim("C_corrupt", bad, a1.P_CORRUPT) - truth, -a1.CORRUPT_CM, places=12)
        self.assertAlmostEqual(a1.aim("C_corrupt", bad, 0.05), truth, places=12)

    def test_strict_tolerance_and_hand_calcs(self):
        self.assertFalse(a1.TOL < a1.TOL)
        self.assertGreater(a1.V_LO * a1.H, a1.TOL)
        self.assertAlmostEqual(math.sqrt(4 + 1) * a1.SIGMA_LO, 0.670820393, places=8)

    def test_printed_regimes(self):
        out = (ROOT / A1_EXP).read_text()
        self.assertIn("success iff aim_err < TOL, strict", out)
        self.assertIn("5.0000 cm to 30.0*0.5 = 15.0000 cm", out)
        static = section(out, "static (", "dynamic (")
        self.assertIn("paired B-A success: -0.0040+-0.0089: near-tie", static)
        dyn = section(out, "dynamic (", "static_noisy (")
        self.assertIn("paired B-A success: 0.9920+-0.0110: clear gap", dyn)
        self.assertIn("paired C-B success: -0.3120+-0.0576: clear gap", dyn)
        noisy = section(out, "static_noisy (", "alternative TOL")
        self.assertIn("paired B-A success: -0.3720+-0.0729: clear gap", noisy)
        for block in (static, dyn, noisy):
            self.assertRegex(block, r"paired C-B success: -\d\.\d{4}\+-\d\.\d{4}: clear gap, not a tie \(\|m\| > sd\); same sign on all 5 seeds")
        self.assertIn("paired C-B success@alt: -0.1080+-0.0642: small but consistent", out)


class GraspVLA(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((gv.DIM, gv.S_CAT, gv.W_CAT, gv.N_PER, gv.N_OBJ, gv.N_SCENES), (8, 6, 4, 30, 3, 60))
        self.assertEqual((gv.DR_GAIN, gv.DR_OFF, gv.REAL_GAIN, gv.REAL_OFF), ((0.4, 1.6), (-0.5, 0.5), 0.6, 0.35))
        self.assertEqual((gv.ORI_SIGMA, gv.ORI_TOL), (5.0, 10.0))
        self.assertEqual(gv.ARMS, ("A_geom", "B_cot_dr", "C_no_dr", "D_shuffled"))
        self.assertEqual(gv.REGIMES, ("in_family", "web_category", "single_object"))

    def test_crn_training_shared(self):
        b, c, d = (gv.train_set(arm, 0) for arm in ("B_cot_dr", "C_no_dr", "D_shuffled"))
        self.assertEqual([lab for lab, _ in b], [lab for lab, _ in c])
        n_syn = gv.S_CAT * gv.N_PER
        self.assertEqual([x for _, x in b[n_syn:]], [x for _, x in c[n_syn:]])     # same Internet set
        self.assertEqual([x for _, x in b], [x for _, x in d])                    # D differs only in labels
        self.assertTrue(all(ld == (lb + 1) % (gv.S_CAT + gv.W_CAT) for (lb, _), (ld, _) in zip(b, d)))
        self.assertEqual(gv.test_scenes("in_family", 3), gv.test_scenes("in_family", 3))

    def test_web_categories_only_in_internet_set(self):
        syn, web = gv.train_draws(1)
        self.assertTrue(all(c < gv.S_CAT for c, *_ in syn))
        self.assertTrue(all(c >= gv.S_CAT for c, *_ in web))
        for named, objs in gv.test_scenes("web_category", 1):
            self.assertGreaterEqual(named, gv.S_CAT)
            self.assertEqual(sum(1 for o in objs if o[0] >= gv.S_CAT), 1)

    def test_single_object_identical(self):
        for seed in gv.SEEDS:
            rows = [gv.evaluate(arm, "single_object", seed, gv.trained(arm, seed)) for arm in gv.ARMS]
            self.assertTrue(all(r == rows[0] for r in rows))

    def test_ceiling_hand_calc(self):
        self.assertAlmostEqual(math.erf(gv.ORI_TOL / (gv.ORI_SIGMA * math.sqrt(2))), 0.954499736, places=8)
        self.assertTrue(gv.DR_GAIN[0] <= gv.REAL_GAIN <= gv.DR_GAIN[1] and gv.DR_OFF[0] <= gv.REAL_OFF <= gv.DR_OFF[1])

    def test_printed_regimes(self):
        out = (ROOT / GV_EXP).read_text()
        self.assertIn("domain_check: real domain inside the wide DR range: True; equal to the canonical no-DR domain: False; inside the narrow DR range: False", out)
        fam = section(out, "in_family:", "web_category:")
        self.assertIn("paired B-A success: 0.5400+-0.1217: clear gap", fam)
        self.assertIn("paired D-B success: -0.6467+-0.1114: clear gap", fam)
        self.assertIn("paired C-B success: 0.0233+-0.0630: near-tie", fam)
        web = section(out, "web_category:", "single_object:")
        self.assertIn("paired B-A success: 0.5667+-0.1074: clear gap", web)
        self.assertIn("paired C-B success: 0.0000+-0.0000: tie: identical on every seed", web)
        single = section(out, "single_object:", "alternative narrow")
        self.assertEqual(single.count("tie: identical on every seed"), 4)
        self.assertIn("here the canonical no-DR arm did not lose", out)
        self.assertNotIn("needs DR on the synthetic side", out)


if __name__ == "__main__":
    unittest.main()
