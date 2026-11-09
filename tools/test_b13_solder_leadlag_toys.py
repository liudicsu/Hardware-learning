#!/usr/bin/env python3
"""Independent contract tests for batch-13 PR1 soldering thermal-window + lead-lag toys; stdlib only."""
from __future__ import annotations

import cmath
import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SO_REL = "examples/month-1/soldering/soldering_thermal_window_toy.py"
LL_REL = "examples/month-3/pid-control/lead_lag_vs_pid_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


so = load("soldering_thermal_window_toy", SO_REL)
ll = load("lead_lag_vs_pid_toy", LL_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def lines_with(out: str, *keys: str) -> list[str]:
    return [l for l in out.splitlines() if all(k in l for k in keys)]


class Soldering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(SO_REL)

    def test_constants_seeds_scope(self):
        self.assertEqual(so.SEEDS, (0, 1, 2, 3, 4))
        self.assertEqual([d for _, d in so.ARMS], [1.0, 3.0, 8.0])
        text = (ROOT / SO_REL).read_text()
        self.assertIn("本页未运行", text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")

    def test_common_random_numbers(self):
        spec = so.REGIMES[0]
        self.assertEqual(so.shared_joint(spec[0], 3, 7, spec), so.shared_joint(spec[0], 3, 7, spec))
        self.assertNotEqual(so.shared_joint(spec[0], 3, 7, spec), so.shared_joint(spec[0], 4, 7, spec))

    def test_steady_state_matches_conductance_divider(self):
        # Independent check: with the iron held forever the joint settles where heat in = heat out.
        jt = {"c_j": 0.2, "g_loss": 0.05, "oxide": 0.0, "t_wet": 0.5, "d_crit": 1e9}
        old = so.T_COOL
        try:
            so.T_COOL = 0.0
            r = so.solder(60.0, 183.0, 340.0, 1.0, jt)
        finally:
            so.T_COOL = old
        # tip regulated: P = K (Tset - Tt) balances G_c (Tt - Tj) + G_AIR (Tt - T_AMB); joint balances G_c vs G_loss.
        g_c, k, ga, gl, ta, ts = so.G_CLEAN, so.K_HEAT, so.G_AIR, 0.05, so.T_AMB, 340.0
        # solve 2x2 linear system
        a11, a12, b1 = k + g_c + ga, -g_c, k * ts + ga * ta
        a21, a22, b2 = -g_c, g_c + gl, gl * ta
        det = a11 * a22 - a12 * a21
        tj = (a11 * b2 - a21 * b1) / det
        self.assertAlmostEqual(r["peak"], tj, delta=0.05)

    def test_euler_stability_bound(self):
        lam = so.lambda_max(0.10, so.G_CLEAN, 0.04)
        self.assertLess(so.DT, 2.0 / lam)
        # Independent: explicit Euler on the linear two-node system decays below 2/lambda and blows up above it.
        def euler_growth(dt, n=400):
            c_j, g_c, g_l = 0.10, so.G_CLEAN, 0.04
            x = [1.0, -1.0]
            for _ in range(n):
                dt_t = -((g_c + so.G_AIR + so.K_HEAT) * x[0] - g_c * x[1]) / so.C_TIP
                dt_j = -(-g_c * x[0] + (g_c + g_l) * x[1]) / c_j
                x = [x[0] + dt * dt_t, x[1] + dt * dt_j]
            return max(abs(v) for v in x)
        self.assertLess(euler_growth(0.98 * 2 / lam), 1.0)
        self.assertGreater(euler_growth(1.02 * 2 / lam), 1.0)

    def test_dt_convergence(self):
        spec = so.REGIMES[1]
        jt = so.shared_joint(spec[0], 0, 0, spec)
        a = so.solder(3.0, spec[2], spec[3], spec[7], jt)
        old = so.DT
        try:
            so.DT = old / 2
            b = so.solder(3.0, spec[2], spec[3], spec[7], jt)
        finally:
            so.DT = old
        self.assertAlmostEqual(a["peak"], b["peak"], delta=0.1)
        self.assertAlmostEqual(a["dose"], b["dose"], delta=0.01 * max(1.0, b["dose"]))

    def test_labels_match_numbers(self):
        out = self.out
        self.assertTrue(lines_with(out, "paired A-B cold: 0.7700+-0.0737: clear gap", "same sign on all 5 seeds"))
        self.assertTrue(lines_with(out, "paired C-B lift: 0.9750+-0.0177: clear gap", "same sign on all 5 seeds"))
        # matched_clean: A and B identical on every seed for cold and lift
        idx = out.index("matched_clean")
        tail = out[idx:]
        self.assertIn("paired A-B cold: 0.0000+-0.0000: tie: identical on every seed", tail)
        self.assertIn("paired A-B lift: 0.0000+-0.0000: tie: identical on every seed", tail)
        for line in out.splitlines():
            self.assertNotRegex(line, r"(?<![+\d])-0\.0+(?![\d.])")
            if "near-tie" in line:
                m, s = map(float, line.split(": ")[1].split("+-"))
                self.assertLessEqual(abs(m), s)
            if "consistent gap" in line or "clear gap" in line:
                m, s = map(float, line.split(": ")[1].split("+-"))
                self.assertGreater(abs(m), s)
                self.assertRegex(line, r"same sign on all 5 seeds|of 5 seeds ha")

    def test_reflow_reader(self):
        self.assertIn("profile_ok: ramp 2.08 C/s", self.out)
        self.assertIn("TAL 50 s", self.out)
        self.assertIn("TAL < 30 s", self.out)


class LeadLag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(LL_REL)

    def test_constants_seeds_scope(self):
        self.assertEqual(ll.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / LL_REL).read_text()
        self.assertIn("本页未运行", text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|control)")

    def test_lead_and_lag_definitions(self):
        (z, p), (z2, p2) = ll.sections("B_leadlag")
        self.assertLess(abs(z), abs(p))  # lead
        self.assertGreater(abs(z2), abs(p2))  # lag
        # maximum lead phase PHI at sqrt(z p) = WC
        ph = math.degrees(cmath.phase((1j * ll.WC / z + 1) / (1j * ll.WC / p + 1)))
        self.assertAlmostEqual(ph, 30.0, places=6)
        (zc, pc), _ = ll.sections("C_swapped")
        self.assertEqual((zc, pc), (p, z))

    def test_shared_crossover(self):
        for _, wr, zr in ll.REGIMES:
            for arm in ll.ARMS:
                loop = ll.gain(arm, wr, zr) * ll.shape(arm, ll.WC) * ll.plant(ll.WC, wr, zr)
                self.assertAlmostEqual(abs(loop), 1.0, places=12)

    def test_tustin_section_matches_continuous_at_low_frequency(self):
        c = ll.Controller("B_leadlag", 1.0)
        b0, b1, a1, _, _ = c.secs[0]
        z, p = ll.sections("B_leadlag")[0]
        w = 2.0
        zz = cmath.exp(1j * w * ll.TS)
        disc = (b0 + b1 / zz) / (1 + a1 / zz)
        cont = (1j * w / z + 1) / (1j * w / p + 1)
        self.assertLess(abs(disc - cont), 1e-4)
        self.assertAlmostEqual((b0 + b1) / (1 + a1), 1.0, places=12)  # DC gain 1

    def test_rk4_stability_and_convergence(self):
        for _, wr, zr in ll.REGIMES:
            for lam in ll.modes(wr, zr):
                self.assertLess(ll.rk4_amp(ll.H * lam), 1.0)
                hm = ll.rk4_h_max(lam)
                self.assertLess(ll.rk4_amp(0.98 * hm * lam), 1.0)
                self.assertGreater(ll.rk4_amp(1.02 * hm * lam), 1.0)
        self.assertAlmostEqual(ll.rk4_h_max(complex(-1.0, 0.0)), 2.785293563, places=6)
        dr = ll.shared_draws(0)
        a = ll.simulate("B_leadlag", 40.0, 0.3, dr, sub=4)
        b = ll.simulate("B_leadlag", 40.0, 0.3, dr, sub=8)
        for k in a:
            self.assertAlmostEqual(a[k], b[k], delta=1e-6 * max(1.0, abs(b[k])))

    def test_common_random_numbers(self):
        self.assertEqual(ll.shared_draws(3), ll.shared_draws(3))
        self.assertNotEqual(ll.shared_draws(3)[2], ll.shared_draws(4)[2])

    def test_regime_margins(self):
        pm_a, _ = ll.margins("A_pid", 40.0, 0.3)
        pm_b, gm_b = ll.margins("B_leadlag", 40.0, 0.3)
        _, gm_a = ll.margins("A_pid", 40.0, 0.3)
        self.assertGreater(pm_b, pm_a)
        self.assertLess(gm_b, gm_a)
        self.assertLess(ll.margins("B_leadlag", 40.0, 0.2)[0], 0.0)

    def test_labels_match_numbers(self):
        out = self.out
        self.assertTrue(lines_with(out, "resonant paired B-A ise: -2.8025+-0.6749: small but consistent gap", "same sign on all 5 seeds"))
        self.assertTrue(lines_with(out, "well_damped paired B-A ise: 0.7150+-0.1951: small but consistent gap", "same sign on all 5 seeds"))
        self.assertTrue(lines_with(out, "well_damped paired B-A over: 0.0058+-0.1814: near-tie", "3 of 5 seeds have the opposite sign"))
        self.assertIn("resonant_light B_leadlag diverged (|y| > 10 rad) on 5 of 5 seeds", out)
        for line in out.splitlines():
            self.assertNotRegex(line, r"(?<![+\d])-0\.0+(?![\d.])")
            if " paired " in line and "+-" in line:
                m, s = map(float, line.split(": ")[1].split("+-"))
                if "near-tie" in line:
                    self.assertLessEqual(abs(m), s)
                else:
                    self.assertGreater(abs(m), s)
                self.assertRegex(line, r"same sign on all 5 seeds|of 5 seeds ha")


if __name__ == "__main__":
    unittest.main(verbosity=1)
