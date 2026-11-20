#!/usr/bin/env python3
"""Independent contract tests for the current-mode d/q feedforward toy; stdlib only."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = "examples/month-11/foc-actuator-lab/foc_dq_decoupling_toy.py"
EXP = "examples/month-11/expected/foc_dq_decoupling_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


toy = load("foc_dq_decoupling_toy", REL)


def run(rel: str) -> str:
    return subprocess.run(
        [sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True
    ).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        self.assertEqual(toy.NUM_ZERO, 1e-9)
        self.assertEqual(toy.SEEDS, (0, 1, 2, 3, 4))
        self.assertAlmostEqual(toy.SMALL_FRAC, 0.2000)
        self.assertIn("tie: identical on every seed", toy.verdict([1.0] * 5, [1.0] * 5))
        v = toy.verdict([1e-16, -2e-16, 3e-16, 0.0, 1e-16], [0.0] * 5)
        self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
        self.assertIn("near-tie", toy.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
        self.assertIn("clear gap", toy.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
        self.assertIn("small but consistent", toy.verdict([10.5, 10.6, 10.4, 10.5, 10.5], [10.0] * 5))
        self.assertIn("1 of 5 seeds has the opposite sign", toy.verdict([5.0, 5.0, 5.0, 5.0, -0.5], [0.0] * 5))
        self.assertEqual(toy.num(0.12345), "0.1235")
        self.assertEqual(toy.num(-0.0), "0.0000")
        src = (ROOT / REL).read_text()
        for marker in ("Common random numbers", "本页未运行", "ROUND_HALF_UP", "written before the first official run"):
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
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b28p2"):
            self.assertRegex(bad, PROCESS)


class DecouplingContract(unittest.TestCase):
    def test_declared_setup(self):
        self.assertAlmostEqual(toy.R, 0.8000)
        self.assertAlmostEqual(toy.L_D, 0.0020)
        self.assertAlmostEqual(toy.L_Q, 0.0024)
        self.assertEqual(toy.N_PP, 7)
        self.assertAlmostEqual(toy.K_E, 0.0400)
        self.assertAlmostEqual(toy.DT, 1e-4)
        self.assertAlmostEqual(toy.KP_D, 5.0000)
        self.assertAlmostEqual(toy.KI_D, 1000.0000)
        self.assertAlmostEqual(toy.ID_REF, 0.0000)
        self.assertAlmostEqual(toy.LOW_V, 8.0000)
        self.assertAlmostEqual(toy.HIGH_V, 220.0000)

    def test_low_speed_near_tie_and_high_speed_clear(self):
        out = (ROOT / EXP).read_text()
        self.assertIn(
            "paired B-A id_rmse: -1.355e-7+-3.902e-7: near-tie / small gap, within seed noise (|m| <= sd); 1 of 5 seeds has the opposite sign",
            out,
        )
        self.assertIn(
            "paired B-A id_rmse: -0.2667+-0.0008: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn(
            "paired C-B id_rmse: 0.5639+-0.0009: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn("adopted=B not_adopted=ALT_VOLTAGE_MODE_LAG", out)
        self.assertIn("(not adopted)", out)

    def test_crn_shared_noise_and_no_mechanics(self):
        n = int(round(toy.LOW_TOTAL / toy.DT))
        a = toy.noise_stream(0, n)
        b = toy.noise_stream(0, n)
        self.assertEqual(a, b)
        c = toy.noise_stream(1, n)
        self.assertNotEqual(a, c)
        src = (ROOT / REL).read_text()
        self.assertIn("v prescribed, no rotor mechanics", src)
        self.assertIn("anti_windup=omitted", src)

    def test_hook_before_exit(self):
        hook = (ROOT / "examples/month-11/check.sh").read_text()
        self.assertIn("foc_dq_decoupling_toy.txt", hook)
        self.assertLess(hook.index("foc_dq_decoupling_toy"), hook.index("exit $fail"))
        self.assertLess(hook.index("foc_current_loop_toy.txt"), hook.index("foc_dq_decoupling_toy"))


if __name__ == "__main__":
    unittest.main()
