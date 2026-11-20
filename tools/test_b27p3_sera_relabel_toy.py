#!/usr/bin/env python3
"""Independent contract tests for the SeRA autonomous-relabel toy; stdlib only."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = "examples/month-10/intervention-logging/sera_autonomous_relabel_toy.py"
EXP = "examples/month-10/expected/sera_autonomous_relabel_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


toy = load("sera_autonomous_relabel_toy", REL)


def run(rel: str) -> str:
    return subprocess.run(
        [sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True
    ).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        self.assertEqual(toy.NUM_ZERO, 1e-9)
        self.assertEqual(toy.SEEDS, (0, 1, 2, 3, 4))
        self.assertAlmostEqual(toy.SMALL_FRAC, 0.2000)
        self.assertAlmostEqual(toy.AGREE_ABS, 0.1500)
        self.assertAlmostEqual(toy.RADIUS_RATIO, 1.0000)
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
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b27p3"):
            self.assertRegex(bad, PROCESS)


class Sera(unittest.TestCase):
    def test_declared_setup_and_hand_calc(self):
        self.assertEqual(toy.N_TRAJ, 8)
        self.assertEqual(toy.CHUNK_LEN, 4)
        self.assertEqual(toy.HUMAN_STEPS, (0,))
        self.assertEqual(toy.N_CHECKPOINTS, 2)
        self.assertEqual(toy.MIN_CHECKPOINTS, 2)
        self.assertAlmostEqual(toy.a_star(0), 1.0000)
        self.assertAlmostEqual(toy.a_star(1), 1.2500)
        self.assertAlmostEqual(toy.a_star(2), 1.5000)
        self.assertAlmostEqual(toy.a_star(3), 1.7500)
        self.assertAlmostEqual(toy.desired_radius(0.2000, -2.0000, 1.0000), 2.2000)
        self.assertTrue(toy.in_desired_set(1.2500, 0.2000, -2.0000, 1.0000))
        self.assertTrue(toy.in_desired_set(1.0000, 0.2000, -2.0000, 1.0000))
        self.assertFalse(toy.agreement_ok(2.7500, -0.2500))
        self.assertTrue(toy.agreement_ok(1.5000, 1.5000))

    def test_crn_shared_stream_across_arms(self):
        frames = toy.build_stream("wrong_auton_agree")
        self.assertEqual(len(frames), toy.N_TRAJ * toy.CHUNK_LEN)
        for arm in toy.ARMS:
            policy, _ = toy.fit_arm(frames, arm, toy.RADIUS_RATIO)
            self.assertEqual(set(policy), set(toy.STEPS))
        # Same stream object is reused; checkpoint queries do not depend on the arm.
        f = [x for x in frames if x["traj"] == 0 and x["step"] == 1][0]
        self.assertAlmostEqual(f["p1"], f["a_star"])
        self.assertAlmostEqual(f["a_r"], -1.0000)
        self.assertTrue(f["accepted"])

    def test_prefix_rejection(self):
        frames = toy.build_stream("checkpoints_disagree")
        one = [f for f in frames if f["traj"] == 0]
        self.assertTrue(one[0]["human"])
        self.assertFalse(one[1]["accepted"])
        self.assertFalse(one[1]["rejected_prefix"])
        self.assertTrue(one[2]["would_agree"])
        self.assertTrue(one[2]["rejected_prefix"])
        self.assertTrue(one[3]["rejected_prefix"])
        n_pref = sum(1 for f in frames if f["rejected_prefix"])
        self.assertEqual(n_pref, 16)

    def test_declared_regimes_hold(self):
        # already_good: C and B exact-tie on task_mse
        rows, _ = toy.run_regime("already_good")
        self.assertEqual(rows["C"]["task_mse"], rows["B"]["task_mse"])
        self.assertTrue(all(x == 0.0 for x in rows["C"]["task_mse"]))
        # wrong_auton_agree: C better than B (lower task_mse), higher robot_mse
        rows, _ = toy.run_regime("wrong_auton_agree")
        self.assertTrue(all(c < b for c, b in zip(rows["C"]["task_mse"], rows["B"]["task_mse"])))
        self.assertTrue(all(c > b for c, b in zip(rows["C"]["robot_mse"], rows["B"]["robot_mse"])))
        # checkpoints_disagree: C equals A; D worse than C
        rows, _ = toy.run_regime("checkpoints_disagree")
        self.assertEqual(rows["C"]["task_mse"], rows["A"]["task_mse"])
        self.assertTrue(all(d > c for d, c in zip(rows["D"]["task_mse"], rows["C"]["task_mse"])))
        # exact_target_lose: D worse than C
        rows, _ = toy.run_regime("exact_target_lose")
        self.assertTrue(all(d > c for d, c in zip(rows["D"]["task_mse"], rows["C"]["task_mse"])))


if __name__ == "__main__":
    unittest.main()
