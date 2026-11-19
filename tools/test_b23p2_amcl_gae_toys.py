#!/usr/bin/env python3
"""Independent contract tests for the AMCL particle-filter and GAE lambda toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import random
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AM_REL = "examples/month-4/slam-nav/amcl_particle_filter_localization_toy.py"
GAE_REL = "examples/month-7/rl-foundations/gae_lambda_advantage_toy.py"
AM_EXP = "examples/month-4/expected/amcl_particle_filter_localization_toy.txt"
GAE_EXP = "examples/month-7/expected/gae_lambda_advantage_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


am = load("amcl_particle_filter_localization_toy", AM_REL)
gae = load("gae_lambda_advantage_toy", GAE_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        for mod, rel in ((am, AM_REL), (gae, GAE_REL)):
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
        for rel, exp in ((AM_REL, AM_EXP), (GAE_REL, GAE_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b22p3"):
            self.assertRegex(bad, PROCESS)


class AMCL(unittest.TestCase):
    def test_kld_and_hand_calc(self):
        self.assertAlmostEqual(am.kld_count(2), 10 * (1 - 2 / 9 + math.sqrt(2 / 9) * 2.326) ** 3, places=9)
        self.assertLess(am.kld_count(2), am.N_MIN)
        self.assertGreater(am.kld_count(50), am.N_MAX)
        self.assertAlmostEqual(am.Z_RAND / am.R_MAX, 0.0125, places=12)
        out = (ROOT / AM_EXP).read_text()
        for s in ("raw 65.8404, clamped to [100, 600] = 100.0000", "raw 216.9395", "raw 749.3302, clamped to [100, 600] = 600.0000",
                  "Z_RAND/R_MAX = 0.0125", "= 0.1250 m",
                  "bin_size=0.5000 n_steps=25 n_steps_short=6 kidnap_after=10 tail_steps=5 room=10.0000x6.0000 corridor=12.0000x2.0000"):
            self.assertIn(s, out)

    def test_map_geometry(self):
        room, boxes = am.ROOMS["distinctive"]
        self.assertFalse(am.is_free(room, boxes, 2.0, 1.5))
        self.assertTrue(am.is_free(room, boxes, 0.5, 0.5))
        r = am.beam_ranges(room, boxes, 0.5, 1.5)
        self.assertAlmostEqual(r[0], 1.0, places=12)   # +x hits the box at x = 1.5
        self.assertAlmostEqual(r[1], 0.5, places=12)
        c_room, c_boxes = am.ROOMS["corridor"]
        for x in (0.5, 4.0, 6.0, 8.0, 11.5):
            r = am.beam_ranges(c_room, c_boxes, x, 1.0)
            # an end wall is always within the beam range in the 12 m corridor
            self.assertLessEqual(min(r[0], r[1]), am.R_MAX)
            self.assertAlmostEqual(min(r[0], r[1]), min(12.0 - x, x), places=12)

    def test_common_random_numbers_shared(self):
        a = am.precompute("kidnapped", 2)
        self.assertEqual(a, am.precompute("kidnapped", 2))
        rng = random.Random("kidnapped/2")
        room, boxes = am.ROOMS["distinctive"]
        self.assertEqual(a[2], am.sample_free(room, boxes, rng))

    def test_dead_reckoning_from_truth_is_exact_without_noise(self):
        traj = [(1.3, 1.0), (1.6, 1.0)]
        cmds = [(0.3, 0.0), (0.3, 0.0)]
        errs = am.run_arm_a((1.0, 1.0), traj, cmds)
        self.assertAlmostEqual(errs[0], 0.0, places=12)
        self.assertAlmostEqual(errs[1], 0.0, places=12)

    def test_declared_regimes_printed_as_they_came(self):
        out = (ROOT / AM_EXP).read_text()
        for s in ("paired B-A err: -2.9468+-1.1879: clear gap", "paired B-A err: -0.0157+-0.0066: clear gap",
                  "paired C-B err: 4.4777+-1.9964: clear gap", "paired C-B success: -1.0000+-0.0000: clear gap",
                  "paired X-B err: 4.4964+-1.9985: clear gap", "paired X-C err: -2.7986+-1.3081: clear gap"):
            self.assertIn(s, out)


class GAE(unittest.TestCase):
    def test_true_gradient_hand_calc(self):
        self.assertAlmostEqual(gae.true_grad("long_noisy"), 0.25 * (1 - 0.99 ** 50) / 0.01, places=9)
        self.assertAlmostEqual(gae.true_grad("one_step"), 0.25, places=12)
        self.assertAlmostEqual(gae.true_grad("delayed_coarse"), 30 * 0.99 ** 29 * 0.25, places=9)
        out = (ROOT / GAE_EXP).read_text()
        for s in ("hand_calc g_true long_noisy = 9.8748", "hand_calc g_true one_step = 0.2500",
                  "hand_calc g_true delayed_coarse = 5.6038", "for LAM = 0.95 = 16.8067", "for LAM = 1 = 100.0000",
                  "long_noisy_H=50 delayed_coarse_H=30"):
            self.assertIn(s, out)

    def test_recursion_special_cases(self):
        # Eq. 17 / Eq. 18 on one shared episode: lambda = 0 gives delta, lambda = 1 gives return minus V.
        H, data = gae.build_data("long_noisy", 1)
        V = [gae.true_value("long_noisy", t) for t in range(H)]
        actions, deltas = data[0][0]
        for lam in (0.0, 1.0):
            run = 0.0; adv = [0.0] * H
            for t in range(H - 1, -1, -1):
                run = deltas[t] + gae.GAMMA * lam * run; adv[t] = run
            if lam == 0.0:
                self.assertEqual(adv, deltas)
            else:
                ref = sum(gae.GAMMA ** l * deltas[l] for l in range(H))
                self.assertAlmostEqual(adv[0], ref, places=9)
        self.assertEqual(len(V), H)

    def test_one_step_all_lambdas_identical(self):
        res = gae.seed_metrics("one_step", 2, (1.0, gae.LAM_DECL, 0.0))
        self.assertEqual(res[1.0], res[gae.LAM_DECL])
        self.assertEqual(res[1.0], res[0.0])

    def test_common_random_numbers_shared(self):
        a = gae.build_data("delayed_coarse", 3)
        self.assertEqual(a, gae.build_data("delayed_coarse", 3))
        # the value errors are the first H draws of the regime/seed stream; actions follow
        rng = random.Random("long_noisy/0")
        [rng.gauss(0.0, 1.0) for _ in range(50)]
        first_action = 1 if rng.random() < gae.P1 else 0
        H, data = gae.build_data("long_noisy", 0)
        self.assertEqual(data[0][0][0][0], first_action)
        # all arms are computed from the same data in one call
        both = gae.seed_metrics("long_noisy", 0, (1.0, 0.0))
        self.assertEqual(both[0.0], gae.seed_metrics("long_noisy", 0, (0.0,))[0.0])

    def test_declared_regimes_printed_as_they_came(self):
        out = (ROOT / GAE_EXP).read_text()
        for s in ("paired B-A grad_var: -6.7764+-0.6108: clear gap", "paired B-A grad_var: 0.0000+-0.0000: tie: identical on every seed",
                  "paired C-B grad_mse: 18.1442+-3.3853: clear gap", "paired C-A grad_mse: 18.2344+-4.5531: clear gap",
                  "paired B-A grad_mse: 0.0902+-3.7467: near-tie", "(paired X-C grad_mse): 0.2929+-0.5736: near-tie"):
            self.assertIn(s, out)


class ProcessLabels(unittest.TestCase):
    def test_no_process_labels(self):
        for rel in (AM_REL, AM_EXP, GAE_REL, GAE_EXP):
            self.assertIsNone(re.search(PROCESS, (ROOT / rel).read_text()), rel)


if __name__ == "__main__":
    unittest.main()
