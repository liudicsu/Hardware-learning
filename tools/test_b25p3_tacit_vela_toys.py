#!/usr/bin/env python3
"""Independent contract tests for the TacitVLA and Vela toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H5_REL = "examples/month-10/edge-deploy-checklist/tacitvla_reasoning_latency_toy.py"
H6_REL = "examples/month-10/real-time-chunking/vela_spline_action_toy.py"
H5_EXP = "examples/month-10/expected/tacitvla_reasoning_latency_toy.txt"
H6_EXP = "examples/month-10/expected/vela_spline_action_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


h5 = load("tacitvla_reasoning_latency_toy", H5_REL)
h6 = load("vela_spline_action_toy", H6_REL)


def run(rel: str) -> str:
    return subprocess.run(
        [sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True
    ).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        for mod, rel in ((h5, H5_REL), (h6, H6_REL)):
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

    def test_expected_byte_identical_and_no_process_labels(self):
        for rel, exp in ((H5_REL, H5_EXP), (H6_REL, H6_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b25p3"):
            self.assertRegex(bad, PROCESS)


class TacitVLA(unittest.TestCase):
    def test_declared_parameters_and_hand_calcs(self):
        self.assertAlmostEqual(h5.T_ACTION, 8.0000)
        self.assertAlmostEqual(h5.T_REASON, 12.0000)
        self.assertAlmostEqual(h5.WINDOW, 20.0000)
        self.assertEqual(h5.N_EP, 40)
        self.assertEqual(h5.N_STEPS, 6)
        self.assertAlmostEqual(h5.P_SHORT, 0.8500)
        self.assertAlmostEqual(h5.P_SHORT_NOSUP, 0.7000)
        self.assertEqual(h5.C_FIXED_PRESSES, 4)
        self.assertEqual(h5.TARGETS, (2, 3, 4, 5))
        self.assertAlmostEqual(h5.T_ACTION + h5.T_REASON, 20.0000)
        self.assertAlmostEqual(h5.WINDOW - h5.T_REASON, 8.0000)
        self.assertAlmostEqual((h5.T_ACTION + h5.T_REASON) / h5.T_ACTION, 2.5000)
        self.assertGreater(h5.ALT_T_REASON, h5.WINDOW)

    def test_crn_shared_bank(self):
        a = h5.shared_bank("memory_ledger", 2)
        b = h5.shared_bank("memory_ledger", 2)
        self.assertEqual(a, b)
        c = h5.shared_bank("memory_ledger", 3)
        self.assertNotEqual(a, c)

    def test_official_output_markers(self):
        out = (ROOT / H5_EXP).read_text()
        for x in (
            "0.0000+-0.0000: tie: identical on every seed",
            "-12.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "0.7500+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "-1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "SMALL_FRAC=0.2000",
            "paper_figure explicit_latency_ratio_up_to = 3.4x",
            "paper_figure no_reasoning_latency_success_gain_pct = 17.1",
            "本页未运行",
            "ALT_T_REASON=25.0000",
            "hand_calc explicit_over_tacit_latency = 2.5000",
        ):
            self.assertIn(x, out)

    def test_official_regimes_hold(self):
        short = h5.official_rows("short_reactive")
        mem = h5.official_rows("memory_ledger")
        stale = h5.official_rows("stale_memory")
        a_s = [r["A_success"] for r in short]
        b_s = [r["B_success"] for r in short]
        self.assertEqual(a_s, b_s)
        a_l = [r["A_latency"] for r in short]
        b_l = [r["B_latency"] for r in short]
        self.assertTrue(all(bl < al for al, bl in zip(a_l, b_l)))
        mem_b = [r["B_success"] for r in mem]
        mem_c = [r["C_success"] for r in mem]
        self.assertTrue(all(b > c for b, c in zip(mem_b, mem_c)))
        self.assertEqual([r["B_latency"] for r in mem], [r["C_latency"] for r in mem])
        stale_c = [r["C_success"] for r in stale]
        stale_b = [r["B_success"] for r in stale]
        self.assertTrue(all(c < b for c, b in zip(stale_c, stale_b)))


class Vela(unittest.TestCase):
    def test_declared_parameters_and_hand_calcs(self):
        self.assertEqual(h6.K, 8)
        self.assertEqual(h6.N_QUERY, 121)
        self.assertAlmostEqual(h6.T_SHORT, 1.0000)
        self.assertAlmostEqual(h6.T_LONG, 4.0000)
        self.assertAlmostEqual(h6.T_PRECISE, 1.0000)
        self.assertAlmostEqual(h6.T_MIXED, 5.0000)
        self.assertAlmostEqual(h6.T_LONG + h6.T_PRECISE, h6.T_MIXED)
        self.assertAlmostEqual(h6.C_STRETCH, 2.0000)
        self.assertAlmostEqual(h6.T_MIXED * h6.C_STRETCH, 10.0000)
        self.assertAlmostEqual(h6.T_SHORT / (h6.N_QUERY - 1), 1.0 / 120.0)

    def test_title_spelling_in_source(self):
        src = (ROOT / H6_REL).read_text()
        self.assertIn("Parametrization", src)
        self.assertNotIn("Parameterization", src)

    def test_official_output_markers(self):
        out = (ROOT / H6_EXP).read_text()
        for x in (
            "numerically zero (floating-point residue), effectively a tie",
            "-0.1478+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "0.1692+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "SMALL_FRAC=0.2000",
            "C_STRETCH=2.0000",
            "hand_calc T_LONG + T_PRECISE = 5.0000",
            "本页未运行",
            "alt_dropped_knot",
            "0.0030+-0.0000",
        ):
            self.assertIn(x, out)

    def test_official_regimes_hold(self):
        short = h6.official_rows("short_smooth")
        mixed = h6.official_rows("mixed_motion")
        coarse = h6.official_rows("coarse_horizon")
        diffs = [r["B_rmse"] - r["A_rmse"] for r in short]
        self.assertTrue(all(abs(d) < 1e-9 for d in diffs))
        self.assertTrue(all(r["B_rmse"] < r["A_rmse"] for r in mixed))
        self.assertTrue(all(r["C_rmse"] > r["B_rmse"] for r in coarse))


if __name__ == "__main__":
    unittest.main()
