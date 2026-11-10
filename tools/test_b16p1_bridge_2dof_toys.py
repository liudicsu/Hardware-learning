#!/usr/bin/env python3
"""Independent contract tests for batch-16 PR1 bridge-rectifier ripple + 2DOF setpoint-weighting toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BR_REL = "examples/month-1/components/bridge_rectifier_ripple_toy.py"
SW_REL = "examples/month-3/pid-control/pid_setpoint_weighting_2dof_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


br = load("bridge_rectifier_ripple_toy", BR_REL)
sw = load("pid_setpoint_weighting_2dof_toy", SW_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((br, BR_REL), (sw, SW_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertEqual(mod.SEEDS, (0, 1, 2, 3, 4))
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1.0 + 1e-12, 1.0, 1.0 - 1e-12, 1.0, 1.0], [1.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertNotIn("seeds", v)
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("small but consistent", mod.verdict([10.5, 10.6, 10.4, 10.5, 10.5], [10.0] * 5))
            src = (ROOT / rel).read_text()
            self.assertIn("Common random numbers", src)
            self.assertIn("本页未运行", src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|control)")
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))
            self.assertEqual(mod.num(0.0), "0.0000")
            self.assertNotEqual(mod.num(-4e-5), "-0.0000")


class Bridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(BR_REL)

    def test_common_random_numbers(self):
        self.assertEqual(br.shared_draws(2), br.shared_draws(2))
        self.assertNotEqual(br.shared_draws(2), br.shared_draws(3))
        d = br.shared_draws(1)
        a, b = br.simulate("A_half", "medium", d), br.simulate("B_bridge", "medium", d)
        self.assertEqual((a["c"], a["r"]), (b["c"], b["r"]))  # same part draws in every arm

    def test_euler_stability_boundary(self):
        # Independent: the conducting node V' = -(1/(RS C) + 1/(R C)) V under forward Euler
        # decays at 0.98 h_max and grows at 1.02 h_max.
        for c, r in ((470e-6, 20.0), (220e-6 * 0.8, 15.0 * 0.9), (4700e-6, 200.0)):
            lam = 1.0 / (br.RS * c) + 1.0 / (r * c)
            h_max = br.euler_h_max(c, r)
            self.assertAlmostEqual(h_max, 2.0 / lam, delta=1e-15)
            self.assertGreater(h_max, 20 * br.DT)
            for factor, grows in ((0.98, False), (1.02, True)):
                x = 1.0
                for _ in range(3000):
                    x *= 1.0 - factor * h_max * lam
                self.assertEqual(abs(x) > 1.0, grows, factor)
                self.assertEqual(br.euler_amp(factor * h_max, c, r) > 1.0, grows)

    def test_step_halving(self):
        d = br.shared_draws(4)
        for arm in ("A_half", "B_bridge"):
            a, b = br.simulate(arm, "small_C_heavy", d), br.simulate(arm, "small_C_heavy", d, br.DT / 2)
            self.assertLess(abs(a["vdc"] - b["vdc"]), 0.01)
            self.assertLess(abs(a["ripple"] - b["ripple"]), 0.02)

    def test_no_capacitor_average(self):
        # Independent quadrature of max(0, |v| - 2 VF) R / (R + RS) over one cycle.
        d = br.shared_draws(0)
        res = br.simulate("C_noC", "medium", d)
        vpk, vf, r = br.VPK * d["amp"], d["vf"], res["r"]
        n = 200000
        avg = sum(max(0.0, abs(vpk * math.sin(2 * math.pi * k / n)) - 2 * vf) for k in range(n)) / n * r / (r + br.RS)
        self.assertAlmostEqual(res["vdc"], avg, delta=2e-3)
        self.assertAlmostEqual(res["ripple"], (vpk - 2 * vf) * r / (r + br.RS), delta=2e-3)

    def test_ripple_law_approached_from_below(self):
        # The linear-discharge law I/(k f C) ignores the conduction time, so it over-predicts;
        # as C grows (ripple shrinks) the simulated / law ratio rises towards 1.
        d = {"amp": 1.0, "c": 1.0, "r": 1.0, "vf": 0.7}
        for arm, k in (("A_half", 1.0), ("B_bridge", 2.0)):
            ratios = []
            for regime in ("medium", "large_C_light"):
                res = br.simulate(arm, regime, d)
                ratios.append(res["ripple"] / (res["vdc"] / res["r"] / (k * br.F * res["c"])))
            self.assertLess(ratios[0], ratios[1])
            self.assertLess(ratios[1], 1.0)
            self.assertGreater(ratios[1], 1.0 - br.TOL_LAW)

    def test_output_lines(self):
        self.assertEqual(self.out, (ROOT / "examples/month-1/expected/bridge_rectifier_ripple_toy.txt").read_text())
        self.assertRegex(self.out, r"small_C_heavy[\s\S]*?paired B-A ripple: -[\d.]+\+-[\d.]+: clear gap")
        self.assertRegex(self.out, r"large_C_light[\s\S]*?paired B-A vdc: -[\d.]+\+-[\d.]+: small but consistent gap")
        self.assertRegex(self.out, r"medium[\s\S]*?law B_bridge: [^\n]*within 25 %")
        self.assertRegex(self.out, r"C_noC [^\n]*not DC")
        self.assertIn("No winner declared", self.out)


class SetpointWeighting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(SW_REL)

    def test_common_random_numbers(self):
        self.assertEqual(sw.shared_draws(3), sw.shared_draws(3))
        self.assertNotEqual(sw.shared_draws(3)[3], sw.shared_draws(4)[3])

    def test_rk4_stability_boundary(self):
        lam = complex(-1.0 / sw.TM)
        h_max = sw.rk4_h_max(lam)
        self.assertGreater(h_max, 100 * sw.H)
        for factor, grows in ((0.98, False), (1.02, True)):
            z = factor * h_max * lam
            r = 1 + z + z * z / 2 + z ** 3 / 6 + z ** 4 / 24
            x = 1.0 + 0j
            for _ in range(5000):
                x *= r
                if abs(x) > 1e6:
                    break
            self.assertEqual(abs(x) > 1.0, grows, factor)

    def test_weights_do_not_enter_the_loop(self):
        # With r held constant (no setpoint steps) every arm sees the same loads and noise
        # and its integral starts at the steady-state value, so the outputs agree to rounding.
        d = sw.shared_draws(2)
        a = sw.simulate("A_1dof", "load_step", d)
        for arm in ("B_2dof", "C_aggr"):
            b = sw.simulate(arm, "load_step", d)
            for k in a:
                self.assertAlmostEqual(a[k], b[k], delta=1e-9)

    def test_preset_is_steady(self):
        c = sw.Controller(sw.gain(sw.TI0), sw.TI0, 0.5, 0.0)
        c.preset(0.3, 0.3)
        for _ in range(100):
            self.assertAlmostEqual(c.step(0.3, 0.3), 0.0, delta=1e-12)

    def test_unit_weights_reduce_to_error_pid(self):
        k = sw.gain(sw.TI0)
        p, q = sw.Controller(k, sw.TI0, 1.0, 1.0), sw.Controller(k, sw.TI0, 1.0, 1.0)
        seq = [(0.0, 0.0), (1.0, 0.0), (1.0, 0.1), (1.0, 0.4), (0.5, 0.6)]
        for r, y in seq:
            self.assertAlmostEqual(p.step(r, y), q.step(r - y, 0.0), delta=1e-9)

    def test_step_halving(self):
        d = sw.shared_draws(0)
        a = sw.simulate("B_2dof", "mixed_noise", d)
        b = sw.simulate("B_2dof", "mixed_noise", d, sub=2 * sw.SUB)
        for k in ("over", "ise_sp", "ise_load"):
            self.assertAlmostEqual(a[k], b[k], delta=1e-4 * max(1.0, abs(a[k])))

    def test_output_lines(self):
        self.assertEqual(self.out, (ROOT / "examples/month-3/expected/pid_setpoint_weighting_2dof_toy.txt").read_text())
        self.assertRegex(self.out, r"setpoint_large[\s\S]*?paired B-A over: -[\d.]+\+-[\d.]+: clear gap")
        self.assertRegex(self.out, r"load_step[\s\S]*?paired B-A ise_load: [-\d.e]+\+-[\d.e-]+: numerically zero")
        self.assertRegex(self.out, r"tiny_b[\s\S]*?paired B-A rise: [\d.]+\+-[\d.]+: clear gap")
        self.assertIn("No winner declared", self.out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
