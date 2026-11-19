#!/usr/bin/env python3
"""Independent contract tests for the NaVILA mid-level locomotion and FD-VLA force-distillation toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAV_REL = "examples/month-11/humanoid-wbc-overview/navila_midlevel_locomotion_toy.py"
FD_REL = "examples/month-11/contact-rich-policies/fdvla_force_distill_toy.py"
NAV_EXP = "examples/month-11/expected/navila_midlevel_locomotion_toy.txt"
FD_EXP = "examples/month-11/expected/fdvla_force_distill_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


nav = load("navila_midlevel_locomotion_toy", NAV_REL)
fd = load("fdvla_force_distill_toy", FD_REL)


def run(rel: str) -> str:
    return subprocess.run(
        [sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True
    ).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        for mod, rel in ((nav, NAV_REL), (fd, FD_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertEqual(mod.SEEDS, (0, 1, 2, 3, 4))
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
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")

    def test_expected_byte_identical_and_no_process_labels(self):
        for rel, exp in ((NAV_REL, NAV_EXP), (FD_REL, FD_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b24p3"):
            self.assertRegex(bad, PROCESS)


class NavilaMidlevel(unittest.TestCase):
    def test_hand_calc_and_stand_in(self):
        self.assertAlmostEqual(nav.LEN, 8.0, places=12)
        self.assertAlmostEqual(nav.HALF_W, 1.2, places=12)
        self.assertAlmostEqual(nav.ROBOT_R, 0.15, places=12)
        self.assertAlmostEqual(nav.OBS_R, 0.25, places=12)
        self.assertAlmostEqual(nav.HALF_W - nav.ROBOT_R, 1.05, places=12)
        self.assertAlmostEqual(nav.ROBOT_R + nav.OBS_R, 0.40, places=12)
        out = (ROOT / NAV_EXP).read_text()
        for s in (
            "hand_calc n_scenes = 25.0000",
            "hand_calc wall_clear = 1.2000 - 0.1500 = 1.0500",
            "hand_calc hit_clear = 0.1500 + 0.2500 = 0.4000",
            "hand_calc mid-level vocabulary forward 0.7500 m, sidestep 0.5000 m, turn 30.0000 deg",
            "hand_calc C yaw bias 0.2000 rad, tan = 0.2027, y at LEN = 8.0000 * tan(0.2000) = 1.6217, which is > 1.0500 so C hits the wall",
            "hand_calc C wall x = 1.0500 / tan(0.2000) = 5.1798",
            "hand_calc n_obs open = 0.0000; clutter n_obs = 4.0000 of which n_transparent = 2.0000",
            "hand_calc small-gap threshold = 0.2000 of the smaller arm mean",
            "paired B-A success: 0.0000+-0.0000: tie: identical on every seed",
            "paired B-A collisions: 0.0000+-0.0000: tie: identical on every seed",
            "paired C-B success: -1.0000+-0.0000: clear gap",
            "paired B-A success: 1.0000+-0.0000: clear gap",
            "paired B-A collisions: -2.0000+-0.0000: clear gap",
        ):
            self.assertIn(s, out)
        self.assertNotIn("17 %", out)
        self.assertNotIn("88 %", out)

    def test_stdlib_and_crn_header(self):
        src = (ROOT / NAV_REL).read_text()
        self.assertIn("import math", src)
        self.assertIn("import random", src)
        out = (ROOT / NAV_EXP).read_text()
        self.assertIn("Common random numbers: the instruction, occupancy / clutter and mid-level command vocabulary", out)
        self.assertIn("Regimes and parameters were written before the first run", out)
        self.assertIn("本页未运行", out)
        self.assertIn("以论文为准", out)


class FdvlaDistill(unittest.TestCase):
    def test_weights_and_hand_calc(self):
        self.assertEqual(fd.N_SCENES, 25)
        self.assertAlmostEqual(fd.W_V + fd.W_S, 1.0, places=12)
        self.assertAlmostEqual(fd.W_V, 0.3, places=12)
        self.assertAlmostEqual(fd.W_S, 0.7, places=12)
        out = (ROOT / FD_EXP).read_text()
        for s in (
            "hand_calc n_scenes = 25.0000",
            "hand_calc B weights 0.3000 + 0.7000 = 1.0000",
            "hand_calc bias = 0.0000 k_err = 1.0000 clip = 0.0000 to 1.0000",
            "hand_calc mu_z = 0.4000 sig_z = 0.0800",
            "hand_calc easy: v = 1.0000 * z + 0.0000 + N(0, 0.0200), s = z + N(0, 0.0200)",
            "hand_calc occluded: v = 0.0000 * z + 0.5000 + N(0, 0.1500), s = z + N(0, 0.0600)",
            "hand_calc C sensor_bias = 0.5500 sensor_sig = 0.0800 dropout_p = 0.2500",
            "hand_calc small-gap threshold = 0.2000 of the smaller arm mean",
            "paired B-A success: 0.0021+-0.0017: small but consistent gap",
            "paired C-B success: -0.4815+-0.0067: clear gap",
            "paired B-A success: 0.1070+-0.0087: small but consistent gap",
            "paired C-B success: -0.4377+-0.0175: clear gap",
            "paired B-oracle success: -0.0137+-0.0024: small but consistent gap",
            "paired B-oracle success: -0.0637+-0.0035: small but consistent gap",
        ):
            self.assertIn(s, out)

    def test_stdlib_and_crn_header(self):
        src = (ROOT / FD_REL).read_text()
        self.assertIn("import math", src)
        self.assertIn("import random", src)
        out = (ROOT / FD_EXP).read_text()
        self.assertIn("Common random numbers: the scene / vision / state / true-force draws", out)
        self.assertIn("Regimes and parameters were written before the first run", out)
        self.assertIn("本页未运行", out)
        self.assertIn("以论文为准", out)


if __name__ == "__main__":
    unittest.main()
