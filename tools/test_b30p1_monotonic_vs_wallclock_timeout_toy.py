#!/usr/bin/env python3
"""Independent contract tests for the monotonic vs wall-clock timeout toy; stdlib only."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = "examples/month-1/python-terminal/monotonic_vs_wallclock_timeout_toy.py"
EXP = "examples/month-1/expected/monotonic_vs_wallclock_timeout_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


toy = load("monotonic_vs_wallclock_timeout_toy", REL)


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

    def test_does_not_touch_machine_clock(self):
        src = (ROOT / REL).read_text()
        self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+time\b")
        self.assertNotIn("time.clock_settime", src)
        self.assertNotRegex(src, r"(?m)^\s*time\.(time|monotonic)\s*\(")

    def test_expected_byte_identical_and_no_process_labels(self):
        out = run(REL)
        self.assertEqual(out, run(REL))
        self.assertEqual(out, (ROOT / EXP).read_text())
        for text in (out, (ROOT / REL).read_text()):
            self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b30p1"):
            self.assertRegex(bad, PROCESS)


class TimeoutContract(unittest.TestCase):
    def test_declared_setup(self):
        self.assertAlmostEqual(toy.TIMEOUT_S, 1.0000)
        self.assertAlmostEqual(toy.DT_S, 0.1250)
        self.assertAlmostEqual(toy.JUMP_AT_S, 0.2500)
        self.assertAlmostEqual(toy.BACKWARD_S, -2.0000)
        self.assertAlmostEqual(toy.FORWARD_S, 2.0000)
        self.assertAlmostEqual(toy.FORWARD_ALT_S, 0.5000)
        self.assertAlmostEqual(toy.WALL_ORIGIN_S, 1700000000.0000)
        self.assertAlmostEqual(toy.MONO_ORIGIN_S, 1000.0000)
        self.assertAlmostEqual(toy.MAX_WAIT_S, 5.0000)
        self.assertEqual(toy.ARMS, ("A_wall", "B_mono", "C_stamp"))
        self.assertEqual(
            toy.REGIMES,
            ("no_jump", "backward_jump", "forward_jump", "stamp_confusion"),
        )

    def test_closed_form_matches_step(self):
        self.assertEqual(toy.closed_form_wall(0.0), 1.0)
        self.assertEqual(toy.closed_form_wall(toy.BACKWARD_S), 3.0)
        self.assertEqual(toy.closed_form_wall(toy.FORWARD_S), 0.25)
        self.assertEqual(toy.closed_form_wall(toy.FORWARD_ALT_S), 0.5)
        self.assertEqual(toy.fire_time("A_wall", 0.0), toy.closed_form_wall(0.0))
        self.assertEqual(toy.fire_time("A_wall", toy.BACKWARD_S), toy.closed_form_wall(toy.BACKWARD_S))
        self.assertEqual(toy.fire_time("A_wall", toy.FORWARD_S), toy.closed_form_wall(toy.FORWARD_S))
        self.assertEqual(toy.fire_time("B_mono", toy.BACKWARD_S), 1.0)
        self.assertEqual(toy.fire_time("B_mono", toy.FORWARD_S), 1.0)
        self.assertEqual(toy.fire_time("C_stamp", 0.0), 5.0)

    def test_predeclared_regimes(self):
        out = (ROOT / EXP).read_text()
        self.assertIn("clear_frac=0.2000", out)
        self.assertIn("hand_calc work_plan 30+25+50+40+35=180", out)
        self.assertIn(
            "paired A-B fire_s: 0.0000+-0.0000: tie: identical on every seed",
            out,
        )
        self.assertIn(
            "paired A-B fire_s: 2.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn(
            "paired A-B fire_s: -0.7500+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn(
            "paired C-B fire_s: 4.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn("alternative forward_jump 0.5000s (same jump_at, not adopted)", out)
        self.assertIn("本页未运行", out)
        self.assertIn("以文档为准", out)
        self.assertIn("residual_step-closed_A=0.000e+00s", out)

    def test_hook_before_exit(self):
        hook = (ROOT / "examples/month-1/check.sh").read_text()
        self.assertIn("monotonic_vs_wallclock_timeout_toy.txt", hook)
        self.assertLess(hook.index("ydelta_network_reduction_toy"), hook.index("monotonic_vs_wallclock_timeout_toy"))
        self.assertLess(hook.index("monotonic_vs_wallclock_timeout_toy"), hook.index("exit $fail"))
        self.assertGreater(hook.index("exit $fail"), hook.rindex("monotonic_vs_wallclock_timeout_toy"))
        # new hook is the last hook, immediately before exit
        after_new = hook[hook.rindex("monotonic_vs_wallclock_timeout_toy"):]
        self.assertIn("exit $fail", after_new)
        self.assertNotRegex(after_new.split("exit $fail")[0], r"python3 \"\$M1/")


if __name__ == "__main__":
    unittest.main()
