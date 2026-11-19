#!/usr/bin/env python3
"""Independent contract tests for the rmw_zenoh QoS-discovery and redundant-IK toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H1_REL = "examples/month-4/ros2-setup/rmw_zenoh_qos_discovery_toy.py"
H2_REL = "examples/month-5/kinematics-ik/redundant_ik_nullspace_toy.py"
H1_EXP = "examples/month-4/expected/rmw_zenoh_qos_discovery_toy.txt"
H2_EXP = "examples/month-5/expected/redundant_ik_nullspace_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


h1 = load("rmw_zenoh_qos_discovery_toy", H1_REL)
h2 = load("redundant_ik_nullspace_toy", H2_REL)


def run(rel: str) -> str:
    return subprocess.run(
        [sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True
    ).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        for mod, rel in ((h1, H1_REL), (h2, H2_REL)):
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
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|rclpy|rclcpp)")
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+subprocess")
            self.assertNotIn("subprocess.", src)
            self.assertNotIn("Popen", src)

    def test_expected_byte_identical_and_no_process_labels(self):
        for rel, exp in ((H1_REL, H1_EXP), (H2_REL, H2_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b25p1"):
            self.assertRegex(bad, PROCESS)


class RmwZenoh(unittest.TestCase):
    def test_declared_rules_and_crn(self):
        self.assertEqual(h1.N_PUB, 40)
        self.assertAlmostEqual(h1.P_DROP, 0.0500)
        self.assertFalse(h1.qos_compatible_dds(h1.RELIABLE, h1.BEST_EFFORT))
        self.assertTrue(h1.qos_compatible_dds(h1.RELIABLE, h1.RELIABLE))
        self.assertTrue(h1.qos_compatible_dds(h1.BEST_EFFORT, h1.RELIABLE))
        draws = h1.shared_draws(0, h1.P_DROP, tag="compatible_qos")
        a = h1.evaluate("A_dds_like", h1.RELIABLE, h1.RELIABLE, True, draws)
        b = h1.evaluate("B_zenoh_like", h1.RELIABLE, h1.RELIABLE, True, draws)
        c = h1.evaluate("C_zenoh_no_router", h1.RELIABLE, h1.RELIABLE, True, draws)
        self.assertEqual(a["received"], b["received"])
        self.assertEqual(c["received"], 0.0)
        self.assertEqual(c["discovered"], 0.0)
        inc = h1.evaluate("A_dds_like", h1.RELIABLE, h1.BEST_EFFORT, True, draws)
        self.assertEqual(inc["received"], 0.0)
        self.assertEqual(inc["discovered"], 1.0)
        out = (ROOT / H1_EXP).read_text()
        for s in (
            "hand_calc full-delivery count if discovered and delivered with P_DROP=0 = 40.0000",
            "hand_calc expected received if discovered and P_DROP=0.0500 = 38.0000",
            "hand_calc 20 percent small-vs-clear factor = 0.2000",
            "hand_calc expected received if discovered and P_DROP=0.2000 = 32.0000",
            "paired B-A received: 0.0000+-0.0000: tie: identical on every seed",
            "paired B-A received: 38.0000+-1.0000: clear gap",
            "paired C-B received: -38.4000+-1.3416: clear gap",
            "No real rmw_* process was started",
            "Regimes and parameters were written before the first run",
            "Common random numbers",
            "本页未运行",
            "以文档为准",
        ):
            self.assertIn(s, out)
        self.assertNotIn("rmw_zenohd started", out.lower())


class RedundantIK(unittest.TestCase):
    def test_rectangular_jacobian_and_projector(self):
        self.assertEqual(len(h2.LINKS), 4)
        j = h2.jacobian(h2.Q_MID)
        self.assertEqual(len(j), 2)
        self.assertEqual(len(j[0]), 4)
        jp, rank, _det = h2.pinv_and_rank(j)
        self.assertEqual(rank, 2)
        residual = h2.matmul(j, h2.nullspace_projector(j, jp))
        self.assertLess(h2.frobenius(residual), 1e-12)
        j_s = h2.jacobian(h2.Q_STRETCH)
        _jp_s, rank_s, det_s = h2.pinv_and_rank(j_s)
        self.assertEqual(rank_s, 1)
        self.assertAlmostEqual(det_s, 0.0, places=12)
        tip = h2.fk(h2.Q_STRETCH)
        self.assertAlmostEqual(tip[0], 0.4000, places=12)
        self.assertAlmostEqual(tip[1], 0.0000, places=12)
        # Lesson 3x3 model is not used.
        src = (ROOT / H2_REL).read_text()
        self.assertIn("2 by 4", src)
        self.assertIn("unweighted specialization", src)
        self.assertIn("not a rewrite of kinematics.py", src)
        out = (ROOT / H2_EXP).read_text()
        for s in (
            "hand_calc reach_max = 4 * 0.1000 = 0.4000 m",
            "hand_calc 20 percent small-vs-clear factor = 0.2000",
            "hand_calc horizon = N_STEP * DT = 1.6000 s",
            "rank_deficient stretched configuration: rank=1",
            "no secondary-task win is declared at a rank-deficient J",
            "paired B-A primary_mm: -2.175e-6+-2.755e-7: small but consistent gap",
            "paired B-A primary_mm: -0.0016+-0.0031: near-tie",
            "paired B-A secondary_cost: -0.7757+-4.637e-5: clear gap",
            "paired C-A primary_mm: 42.6440+-0.0731: clear gap",
            "unweighted specialization",
            "以原文为准",
            "本页未运行",
        ):
            self.assertIn(s, out)


if __name__ == "__main__":
    unittest.main()
