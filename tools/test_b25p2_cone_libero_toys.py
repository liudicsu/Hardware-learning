#!/usr/bin/env python3
"""Independent contract tests for the friction-cone and LIBERO-X ladder toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H3_REL = "examples/month-7/mujoco-so101/friction_cone_elliptic_pyramid_toy.py"
H4_REL = "examples/month-8/sim-benchmarks/libero_x_robustness_ladder_toy.py"
H3_EXP = "examples/month-7/expected/friction_cone_elliptic_pyramid_toy.txt"
H4_EXP = "examples/month-8/expected/libero_x_robustness_ladder_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


h3 = load("friction_cone_elliptic_pyramid_toy", H3_REL)
h4 = load("libero_x_robustness_ladder_toy", H4_REL)


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

    def test_expected_byte_identical_and_no_process_labels(self):
        for rel, exp in ((H3_REL, H3_EXP), (H4_REL, H4_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b25p2"):
            self.assertRegex(bad, PROCESS)


class FrictionCones(unittest.TestCase):
    def test_documented_dimensions_and_sets(self):
        self.assertEqual(h3.elliptic_dims(1), 1)
        self.assertEqual(h3.pyramidal_dims(1), 1)
        self.assertEqual(h3.elliptic_dims(3), 3)
        self.assertEqual(h3.pyramidal_dims(3), 4)
        self.assertAlmostEqual(h3.MU_Y, 0.5000)
        self.assertAlmostEqual(h3.MU_Z, 0.5000)
        # Mid-diagonal hand calc: inside elliptic, outside pyramid.
        fn, r = 1.0000, 0.8500
        u = r / math.sqrt(2.0)
        fy = u * h3.MU_Y * fn
        fz = u * h3.MU_Z * fn
        self.assertTrue(h3.in_elliptic(fn, fy, fz, h3.MU_Y, h3.MU_Z, 3))
        self.assertFalse(h3.in_pyramid(fn, fy, fz, h3.MU_Y, h3.MU_Z, 3))
        # Documented pyramid is an inner set: no sample in the pyramid outside the ellipse
        # along the official mid-band or the axes.
        self.assertTrue(h3.in_elliptic(1.0, 0.20, 0.0, 0.5000, 0.5000, 3))
        self.assertTrue(h3.in_pyramid(1.0, 0.20, 0.0, 0.5000, 0.5000, 3))
        # condim=1: both cones are the non-negative ray; tangent is ignored.
        self.assertTrue(h3.in_elliptic(0.4, 9.0, 9.0, 0.5000, 0.5000, 1))
        self.assertTrue(h3.in_pyramid(0.4, 9.0, 9.0, 0.5000, 0.5000, 1))
        self.assertFalse(h3.in_elliptic(-0.1, 0.0, 0.0, 0.5000, 0.5000, 1))
        self.assertFalse(h3.in_pyramid(-0.1, 0.0, 0.0, 0.5000, 0.5000, 1))
        # Unbounded arm drops the normal-component coupling.
        self.assertTrue(h3.in_unbounded(0.2, 9.0, 9.0, 0.5000, 0.5000, 3))
        self.assertFalse(h3.in_unbounded(-0.2, 0.0, 0.0, 0.5000, 0.5000, 3))

    def test_crn_and_frictionless_tie(self):
        a = h3.shared_samples("mid_tangential", 2)
        b = h3.shared_samples("mid_tangential", 2)
        self.assertEqual(a, b)
        ev = h3.evaluate("frictionless", 0)
        self.assertEqual(ev["condim"], 1)
        self.assertEqual(ev["arms"]["A_elliptic"]["admit"], ev["arms"]["B_pyramid"]["admit"])
        self.assertEqual(ev["n_ell_in_pyr_out"], 0)
        self.assertEqual(ev["n_pyr_in_ell_out"], 0)

    def test_official_output_markers(self):
        out = (ROOT / H3_EXP).read_text()
        for x in (
            "0.0000+-0.0000: tie: identical on every seed",
            "ell_in_pyr_out 8.0000+-0.0000",
            "pyr_in_ell_out 0.0000+-0.0000",
            "-0.2000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "0.8250+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "SMALL_FRAC=0.2000",
            "pyramidal_dims=4",
            "本页未运行",
            "alternative same seeds MU_Y=MU_Z=1.0000 (not adopted)",
        ):
            self.assertIn(x, out)
        self.assertNotIn("±", out)
        self.assertNotIn("−", out)


class LiberoXLadder(unittest.TestCase):
    def test_cumulative_penalties_and_leak(self):
        self.assertAlmostEqual(h4.P_BASE, 0.8000)
        self.assertEqual(h4.N_EP, 40)
        self.assertAlmostEqual(h4.cumulative_penalty(1), 0.0200)
        self.assertAlmostEqual(h4.cumulative_penalty(2), 0.1400)
        self.assertAlmostEqual(h4.cumulative_penalty(3), 0.3200)
        self.assertAlmostEqual(h4.cumulative_penalty(4), 0.4800)
        self.assertAlmostEqual(h4.cumulative_penalty(5), 0.6200)
        ev = h4.evaluate("leak_misreport", 1)
        self.assertAlmostEqual(ev["C_leak_l5"], ev["B_level"][1])
        self.assertGreater(ev["A_unperturbed"], ev["B_level"][5])

    def test_crn_shared_bank(self):
        a = h4.shared_bank("l1_jitter", 3)
        b = h4.shared_bank("l1_jitter", 3)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 40)

    def test_official_output_markers(self):
        out = (ROOT / H4_EXP).read_text()
        for x in (
            "paper_figure demonstrations = 2,520",
            "paper_figure tasks = 600",
            "paper_figure scenes = 100",
            "paper_figure L1_to_L2_average_success_drop_pct = 9.8",
            "-0.0150+-0.0224: near-tie / small gap, within seed noise (|m| <= sd)",
            "-0.3900+-0.1009: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "-0.5000+-0.0530: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "-0.6250+-0.0250: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "0.6300+-0.0671: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "SMALL_FRAC=0.2000",
            "本页未运行",
            "alternative same seeds HARSH_PENALTY=0.7000 unstructured (not adopted)",
            "0.0750+-0.0177",
        ):
            self.assertIn(x, out)
        self.assertNotIn("±", out)
        self.assertNotIn("−", out)
        self.assertIn("not LIBERO-Plus", out)
        self.assertNotIn("ICRA", out)


if __name__ == "__main__":
    unittest.main()
