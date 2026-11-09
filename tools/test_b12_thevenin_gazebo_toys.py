#!/usr/bin/env python3
"""Independent contract tests for batch-12 PR1 Thevenin + Gazebo step-size toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import random
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TH_REL = "examples/month-1/ohms-law/thevenin_loaded_divider_toy.py"
GZ_REL = "examples/month-4/gazebo-sim/gazebo_step_contact_stability_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


th = load("thevenin_loaded_divider_toy", TH_REL)
gz = load("gazebo_step_contact_stability_toy", GZ_REL)


def run(rel: str) -> str:
    return subprocess.run(
        [sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True
    ).stdout


class Thevenin(unittest.TestCase):
    def test_constants_and_seeds(self):
        self.assertGreaterEqual(len(th.SEEDS), 5)
        self.assertEqual(th.SEEDS, (0, 1, 2, 3, 4))
        self.assertEqual((th.R1_NOM, th.R2_NOM, th.VS), (10_000.0, 4_700.0, 5.0))
        self.assertIn("本页未运行", (ROOT / TH_REL).read_text())

    def test_theorem_against_independent_nodal_solve(self):
        rng = random.Random(123)
        for _ in range(200):
            vs, r1, r2, rl = rng.uniform(1, 12), rng.uniform(100, 1e5), rng.uniform(100, 1e5), rng.uniform(10, 1e7)
            vth, rth = th.thevenin(vs, r1, r2)
            # independent: mesh current through R1 with R2||RL below it
            rb = r2 * rl / (r2 + rl)
            v_mesh = vs * rb / (r1 + rb)
            self.assertAlmostEqual(vth * rl / (rth + rl), v_mesh, delta=1e-12 * vs)
            self.assertAlmostEqual(th.truth_kcl(vs, r1, r2, rl), v_mesh, delta=1e-12 * vs)
            i_n = vth / rth  # Norton twin
            self.assertAlmostEqual(i_n * th.parallel(rth, rl), v_mesh, delta=1e-12 * vs)

    def test_lesson_numbers(self):
        vth, rth = th.thevenin(5.0, 10_000.0, 4_700.0)
        self.assertAlmostEqual(vth, 1.5986, places=4)
        self.assertAlmostEqual(rth, 3197.3, places=1)
        self.assertAlmostEqual(vth * 1e4 / (rth + 1e4), 1.2113, places=4)

    def test_common_random_numbers(self):
        a = th.shared_board(2, 5, 3_300.0)
        b = th.shared_board(2, 5, 3_300.0)
        self.assertEqual(a, b)
        # every arm reads the same Voc: with RL -> infinity B and C collapse onto A
        big = dict(a, rl=1e18)
        va = th.predict("A_voc_only", big)
        self.assertAlmostEqual(th.predict("B_thevenin", big), va, delta=1e-9)
        self.assertAlmostEqual(th.predict("C_norton", big), va, delta=1e-9)

    def test_norton_equals_thevenin_without_burden(self):
        old = (th.R_BURDEN, th.I_NOISE, th.V_NOISE, th.TOL)
        try:
            th.R_BURDEN, th.I_NOISE, th.V_NOISE, th.TOL = 0.0, 0.0, 0.0, 0.0
            res = th.run_regime(3_300.0)
            for arm in ("B_thevenin", "C_norton"):
                self.assertLess(max(res[arm]), 1e-9)
        finally:
            th.R_BURDEN, th.I_NOISE, th.V_NOISE, th.TOL = old

    def test_regimes(self):
        heavy = th.run_regime(3_300.0)
        light = th.run_regime(10_000_000.0)
        mean = lambda xs: sum(xs) / len(xs)  # noqa: E731
        self.assertGreater(mean(heavy["A_voc_only"]), 100 * mean(heavy["B_thevenin"]))
        self.assertGreater(mean(heavy["C_norton"]), mean(heavy["B_thevenin"]))
        gap = mean(light["A_voc_only"]) - mean(light["B_thevenin"])
        self.assertGreater(gap, 0.0)  # not a tie
        self.assertLess(gap, 0.3)  # but a small gap (mV)
        ab = [x - y for x, y in zip(light["A_voc_only"], light["B_thevenin"])]
        self.assertTrue(all(d > 0 for d in ab))  # consistent: A worse on every seed
        cb = [x - y for x, y in zip(light["C_norton"], light["B_thevenin"])]
        m = sum(cb) / len(cb)
        sd = math.sqrt(sum((d - m) ** 2 for d in cb) / (len(cb) - 1))
        self.assertLess(abs(m), sd)  # B vs C within seed noise
        self.assertGreater(abs(m), 0.0)  # but not identical

    def test_expected_file(self):
        exp = (ROOT / "examples/month-1/expected/thevenin_loaded_divider_toy.txt").read_text()
        self.assertEqual(run(TH_REL), exp)
        bc = next(line for line in exp.splitlines() if line.startswith("light_load B vs C:"))
        ab = next(line for line in exp.splitlines() if line.startswith("light_load A vs B:"))
        self.assertIn("near-tie / small gap, within seed noise", bc)
        self.assertNotIn("not a tie", bc)
        self.assertIn("small but consistent gap, not a tie", ab)
        self.assertNotIn("near-tie", ab)


def free_oscillation(dt: float, steps: int, explicit: bool) -> float:
    """Bilateral spring-damper, no gravity; returns final/initial energy-like amplitude."""
    x, v = 1e-3, 0.0
    for _ in range(steps):
        a = (-gz.K * x - gz.C * v) / gz.M
        if explicit:
            x, v = x + dt * v, v + dt * a
        else:
            v = v + dt * a
            x = x + dt * v
    return math.hypot(x * gz.OMEGA, v) / (1e-3 * gz.OMEGA)


class GazeboStep(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(gz.SEEDS, (0, 1, 2, 3, 4))
        self.assertEqual([dt for _, dt in gz.ARMS], [3e-3, 1e-3, 1e-4])
        self.assertAlmostEqual(gz.OMEGA, 500.0)
        self.assertIn("本页未运行", (ROOT / GZ_REL).read_text())

    def test_closed_form_limits(self):
        self.assertAlmostEqual(gz.si_euler_limit(0.0), 2.0)
        for z in (0.0, 0.1, 0.2, 0.5, 1.0):
            w = gz.si_euler_limit(z)
            self.assertAlmostEqual(w * w + 4 * z * w, 4.0, places=12)
        self.assertAlmostEqual(gz.explicit_euler_limit(0.2), 0.4)

    def test_criterion_numerically(self):
        lim = gz.si_euler_limit() / gz.OMEGA
        self.assertLess(gz.spectral_radius_si(0.99 * lim), 1.0)
        self.assertGreater(gz.spectral_radius_si(1.01 * lim), 1.0)
        self.assertLess(free_oscillation(0.98 * lim, 3000, explicit=False), 1.0)
        self.assertGreater(free_oscillation(1.02 * lim, 3000, explicit=False), 1e3)
        elim = gz.explicit_euler_limit() / gz.OMEGA
        self.assertLess(free_oscillation(0.9 * elim, 3000, explicit=True), 1.0)
        self.assertGreater(free_oscillation(1e-3, 3000, explicit=True), 1e3)  # 1 ms explicit diverges
        for _, dt in gz.ARMS:
            self.assertLess(gz.spectral_radius_si(dt), 1.0)  # every arm is stable

    def test_common_random_numbers_and_impulse(self):
        h0a, fa = gz.shared_draws(3, "impact_drop", 0.6)
        h0b, fb = gz.shared_draws(3, "impact_drop", 0.6)
        self.assertEqual((h0a, fa), (h0b, fb))
        prefix = gz.impulse_prefix(fa)
        total = gz.impulse_until(fa, prefix, 0.6)
        for _, dt in gz.ARMS + (("ref", gz.REF_DT),):
            n = int(round(0.6 / dt))
            s = sum(
                gz.impulse_until(fa, prefix, (k + 1) * dt) - gz.impulse_until(fa, prefix, k * dt)
                for k in range(n)
            )
            self.assertAlmostEqual(s, total, delta=1e-9)

    def test_regimes(self):
        imp = gz.run_regime("impact_drop", 0.6)
        rest = gz.run_regime("gentle_rest", 0.2)
        mean = lambda xs: sum(xs) / len(xs)  # noqa: E731
        a, b, c = (mean(imp[n]["pen_err_um"]) for n, _ in gz.ARMS)
        self.assertGreater(a, b)
        self.assertGreater(b, c)
        sag_um = gz.M * gz.G / gz.K * 1e6
        for n, _ in gz.ARMS:
            self.assertEqual(rest[n]["bounces"], [0.0] * len(gz.SEEDS))
            self.assertLess(mean(rest[n]["pen_err_um"]), 0.05 * sag_um)
        self.assertGreater(mean(rest["A_coarse_3ms"]["pen_err_um"]), 0.0)  # not a tie
        ref_cor = [r["cor"] for r in imp["_ref"]]
        analytic = math.exp(-gz.ZETA * math.pi / math.sqrt(1 - gz.ZETA**2))
        for x in ref_cor:
            self.assertLess(abs(x - analytic), 0.02)

    def test_expected_file(self):
        exp = (ROOT / "examples/month-4/expected/gazebo_step_contact_stability_toy.txt").read_text()
        self.assertEqual(run(GZ_REL), exp)
        self.assertIn("near-tie / small gap, not a tie", exp)
        self.assertIn("UNSTABLE", exp)


if __name__ == "__main__":
    unittest.main(verbosity=1)
