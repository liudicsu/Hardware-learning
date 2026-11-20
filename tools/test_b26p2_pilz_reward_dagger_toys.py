#!/usr/bin/env python3
"""Independent contract tests for the Pilz LIN-vs-PTP and Reward-DAgger toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H3_REL = "examples/month-5/moveit-pick-place/pilz_lin_vs_ptp_path_toy.py"
H4_REL = "examples/month-6/behaviour-cloning/reward_dagger_progress_gate_toy.py"
H3_EXP = "examples/month-5/expected/pilz_lin_vs_ptp_path_toy.txt"
H4_EXP = "examples/month-6/expected/reward_dagger_progress_gate_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


h3 = load("pilz_lin_vs_ptp_path_toy", H3_REL)
h4 = load("reward_dagger_progress_gate_toy", H4_REL)


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
            idx_tie = src.index("all(d == 0.0 for d in diffs)")
            idx_zero = src.index("abs(m) < NUM_ZERO")
            idx_sd = src.index("if abs(m) <= s:")
            self.assertLess(idx_tie, idx_zero)
            self.assertLess(idx_zero, idx_sd)
            for marker in ("Common random numbers", "本页未运行", "ROUND_HALF_UP", "written before the first run"):
                self.assertIn(marker, src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|rclpy|rclcpp)")
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+subprocess")
            self.assertNotIn("subprocess.", src)
            self.assertNotIn("Popen", src)

    def test_expected_byte_identical_and_no_process_labels(self):
        for rel, exp in ((H3_REL, H3_EXP), (H4_REL, H4_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b26p2"):
            self.assertRegex(bad, PROCESS)


class PilzLinVsPtp(unittest.TestCase):
    def test_path_shape_and_crn(self):
        self.assertAlmostEqual(h3.L1, 0.3000)
        self.assertAlmostEqual(h3.L2, 0.2500)
        self.assertEqual(h3.N_PATH, 41)
        self.assertAlmostEqual(h3.SIG_MEAS, 4e-4)
        self.assertAlmostEqual(h3.SIG_MEAS_ALT, 0.0)
        n0 = h3.shared_noise(0, "short_straight", h3.SIG_MEAS)
        n1 = h3.shared_noise(0, "short_straight", h3.SIG_MEAS)
        self.assertEqual(n0, n1)
        p0 = h3.shared_problem(0, "long_reconfig", 0.0)
        ptp = h3.evaluate("A_ptp", p0)
        lin = h3.evaluate("B_lin", p0)
        self.assertGreater(ptp["bow_m"], lin["bow_m"])
        self.assertEqual(ptp["n_collide"], 0.0)
        self.assertEqual(lin["n_collide"], 0.0)
        blocked_row = h3.run_regime("lin_blocked", 0, 0.0)
        self.assertEqual(blocked_row["line_hit"], 1.0)
        self.assertGreater(blocked_row["C_lin_blocked"]["n_collide"], 0.0)
        self.assertEqual(blocked_row["A_ptp"]["n_collide"], 0.0)
        out = (ROOT / H3_EXP).read_text()
        for s in (
            "hand_calc reach L1+L2 = 0.5500 m",
            "hand_calc fold abs(L1-L2) = 0.0500 m",
            "hand_calc SIG_MEAS = 0.0004 m",
            "hand_calc 20 percent small-vs-clear factor = 0.2000",
            "docs_commit=cdee39bbc5746a98630a4d631ab7d0184de2f1e1",
            "docs_blob=54f4ee6cc3379f2198ac5d4a9a26349a1428ade0",
            "docs_rst_sha256=dff95cb2091f121defb32a7ad90c4a9b34786aa3ce73b283699c19436e71a591",
            "paired B-A bow_m: -1.230e-5+-4.839e-5: near-tie",
            "paired B-A bow_m: -0.1659+-2.886e-4: clear gap",
            "line_hit 1.0000+-0.0000",
            "C_lin_blocked bow_m 0.0011+-1.480e-4 n_collide 9.0000+-0.0000",
            "alternative same seeds SIG_MEAS=0.0000 m (not adopted)",
            "-6.181e-5+-0.0000",
            "No real MoveIt process was started",
            "Regimes and parameters were written before the first run",
            "Common random numbers",
            "本页未运行",
            "以文档为准",
        ):
            self.assertIn(s, out)


class RewardDaggerGate(unittest.TestCase):
    def test_spearman_gate_and_crn(self):
        self.assertEqual(h4.T, 80)
        self.assertEqual(h4.N_EPS, 8)
        self.assertEqual(h4.L_S, 8)
        self.assertEqual(h4.L_L, 24)
        self.assertAlmostEqual(h4.TAU_S, -0.5000)
        self.assertAlmostEqual(h4.TAU_L, 0.2000)
        self.assertAlmostEqual(h4.DELTA_MIN, 0.0800)
        self.assertAlmostEqual(h4.SIG_PHI, 0.0150)
        self.assertAlmostEqual(h4.TAU_L_ALT, 1.0000)
        rising = [float(t) for t in range(10)]
        self.assertAlmostEqual(h4.spearman(rising), 1.0)
        falling = list(reversed(rising))
        self.assertAlmostEqual(h4.spearman(falling), -1.0)
        t0 = h4.shared_traces(0, "uneventful")
        t1 = h4.shared_traces(0, "uneventful")
        self.assertEqual(t0, t1)
        unev = h4.run_regime("uneventful", 0)
        self.assertEqual(unev["A_always"]["success"], 1.0)
        self.assertEqual(unev["B_reward_gate"]["success"], 1.0)
        self.assertEqual(unev["B_reward_gate"]["calls"], 0.0)
        self.assertEqual(unev["A_always"]["calls"], float(h4.T))
        stall = h4.run_regime("drop_stall", 0)
        self.assertEqual(stall["C_never"]["success"], 0.0)
        self.assertEqual(stall["B_reward_gate"]["success"], 1.0)
        self.assertGreater(stall["A_always"]["calls"], stall["B_reward_gate"]["calls"])
        out = (ROOT / H4_EXP).read_text()
        for s in (
            "hand_calc episode length T = 80",
            "hand_calc short window L_S = 8",
            "hand_calc long window L_L = 24",
            "hand_calc 20 percent small-vs-clear factor = 0.2000",
            "Ryan Li, Yigit Korkmaz, Erdem Bıyık",
            "PDF footnote star Equal Contribution",
            "paper_gate=(L_s, tau_s, delta_min, L_l, tau_l)=(75, -0.9, 0.05, 225, 0.0)",
            "paired B-A success: 0.0000+-0.0000: tie: identical on every seed",
            "paired B-A calls: -80.0000+-0.0000: clear gap",
            "paired B-C effort_return: 0.6380+-0.0005: clear gap",
            "paired B-A calls: -34.6000+-0.1046: clear gap",
            "alternative same seeds TAU_L=1.0000 (not adopted)",
            "57.0000+-0.0000",
            "No real VLA, GPU reward model, or human-in-the-loop arm was started",
            "Regimes and parameters were written before the first run",
            "Common random numbers",
            "本页未运行",
            "以论文为准",
        ):
            self.assertIn(s, out)


if __name__ == "__main__":
    unittest.main()
