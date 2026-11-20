#!/usr/bin/env python3
"""Independent contract tests for the Y-Δ / Δ-Y network-reduction toy; stdlib only."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = "examples/month-1/ohms-law/ydelta_network_reduction_toy.py"
EXP = "examples/month-1/expected/ydelta_network_reduction_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


toy = load("ydelta_network_reduction_toy", REL)


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

    def test_expected_byte_identical_and_no_process_labels(self):
        out = run(REL)
        self.assertEqual(out, run(REL))
        self.assertEqual(out, (ROOT / EXP).read_text())
        for text in (out, (ROOT / REL).read_text()):
            self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b29p1"):
            self.assertRegex(bad, PROCESS)


class YDeltaContract(unittest.TestCase):
    def test_declared_setup(self):
        self.assertAlmostEqual(toy.RS1, 1000.0)
        self.assertAlmostEqual(toy.RP1, 2000.0)
        self.assertAlmostEqual(toy.RS2, 3000.0)
        self.assertAlmostEqual(toy.RP2, 4000.0)
        self.assertAlmostEqual(toy.RS3, 5000.0)
        self.assertAlmostEqual(toy.RPL, 100.0)
        self.assertAlmostEqual(toy.RPR, 10000.0)
        self.assertAlmostEqual(toy.RQL, 10000.0)
        self.assertAlmostEqual(toy.RQR, 100.0)
        self.assertAlmostEqual(toy.RX_LARGE, 1000000.0)
        self.assertAlmostEqual(toy.RX_MODERATE, 100.0)
        self.assertAlmostEqual(toy.VTEST, 1.0)
        self.assertEqual(toy.ARMS, ("A_series_parallel", "B_official", "C_swapped"))
        self.assertEqual(
            toy.REGIMES,
            ("series_parallel_ladder", "large_cross_bridge", "moderate_bridge"),
        )

    def test_official_formulae_with_article_labels(self):
        r1, r2, r3 = toy.wye_from_delta(20100.0, 201.0, 20100.0)
        self.assertAlmostEqual(r1, 100.0)
        self.assertAlmostEqual(r2, 10000.0)
        self.assertAlmostEqual(r3, 100.0)
        ra, rb, rc = toy.delta_from_wye(100.0, 10000.0, 100.0)
        self.assertAlmostEqual(ra, 20100.0)
        self.assertAlmostEqual(rb, 201.0)
        self.assertAlmostEqual(rc, 20100.0)
        ra_rw = 10000.0 + 100.0 + (10000.0 * 100.0) / 100.0
        self.assertAlmostEqual(ra, ra_rw)

    def test_predeclared_regimes(self):
        out = (ROOT / EXP).read_text()
        self.assertIn("clear_frac=0.2000", out)
        self.assertIn("hand_calc work_plan 30+25+50+40+35=180", out)
        self.assertIn(
            "paired A-B Req: 0.0000+-0.0000: tie: identical on every seed",
            out,
        )
        self.assertIn(
            "paired A-B Req: 24.3794+-0.0000: small but consistent gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn(
            "paired A-B Req: 4757.7670+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn(
            "paired C-B Req: -258.9083+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn("alternative large_cross RX=10000000ohm (same bridge arms, not adopted)", out)
        self.assertIn("not a Wheatstone measurement bridge", out)
        self.assertIn("本页未运行", out)
        # Truth is B; nodal is a printed checker only
        self.assertIn("residual_B-nodal=-4.547e-13ohm", out)
        self.assertIn("residual_B-nodal=-5.684e-14ohm", out)

    def test_ladder_exact_tie_and_nodal_not_a_retune(self):
        a = toy.series_parallel_ladder()
        b = toy.official_ladder(toy.delta_from_wye)
        c = toy.official_ladder(toy.wye_from_delta)
        self.assertEqual(a, b)
        self.assertNotEqual(c, b)
        nodal = toy.nodal_ladder()
        self.assertLess(abs(b - nodal), 1e-9)

    def test_hook_before_exit(self):
        hook = (ROOT / "examples/month-1/check.sh").read_text()
        self.assertIn("ydelta_network_reduction_toy.txt", hook)
        self.assertLess(hook.index("ydelta_network_reduction_toy"), hook.index("exit $fail"))
        self.assertLess(hook.index("superposition_linear_circuit_toy.txt"), hook.index("ydelta_network_reduction_toy"))
        self.assertGreater(hook.index("exit $fail"), hook.rindex("ydelta_network_reduction_toy"))


if __name__ == "__main__":
    unittest.main()
