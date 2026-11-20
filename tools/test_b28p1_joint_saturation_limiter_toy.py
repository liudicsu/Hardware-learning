#!/usr/bin/env python3
"""Independent contract tests for the JointSaturationLimiter stand-in; stdlib only."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = "examples/month-8/ros2-hardware-interface/joint_saturation_limiter_toy.py"
EXP = "examples/month-8/expected/joint_saturation_limiter_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


toy = load("joint_saturation_limiter_toy", REL)


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
        for marker in ("Common random numbers", "本页未运行", "ROUND_HALF_UP", "written before the first run"):
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
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b28p1"):
            self.assertRegex(bad, PROCESS)


class SaturationContract(unittest.TestCase):
    def test_declared_setup(self):
        self.assertAlmostEqual(toy.DT, 0.1000)
        self.assertAlmostEqual(toy.POS_MIN, -0.5000)
        self.assertAlmostEqual(toy.POS_MAX, 0.5000)
        self.assertAlmostEqual(toy.V_MAX, 1.0000)
        self.assertAlmostEqual(toy.A_MAX, 5.0000)
        self.assertEqual(toy.DOC_POS_MIN, -1.0)
        self.assertEqual(toy.DOC_POS_MAX, 1.0)
        self.assertEqual(toy.DOC_VEL, 1)
        self.assertEqual(toy.DOC_EFFORT, 100)

    def test_far_exact_tie(self):
        far = toy.FAR
        a, b, c = toy.result_for("A", far), toy.result_for("B", far), toy.result_for("C", far)
        self.assertEqual(a["throws"], 0)
        self.assertAlmostEqual(a["v"], 0.3000)
        self.assertAlmostEqual(b["v"], 0.3000)
        self.assertAlmostEqual(c["v"], 0.3000)
        self.assertAlmostEqual(a["pos_violation"], 0.0)
        self.assertAlmostEqual(b["pos_violation"], 0.0)
        self.assertAlmostEqual(c["pos_violation"], 0.0)
        self.assertAlmostEqual(c["a"], 3.0000)

    def test_near_c_keeps_box_b_and_a_lose(self):
        near = toy.NEAR
        a, b, c, alt = (
            toy.result_for("A", near),
            toy.result_for("B", near),
            toy.result_for("C", near),
            toy.result_for("ALT", near),
        )
        self.assertAlmostEqual(a["next_pos"], 0.6100)
        self.assertAlmostEqual(a["pos_violation"], 0.1100)
        self.assertAlmostEqual(b["v"], 1.0000)
        self.assertAlmostEqual(b["next_pos"], 0.5600)
        self.assertAlmostEqual(b["pos_violation"], 0.0600)
        self.assertAlmostEqual(c["v"], 0.4000)
        self.assertAlmostEqual(c["next_pos"], 0.5000)
        self.assertAlmostEqual(c["pos_violation"], 0.0)
        self.assertAlmostEqual(alt["pos_violation"], 0.0600)

    def test_continuous_invents_no_position_box(self):
        cell = toy.CONTINUOUS
        self.assertFalse(cell["has_pos_limits"])
        a, b, c = (
            toy.result_for("A", cell),
            toy.result_for("B", cell),
            toy.result_for("C", cell),
        )
        self.assertIsNone(a["pos_violation"])
        self.assertIsNone(b["pos_violation"])
        self.assertIsNone(c["pos_violation"])
        # A position box at the same numeric pos would have tightened C to 0.4000.
        self.assertAlmostEqual(c["v"], 1.0000)
        self.assertAlmostEqual(b["v"], 1.0000)
        self.assertAlmostEqual(a["vel_box_violation"], 0.5000)

    def test_out_of_bounds_throws_only_on_c(self):
        cell = toy.OUT_OF_BOUNDS
        c = toy.result_for("C", cell)
        self.assertEqual(c["throws"], 1)
        self.assertIn("out of bounds when commanding position", c["message"])
        self.assertEqual(toy.result_for("A", cell)["throws"], 0)
        self.assertEqual(toy.result_for("B", cell)["throws"], 0)
        with self.assertRaises(toy.OutOfBounds):
            toy.apply_C(cell)

    def test_hook_before_exit(self):
        hook = (ROOT / "examples/month-8/check.sh").read_text()
        self.assertIn("joint_saturation_limiter_toy.txt", hook)
        self.assertLess(hook.index("joint_saturation_limiter_toy"), hook.index("exit $fail"))
        self.assertLess(hook.index("can_fault_confinement_toy.txt"), hook.index("joint_saturation_limiter_toy"))


if __name__ == "__main__":
    unittest.main()
