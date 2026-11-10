#!/usr/bin/env python3
"""Independent contract tests for batch-17 PR1 interference-fit + QoS deadline/lifespan toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PF_REL = "examples/month-3/cad-parametric/interference_press_fit_toy.py"
QS_REL = "examples/month-4/ros2-graph/qos_deadline_lifespan_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pf = load("interference_press_fit_toy", PF_REL)
qs = load("qos_deadline_lifespan_toy", QS_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((pf, PF_REL), (qs, QS_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertEqual(mod.SEEDS, (0, 1, 2, 3, 4))
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1e-16, -2e-16, 3e-16, 0.0, 1e-16], [0.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertNotIn("seeds", v)
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("1 of 5 seeds has the opposite sign", mod.verdict([5.0, 5.0, 5.0, 5.0, -0.5], [0.0] * 5))
            src = (ROOT / rel).read_text()
            self.assertIn("Common random numbers", src)
            self.assertIn("本页未运行", src)
            self.assertIn("No integration step", src)
            self.assertIn("written before the first run", src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))


class PressFit(unittest.TestCase):
    def test_pressure_formula_by_hand(self):
        # p = E delta / (2 d) (1 - (d/D)^2): 200000 * 0.025 / 40 * 0.75 = 93.75 MPa
        self.assertAlmostEqual(pf.pressure(0.025), 93.75, places=9)
        self.assertEqual(pf.pressure(-0.02), 0.0)
        self.assertAlmostEqual(pf.K_HOOP, (40.0 ** 2 + 20.0 ** 2) / (40.0 ** 2 - 20.0 ** 2), places=12)
        self.assertAlmostEqual(pf.P_YIELD * pf.K_HOOP, pf.SIGMA_Y, places=9)
        self.assertAlmostEqual(pf.axial_force(100.0), 0.15 * 100.0 * math.pi * 20.0 * 15.0, places=6)
        self.assertAlmostEqual(pf.torque(100.0), pf.axial_force(100.0) * 0.01, places=9)

    def test_interference_sign_and_shrink(self):
        part = (0.0, 0.0, 40.0, [10.0] * 5)
        a = pf.part_result("A_clear", part, 150.0)
        b = pf.part_result("B_fit", part, 150.0)
        c = pf.part_result("C_heavy", part, 0.0)
        self.assertAlmostEqual(a["delta"], -0.020, places=12)
        self.assertAlmostEqual(b["delta"], 0.025, places=12)
        self.assertAlmostEqual(c["delta"], 0.070, places=12)
        # shrink: bore grows by alpha * dT * d = 0.036 mm, so B assembles with no force
        self.assertAlmostEqual(b["hot"], 0.025 - 12e-6 * 150.0 * 20.0, places=12)
        self.assertEqual(b["press"], 0.0)
        self.assertEqual(a["press"], 0.0)
        self.assertGreater(c["press"], 0.0)
        self.assertEqual(c["yield"], 100.0)
        self.assertEqual(b["yield"], 0.0)

    def test_crn_and_no_time_step(self):
        d1 = pf.shared_draws("loaded_vibration", 3)
        d2 = pf.shared_draws("loaded_vibration", 3)
        self.assertEqual(d1, d2)
        self.assertFalse(any(name in vars(pf) for name in ("DT", "dt", "STEP", "rk4", "euler")))

    def test_declared_regimes(self):
        self.assertEqual(list(pf.REGIMES), ["loaded_vibration", "no_load", "press_no_oven"])
        out = run(PF_REL)
        self.assertIn("paired B-A slip: -25.4300+-4.5789: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        no_load = out.split("no_load (")[1].split("press_no_oven (")[0]
        self.assertIn("paired B-A slip: 0.0000+-0.0000: tie: identical on every seed", no_load)
        self.assertIn("paired B-A press: 0.0000+-0.0000: tie: identical on every seed", no_load)
        press = out.split("press_no_oven (")[1]
        self.assertIn("paired B-A press: 13.2461+-0.3928: clear gap", press)
        self.assertEqual((ROOT / "examples/month-3/expected/interference_press_fit_toy.txt").read_text(), out)


class Qos(unittest.TestCase):
    def test_compatibility_table(self):
        self.assertTrue(qs.compatible(None, None))
        self.assertFalse(qs.compatible(None, 20))
        self.assertTrue(qs.compatible(20, None))
        self.assertTrue(qs.compatible(20, 20))
        self.assertTrue(qs.compatible(5, 20))
        self.assertFalse(qs.compatible(20, 5))
        for arm in ("B_dl", "C_tight"):
            dl = qs.QOS[arm][0]
            self.assertTrue(qs.compatible(dl, dl))

    def test_deadline_and_lifespan_by_hand(self):
        ms = qs.MS
        samples = [(10 * ms, 12 * ms), (20 * ms, 22 * ms), (30 * ms, 45 * ms), (40 * ms, 42 * ms), (90 * ms, 92 * ms)]
        ticks = [15 * ms, 25 * ms, 35 * ms, 47 * ms, 70 * ms, 95 * ms]
        a = qs.run_arm("A_rel", (samples, ticks))
        b = qs.run_arm("B_dl", (samples, ticks))
        # lifespan 10 ms drops the sample delayed by 15 ms; A keeps it (newest stamp rule)
        self.assertEqual(b["drop"], 1.0)
        self.assertEqual(a["drop"], 0.0)
        # B accepted receptions at 12, 22, 42, 92 ms: gaps 10, 20, 50 -> misses 0, 0 (equal is not a miss),
        # and 2 (at 62 and 82 ms)
        self.assertEqual(b["miss"], 2.0)
        # tick 70 ms: B's last reception was 42 ms, 28 > 20 -> hold; A acts on the 40 ms sample (age 30 > 25 -> stale)
        self.assertEqual(b["hold"], 100.0 / 6)
        self.assertEqual(a["stale"], 100.0 / 6)
        self.assertEqual(b["stale"], 0.0)

    def test_integer_times_no_time_step(self):
        for regime in qs.REGIMES:
            samples, ticks = qs.shared_draws(regime, 0)
            self.assertTrue(all(isinstance(t, int) and isinstance(r, int) and r > t for t, r in samples))
            self.assertTrue(all(isinstance(t, int) for t in ticks))
        self.assertEqual(qs.shared_draws("late_sensor", 2), qs.shared_draws("late_sensor", 2))

    def test_declared_regimes(self):
        self.assertEqual(list(qs.REGIMES), ["late_sensor", "on_time", "lossy_reliable"])
        out = run(QS_REL)
        late = out.split("late_sensor (")[1].split("on_time (")[0]
        self.assertIn("paired B-A stale: -6.6633+-1.6806: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", late)
        on_time = out.split("on_time (")[1].split("lossy_reliable (")[0]
        for key in ("stale", "hold", "age"):
            self.assertIn(f"paired B-A {key}: 0.0000+-0.0000: tie: identical on every seed", on_time)
        lossy = out.split("lossy_reliable (")[1]
        self.assertIn("paired B-A hold: 2.7814+-0.3652: clear gap", lossy)
        self.assertIn("paired B-A stale: -1.0705+-0.1824: clear gap", lossy)
        self.assertEqual((ROOT / "examples/month-4/expected/qos_deadline_lifespan_toy.txt").read_text(), out)


if __name__ == "__main__":
    unittest.main()
