#!/usr/bin/env python3
"""Independent contract tests for batch-14 PR3 HybridVLA ensemble + CoT-VLA subgoal toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HY_REL = "examples/month-6/act-diffusion/hybridvla_action_ensemble_toy.py"
CO_REL = "examples/month-6/vla-models/cot_vla_subgoal_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


hy = load("hybridvla_action_ensemble_toy", HY_REL)
co = load("cot_vla_subgoal_toy", CO_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Labels(unittest.TestCase):
    """Both toys share one labelling rule; check it on hand-made paired data."""

    def test_order_and_thresholds(self):
        for mod, rel in ((hy, HY_REL), (co, CO_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1.0 + 1e-12, 1.0, 1.0 - 1e-12, 1.0, 1.0], [1.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertNotIn("seeds", v)  # no sign count on a numerically-zero line
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("same sign on all 5 seeds", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("1 of 5 seeds has the opposite sign", mod.verdict([5.0, 5.1, 4.9, 5.2, 0.5], [1.0] * 5))
            self.assertIn("small but consistent", mod.verdict([10.5, 10.6, 10.4, 10.5, 10.5], [10.0] * 5))
            src = (ROOT / rel).read_text()
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))

    def test_no_signed_zero(self):
        for mod in (hy, co):
            self.assertEqual(mod.num(-1e-5), "-1.000e-05")
            self.assertEqual(mod.num(0.0), "0.0000")
            self.assertNotEqual(mod.num(-4e-5), "-0.0000")
        for rel in (HY_REL, CO_REL):
            self.assertNotRegex(run(rel), r"(?<![\d.e+])-0\.0+(?![\d.e])")


class NoIntegrationStep(unittest.TestCase):
    """Neither toy steps anything in continuous time, so no step-size criterion applies."""

    def test_no_time_step_constant(self):
        for rel in (HY_REL, CO_REL):
            text = (ROOT / rel).read_text()
            self.assertNotRegex(text, r"(?m)^(DT|H|dt|TS)\s*=")
            self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
            self.assertIn("本页未运行", text)
            self.assertIn("Common random numbers", text)
        self.assertIn("no time step", (ROOT / HY_REL).read_text())
        self.assertIn("no time-step integration", (ROOT / CO_REL).read_text())

    def test_cot_moves_are_integer_cells(self):
        for regime in co.REGIMES:
            d = co.shared_draws(regime, 0)
            for states, acts in d["own"] + d["others"]:
                self.assertTrue(all(a in (-1, 0, 1) for a in acts))
                self.assertTrue(all(isinstance(c, int) and 0 <= c < co.W for c, _ in states))


class Hybrid(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(HY_REL)

    def test_expected_bytes(self):
        self.assertEqual(self.out, (ROOT / "examples/month-6/expected/hybridvla_action_ensemble_toy.txt").read_text())
        self.assertEqual(self.out, run(HY_REL))

    def test_scope(self):
        self.assertEqual(hy.SEEDS, (0, 1, 2, 3, 4))
        self.assertEqual(hy.THETA, 0.96)
        self.assertAlmostEqual(math.log(0.5 / (1 - hy.THETA)) / hy.KAPPA, 2.1048, places=4)

    def test_common_random_numbers(self):
        self.assertEqual(hy.shared_draws("mixed", 2), hy.shared_draws("mixed", 2))
        self.assertNotEqual(hy.shared_draws("mixed", 2), hy.shared_draws("mixed", 3))

    def test_semantic_tie_is_structural(self):
        """On semantic steps C succeeds exactly when B does: averaging cannot fix a wrong diffusion mode."""
        for seed in hy.SEEDS:
            for ep in hy.shared_draws("semantic", seed):
                a_ar, a_d, conf = hy.heads(ep)
                a_c = 0.5 * (a_ar + a_d) if conf > hy.THETA else a_d
                ok_b = abs(a_d - ep["target"]) < hy.TOL_SEMANTIC
                ok_c = abs(a_c - ep["target"]) < hy.TOL_SEMANTIC
                self.assertEqual(ok_b, ok_c)

    def test_worked_example(self):
        b = sum(hy.run("precision", s, "B_diffusion_only")["succ"] for s in hy.SEEDS) / 5
        self.assertLess(abs(b - 100 * math.erf(1.2 / math.sqrt(2))), 3.0)  # P(|Z| < 1.2) = 0.770
        g = sum(hy.run("precision", s, "C_hybrid_ensemble")["gate"] for s in hy.SEEDS) / 5
        p = 0.5 * (1 + math.erf((3.0 - 2.1048) / math.sqrt(2)))
        self.assertLess(abs(g - 100 * p), 3.0)

    def test_regime_lines(self):
        for line in ("paired C-A succ: 21.8500+-1.3647: clear gap", "paired C-B succ: 0.0000+-0.0000: tie: identical on every seed",
                     "paired C-A succ: -26.8500+-2.5593: clear gap", "paired C-A succ: -2.9000+-1.5268: small but consistent gap"):
            self.assertIn(line, self.out)


class CoT(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(CO_REL)

    def test_expected_bytes(self):
        self.assertEqual(self.out, (ROOT / "examples/month-6/expected/cot_vla_subgoal_toy.txt").read_text())
        self.assertEqual(self.out, run(CO_REL))

    def test_scope(self):
        self.assertEqual(co.SEEDS, (0, 1, 2, 3, 4))
        self.assertEqual((co.TOK_ACTION, co.TOK_IMAGE), (7, 256))

    def test_common_random_numbers(self):
        self.assertEqual(co.shared_draws("multi_stage_video", 1), co.shared_draws("multi_stage_video", 1))
        self.assertNotEqual(co.shared_draws("multi_stage_video", 1)["starts"], co.shared_draws("multi_stage_video", 2)["starts"])

    def test_subgoal_never_skips_a_stage(self):
        for regime in co.REGIMES:
            _, _, sub, _ = co.fit(co.shared_draws(regime, 0))
            for (cell, stage), (gcell, gstage) in sub.items():
                self.assertIn(gstage - stage, (0, 1))

    def test_token_accounting(self):
        r = co.run("single_reach", 0, "A_direct")
        self.assertEqual(round(r["tok"] * co.TESTS) % (co.TOK_ACTION * co.M), 0)  # A pays 28 tokens per chunk, no images

    def test_stale_with_refresh_every_chunk_is_b(self):
        old = co.STALE
        try:
            co.STALE = 1
            for regime in co.REGIMES:
                self.assertEqual(co.run(regime, 0, "C_cot_stale"), co.run(regime, 0, "B_cot"))
        finally:
            co.STALE = old

    def test_stale_alt_block(self):
        """STALE = 2 was picked after seeing STALE = 3; both are printed and both are checked here."""
        self.assertEqual((co.STALE, co.STALE_ALT), (2, 3))
        for regime in co.REGIMES:
            for seed in co.SEEDS:
                self.assertEqual(co.run(regime, seed, "C_cot_stale"), co.run(regime, seed, "C_cot_stale", co.STALE))
        for regime in ("multi_stage_video", "multi_stage_no_video", "multi_stage_action_rich"):
            for seed in co.SEEDS:
                r = co.run(regime, seed, "C_cot_stale", co.STALE_ALT)
                self.assertEqual((r["succ"], r["steps"]), (0.0, float(co.T_MAX)))  # every episode runs out the budget
        c3 = [co.run("single_reach", s, "C_cot_stale", co.STALE_ALT)["succ"] for s in co.SEEDS]
        b = [co.run("single_reach", s, "B_cot")["succ"] for s in co.SEEDS]
        c2 = [co.run("single_reach", s, "C_cot_stale")["succ"] for s in co.SEEDS]
        self.assertEqual(c2, b)                                  # STALE = 2: tie on every seed
        self.assertTrue(all(x <= y for x, y in zip(c3, b)) and c3 != b)  # STALE = 3: C loses, never wins
        blk = self.out.split("stale-refresh sensitivity")[1]
        for line in ("paired C@3-B succ: -100.0000+-0.0000: clear gap", "paired C@3-B succ: -37.5000+-25.3106: clear gap",
                     "paired C@3-C@2 succ: -4.0000+-5.7554: near-tie", "paired C@3-B succ: -7.5000+-7.0711: small but consistent gap",
                     "no seed has the opposite sign, 2 of 5 equal"):
            self.assertIn(line, blk)
        self.assertNotIn("tie: identical on every seed", blk)

    def test_regime_lines(self):
        for line in ("paired B-A succ: 62.0000+-44.8400: clear gap", "paired B-A succ: 2.5000+-3.5355: near-tie",
                     "paired B-A tok: 3610.0800+-111.2090: clear gap", "paired C-B succ: 0.0000+-0.0000: tie: identical on every seed"):
            self.assertIn(line, self.out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
