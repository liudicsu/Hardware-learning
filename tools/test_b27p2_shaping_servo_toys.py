#!/usr/bin/env python3
"""Independent contract tests for the potential-based shaping and Servo proximity toys; stdlib only."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H3_REL = "examples/month-7/rl-manipulation-sim/potential_based_shaping_toy.py"
H4_REL = "examples/month-9/moveit-servo/servo_collision_proximity_toy.py"
H3_EXP = "examples/month-7/expected/potential_based_shaping_toy.txt"
H4_EXP = "examples/month-9/expected/servo_collision_proximity_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


h3 = load("potential_based_shaping_toy", H3_REL)
h4 = load("servo_collision_proximity_toy", H4_REL)


def run(rel: str) -> str:
    return subprocess.run(
        [sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True
    ).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        for mod, rel in ((h3, H3_REL), (h4, H4_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertEqual(mod.SEEDS, (0, 1, 2, 3, 4))
            self.assertAlmostEqual(mod.SMALL_FRAC, 0.2000)
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
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|rclpy|rclcpp|mujoco)")
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+subprocess")
            self.assertNotIn("subprocess.", src)
            self.assertNotIn("Popen", src)
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))

    def test_expected_byte_identical_and_no_process_labels(self):
        for rel, exp in ((H3_REL, H3_EXP), (H4_REL, H4_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b27p2"):
            self.assertRegex(bad, PROCESS)


class Shaping(unittest.TestCase):
    def test_declared_identity_and_hand_calc_cycle(self):
        self.assertAlmostEqual(h3.GAMMA, 0.9000)
        self.assertAlmostEqual(h3.GOAL_REWARD, 1.0000)
        self.assertAlmostEqual(h3.ILLEGAL_CYCLE_BONUS, 0.2500)
        self.assertAlmostEqual(h3.ILLEGAL_FORWARD_BONUS, 0.0500)
        self.assertAlmostEqual(h3.CONST_PHI, 3.0000)
        self.assertAlmostEqual(h3.GAMMA ** 2 * h3.GOAL_REWARD, 0.8100)
        src = (ROOT / H3_REL).read_text()
        self.assertIn("F(s,a,s') = gamma * Phi(s') - Phi(s)", src)
        self.assertIn("GAMMA*Phi(s')-Phi(s)", src)
        out = (ROOT / H3_EXP).read_text()
        self.assertIn("hand_calc potential 2-cycle 1->0->1 F terms = -1.0000, 1.0000 cycle sum = 0.0000", out)
        self.assertIn("cycle sum = 1.0000 (not 0)", out)
        self.assertIn("hand_calc unshaped return from S along S->J->P->G = GAMMA^2 * GOAL_REWARD = 0.9000^2 * 1.0000 = 0.8100", out)

    def test_regimes(self):
        # acyclic corridor: all arms reach the goal with the same unshaped return
        for arm in ("A", "B", "C"):
            rec = h3.run_arm(h3.STATES_CORRIDOR, h3.DIST_CORRIDOR, arm)
            self.assertEqual(rec["success"], 1.0)
            self.assertAlmostEqual(rec["original_return"], 0.8100)
            self.assertEqual(rec["uses_cycle"], 0.0)
            self.assertEqual(rec["path"], ["S", "J", "P", "G"])
        rec_a = h3.run_arm(h3.STATES_CYCLE, h3.DIST_CYCLE, "A")
        rec_b = h3.run_arm(h3.STATES_CYCLE, h3.DIST_CYCLE, "B")
        rec_c = h3.run_arm(h3.STATES_CYCLE, h3.DIST_CYCLE, "C")
        rec_k = h3.run_arm(h3.STATES_CYCLE, h3.DIST_CYCLE, "B_const")
        self.assertEqual(rec_a["path"], ["S", "J", "P", "G"])
        self.assertEqual(rec_b["path"], ["S", "J", "P", "G"])
        self.assertEqual(h3.policy_agree(rec_a["pi"], rec_b["pi"], h3.STATES_CYCLE), 1.0)
        self.assertEqual(h3.policy_agree(rec_a["pi"], rec_k["pi"], h3.STATES_CYCLE), 1.0)
        self.assertEqual(rec_c["success"], 0.0)
        self.assertAlmostEqual(rec_c["original_return"], 0.0)
        self.assertEqual(rec_c["uses_cycle"], 1.0)
        self.assertIn("B", rec_c["path"])
        self.assertEqual(h3.policy_agree(rec_a["pi"], rec_c["pi"], h3.STATES_CYCLE), 0.0)
        err = h3.q_shift_err(rec_b["q"], rec_a["q"], lambda s: h3.phi_dist(s, h3.DIST_CYCLE, 1.0), h3.STATES_CYCLE)
        self.assertLess(err, 1e-12)

    def test_expected_markers(self):
        out = (ROOT / H3_EXP).read_text()
        for x in (
            "Synthetic potential-based shaping stand-in; not ManiSkill, SB3, or a real arm",
            "以论文为准",
            "本页未运行",
            "paired B-A success: 0.0000+-0.0000: tie: identical on every seed",
            "paired C-A original_return: -0.8100+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "paired B_const-A original_return: 0.0000+-0.0000: tie: identical on every seed",
            "named alternative B_alt (Phi = -2 * distance, still potential-based) - not adopted",
            "No winner declared",
        ):
            self.assertIn(x, out)


class ServoProximity(unittest.TestCase):
    def test_demo_config_constants_and_scale_law(self):
        self.assertAlmostEqual(h4.SELF_COLLISION_PROXIMITY_THRESHOLD, 0.01)
        self.assertAlmostEqual(h4.SCENE_COLLISION_PROXIMITY_THRESHOLD, 0.02)
        self.assertTrue(h4.CHECK_COLLISIONS_DEMO)
        self.assertAlmostEqual(h4.COLLISION_CHECK_RATE, 10.0)
        self.assertAlmostEqual(h4.proximity_scale(0.02, 0.02, "linear"), 1.0)
        self.assertAlmostEqual(h4.proximity_scale(0.01, 0.02, "linear"), 0.5)
        self.assertAlmostEqual(h4.proximity_scale(0.0, 0.02, "linear"), 0.0)
        self.assertAlmostEqual(h4.proximity_scale(-0.01, 0.02, "linear"), 0.0)
        self.assertAlmostEqual(h4.proximity_scale(0.03, 0.02, "linear"), 1.0)
        self.assertAlmostEqual(h4.proximity_scale(0.01, 0.01, "linear"), 1.0)

    def test_regimes(self):
        far_a = h4.run_arm("A", h4.FAR_START_CLEARANCE, h4.FAR_HORIZON_STEPS, h4.SCENE_COLLISION_PROXIMITY_THRESHOLD)
        far_b = h4.run_arm("B", h4.FAR_START_CLEARANCE, h4.FAR_HORIZON_STEPS, h4.SCENE_COLLISION_PROXIMITY_THRESHOLD)
        far_c = h4.run_arm("C", h4.FAR_START_CLEARANCE, h4.FAR_HORIZON_STEPS, h4.SCENE_COLLISION_PROXIMITY_THRESHOLD)
        self.assertAlmostEqual(far_a["progress"], far_b["progress"])
        self.assertAlmostEqual(far_a["progress"], 0.0500)
        self.assertEqual(far_a["collision_steps"], 0.0)
        self.assertEqual(far_b["collision_steps"], 0.0)
        self.assertLess(far_c["progress"], far_a["progress"])
        scene_a = h4.run_arm("A", h4.SCENE_START_CLEARANCE, h4.SCENE_HORIZON_STEPS, h4.SCENE_COLLISION_PROXIMITY_THRESHOLD)
        scene_b = h4.run_arm("B", h4.SCENE_START_CLEARANCE, h4.SCENE_HORIZON_STEPS, h4.SCENE_COLLISION_PROXIMITY_THRESHOLD)
        self.assertGreater(scene_a["collision_steps"], 0.0)
        self.assertEqual(scene_b["collision_steps"], 0.0)
        self.assertGreater(scene_a["max_penetration"], 0.0)
        self.assertEqual(scene_b["max_penetration"], 0.0)
        self.assertAlmostEqual(scene_a["collision_steps"], 41.0)
        self_a = h4.run_arm("A", h4.SELF_START_CLEARANCE, h4.SELF_HORIZON_STEPS, h4.SELF_COLLISION_PROXIMITY_THRESHOLD)
        self_b = h4.run_arm("B", h4.SELF_START_CLEARANCE, h4.SELF_HORIZON_STEPS, h4.SELF_COLLISION_PROXIMITY_THRESHOLD)
        self.assertGreater(self_a["collision_steps"], 0.0)
        self.assertEqual(self_b["collision_steps"], 0.0)
        self.assertAlmostEqual(self_a["collision_steps"], 71.0)

    def test_expected_markers(self):
        out = (ROOT / H4_EXP).read_text()
        src = (ROOT / H4_REL).read_text()
        self.assertIn("not vendor-universal defaults", src)
        self.assertIn("opened demo-config", src)
        for x in (
            "declared demo-config constants self_collision_proximity_threshold=0.0100 scene_collision_proximity_threshold=0.0200 check_collisions=true collision_check_rate=10.0000",
            "以文档为准",
            "本页未运行",
            "paired B-A progress: 0.0000+-0.0000: tie: identical on every seed",
            "paired C-A progress: -0.0253+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "paired B-A collision_steps: -41.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "paired B-A collision_steps: -71.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "named alternative B_quad (quadratic scale (clearance/threshold)^2) - not adopted",
            "No winner declared",
        ):
            self.assertIn(x, out)


if __name__ == "__main__":
    unittest.main()
