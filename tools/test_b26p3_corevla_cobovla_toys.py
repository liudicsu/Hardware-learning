#!/usr/bin/env python3
"""Independent contract tests for the CoRe-VLA and CoBoVLA toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H5_REL = "examples/month-10/multi-view-extrinsics/corevla_training_view_restore_toy.py"
H6_REL = "examples/month-6/vla-models/cobovla_paraphrase_codes_toy.py"
H5_EXP = "examples/month-10/expected/corevla_training_view_restore_toy.txt"
H6_EXP = "examples/month-6/expected/cobovla_paraphrase_codes_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


h5 = load("corevla_training_view_restore_toy", H5_REL)
h6 = load("cobovla_paraphrase_codes_toy", H6_REL)


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
        for rel, exp in ((H5_REL, H5_EXP), (H6_REL, H6_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b26p3"):
            self.assertRegex(bad, PROCESS)


class CorevlaRestore(unittest.TestCase):
    def test_geometry_and_crn(self):
        self.assertAlmostEqual(h5.SHIFT_OFFICIAL, 0.2000)
        self.assertAlmostEqual(h5.SHIFT_ALT, 0.4000)
        self.assertAlmostEqual(h5.SHIFT_NONE, 0.0000)
        self.assertAlmostEqual(h5.RENDER_SIGMA, 0.5000)
        self.assertAlmostEqual(h5.FX, 400.0000)
        n0 = h5.shared_noise(0, h5.SHIFT_OFFICIAL)
        n1 = h5.shared_noise(0, h5.SHIFT_OFFICIAL)
        self.assertEqual(n0, n1)
        none = h5.run_seed(h5.SHIFT_NONE, 0)
        self.assertEqual(none["A_shifted"]["order_acc"], 1.0)
        self.assertEqual(none["B_restore"]["order_acc"], 1.0)
        self.assertAlmostEqual(none["A_shifted"]["rmse_px"], none["B_restore"]["rmse_px"], places=9)
        large = h5.run_seed(h5.SHIFT_OFFICIAL, 0)
        self.assertLess(large["B_restore"]["rmse_px"], large["A_shifted"]["rmse_px"])
        self.assertEqual(large["B_restore"]["order_acc"], 1.0)
        self.assertEqual(large["A_shifted"]["order_acc"], 0.0)
        self.assertEqual(large["C_wrong"]["order_acc"], 0.0)
        self.assertAlmostEqual(large["C_wrong"]["rmse_px"], large["A_shifted"]["rmse_px"], places=9)
        out = (ROOT / H5_EXP).read_text()
        for s in (
            "hand_calc official SHIFT=0.2000 m along +x, fixed training orientation",
            "hand_calc noiseless official-shift RMSE vs training view = 78.5675 px, closer=bowl",
            "hand_calc 20 percent small-vs-clear factor = 0.2000",
            "Tianhang Pan, Xuanhao Wang, Yiwen Pang, Bo Zhou, Jun Yang, Min-Ling Zhang, Shimin Di",
            "no corresponding-author dagger and no equal-contribution star",
            "paper_version=arXiv 2609.37150 v1, submitted 2026-09-29",
            "13.3 % to 83.3 % at a 1.6 m",
            "paired B-A rmse_px: -4.863e-15+-1.254e-14: numerically zero",
            "paired B-A rmse_px: -77.9351+-0.2948: clear gap",
            "paired B-A order_acc: 1.0000+-0.0000: clear gap",
            "alternative same seeds SHIFT=0.4000 m (not adopted)",
            "-156.4236+-0.2585",
            "No real RGB-D, point-cloud renderer, or VLA weight was started",
            "Regimes and parameters were written before the first run",
            "Common random numbers",
            "本页未运行",
            "以论文为准",
        ):
            self.assertIn(s, out)


class CobovlaCodes(unittest.TestCase):
    def test_codes_and_crn(self):
        self.assertEqual(h6.NGRAM, 2)
        self.assertEqual(h6.CANONICAL["pick_cup"], "pick the red cup")
        chosen, scores = h6.coupled_choice("grab the crimson mug")
        self.assertEqual(chosen, "open_drawer")
        self.assertGreater(scores["open_drawer"], scores["pick_cup"])
        self.assertEqual(h6.SYNONYM["grab the crimson mug"], "pick_cup")
        s0 = h6.run_seed("canonical", 0)
        s1 = h6.run_seed("canonical", 0)
        self.assertEqual(s0, s1)
        self.assertEqual(s0["A_coupled"], 1.0)
        self.assertEqual(s0["B_codes"], 1.0)
        self.assertEqual(s0["C_foreign"], 0.0)
        para = h6.run_seed("paraphrase", 0)
        self.assertEqual(para["A_coupled"], 0.0)
        self.assertEqual(para["B_codes"], 1.0)
        self.assertEqual(para["C_foreign"], 0.0)
        out = (ROOT / H6_EXP).read_text()
        for s in (
            "hand_calc 2-gram cosine 'grab the crimson mug'",
            "coupled_choice=open_drawer",
            "hand_calc 20 percent small-vs-clear factor = 0.2000",
            "Mehul Arora, Dhruv Agarwal, Ambuj Agrawal",
            "no equal-contribution or corresponding typography",
            "paper_version=arXiv 2611.22395 v1, submitted 2026-11-17",
            "91.4 % on LIBERO-Goal",
            "paired B-A success: 0.0000+-0.0000: tie: identical on every seed",
            "paired B-A success: 1.0000+-0.0000: clear gap",
            "alternative same seeds continuous pre-quantization vector (not adopted)",
            "regime canonical_continuous",
            "No real LIBERO, LIBERO-Para, or GPU VLA was started",
            "Regimes and parameters were written before the first run",
            "Common random numbers",
            "本页未运行",
            "以论文为准",
        ):
            self.assertIn(s, out)


if __name__ == "__main__":
    unittest.main()
