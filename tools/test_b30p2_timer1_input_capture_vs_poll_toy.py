#!/usr/bin/env python3
"""Independent contract tests for the Timer1 input-capture vs poll toy; stdlib only."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = "examples/month-2/timing-interrupts/timer1_input_capture_vs_poll_toy.py"
EXP = "examples/month-2/expected/timer1_input_capture_vs_poll_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


toy = load("timer1_input_capture_vs_poll_toy", REL)


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

    def test_does_not_flash_or_step_hardware(self):
        src = (ROOT / REL).read_text()
        self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(serial|pyvisa|usb|periphery|gpiozero|spidev)\b")
        self.assertNotIn("clock_settime", src)

    def test_expected_byte_identical_and_no_process_labels(self):
        out = run(REL)
        self.assertEqual(out, run(REL))
        self.assertEqual(out, (ROOT / EXP).read_text())
        for text in (out, (ROOT / REL).read_text()):
            self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b30p2"):
            self.assertRegex(bad, PROCESS)


class CaptureContract(unittest.TestCase):
    def test_declared_setup(self):
        self.assertEqual(toy.F_CLK_HZ, 16_000_000)
        self.assertEqual(toy.N_PRESCALER, 8)
        self.assertFalse(toy.ICNC_ON)
        self.assertEqual(toy.ICES_RISING, 1)
        self.assertEqual(toy.ICES_FALLING, 0)
        self.assertEqual(toy.POLL_PERIOD_TICKS, 20)
        self.assertEqual(toy.POLL_PERIOD_ALT_TICKS, 1)
        self.assertEqual(toy.SPARSE_RISES, (200, 1000, 1800))
        self.assertEqual(toy.SPARSE_WIDTH_TICKS, 40)
        self.assertEqual(toy.SHORT_N_PULSES, 16)
        self.assertEqual(toy.SHORT_PERIOD_TICKS, 8)
        self.assertEqual(toy.SHORT_WIDTH_TICKS, 3)
        self.assertEqual(toy.OVERWRITE_RISES, (100, 108))
        self.assertEqual(toy.LATE_READ_TICKS, 120)
        self.assertEqual(toy.ARMS, ("A_poll", "B_icr", "C_ices"))
        self.assertEqual(
            toy.REGIMES,
            ("sparse_edges", "short_pulses", "icr_overwrite", "wrong_ices"),
        )

    def test_closed_form_matches_step(self):
        sparse = toy.run_sparse(toy.POLL_PERIOD_TICKS)
        short = toy.run_short(toy.POLL_PERIOD_TICKS)
        overw = toy.run_overwrite()
        self.assertEqual(sparse["A_poll"], [200, 1000, 1800])
        self.assertEqual(sparse["B_icr"], [200, 1000, 1800])
        self.assertEqual(sparse["C_ices"], [240, 1040, 1840])
        self.assertEqual(short["A_poll"], [])
        self.assertEqual(len(short["B_icr"]), 16)
        self.assertEqual(short["B_icr"][0], 1)
        self.assertEqual(overw["B_icr_late"], [108])
        self.assertEqual(overw["keep_first"], 100)
        self.assertEqual(overw["A_poll"], [100])

    def test_predeclared_regimes(self):
        out = (ROOT / EXP).read_text()
        self.assertIn("clear_frac=0.2000", out)
        self.assertIn("hand_calc work_plan 30+25+50+40+35=180", out)
        self.assertIn("pre-declared C lose mode: wrong ICES only", out)
        self.assertIn(
            "paired A-B period_ticks: 0.0000+-0.0000: tie: identical on every seed",
            out,
        )
        self.assertIn(
            "paired A-B first_ticks: 0.0000+-0.0000: tie: identical on every seed",
            out,
        )
        self.assertIn(
            "paired A-B n_capt: -16.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn("B_icr late_read ICR_ticks 108.0000+-0.0000", out)
        self.assertIn("keep_first ICR_ticks 100.0000+-0.0000", out)
        self.assertIn(
            "paired C-B first_ticks: 40.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn("alternative short_pulses poll_ticks=1 (not adopted)", out)
        self.assertIn("本页未运行", out)
        self.assertIn("以文档为准", out)
        self.assertIn("residual_step-closed_A_first=0.000e+00ticks", out)

    def test_hook_before_exit(self):
        hook = (ROOT / "examples/month-2/check.sh").read_text()
        self.assertIn("timer1_input_capture_vs_poll_toy.txt", hook)
        self.assertLess(hook.index("rmt_symbol_vs_bitbang_toy"), hook.index("timer1_input_capture_vs_poll_toy"))
        self.assertLess(hook.index("timer1_input_capture_vs_poll_toy"), hook.index("exit $fail"))
        self.assertGreater(hook.index("exit $fail"), hook.rindex("timer1_input_capture_vs_poll_toy"))
        after_new = hook[hook.rindex("timer1_input_capture_vs_poll_toy"):]
        self.assertIn("exit $fail", after_new)
        self.assertNotRegex(after_new.split("exit $fail")[0], r"python3 \"\$M2/")


if __name__ == "__main__":
    unittest.main()
