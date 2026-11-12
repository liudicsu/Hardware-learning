#!/usr/bin/env python3
"""Independent contract tests for batch-19 PR2 ESP32 sleep + I2C clock-stretch toys; stdlib only."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLP_REL = "examples/month-2/esp32/esp32_light_deep_sleep_toy.py"
I2C_REL = "examples/month-2/sensors-fusion/i2c_clock_stretch_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


slp = load("esp32_light_deep_sleep_toy", SLP_REL)
i2c = load("i2c_clock_stretch_toy", I2C_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def section(out: str, start: str, end: str) -> str:
    return out.split(start)[1].split(end)[0]


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((slp, SLP_REL), (i2c, I2C_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertEqual(mod.SEEDS, (0, 1, 2, 3, 4))
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1e-16, -2e-16, 3e-16, 0.0, 1e-16], [0.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertNotIn("seeds", v)
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("small but consistent", mod.verdict([10.5, 10.6, 10.4, 10.5, 10.5], [10.0] * 5))
            self.assertIn("1 of 5 seeds has the opposite sign", mod.verdict([5.0, 5.0, 5.0, 5.0, -0.5], [0.0] * 5))
            src = (ROOT / rel).read_text()
            self.assertIn("Common random numbers", src)
            self.assertIn("本页未运行", src)
            self.assertIn("No integration step", src)
            self.assertIn("written before the first run", src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))
            self.assertFalse(any(name in vars(mod) for name in ("DT", "dt", "STEP", "rk4", "euler")))


class Esp32Sleep(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((slp.I_ACTIVE, slp.I_LIGHT, slp.I_DEEP, slp.I_BOOT), (40.0, 0.8, 0.01, 50.0))
        self.assertEqual((slp.T_WAKE_LIGHT, slp.T_BOOT_DEEP, slp.WORK), (0.001, 0.300, 0.050))
        self.assertEqual(slp.ARMS, ("A_active", "B_light", "C_deep"))
        self.assertEqual(list(slp.REGIMES), ["long_idle", "high_wake_rate", "missed_wake_source"])
        self.assertNotIn("digital_gpio", slp.WAKE_SOURCES["C_deep"])
        self.assertIn("digital_gpio", slp.WAKE_SOURCES["B_light"])

    def test_break_even_is_strict(self):
        g_ca, g_cb = slp.breakeven()
        self.assertAlmostEqual(g_ca, 0.4250, places=4)
        self.assertAlmostEqual(g_cb, 18.9839, places=4)
        # At equality the two arms tie; strictly above, C is lower.
        self.assertAlmostEqual(slp.per_cycle_charge("C_deep", g_ca), slp.per_cycle_charge("A_active", g_ca), places=9)
        self.assertLess(slp.per_cycle_charge("C_deep", g_ca + 1e-3), slp.per_cycle_charge("A_active", g_ca + 1e-3))
        self.assertGreater(slp.per_cycle_charge("C_deep", g_ca - 1e-3), slp.per_cycle_charge("A_active", g_ca - 1e-3))
        self.assertAlmostEqual(slp.per_cycle_charge("C_deep", g_cb), slp.per_cycle_charge("B_light", g_cb), places=9)
        self.assertLess(slp.per_cycle_charge("C_deep", g_cb + 1e-3), slp.per_cycle_charge("B_light", g_cb + 1e-3))

    def test_crn_and_state(self):
        a = slp.shared_timeline("missed_wake_source", 3)
        self.assertEqual(a, slp.shared_timeline("missed_wake_source", 3))
        w = slp.REGIMES["missed_wake_source"]["window"]
        rb = slp.simulate("B_light", a, w)
        rc = slp.simulate("C_deep", a, w)
        self.assertEqual(rb["missed"], 0)
        self.assertGreater(rc["missed"], 0)
        self.assertEqual(rb["ram"], rb["served"])
        self.assertEqual(rc["rtc"], rc["served"])
        self.assertLess(rc["ram"], rc["served"])
        # A source that is not enabled never wakes the chip: a single digital event is missed by C only.
        one = [(10.0, "digital_gpio")]
        self.assertEqual(slp.simulate("C_deep", one, 20.0)["missed"], 1)
        self.assertEqual(slp.simulate("B_light", one, 20.0)["missed"], 0)

    def test_expected(self):
        out = run(SLP_REL)
        self.assertIn("hand_calc break-even: C<A iff g>0.4250 s; C<B iff g>18.9839 s (strict; equality is a tie)", out)
        idle = section(out, "long_idle (", "high_wake_rate (")
        self.assertIn("paired C-A avg_mA: -39.7086+-0.0026: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", idle)
        self.assertIn("paired C-B avg_mA: -0.5417+-0.0023: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", idle)
        high = section(out, "high_wake_rate (", "missed_wake_source (")
        self.assertIn("paired C-B avg_mA: 21.1306+-0.2356: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", high)
        self.assertIn("paired C-A avg_mA: -9.9044+-0.2135: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", high)
        miss = section(out, "missed_wake_source (", "alternative ")
        self.assertIn("paired C-B missed: 122.0000+-10.3199: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", miss)
        for reg in (idle, high, miss):
            self.assertIn("state_check: B ram==served and rtc==served on every seed: True; C rtc==served on every seed: True; C ram<served (RAM lost) on every seed: True", reg)
        self.assertIn("alternative I_BOOT=40.0 mA (= I_ACTIVE) on high_wake_rate (same seeds; C-vs-A break-even g>0.3500 s):", out)
        self.assertIn("alternative T_BOOT_DEEP=0.100 s on high_wake_rate (same seeds; C-vs-A break-even g>0.1750 s):", out)
        self.assertIn("declared toy currents, not datasheet values", out)
        self.assertEqual((ROOT / "examples/month-2/expected/esp32_light_deep_sleep_toy.txt").read_text(), out)


class I2cStretch(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(i2c.T_BIT_US, 10.0)
        self.assertGreaterEqual(i2c.T_HIGH_US, 4.0)
        self.assertEqual(len(i2c.early_bits(2.5)), 0)
        self.assertEqual(len(i2c.early_bits(2.5001)), 1)
        self.assertEqual(len(i2c.early_bits(0.0)), 0)
        tx = {"data": [0xA5] * i2c.N_BYTES, "garbage": [0x5A] * i2c.N_BYTES,
              "stretch": [0.0] + [i2c.TIMEOUT_US] * (i2c.N_BYTES - 1)}
        self.assertEqual(i2c.run_tx("C_timeout", tx)["aborted"], 0)
        tx["stretch"] = [0.0] + [i2c.TIMEOUT_US + 0.001] * (i2c.N_BYTES - 1)
        r = i2c.run_tx("C_timeout", tx)
        self.assertEqual((r["aborted"], r["lost"]), (1, i2c.N_BYTES - 1))
        self.assertEqual(i2c.run_tx("B_wait", tx)["errors"], 0)
        self.assertGreater(i2c.run_tx("A_ignore", tx)["errors"], 0)

    def test_crn(self):
        self.assertEqual(i2c.shared_bus("moderate_stretch", 2), i2c.shared_bus("moderate_stretch", 2))
        self.assertEqual(list(i2c.REGIMES), ["no_stretch", "moderate_stretch", "overtime_stretch"])

    def test_expected(self):
        out = run(I2C_REL)
        self.assertIn("hand_calc bit rate: 1/T_BIT = 1/10.0 us = 100.0 kHz", out)
        self.assertIn("timeout_rule: C aborts iff stretch > TIMEOUT_US (strict); stretch=200.0000 us aborts=0; stretch=200.0010 us aborts=1", out)
        none = section(out, "no_stretch (", "moderate_stretch (")
        for line in none.strip().splitlines():
            if "paired" in line:
                self.assertIn("0.0000+-0.0000: tie: identical on every seed", line)
        mod = section(out, "moderate_stretch (", "overtime_stretch (")
        self.assertIn("paired A-B bad_rate: 0.8681+-0.0111: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", mod)
        self.assertIn("paired C-B bad_rate: 0.0000+-0.0000: tie: identical on every seed", mod)
        self.assertIn("paired B-A bus_ms: 12.0501+-0.1307: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", mod)
        over = section(out, "overtime_stretch (", "alternative ")
        self.assertIn("paired C-B bad_rate: 0.9375+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", over)
        self.assertIn("paired C-B aborts: 20.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", over)
        self.assertIn("alternative TIMEOUT_US=1000.0 on overtime_stretch (same seeds):", out)
        self.assertIn("alternative TIMEOUT_US=50.0 on moderate_stretch (same seeds):", out)
        self.assertIn("paired C-B bad_rate@alt: 0.7800+-0.0216: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertEqual((ROOT / "examples/month-2/expected/i2c_clock_stretch_toy.txt").read_text(), out)


if __name__ == "__main__":
    unittest.main()
