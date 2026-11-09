#!/usr/bin/env python3
"""Independent contract tests for batch-12 PR3 WorldVLA action-mask + X-VLA soft-prompt toys; stdlib only."""
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
WV_REL = "examples/month-9/world-models-overview/worldvla_action_mask_toy.py"
XV_REL = "examples/month-11/cross-embodiment-datasets/xvla_soft_prompt_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


wv = load("worldvla_action_mask_toy", WV_REL)
xv = load("xvla_soft_prompt_toy", XV_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Labels(unittest.TestCase):
    def test_label_rule(self):
        for mod in (wv, xv):
            self.assertEqual(mod.label([0.0] * 5, 1.0, 1.0), "tie: identical on every seed")
            self.assertTrue(mod.label([0.1, -0.1, 0.1, -0.1, 0.0], 1.0, 1.0).startswith("near-tie / small gap"))
            self.assertEqual(mod.label([0.10, 0.11, 0.09, 0.10, 0.10], 1.0, 1.0), "small but consistent gap, not a tie")
            self.assertEqual(mod.label([0.50, 0.51, 0.49, 0.50, 0.50], 1.0, 1.0), "clear gap, not a tie")
            # the 20 % rule never decides consistency: a huge but noisy gap is still a near-tie
            self.assertTrue(mod.label([3.0, -1.0, 3.0, -1.0, 0.0], 1.0, 1.0).startswith("near-tie"))

    def test_fmt_never_signed_zero(self):
        for mod in (wv, xv):
            self.assertEqual(mod.fmt(0.0), "0.0000")
            self.assertNotEqual(mod.fmt(-1e-6), "-0.0000")
            self.assertIn("e-", mod.fmt(-1e-6))

    def test_outputs_have_no_signed_zero_and_match_expected(self):
        for rel, exp in ((WV_REL, "examples/month-9/expected/worldvla_action_mask_toy.txt"),
                         (XV_REL, "examples/month-11/expected/xvla_soft_prompt_toy.txt")):
            out = run(rel)
            self.assertEqual(out, (ROOT / exp).read_text())
            self.assertNotRegex(out, r"(?<![+\d])-0\.0+(?![0-9])")
            self.assertNotRegex(out, r"exact tie|ties exactly")
            self.assertIn("本页未运行", out)
            self.assertIn("以论文为准", out)
            # every pair line carries exactly one label and labels agree with the tie definition
            for line in out.splitlines():
                if " paired " in line:
                    m = re.search(r" (-?[0-9.e-]+)\+-([0-9.]+): (.*)$", line)
                    self.assertIsNotNone(m, line)
                    if m.group(3).startswith("tie"):
                        self.assertEqual(float(m.group(1)), 0.0)
                        self.assertEqual(float(m.group(2)), 0.0)


class WorldVLA(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(wv.SEEDS, (0, 1, 2, 3, 4))
        self.assertEqual((wv.N_TRAIN, wv.N_TEST, wv.BINS, wv.TOL), (40, 200, 256, 0.5))
        self.assertEqual((wv.SIGMA_DEMO, wv.SIGMA_DEC), (0.10, 0.15))
        self.assertEqual([r[1] for r in wv.REGIMES], [1, 5, 10, 10])
        self.assertEqual(wv.H_MAX, 10)

    def test_ridge_matches_closed_form(self):
        rng = random.Random(3)
        rows = [[rng.gauss(0, 1)] for _ in range(50)]
        ys = [2.5 * r[0] + rng.gauss(0, 0.1) for r in rows]
        sxx = sum(r[0] ** 2 for r in rows)
        sxy = sum(r[0] * y for r, y in zip(rows, ys))
        self.assertAlmostEqual(wv.ridge(rows, ys)[0], sxy / (sxx + wv.LAM * 50), places=12)

    def test_crn_across_regimes(self):
        tr1, te1 = wv.shared_draws(2, 1, 0.3)
        tr10, te10 = wv.shared_draws(2, 10, 0.3)
        trc, tec = wv.shared_draws(2, 10, 0.05)
        for a, b, c in zip(te1, te10, tec):
            self.assertEqual(a[0], b[0])                  # same vision input for H=1 and H=10
            self.assertEqual(a[1][0], b[1][0])            # same first clean action
            self.assertEqual(a[3], b[3])                  # same decode-error draws
            self.assertEqual(b[1], c[1])                  # clean targets identical across sigma_obs
            self.assertEqual(b[2], c[2])                  # same demo noise
        # x_noisy - x_clean = (0.3 - 0.05) z, and the per-scene z is shared
        for b, c in zip(tr10, trc):
            s = [xc - 0.05 * (xn - xc) / 0.25 for xn, xc in zip(b[0], c[0])]
            for xn, si in zip(b[0], s):
                self.assertAlmostEqual(xn, si + 0.3 * (xn - si) / 0.3, places=12)

    def test_tokenizer_bins(self):
        tr, _ = wv.shared_draws(0, 5, 0.3)
        q = wv.tokenizer(tr, 5)
        lo = min(t[2][0] for t in tr)
        hi = max(t[2][0] for t in tr)
        w = (hi - lo) / wv.BINS
        vals = {q[0](lo + (hi - lo) * i / 997) for i in range(998)}
        self.assertLessEqual(len(vals), wv.BINS)
        for v in vals:
            self.assertGreaterEqual(v, lo)
            self.assertLessEqual(v, hi)
            self.assertAlmostEqual(((v - lo) / w) % 1.0, 0.5, places=6)
        self.assertEqual(q[0](lo - 10), lo + 0.5 * w)    # clamped below
        self.assertEqual(q[0](hi + 10), hi - 0.5 * w)    # clamped above

    def test_h1_and_parallel_identities(self):
        for seed in wv.SEEDS:
            tr, te = wv.shared_draws(seed, 1, 0.3)
            a, _ = wv.fit_predict("A_causal", tr, te, 1)
            b, _ = wv.fit_predict("B_mask", tr, te, 1)
            self.assertEqual(a, b)
        tr, te = wv.shared_draws(1, 10, 0.3)
        b, _ = wv.fit_predict("B_mask", tr, te, 10)
        c, _ = wv.fit_predict("C_parallel", tr, te, 10)
        self.assertEqual(b, c)

    def test_previous_action_weight_falls_with_clean_vision(self):
        tr, te = wv.shared_draws(0, 10, 0.3)
        _, beta_noisy = wv.fit_predict("A_causal", tr, te, 10)
        tr, te = wv.shared_draws(0, 10, 0.05)
        _, beta_clean = wv.fit_predict("A_causal", tr, te, 10)
        self.assertEqual(len(beta_noisy), 9)
        self.assertGreater(sum(beta_noisy) / 9, 0.8)
        self.assertLess(sum(beta_clean) / 9, 0.4)

    def test_gap_vanishes_without_decode_error(self):
        """Linear-Gaussian argument in the prose: without decode error and with many demos A ~ B."""
        old = (wv.SIGMA_DEC, wv.N_TRAIN)
        try:
            wv.SIGMA_DEC, wv.N_TRAIN = 0.0, 1500
            tr, te = wv.shared_draws(0, 10, 0.3)
            ra = wv.metrics(wv.fit_predict("A_causal", tr, te, 10)[0], te, 10)[0]
            rb = wv.metrics(wv.fit_predict("B_mask", tr, te, 10)[0], te, 10)[0]
            self.assertLess(abs(ra - rb), 0.005)
        finally:
            wv.SIGMA_DEC, wv.N_TRAIN = old


class XVLA(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(xv.SEEDS, (0, 1, 2, 3, 4))
        self.assertEqual((xv.D, xv.K, xv.N_NEW, xv.N_TEST), (6, 2, 4, 100))
        self.assertEqual([r[0] for r in xv.REGIMES], ["single_embodiment", "shared_low_rank", "unrelated_full_rank"])

    def test_one_hot_prompt_is_a_separate_head(self):
        rng = random.Random(5)
        b = [[[rng.gauss(0, 1) for _ in range(xv.D)] for _ in range(2)] for _ in range(xv.K)]
        for j in range(xv.K):
            p = [1.0 if i == j else 0.0 for i in range(xv.K)]
            self.assertEqual(xv.prompt_map(p, b), b[j])

    def test_ridge_prior_pull(self):
        rng = random.Random(1)
        rows = [[rng.gauss(0, 1) for _ in range(3)] for _ in range(4)]
        ys = [rng.gauss(0, 1) for _ in range(4)]
        w = xv.ridge(rows, ys, prior=[1.0, -2.0, 3.0], lam=1e9)
        for a, b in zip(w, [1.0, -2.0, 3.0]):
            self.assertAlmostEqual(a, b, places=6)

    def test_single_embodiment_pooled_equals_head(self):
        for seed in xv.SEEDS:
            maps, train, _, _, _ = xv.shared_draws(seed, 1, 2, 24)
            self.assertEqual(xv.fit_pooled(train), xv.fit_head(train[0][0], train[0][1]))

    def test_crn_deterministic(self):
        a = xv.shared_draws(3, 6, 2, 8)
        b = xv.shared_draws(3, 6, 2, 8)
        self.assertEqual(a, b)
        _, _, _, _, tx = xv.shared_draws(3, 6, 6, 30)
        self.assertEqual(len(tx), xv.N_TEST)

    def test_soft_prompt_recovers_low_rank_without_noise(self):
        old = xv.SIGMA
        try:
            xv.SIGMA = 0.0
            maps, train, _, _, test_x = xv.shared_draws(0, 6, 2, 8)
            prompts, b = xv.fit_soft(train, 0)
            for p, w in zip(prompts, maps):
                truth = [xv.apply(w, x) for x in test_x]
                self.assertLess(xv.rmse(xv.prompt_map(p, b), test_x, truth), 0.01)  # ridge shrinkage only
        finally:
            xv.SIGMA = old

    def test_unrelated_soft_prompt_cannot_fit(self):
        for seed in xv.SEEDS:
            seen, _ = xv.run(seed, 6, 6, 30)
            self.assertGreater(seen["C_soft_prompt"], 5 * seen["B_hard_id"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
