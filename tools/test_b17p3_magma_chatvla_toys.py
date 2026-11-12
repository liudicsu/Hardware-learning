#!/usr/bin/env python3
"""Independent checks for batch-17 PR3 toys: Magma-style marks / traces and ChatVLA-style phased alignment."""
import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MG_REL = "examples/month-6/policy-evaluation/magma_som_tom_toy.py"
CV_REL = "examples/month-8/vla-finetune/chatvla_phased_alignment_toy.py"


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mg = load("magma_som_tom_toy", MG_REL)
cv = load("chatvla_phased_alignment_toy", CV_REL)


class Magma(unittest.TestCase):
    def test_quantise_hand(self):
        self.assertAlmostEqual(mg.quantise(0.0), 0.5 / 256, places=12)
        self.assertAlmostEqual(mg.quantise(0.999999), 255.5 / 256, places=12)
        self.assertAlmostEqual(mg.quantise(0.5), 128.5 / 256, places=12)
        for u in (0.05, 0.3141, 0.77, 0.95):
            self.assertLessEqual(abs(mg.quantise(u) - u), 0.5 / 256 + 1e-12)

    def test_plans_hand(self):
        pos = [(0.2, 0.2), (0.8, 0.8)]
        vel = [(0.01, 0.0), (0.0, 0.0)]
        scene = (pos, vel, [10.0, 10.0], (0.0, 0.0), (0.0, 0.0), [1, 0])
        a = mg.plan("A_direct", scene)
        self.assertAlmostEqual(a[0][0], 0.5, places=12)
        self.assertEqual(a[0], a[mg.L])
        b = mg.plan("B_somtom", scene)
        self.assertAlmostEqual(b[mg.L][0], mg.quantise(0.2) + 0.08, places=12)
        c = mg.plan("C_shuffle", scene)
        self.assertAlmostEqual(c[0][0], mg.quantise(0.8), places=12)

    def test_single_target_permutation_identity(self):
        for sc in mg.shared_draws("single_target", 0):
            self.assertEqual(sc[5], [0])

    def test_crn_and_regimes(self):
        self.assertEqual(mg.shared_draws("cluttered", 3), mg.shared_draws("cluttered", 3))
        self.assertEqual(set(mg.REGIMES), {"cluttered", "single_target", "static_jitter"})
        src = (ROOT / MG_REL).read_text()
        self.assertIn("written before the first run", src)
        self.assertIn("No integration step", src)
        self.assertIn("B ties or loses to A on success", src)

    def test_expected_byte_identical(self):
        out = subprocess.run([sys.executable, str(ROOT / MG_REL)], capture_output=True, text=True, check=True).stdout
        self.assertEqual(out, (ROOT / "examples/month-6/expected/magma_som_tom_toy.txt").read_text())
        self.assertIn("noise-free target weight 0.7416", out)
        self.assertAlmostEqual(math.exp(3) / (math.exp(3) + 7), 0.7416, places=4)


class ChatVLA(unittest.TestCase):
    def test_baseline_is_its_own_teacher(self):
        draws = cv.shared_draws("conflict", 0)
        self.assertEqual(cv.Net(draws[0], moe=False).evaluate(draws[3])[1], 100.0)

    def test_prototypes_hand(self):
        self.assertAlmostEqual(cv.V0[1][0], -0.5, places=12)
        self.assertAlmostEqual(cv.V0[1][1], math.sqrt(3) / 2, places=12)

    def test_moe_isolates_vqa_expert_in_stage1(self):
        draws = cv.shared_draws("conflict", 1)
        net = cv.Net(draws[0], moe=True)
        for b in draws[1][:5]:
            net.step(b, "ctrl")
        self.assertEqual(net.P["vqa"], cv.P0)
        self.assertEqual(net.V, cv.V0)
        self.assertNotEqual(net.P["ctrl"], cv.P0)

    def test_crn_and_regimes(self):
        self.assertEqual(cv.shared_draws("few_vqa", 2), cv.shared_draws("few_vqa", 2))
        self.assertEqual(set(cv.REGIMES), {"conflict", "aligned", "few_vqa"})
        src = (ROOT / CV_REL).read_text()
        self.assertIn("written before the first run", src)
        self.assertIn("No integration step", src)
        self.assertIn("all three near-tie on control and VQA", src)

    def test_expected_byte_identical(self):
        out = subprocess.run([sys.executable, str(ROOT / CV_REL)], capture_output=True, text=True, check=True).stdout
        self.assertEqual(out, (ROOT / "examples/month-8/expected/chatvla_phased_alignment_toy.txt").read_text())


if __name__ == "__main__":
    unittest.main(verbosity=1)
