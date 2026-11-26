#!/usr/bin/env python3
"""Independent contract tests for the Type A mean-uncertainty toy; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = "examples/month-1/bench-multimeter/type_a_mean_uncertainty_toy.py"
EXP = "examples/month-1/expected/type_a_mean_uncertainty_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


toy = load("type_a_mean_uncertainty_toy", REL)


def run(rel: str) -> str:
    return subprocess.run(
        [sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True
    ).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        self.assertEqual(toy.NUM_ZERO, 1e-9)
        self.assertEqual(toy.SEEDS, (0, 1, 2, 3, 4))
        self.assertAlmostEqual(toy.CLEAR_FRAC, 0.2000)
        self.assertIn("tie: identical on every seed", toy.verdict([1.0] * 5, [1.0] * 5))
        v = toy.verdict([1e-16, -2e-16, 3e-16, 0.0, 1e-16], [0.0] * 5)
        self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
        self.assertIn("near-tie", toy.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
        self.assertIn("clear gap", toy.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
        self.assertIn("small but consistent", toy.verdict([10.5, 10.6, 10.4, 10.5, 10.5], [10.0] * 5))
        self.assertIn("1 of 5 seeds has the opposite sign", toy.verdict([5.0, 5.0, 5.0, 5.0, -0.5], [0.0] * 5))
        self.assertEqual(toy.num(0.12345), "0.1235")
        self.assertEqual(toy.num(0.0), "0.0000")
        src = (ROOT / REL).read_text()
        for marker in ("Common random numbers", "本页未运行", "declared before the first run"):
            self.assertIn(marker, src)
        self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|rclpy|rclcpp|mujoco)")
        self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+subprocess")
        self.assertNotIn("subprocess.", src)
        self.assertNotIn("Popen", src)
        self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
        self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))

    def test_expected_byte_identical_and_no_process_labels(self):
        out = run(REL)
        self.assertEqual(out, run(REL))
        self.assertEqual(out, (ROOT / EXP).read_text())
        for text in (out, (ROOT / REL).read_text()):
            self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b31p1"):
            self.assertRegex(bad, PROCESS)


class TypeAContract(unittest.TestCase):
    def test_declared_setup(self):
        self.assertAlmostEqual(toy.MU, 5.0000)
        self.assertAlmostEqual(toy.SIGMA, 0.0200)
        self.assertEqual(toy.N, 16)
        self.assertEqual(toy.N_LARGE, 64)
        self.assertEqual(toy.N_ALT, 256)
        self.assertGreaterEqual(toy.N, 2)
        self.assertAlmostEqual(toy.L, 0.0500)
        self.assertAlmostEqual(toy.U_B, toy.L / math.sqrt(3.0))
        self.assertEqual(toy.ARMS, ("A_type_a", "B_type_b", "C_s_as_u_mean"))
        self.assertEqual(len(toy.SEEDS), 5)

    def test_crn_prefixes(self):
        for seed in toy.SEEDS:
            small = toy.draw_series(seed, toy.N)
            large = toy.draw_series(seed, toy.N_LARGE)
            alt = toy.draw_series(seed, toy.N_ALT)
            self.assertEqual(small, large[: toy.N])
            self.assertEqual(large, alt[: toy.N_LARGE])

    def test_eq5_matches_hand_s_over_sqrt_n_and_c_is_s(self):
        for seed in toy.SEEDS:
            for n in (toy.N, toy.N_LARGE, toy.N_ALT):
                xs = toy.draw_series(seed, n)
                a = toy.type_a_eq5(xs)
                hand = toy.hand_s_over_sqrt_n(xs)
                c = toy.sample_s(xs)
                self.assertEqual(a, hand)
                self.assertEqual(c, toy.sample_s(xs))
                self.assertAlmostEqual(c / a, math.sqrt(n))
                # Arm B is not computed from this series
                self.assertEqual(toy.arm_values(xs)["B_type_b"], toy.U_B)

    def test_predeclared_regimes(self):
        out = (ROOT / EXP).read_text()
        self.assertIn("clear_frac=0.2000", out)
        self.assertIn("hand_calc L/sqrt(3)=0.0288675135 V (L=0.0500 V); work_plan 30+25+50+40+35=180", out)
        self.assertIn("Arm C lose mode, declared before the first run: treat the observation sample sd s as if it were s(mean)", out)
        self.assertIn("paired A-hand_s_over_sqrt_n u: 0.0000+-0.0000: tie: identical on every seed", out)
        self.assertIn("hand_calc C/A vs sqrt(16)=4.0000000000: 0.0000+-0.0000: tie: identical on every seed", out)
        self.assertIn("hand_calc C/A vs sqrt(64)=8.0000000000: 0.0000+-0.0000: tie: identical on every seed", out)
        self.assertIn(
            "paired A(n=64)-A(n=16) u: -0.0020+-0.0006: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn("paired B(n=64)-B(n=16) u: 0.0000+-0.0000: tie: identical on every seed", out)
        self.assertIn(
            "paired C-A u: 0.0137+-0.0022: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn("alternative n=256 (same seed family, CRN: first 64 observations shared, not adopted)", out)
        self.assertIn("本页未运行", out)
        self.assertIn("以原文为准", out)
        self.assertNotIn("s/sqrt(n)", out.split("hand_calc eq(5)=s/sqrt(n)", 1)[0])

    def test_hook_before_exit(self):
        hook = (ROOT / "examples/month-1/check.sh").read_text()
        self.assertIn("type_a_mean_uncertainty_toy.txt", hook)
        self.assertLess(hook.index("monotonic_vs_wallclock_timeout_toy"), hook.index("type_a_mean_uncertainty_toy"))
        self.assertLess(hook.index("type_a_mean_uncertainty_toy"), hook.index("exit $fail"))
        self.assertGreater(hook.index("exit $fail"), hook.rindex("type_a_mean_uncertainty_toy"))
        after_new = hook[hook.rindex("type_a_mean_uncertainty_toy") :]
        self.assertIn("exit $fail", after_new)
        self.assertNotRegex(after_new.split("exit $fail")[0], r"python3 \"\$M1/")


if __name__ == "__main__":
    unittest.main()
