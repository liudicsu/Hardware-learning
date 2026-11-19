#!/usr/bin/env python3
"""Independent contract tests for the Steinhart-Hart NTC and Nyquist-stability toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SH_REL = "examples/month-2/sensors-fusion/steinhart_hart_ntc_sense_toy.py"
NY_REL = "examples/month-5/control-modelling/nyquist_stability_criterion_toy.py"
SH_EXP = "examples/month-2/expected/steinhart_hart_ntc_sense_toy.txt"
NY_EXP = "examples/month-5/expected/nyquist_stability_criterion_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sh = load("steinhart_hart_ntc_sense_toy", SH_REL)
ny = load("nyquist_stability_criterion_toy", NY_REL)


def run(rel: str) -> str:
    return subprocess.run(
        [sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True
    ).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        for mod, rel in ((sh, SH_REL), (ny, NY_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertEqual(mod.SEEDS, (0, 1, 2, 3, 4))
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1e-16, -2e-16, 3e-16, 0.0, 1e-16], [0.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("small but consistent", mod.verdict([10.5, 10.6, 10.4, 10.5, 10.5], [10.0] * 5))
            self.assertIn("1 of 5 seeds has the opposite sign", mod.verdict([5.0, 5.0, 5.0, 5.0, -0.5], [0.0] * 5))
            self.assertEqual(mod.num(0.12345), "0.1235")
            self.assertEqual(mod.num(-0.0), "0.0000")
            src = (ROOT / rel).read_text()
            for marker in ("Common random numbers", "本页未运行", "ROUND_HALF_UP", "written before the first run"):
                self.assertIn(marker, src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")

    def test_expected_byte_identical_and_no_process_labels(self):
        for rel, exp in ((SH_REL, SH_EXP), (NY_REL, NY_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b24p1"):
            self.assertRegex(bad, PROCESS)


class SteinhartHart(unittest.TestCase):
    def test_hand_calc_and_inverse(self):
        self.assertAlmostEqual(sh.T0_K, 298.15, places=12)
        self.assertAlmostEqual(0.0 + sh.K0, 273.15, places=12)
        self.assertAlmostEqual(80.0 + sh.K0, 353.15, places=12)
        self.assertAlmostEqual(1.0 / sh.T0_K, 1.0 / 298.15, places=15)
        self.assertAlmostEqual(sh.true_R(25.0), 10000.0, places=9)
        v25 = sh.VCC * sh.true_R(25.0) / (sh.true_R(25.0) + sh.R_DIV)
        self.assertAlmostEqual(v25, 1.65, places=12)
        # Inverse reconstructs the three declared points.
        for R, T in sh.CAL_POINTS:
            self.assertAlmostEqual(sh.sh_R_from_T(T, sh.SH_A, sh.SH_B, sh.SH_C), R, places=9)
            self.assertAlmostEqual(sh.sh_T_from_R(R, sh.SH_A, sh.SH_B, sh.SH_C), T, places=9)
        out = (ROOT / SH_EXP).read_text()
        for s in (
            "hand_calc 25 C in kelvin = 298.1500",
            "hand_calc 1/T at 25 C = 3.3540164347e-03",
            "hand_calc true R at 25 C = 10000.0000",
            "hand_calc divider V at 25 C, no noise = 1.6500",
            "sh_A=1.7038685512e-03",
            "beta=3182.6587",
            "adc_p=81.0959",
            "near-tie / small gap, within seed noise (|m| <= sd)",
            "paired B-A rmse_C: -4.1852+-0.4341: clear gap",
            "paired C-B rmse_C: 11.6515+-0.2455: clear gap",
        ):
            self.assertIn(s, out)

    def test_stdlib_and_crn_header(self):
        src = (ROOT / SH_REL).read_text()
        self.assertIn("import math", src)
        self.assertIn("import random", src)
        out = (ROOT / SH_EXP).read_text()
        self.assertIn("Common random numbers: the resistance noise draw is shared across arms", out)
        self.assertIn("Regimes and parameters were written before the first run", out)
        self.assertIn("本页未运行", out)
        self.assertIn("cited error-bound claim 以原文为准", out)
        self.assertNotIn("0.02 C", out)


class Nyquist(unittest.TestCase):
    def test_declared_plants_and_hand_calc(self):
        stable = ny.analyze(ny.PLANTS["ol_stable_joint"], ny.PTS_PER_DEC)
        unstable = ny.analyze(ny.PLANTS["ol_unstable"], ny.PTS_PER_DEC)
        nmp = ny.analyze(ny.PLANTS["nmp_encircle"], ny.PTS_PER_DEC)
        self.assertEqual(stable["N"], 0)
        self.assertEqual(stable["P"], 0)
        self.assertEqual(stable["Z"], 0)
        self.assertGreater(stable["first_pm"], 30.0)
        self.assertEqual(unstable["N"], 0)
        self.assertEqual(unstable["P"], 1)
        self.assertEqual(unstable["Z"], 1)
        self.assertGreater(unstable["first_pm"], 30.0)
        self.assertEqual(nmp["N"], 2)
        self.assertEqual(nmp["P"], 0)
        self.assertEqual(nmp["Z"], 2)
        self.assertGreater(nmp["first_pm"], 30.0)
        # Closed-loop DC of the stable plant: G(0)=2, 2/3 ≈ 0.6667.
        self.assertAlmostEqual(stable["y_end"], 2.0 / 3.0, places=3)
        scores_s = ny.arm_scores(stable)
        scores_u = ny.arm_scores(unstable)
        scores_n = ny.arm_scores(nmp)
        self.assertEqual(scores_s["A_bode_first"]["call"], 1.0)
        self.assertEqual(scores_s["B_nyquist"]["call"], 1.0)
        self.assertEqual(scores_u["A_bode_first"]["miss"], 1.0)
        self.assertEqual(scores_u["B_nyquist"]["call"], 0.0)
        self.assertEqual(scores_n["C_bode_any"]["miss"], 1.0)
        self.assertEqual(scores_n["B_nyquist"]["miss"], 0.0)
        out = (ROOT / NY_EXP).read_text()
        for s in (
            "hand_calc Z = N + P, closed-loop stable iff Z = 0",
            "hand_calc step-stability bound: |y| clipped at 20.0000",
            "hand_calc ol_stable_joint wn=6.0000 zeta=0.5000 K=2.0000",
            "hand_calc ol_unstable factor 0.2000",
            "hand_calc nmp_encircle factor 0.2000",
            "first_pm=49.3542",
            "first_pm=90.1206",
            "first_pm=84.9799",
            "Z=1",
            "Z=2",
            "tie: identical on every seed",
            "paired B-A miss: -1.0000+-0.0000: clear gap",
            "paired C-B miss: 1.0000+-0.0000: clear gap",
        ):
            self.assertIn(s, out)


if __name__ == "__main__":
    unittest.main()
