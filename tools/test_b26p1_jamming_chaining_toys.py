#!/usr/bin/env python3
"""Independent contract tests for the jamming holding-force and controller-chaining toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H1_REL = "examples/month-3/gripper-fingers/jamming_gripper_holding_force_toy.py"
H2_REL = "examples/month-4/ros2-control/controller_chaining_cascade_toy.py"
H1_EXP = "examples/month-3/expected/jamming_gripper_holding_force_toy.txt"
H2_EXP = "examples/month-4/expected/controller_chaining_cascade_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


h1 = load("jamming_gripper_holding_force_toy", H1_REL)
h2 = load("controller_chaining_cascade_toy", H2_REL)


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
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b26p1"):
            self.assertRegex(bad, PROCESS)


class JammingHoldingForce(unittest.TestCase):
    def test_equations_clamp_and_crn(self):
        self.assertAlmostEqual(h1.R, 0.0125)
        self.assertAlmostEqual(h1.MU, 1.04)
        self.assertAlmostEqual(h1.SIGMA_STAR, 50000.0)
        self.assertAlmostEqual(h1.D, 0.00107)
        tc = h1.theta_c(h1.MU)
        self.assertAlmostEqual(tc, math.atan(1.0 / h1.MU))
        self.assertEqual(h1.holding_force(0.5 * tc, h1.SIGMA_STAR, h1.MU, h1.R, h1.D, False), 0.0)
        self.assertEqual(h1.holding_force(0.5 * tc, h1.SIGMA_STAR, h1.MU, h1.R, h1.D, True), 0.0)
        self.assertEqual(h1.holding_force(math.pi / 3.0, 0.0, h1.MU, h1.R, h1.D, False), 0.0)
        mid = math.pi / 3.0
        ff = h1.holding_force(mid, h1.SIGMA_STAR, h1.MU, h1.R, h1.D, False)
        fs = h1.holding_force(mid, h1.SIGMA_STAR, h1.MU, h1.R, h1.D, True)
        self.assertGreater(ff, 0.0)
        self.assertGreater(fs, ff)
        t0 = h1.shared_theta(0, "modest_seal", h1.MU)
        t1 = h1.shared_theta(0, "modest_seal", h1.MU)
        self.assertEqual(t0, t1)
        a = h1.evaluate("A_unjammed", t0)
        b = h1.evaluate("B_friction", t0)
        c = h1.evaluate("C_seal", t0)
        self.assertEqual(a["F_h"], 0.0)
        self.assertGreater(c["F_h"], b["F_h"])
        out = (ROOT / H1_EXP).read_text()
        for s in (
            "hand_calc theta_c = arctan(1/MU) = 0.7658 rad",
            "hand_calc D=1.0700 mm, SIGMA_STAR=50.0000 kPa",
            "hand_calc 20 percent small-vs-clear factor = 0.2000",
            "D=0.00107 m",
            "paper_volume_change_less_than=0.5 %",
            "paper_suction_enhancement_order=10 times",
            "Eric Brown, Nicholas Rodenberg, John Amend, Annan Mozeika, Erik Steltz, Mitchell R. Zakin, Hod Lipson, Heinrich M. Jaeger",
            "paired B-A F_h: 0.0000+-0.0000: tie: identical on every seed",
            "paired C-B F_h: 11.8387+-8.5333: clear gap",
            "paired B-A F_h: 3.0794+-0.9884: clear gap",
            "alternative same seeds MU=1.1000 (not adopted)",
            "No real vacuum pump or bag was started",
            "Regimes and parameters were written before the first run",
            "Common random numbers",
            "本页未运行",
            "以论文为准",
        ):
            self.assertIn(s, out)


class ControllerChaining(unittest.TestCase):
    def test_declared_plant_and_crn(self):
        self.assertAlmostEqual(h2.DT, 0.002)
        self.assertAlmostEqual(h2.TAU_INNER, 0.025)
        self.assertAlmostEqual(h2.TAU_OUTER, 0.6)
        self.assertAlmostEqual(h2.KP_SINGLE, 1.85)
        self.assertAlmostEqual(h2.KP_OUTER, 2.0)
        self.assertAlmostEqual(h2.KP_INNER, 12.0)
        a, b = h2.zoh(h2.TAU_INNER)
        self.assertAlmostEqual(a, math.exp(-h2.DT / h2.TAU_INNER))
        self.assertAlmostEqual(b, 1.0 - a)
        d0 = h2.shared_draws(0, False, tag="official|slow_no_dist")
        d1 = h2.shared_draws(0, False, tag="official|slow_no_dist")
        self.assertEqual(d0["meas"], d1["meas"])
        self.assertTrue(all(x == 0.0 for x in d0["dist"]))
        row = h2.run_regime("slow_no_dist", 0)
        self.assertIn("outer_rmse", row["A_single"])
        out = (ROOT / H2_EXP).read_text()
        for s in (
            "hand_calc inner ZOH a=0.9231 b=0.0769",
            "hand_calc outer ZOH a=0.9967 b=0.0033",
            "hand_calc TAU_OUTER/TAU_INNER = 24.0000",
            "hand_calc RMSE window steps after T_WARM = 3500",
            "hand_calc 20 percent small-vs-clear factor = 0.2000",
            "docs_commit=b558c3ab693fbf9aa472392cafc0c0f14f9fc549",
            "docs_blob=0b91260a4064e51fce45e0de1e09101c5147fd02",
            "docs_example16_commit=b34cc5917f216b36ff3bda1ca0cc0736ecc00235",
            "docs_example16_blob=331f9881206b6a71a60b6c5b0463161c2039e99b",
            "paired B-A outer_rmse: 1.234e-7+-1.824e-6: near-tie",
            "paired B-A outer_rmse: -0.9775+-9.508e-5: clear gap",
            "paired C-B outer_rmse: 0.5038+-5.723e-5: clear gap",
            "alternative same seeds KP_SINGLE=1.5000 (not adopted)",
            "No real controller_manager process was started",
            "Regimes and parameters were written before the first run",
            "Common random numbers",
            "本页未运行",
            "以文档为准",
        ):
            self.assertIn(s, out)
        self.assertNotIn("controller_manager started", out.lower())


if __name__ == "__main__":
    unittest.main()
