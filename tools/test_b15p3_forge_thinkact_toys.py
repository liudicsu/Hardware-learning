#!/usr/bin/env python3
"""Independent contract tests for batch-15 PR3 FORGE-Tree-style and ThinkAct-style toys; stdlib only.

The FORGE toy takes about 16 s to print its tables, so these tests call its functions directly and
leave the full-output comparison to check.sh / check_diagrams; the ThinkAct toy is run end to end.
"""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FG_REL = "examples/month-10/real-time-chunking/forge_tree_mctd_toy.py"
TA_REL = "examples/month-10/real-world-rl/thinkact_visual_latent_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


fg = load("forge_tree_mctd_toy", FG_REL)
ta = load("thinkact_visual_latent_toy", TA_REL)


class Labels(unittest.TestCase):
    """Both toys share one labelling rule; check it on hand-made paired data."""

    def test_order_and_thresholds(self):
        for mod, rel in ((fg, FG_REL), (ta, TA_REL)):
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
        for mod in (fg, ta):
            self.assertEqual(mod.num(-1e-5), "-1.000e-05")
            self.assertEqual(mod.num(0.0), "0.0000")
            self.assertNotEqual(mod.num(-4e-5), "-0.0000")


class ForgeToy(unittest.TestCase):
    def test_scope(self):
        self.assertEqual(fg.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / FG_REL).read_text()
        for s in ("本页未运行", "以论文为准", "Common random numbers", "No integration step", "depth 1"):
            self.assertIn(s, text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
        self.assertEqual(fg.ARMS, ("A_oneshot", "B_tree", "C_random"))
        # every regime that was run stays, including the two where search does not help
        self.assertEqual(tuple(fg.REGIMES), ("single_stage", "long_loose", "long_tight", "low_budget", "noisy_graph"))
        self.assertEqual(fg.REGIMES["low_budget"][2], 1)
        self.assertEqual(fg.BUDGETS, (1, 2, 4, 8, 16))

    def test_edit_touches_only_segment_k(self):
        goals, mu, bias, eps, pool, evals, picks = fg.world(4, 3, 7, "long_tight")
        tokens = fg.decode(mu, bias, eps)
        for k in range(4):
            out, _ = fg.edit(tokens, mu, bias, eps, k, 1.0, 0.6, (1.0, -1.0), pool[k])
            for i, (p, q) in enumerate(zip(tokens, out)):
                if i // fg.M == k:
                    self.assertNotEqual(p, q)
                else:
                    self.assertEqual(p, q)

    def test_prefix_frozen_in_every_arm(self):
        for regime in fg.REGIMES:
            for arm in fg.ARMS:
                for seed in (0, 4):
                    for trial in (0, 1):
                        r = fg.run(arm, regime, seed, trial)
                        self.assertEqual(r["prefix"], 0.0, (arm, regime, seed, trial))
                        if arm == "A_oneshot":
                            self.assertEqual(r["edits"], 0.0)

    def test_unmasked_counterexample(self):
        self.assertEqual(fg.unmasked_edit_check(), (fg.M, 0))

    def test_common_random_numbers(self):
        self.assertEqual(fg.world(4, 2, 3, "long_tight"), fg.world(4, 2, 3, "long_tight"))
        self.assertNotEqual(fg.world(4, 2, 3, "long_tight")[3], fg.world(4, 3, 3, "long_tight")[3])

    def test_one_shot_end_error_variance(self):
        # per-axis variance of the stage-1 end error: M SIGMA^2 + (M BIAS)^2 = 1.28 + 1.44 = 2.72
        self.assertAlmostEqual(fg.M * fg.SIGMA ** 2 + (fg.M * fg.BIAS) ** 2, 2.72, places=9)
        xs = []
        for t in range(500):
            goals, mu, bias, eps, *_ = fg.world(1, 9, t, "variance")
            e = fg.stage_errors(fg.decode(mu, bias, eps), goals)[0]
            xs += [e[0], e[1]]
        var = sum(x * x for x in xs) / len(xs)
        self.assertLess(abs(var - 2.72), 0.35)

    def test_expected_regime_lines(self):
        out = (ROOT / "examples/month-10/expected/forge_tree_mctd_toy.txt").read_text()
        self.assertIn("integrity check: a re-denoise without the segment mask changes 8 of the 8 committed stage-1 tokens; a masked edit of segment 2 changes 0", out)
        self.assertIn("  paired B-A final: 0.1400+-0.0548: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("  paired C-B stage: 0.0363+-0.0284: small but consistent gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("  budget=1: A 0.0000 B 0.0000 C 0.0050; B-A final: 0.0000+-0.0000: tie: identical on every seed", out)
        for line in out.splitlines():
            if line.startswith("  B_tree") or line.startswith("  C_random") or line.startswith("  A_oneshot"):
                self.assertTrue(line.endswith(" 0.0000+-0.0000"), line)  # prefix column


class ThinkActToy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = subprocess.run([sys.executable, str(ROOT / TA_REL)], check=True, capture_output=True, text=True).stdout

    def test_expected_byte_identical(self):
        self.assertEqual(self.out, (ROOT / "examples/month-10/expected/thinkact_visual_latent_toy.txt").read_text())

    def test_scope(self):
        self.assertEqual(ta.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / TA_REL).read_text()
        for s in ("本页未运行", "以论文为准", "Common random numbers", "No integration step", "added after", "first version"):
            self.assertIn(s, text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
        self.assertEqual(ta.ARMS, ("A_direct", "B_latent", "C_scrambled"))
        self.assertEqual(len(ta.REGIMES), 8)
        for name in ("single_step", "multi_stage", "noisy_plan", "drop_sparse"):
            self.assertIn(name, ta.REGIMES)

    def test_plan_rewards_worked_example(self):
        P, Q = (2, 6), (6, 2)
        task = [P, Q, P]
        self.assertEqual(ta.plan_scores(task, task), (0.0, 1.0))
        end, r = ta.plan_scores([Q, P, P], task)
        self.assertEqual(end, 0.0)
        self.assertAlmostEqual(r, 0.375 + 0.5 * (1.0 - math.sqrt(0.5)), places=12)
        self.assertAlmostEqual(r, 0.5214, places=4)
        self.assertAlmostEqual(ta.plan_scores([(3, 6), Q, P], task)[1], 0.93359375, places=12)

    def test_dtw(self):
        a = [(0.0, 0.0), (1.0, 0.0)]
        self.assertEqual(ta.dtw(a, a), 0.0)
        self.assertAlmostEqual(ta.dtw(a, [(0.0, 0.0), (0.0, 0.0), (1.0, 0.0)]), 0.0)
        self.assertAlmostEqual(ta.dtw([(0.0, 0.0)], [(3.0, 4.0)]), 5.0)

    def test_shared_draws_and_single_stage_identity(self):
        self.assertEqual(ta.world("multi_stage", 1, 2), ta.world("multi_stage", 1, 2))
        self.assertEqual(ta.rotate([(1, 1)]), [(1, 1)])
        for seed in ta.SEEDS:
            for t in range(10):
                self.assertEqual(ta.run("B_latent", "single_step", seed, t), ta.run("C_scrambled", "single_step", seed, t))

    def test_block_hides(self):
        hides = ta.world("ambiguous_block", 0, 0)[7]
        for t in range(len(hides)):
            self.assertEqual(hides[t], hides[(t // 8) * 8])

    def test_expected_regime_lines(self):
        self.assertIn("  paired B-A full: 0.0950+-0.0371: small but consistent gap, not a tie (|m| > sd); same sign on all 5 seeds", self.out)
        self.assertIn("  paired B-A full: -0.0250+-0.0306: near-tie / small gap, within seed noise (|m| <= sd); no seed has the opposite sign, 2 of 5 equal", self.out)
        self.assertIn("  paired B-A full: -0.0950+-0.0622: small but consistent gap, not a tie (|m| > sd); no seed has the opposite sign, 1 of 5 equal", self.out)
        self.assertIn("  multi_stage: -0.2000+-0.0901: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", self.out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
