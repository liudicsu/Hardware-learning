#!/usr/bin/env python3
"""Independent contract tests for batch-14 PR1 Kelvin four-wire + pressure-advance corner toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KV_REL = "examples/month-1/bench-multimeter/kelvin_four_wire_sense_toy.py"
PA_REL = "examples/month-3/fdm-printing/pressure_advance_corner_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


kv = load("kelvin_four_wire_sense_toy", KV_REL)
pa = load("pressure_advance_corner_toy", PA_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Labels(unittest.TestCase):
    """Both toys share one labelling rule; check it on hand-made paired data."""

    def test_order_and_thresholds(self):
        for mod in (kv, pa):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1.0 + 1e-12, 1.0, 1.0 - 1e-12, 1.0, 1.0], [1.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertNotIn("seeds", v)  # no sign count on a numerically-zero line
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("same sign on all 5 seeds", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            src = (ROOT / (KV_REL if mod is kv else PA_REL)).read_text()
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))

    def test_no_signed_zero(self):
        for mod in (kv, pa):
            self.assertEqual(mod.num(-1e-5), "-1.000e-05")
            self.assertEqual(mod.num(0.0), "0.0000")
            self.assertNotEqual(mod.num(-4e-5), "-0.0000")


class Kelvin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(KV_REL)

    def test_scope(self):
        self.assertEqual(kv.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / KV_REL).read_text()
        self.assertIn("本页未运行", text)
        self.assertIn("Common random numbers", text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
        self.assertNotRegex(text, r"\bDT\b")  # DC steady state, nothing to integrate

    def test_common_random_numbers(self):
        self.assertEqual(kv.shared_part("shunt_small_dut", 2, 5), kv.shared_part("shunt_small_dut", 2, 5))
        self.assertNotEqual(kv.shared_part("shunt_small_dut", 2, 5), kv.shared_part("shunt_small_dut", 3, 5))

    def test_ideal_meter_algebra(self):
        # Independent of the toy's helpers: zero meter error, then two-wire = R + loop, Kelvin = R up to R_IN loading.
        d = dict(kv.shared_part("shunt_small_dut", 0, 0), gain=0.0, emf=0.0, noise=0.0, null_noise=0.0, warm=0.0)
        loop = d["lead"][0] + d["lead"][1] + d["contact"][0] + d["contact"][1]
        r = d["R"]
        self.assertAlmostEqual(kv.measure("shunt_small_dut", d, "A_two_wire"), r + loop, delta=1e-10)
        self.assertAlmostEqual(kv.measure("shunt_small_dut", d, "B_kelvin"), r, delta=1e-10)
        null_loop = d["lead"][0] + d["lead"][1] + d["null_contact"][0] + d["null_contact"][1]
        self.assertAlmostEqual(kv.measure("shunt_small_dut", d, "C_nulled"), r + loop - null_loop, delta=1e-10)

    def test_zero_leads_bit_identical(self):
        for seed in kv.SEEDS:
            for part in range(kv.PARTS):
                d = kv.shared_part("zero_lead", seed, part)
                self.assertEqual(kv.measure("zero_lead", d, "A_two_wire"), kv.measure("zero_lead", d, "B_kelvin"))

    def test_output_lines(self):
        self.assertEqual(self.out, (ROOT / "examples/month-1/expected/kelvin_four_wire_sense_toy.txt").read_text())
        self.assertRegex(self.out, r"shunt_small_dut[\s\S]*paired A-B abs: [\d.]+\+-[\d.]+: clear gap")
        self.assertRegex(self.out, r"large_dut[\s\S]*paired A-B abs: [-\d.e]+\+-[\d.e-]+: near-tie")
        self.assertRegex(self.out, r"zero_lead[\s\S]*paired A-B abs: 0\.0000\+-0\.0000: tie: identical on every seed")


class PressureAdvance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(PA_REL)

    def test_scope(self):
        self.assertEqual(pa.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / PA_REL).read_text()
        self.assertIn("本页未运行", text)
        self.assertIn("Common random numbers", text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")

    def test_common_random_numbers(self):
        self.assertEqual(pa.shared_draws("sharp_corner", 1, ), pa.shared_draws("sharp_corner", 1))
        self.assertNotEqual(pa.shared_draws("sharp_corner", 1)[0], pa.shared_draws("sharp_corner", 2)[0])

    def test_euler_stability_boundary(self):
        # Linear melt (n = 1): ds/dt = -s / K.  Explicit Euler decays for DT < 2K and grows for DT > 2K.
        k = 0.05
        for factor, grows in ((0.98, False), (1.02, True)):
            dt, s = factor * 2.0 * k, 1.0
            for _ in range(400):
                s += -s / k * dt
            self.assertEqual(abs(s) > 1.0, grows, factor)

    def test_recorded_lambda_inside_bound(self):
        for regime in pa.REGIMES:
            for seed in pa.SEEDS:
                for arm in pa.ARMS:
                    self.assertLess(pa.DT * pa.run(regime, seed, arm)["lam"], 2.0)

    def test_step_halving_converged(self):
        base = pa.run("sharp_corner", 0, "B_tuned")
        old = pa.DT
        try:
            pa.DT = old / 2
            half = pa.run("sharp_corner", 0, "B_tuned")
        finally:
            pa.DT = old
        self.assertLess(abs(half["rms"] - base["rms"]), 0.05 * base["rms"])

    def test_matched_linear_advance_cancels_lag(self):
        # Independent check: n = 1 and K = K_true make s track K * k_e * v, so the corner bulge collapses.
        old = pa.shared_draws
        try:
            pa.shared_draws = lambda r, s: (0.05, 1.0, 0.0, [0.0] * 2000)
            a = pa.run("sharp_corner", 0, "A_K0")
            b = pa.run("sharp_corner", 0, "B_tuned")
        finally:
            pa.shared_draws = old
        self.assertAlmostEqual(b["k"], 0.05, places=12)
        self.assertLess(b["rms"], 0.1 * a["rms"])

    def test_constant_speed_bit_identical(self):
        for seed in pa.SEEDS:
            a, b, c = (pa.run("steady_straight", seed, arm) for arm in pa.ARMS)
            self.assertEqual((a["bulge"], a["starve"], a["rms"]), (b["bulge"], b["starve"], b["rms"]))
            self.assertEqual((a["bulge"], a["starve"], a["rms"]), (c["bulge"], c["starve"], c["rms"]))

    def test_output_lines(self):
        self.assertEqual(self.out, (ROOT / "examples/month-3/expected/pressure_advance_corner_toy.txt").read_text())
        self.assertRegex(self.out, r"sharp_corner[\s\S]*paired A-B bulge: [\d.]+\+-[\d.]+: clear gap, not a tie \(\|m\| > sd\); same sign on all 5 seeds")
        self.assertRegex(self.out, r"paired C-B starve: [\d.]+\+-[\d.]+: clear gap, not a tie \(\|m\| > sd\); same sign on all 5 seeds")
        self.assertRegex(self.out, r"steady_straight[\s\S]*paired A-B rms: 0\.0000\+-0\.0000: tie: identical on every seed")


class ExpectedFiles(unittest.TestCase):
    def test_labels_match_numbers(self):
        for rel in ("examples/month-1/expected/kelvin_four_wire_sense_toy.txt", "examples/month-3/expected/pressure_advance_corner_toy.txt"):
            text = (ROOT / rel).read_text()
            self.assertNotRegex(text, r"(?<![\d.e+])-0\.0+(?![\d.e])")
            for line in text.splitlines():
                m = re.search(r": (-?[\d.]+(?:e-?\d+)?)\+-([\d.]+(?:e-?\d+)?): ", line)
                if not m or "paired" not in line:
                    continue
                mu, sd = float(m.group(1)), float(m.group(2))
                if "near-tie" in line:
                    self.assertLessEqual(abs(mu), sd, line)
                elif "gap" in line:
                    self.assertGreater(abs(mu), sd, line)
                    self.assertRegex(line, r"same sign on all 5 seeds|1 of 5 seeds has the opposite sign|no seed has")


if __name__ == "__main__":
    unittest.main()
