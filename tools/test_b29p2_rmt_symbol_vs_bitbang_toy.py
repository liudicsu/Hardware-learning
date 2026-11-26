#!/usr/bin/env python3
"""Independent contract tests for the RMT symbol vs bit-bang stand-in; stdlib only."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = "examples/month-2/esp32/rmt_symbol_vs_bitbang_toy.py"
EXP = "examples/month-2/expected/rmt_symbol_vs_bitbang_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


toy = load("rmt_symbol_vs_bitbang_toy", REL)


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
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b29p2"):
            self.assertRegex(bad, PROCESS)


class RmtContract(unittest.TestCase):
    def test_declared_setup(self):
        self.assertEqual(toy.RESOLUTION_HZ, 1 * 1000 * 1000)
        self.assertEqual(toy.WRONG_RESOLUTION_HZ, 2 * 1000 * 1000)
        self.assertEqual(toy.SHORT_D0, 8)
        self.assertEqual(toy.SHORT_D1, 4)
        self.assertEqual(toy.N_SHORT, 8)
        self.assertEqual(toy.PERIOD_D0, 20)
        self.assertEqual(toy.PERIOD_D1, 30)
        self.assertEqual(toy.LOOP_COUNT, 4)
        self.assertAlmostEqual(toy.REISSUE_GAP_US, 8.0)
        self.assertEqual(toy.PAYLOAD, 0xA5)
        self.assertTrue(toy.MSB_FIRST)
        self.assertAlmostEqual(toy.LAMBDA_PER_US, 0.15)
        self.assertAlmostEqual(toy.ISR_COST_US, 5.0)
        self.assertAlmostEqual(toy.tick_us(toy.RESOLUTION_HZ), 1.0)
        self.assertAlmostEqual(toy.tick_us(toy.WRONG_RESOLUTION_HZ), 0.5)
        self.assertAlmostEqual(toy.hardware_total_us([toy.SHORT_SYM] * toy.N_SHORT, toy.RESOLUTION_HZ), 96.0)
        self.assertAlmostEqual(toy.hardware_total_us([toy.PERIOD_SYM], toy.RESOLUTION_HZ, loops=toy.LOOP_COUNT), 200.0)
        bits = toy.encode_byte(toy.PAYLOAD, toy.BIT0, toy.BIT1, toy.MSB_FIRST)
        self.assertEqual(toy.decode_byte(bits, toy.BIT0, toy.BIT1, toy.MSB_FIRST), 0xA5)
        swapped = toy.encode_byte(toy.PAYLOAD, toy.BIT1, toy.BIT0, toy.MSB_FIRST)
        self.assertEqual(toy.decode_byte(swapped, toy.BIT0, toy.BIT1, toy.MSB_FIRST), 0x5A)


if __name__ == "__main__":
    unittest.main()
