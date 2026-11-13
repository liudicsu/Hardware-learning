#!/usr/bin/env python3
"""Independent contract tests for the optocoupler CTR/isolation and Ziegler–Nichols toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import random
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OP_REL = "examples/month-2/arduino-io/optocoupler_ctr_isolation_toy.py"
ZN_REL = "examples/month-3/pid-control/ziegler_nichols_ultimate_gain_toy.py"
OP_EXP = "examples/month-2/expected/optocoupler_ctr_isolation_toy.txt"
ZN_EXP = "examples/month-3/expected/ziegler_nichols_ultimate_gain_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


op = load("optocoupler_ctr_isolation_toy", OP_REL)
zn = load("ziegler_nichols_ultimate_gain_toy", ZN_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        for mod, rel in ((op, OP_REL), (zn, ZN_REL)):
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
        for rel, exp in ((OP_REL, OP_EXP), (ZN_REL, ZN_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b22p3"):
            self.assertRegex(bad, PROCESS)


class Optocoupler(unittest.TestCase):
    def test_hand_calc(self):
        i_sat = (op.VCC - op.VCE_SAT) / op.RL
        self.assertAlmostEqual(i_sat * 1e3, 0.659574, places=5)
        self.assertAlmostEqual(op.opto_out(1, 0.5, 1e-3, op.RL), op.VCC - 0.5e-3 * op.RL, places=12)
        self.assertLess(op.opto_out(1, 0.5, 1e-3, op.RL), op.V_IL)
        self.assertAlmostEqual(op.opto_out(1, 0.5, 10e-3, op.RL), op.VCE_SAT, places=12)
        self.assertEqual(op.opto_out(0, 0.5, 10e-3, op.RL), op.VCC)
        self.assertGreater(op.opto_out(1, 0.125, 1e-3, op.RL), op.V_IH)
        out = (ROOT / OP_EXP).read_text()
        for s in ("= 0.6596 mA", "= 1.3191 mA", "= 0.9500 V", "= 20.0000 V", "= 2.7125 V"):
            self.assertIn(s, out)

    def test_read_rule_and_inversion(self):
        self.assertEqual(op.read_pin(0.5), 0)
        self.assertEqual(op.read_pin(3.0), 1)
        self.assertIsNone(op.read_pin(1.5))
        bits = [(1, 0.0, False, 50.0), (0, 0.0, False, 50.0)]
        r = op.run_arm("B_opto", 0.0, bits, False, 1.0)
        self.assertEqual(r["logic_err"], 0.0)

    def test_barrier_blocks_surge_direct_does_not(self):
        bits = [(0, 0.0, True, 200.0)]
        a = op.run_arm("A_direct", 0.0, bits, True, 1.0)
        b = op.run_arm("B_opto", 0.0, bits, True, 1.0)
        self.assertEqual((a["logic_err"] * op.N_BITS, a["overvolt"] * op.N_BITS), (1.0, 1.0))
        self.assertEqual((b["logic_err"], b["overvolt"]), (0.0, 0.0))

    def test_common_random_numbers_shared(self):
        g, bits = op.draws("surge", 2)
        self.assertEqual((g, bits), op.draws("surge", 2))
        rng = random.Random("surge/2")
        self.assertEqual(g, rng.gauss(0.0, 1.0))
        self.assertEqual(len(bits), op.N_BITS)

    def test_declared_regimes_printed(self):
        out = (ROOT / OP_EXP).read_text()
        for s in ("paired B-A logic_err: 0.0000+-0.0000: tie: identical on every seed",
                  "paired B-A overvolt: -0.1790+-0.0444: clear gap", "paired B-A logic_err: -0.1050+-0.0158: clear gap",
                  "paired C-B logic_err: 0.5260+-0.0475: clear gap", "paired C-A logic_err: 0.5260+-0.0475: clear gap"):
            self.assertIn(s, out)


class ZieglerNichols(unittest.TestCase):
    def test_phase_crossover_hand_calc(self):
        for L in (0.1, 0.5):
            w, ku, tu = zn.analytic_ku_tu(L)
            self.assertAlmostEqual(math.atan(w * zn.TAU) + w * L, math.pi, places=9)
            self.assertAlmostEqual(ku * zn.K, math.sqrt(1.0 + (w * zn.TAU) ** 2), places=9)
            self.assertAlmostEqual(tu, 2.0 * math.pi / w, places=12)
        out = (ROOT / ZN_EXP).read_text()
        for s in ("Ku=16.3506 Tu=0.3850", "Ku=3.8069 Tu=1.7106", "identified Ku=15.9619 Tu=0.3943", "identified Ku=3.7913 Tu=1.7179"):
            self.assertIn(s, out)

    def test_exact_zoh_step_is_stable(self):
        self.assertTrue(0.0 < zn.A < 1.0)
        self.assertAlmostEqual(zn.A, math.exp(-zn.DT / zn.TAU), places=15)

    def test_p_only_steady_state_and_identified_below_analytic(self):
        nd = round(0.1 / zn.DT)
        y = zn.simulate(nd, 1.0, t_end=20.0)["y_true"]
        self.assertAlmostEqual(y[-1], 0.5, places=4)
        ku, tu = zn.identify(nd, 0.1)
        ku_a = zn.analytic_ku_tu(0.1)[1]
        self.assertLess(ku, ku_a)
        self.assertGreater(ku, 0.95 * ku_a)

    def test_table_rows(self):
        g = zn.arm_gains(10.0, 2.0)
        self.assertEqual(g["A_classic"], (6.0, 1.0, 0.25))
        self.assertAlmostEqual(g["B_no_overshoot"][0], 2.0)
        self.assertAlmostEqual(g["B_no_overshoot"][2], 2.0 / 3.0)
        self.assertEqual(g["C_p_only"], (5.0, None, None))

    def test_common_random_numbers_shared(self):
        a = zn.build_crn(); b = zn.build_crn()
        self.assertEqual(a, b)
        rng = random.Random("delay_noisy/3")
        d = rng.uniform(0.2, 0.4)
        self.assertEqual(a[("delay_noisy", 3)][0], d)
        self.assertEqual(a[("delay_noisy", 3)][1][0], rng.gauss(0.0, 0.02))

    def test_declared_regimes_printed_as_they_came(self):
        out = (ROOT / ZN_EXP).read_text()
        for s in ("paired B-A iae: 0.3162+-0.0080: clear gap", "paired B-A overshoot: -30.9996+-0.0000: clear gap",
                  "paired B-A overshoot: -31.0408+-0.2830: clear gap", "paired B-A iae: 0.7306+-0.0300: clear gap",
                  "paired C-A iae: 1.7036+-0.0972: clear gap", "stable-step criterion: 0 < A < 1"):
            self.assertIn(s, out)


class ProcessLabels(unittest.TestCase):
    def test_no_process_labels(self):
        for rel in (OP_REL, OP_EXP, ZN_REL, ZN_EXP):
            self.assertIsNone(re.search(PROCESS, (ROOT / rel).read_text()), rel)


if __name__ == "__main__":
    unittest.main()
