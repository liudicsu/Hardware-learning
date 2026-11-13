#!/usr/bin/env python3
"""Independent contract tests for the PointVLA frozen-injector and EgoVLA human-pretrain toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import random
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PV_REL = "examples/month-7/depth-pointcloud/pointvla_frozen_injector_toy.py"
EG_REL = "examples/month-11/umi-style-collection/egovla_human_pretrain_retarget_toy.py"
PV_EXP = "examples/month-7/expected/pointvla_frozen_injector_toy.txt"
EG_EXP = "examples/month-11/expected/egovla_human_pretrain_retarget_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pv = load("pointvla_frozen_injector_toy", PV_REL)
eg = load("egovla_human_pretrain_retarget_toy", EG_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        for mod, rel in ((pv, PV_REL), (eg, EG_REL)):
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
        for rel, exp in ((PV_REL, PV_EXP), (EG_REL, EG_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b22p3"):
            self.assertRegex(bad, PROCESS)


class PointVla(unittest.TestCase):
    def test_grip_quality_and_closing_probability(self):
        self.assertAlmostEqual(pv.q_of(None), 1.0)
        self.assertAlmostEqual(pv.q_of(pv.LATE_BLOCK), 0.97)
        self.assertAlmostEqual(pv.q_of(pv.EARLY_BLOCK), 0.85)
        phi = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
        got = [round(phi((q - pv.GRIP_THR) / pv.SIG_GRIP), 4) for q in (1.0, 0.97, 0.85)]
        self.assertEqual(got, [0.9938, 0.9599, 0.1056])
        self.assertAlmostEqual(sum(pv.W_BLOCK), 1.0)

    def test_hand_calcs_printed(self):
        out = (ROOT / PV_EXP).read_text()
        self.assertAlmostEqual((1 - pv.RGB_CUE) * (pv.H_SHIFT - pv.H_TRAIN), 0.0441, places=6)
        self.assertAlmostEqual(round(pv.SIG_PC / math.sqrt(pv.N_PTS), 4), 0.0007)
        for s in ("0.0441", "0.0007", "0.9938", "0.9599", "0.1056", "0.7000", "0.9400"):
            self.assertIn(s, out)

    def test_common_draws_shared_by_injected_arms(self):
        for regime in ("train_height", "height_shift", "real_vs_photo", "corrupted_cloud"):
            for seed in pv.SEEDS:
                r = pv.run_seed(regime, seed)
                self.assertEqual(r["B_late"]["height_err_mm"], r["C_early"]["height_err_mm"])
                self.assertEqual(r["B_late"]["false_grasp"], r["C_early"]["false_grasp"])
                self.assertGreaterEqual(r["B_late"]["success"], r["C_early"]["success"])

    def test_two_d_head_fails_raised_table_and_grasps_photos(self):
        for seed in pv.SEEDS:
            self.assertEqual(pv.run_seed("height_shift", seed)["A_2d"]["success"], 0.0)
            self.assertEqual(pv.run_seed("real_vs_photo", seed)["A_2d"]["false_grasp"], 1.0)

    def test_median_resists_outliers(self):
        for seed in pv.SEEDS:
            mean_err = pv.run_seed("corrupted_cloud", seed)["B_late"]["height_err_mm"]
            med_err = pv.run_seed("corrupted_cloud", seed, median=True)["B_late"]["height_err_mm"]
            self.assertLess(med_err, mean_err)

    def test_declared_regime_lines(self):
        out = (ROOT / PV_EXP).read_text()
        for line in ("paired B-A success: -0.0300+-0.0326: near-tie",
                     "paired B-A success: 0.9750+-0.0177: clear gap",
                     "paired B-A success: 0.4000+-0.1000: clear gap",
                     "paired B-A success: -0.3050+-0.0925: clear gap",
                     "paired C-B success: -0.7900+-0.0783: clear gap"):
            self.assertIn(line, out)


class EgoVla(unittest.TestCase):
    def test_ridge_solves_declared_objective(self):
        rng = random.Random(11)
        X = [[rng.gauss(0, 1) for _ in range(eg.D)] for _ in range(32)]
        th = [rng.gauss(0, 1) for _ in range(eg.D)]
        Y = [sum(a * b for a, b in zip(x, th)) + 1.0 for x in X]
        t0, b0 = eg.ridge_fit(X, Y, [0.0] * eg.D, 0.0)
        self.assertLess(max(abs(a - b) for a, b in zip(t0, th)), 1e-5)
        self.assertLess(abs(b0 - 1.0), 1e-5)
        mu = [rng.gauss(0, 1) for _ in range(eg.D)]
        Yn = [y + 0.5 * rng.gauss(0, 1) for y in Y]
        t, b = eg.ridge_fit(X, Yn, mu, 25.0)
        g = [0.0] * (eg.D + 1)
        for x, y in zip(X, Yn):
            r = y - sum(p * q for p, q in zip(x, t)) - b
            for j in range(eg.D):
                g[j] += -2 * x[j] * r
            g[eg.D] += -2 * r
        for j in range(eg.D):
            g[j] += 2 * 25.0 * (t[j] - mu[j])
        g[eg.D] += 2 * 1e-6 * b
        self.assertLess(max(abs(v) for v in g), 1e-8)

    def test_hand_calcs(self):
        out = (ROOT / EG_EXP).read_text()
        s_a = math.sqrt(0.25 * 17 / 14)
        p_a = math.erf(0.5 / (s_a * math.sqrt(2)))
        p_h = math.erf(0.5 / (0.4 * math.sqrt(2)))
        for v in (s_a, 0.4, p_a, p_a ** 4, p_h, p_h ** 4):
            self.assertIn(f"{v:.4f}", out)
        self.assertAlmostEqual(eg.LAM_A, 0.25)
        self.assertAlmostEqual(eg.LAM_B, 25.0)
        self.assertAlmostEqual(eg.OFFSET_MISMATCH / eg.TOL, 3.0)

    def test_half_data_uses_first_demos_of_same_draws(self):
        self.assertEqual(eg.REGIMES["half_data"][0], 16)
        self.assertEqual(eg.REGIMES["in_domain_full"][0], 32)
        a = eg.draws_for(0, 0)
        rng = random.Random("0/0")
        th = [rng.gauss(0.0, 1.0) for _ in range(eg.D)]
        self.assertEqual(th, a[0])

    def test_zero_shot_independent_of_demo_count(self):
        full = eg.regime_results("in_domain_full")["C_zero_shot"]
        half = eg.regime_results("half_data")["C_zero_shot"]
        self.assertEqual(full, half)

    def test_declared_regime_lines(self):
        out = (ROOT / EG_EXP).read_text()
        for line in ("paired B-A long_sr: 0.4300+-0.1430: clear gap",
                     "paired C-A short_sr: -0.6320+-0.0746: clear gap",
                     "paired B-A long_sr: -0.2180+-0.0955: clear gap",
                     "paired B(half_data)-B(in_domain_full) long_sr: -0.1620+-0.0841: clear gap",
                     "本页未运行", "以论文为准"):
            self.assertIn(line, out)


if __name__ == "__main__":
    unittest.main()
