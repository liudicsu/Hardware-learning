#!/usr/bin/env python3
"""Independent contract tests for the encoder-speed and pi0.5 co-training toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENC_REL = "examples/month-2/motors-drivers/encoder_speed_frequency_period_toy.py"
PI_REL = "examples/month-8/dataset-engineering/pi05_heterogeneous_cotrain_toy.py"
ENC_EXP = "examples/month-2/expected/encoder_speed_frequency_period_toy.txt"
PI_EXP = "examples/month-8/expected/pi05_heterogeneous_cotrain_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


enc = load("encoder_speed_frequency_period_toy", ENC_REL)
pi = load("pi05_heterogeneous_cotrain_toy", PI_REL)


def run(rel: str) -> str:
    return subprocess.run(
        [sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True
    ).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        for mod, rel in ((enc, ENC_REL), (pi, PI_REL)):
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
        for rel, exp in ((ENC_REL, ENC_EXP), (PI_REL, PI_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b24p2"):
            self.assertRegex(bad, PROCESS)


class EncoderSpeed(unittest.TestCase):
    def test_hand_calc_and_stand_in(self):
        self.assertAlmostEqual(enc.MOTOR_CPR, 12.0, places=12)
        self.assertAlmostEqual(enc.GEAR, 120.0, places=12)
        self.assertAlmostEqual(enc.SHAFT_CPR, 1440.0, places=12)
        self.assertAlmostEqual(enc.PULSES_PER_REV, 360.0, places=12)
        self.assertAlmostEqual(enc.EDGES_PER_REV_A, 720.0, places=12)
        self.assertAlmostEqual(enc.a_period(10.0), 60.0 / (10.0 * 360.0), places=15)
        self.assertAlmostEqual(enc.a_period(300.0), 60.0 / (300.0 * 360.0), places=15)
        self.assertAlmostEqual(0.0200 * 720.0 * 10.0 / 60.0, 2.4, places=12)
        self.assertAlmostEqual(0.1000 * 720.0 * 300.0 / 60.0, 360.0, places=12)
        self.assertAlmostEqual(enc.SYMMETRY / enc.ASSUMED_DUTY_C, 0.6, places=12)
        out = (ROOT / ENC_EXP).read_text()
        for s in (
            "hand_calc motor_cpr * gear = 12.0000 * 120.0000 = 1440.0000",
            "hand_calc pulses_per_rev A-channel = 1440.0000 / 4.0000 = 360.0000",
            "hand_calc frequency edges per rev (A rise+fall) = 720.0000",
            "hand_calc timer_tick = 1.0000000000e-06",
            "expected A-edges=2.4000",
            "expected A-edges=360.0000",
            "C scale factor 0.3000/0.5000 = 0.6000",
            "paired B-A abs_rpm_err: -2.6062+-1.8042: clear gap",
            "paired B-A abs_rpm_err: 2.0576+-1.2790: clear gap",
            "paired C-B abs_rpm_err: 7.4955+-1.4420: clear gap",
            "paired C-B abs_rpm_err: 198.2811+-49.3165: clear gap",
        ):
            self.assertIn(s, out)
        self.assertNotIn("4096", out)

    def test_stdlib_and_crn_header(self):
        src = (ROOT / ENC_REL).read_text()
        self.assertIn("import math", src)
        self.assertIn("import random", src)
        out = (ROOT / ENC_EXP).read_text()
        self.assertIn("Common random numbers: the shaft motion, A-channel edge train and jitter", out)
        self.assertIn("Regimes and parameters were written before the first run", out)
        self.assertIn("本页未运行", out)
        self.assertIn("lesson stand-in", out)
        self.assertIn("not a vendor fact", out)


class Pi05Cotrain(unittest.TestCase):
    def test_weights_and_hand_calc(self):
        self.assertEqual(pi.N_SCENES, 25)
        self.assertAlmostEqual(pi.W_TARGET + pi.W_WEB + pi.W_SUBTASK + pi.W_OTHER, 1.0, places=12)
        self.assertAlmostEqual(pi.W_WEB + pi.W_SUBTASK + pi.W_OTHER, 0.6, places=12)
        self.assertAlmostEqual(pi.W_TARGET_C, 0.0, places=12)
        self.assertAlmostEqual(pi.BIAS, 0.05, places=12)
        out = (ROOT / PI_EXP).read_text()
        for s in (
            "hand_calc n_scenes = 25.0000",
            "hand_calc B mixture weights 0.4000 + 0.2000 + 0.2500 + 0.1500 = 1.0000",
            "hand_calc C used-weight sum 0.2000 + 0.2500 + 0.1500 = 0.6000",
            "hand_calc in_domain expected A ~ 0.0500 + 1.0000 * 0.7500 = 0.8000",
            "hand_calc in_domain expected B ~ 0.0500 + 1.0000 * 0.7500 = 0.8000",
            "hand_calc ood_new_home expected A ~ 0.4000",
            "hand_calc ood_new_home expected B ~ 0.5425",
            "hand_calc ood_new_home expected C ~ 0.4025",
            "paired B-A success: -0.0131+-0.0062: small but consistent gap",
            "paired B-A success: 0.1504+-0.0199: clear gap",
            "paired C-B success: -0.3032+-0.0038: clear gap",
            "paired C-B success: -0.1370+-0.0121: clear gap",
        ):
            self.assertIn(s, out)
        self.assertNotIn("97.6", out)

    def test_stdlib_and_crn_header(self):
        src = (ROOT / PI_REL).read_text()
        self.assertIn("import math", src)
        self.assertIn("import random", src)
        out = (ROOT / PI_EXP).read_text()
        self.assertIn("Common random numbers: the scene / instruction / eval feature draws", out)
        self.assertIn("Regimes and parameters were written before the first run", out)
        self.assertIn("本页未运行", out)
        self.assertIn("以论文为准", out)
        self.assertIn("not a house rollout", out)


if __name__ == "__main__":
    unittest.main()
