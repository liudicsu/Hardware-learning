#!/usr/bin/env python3
"""Independent contract tests for batch-11 PR2 gear η + discrete LQR toys."""
from __future__ import annotations

import importlib.util
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


gear = load(
    "gear_efficiency_load_toy",
    "examples/month-3/transmissions/gear_efficiency_load_toy.py",
)
dlqr = load(
    "discrete_lqr_zoh_toy",
    "examples/month-5/state-space-lqr/discrete_lqr_zoh_toy.py",
)


class GearEta(unittest.TestCase):
    def test_shared_seeds_and_markers(self):
        self.assertEqual(len(gear.SEEDS), 5)
        src = (
            ROOT / "examples/month-3/transmissions/gear_efficiency_load_toy.py"
        ).read_text()
        self.assertIn("shared_friction", src)
        self.assertIn("Coulomb", src)
        self.assertIn("本页未运行", src)
        self.assertIn("near-tie", src)

    def test_identical_friction_across_arms_per_seed(self):
        for seed in gear.SEEDS:
            frics = {}
            for arm in gear.ARMS:
                *_, tau_c, b_v = gear.metrics_for("heavy_load", arm, seed)
                frics[arm] = (tau_c, b_v)
            self.assertEqual(frics["A_constant_eta"], frics["B_coulomb_viscous"])
            self.assertEqual(frics["B_coulomb_viscous"], frics["C_heavy_fit_eta"])

    def test_heavy_near_tie_light_gap(self):
        eta_gaps, light_errs = [], []
        for seed in gear.SEEDS:
            ea, *_ = gear.metrics_for("heavy_load", "A_constant_eta", seed)
            eb, *_ = gear.metrics_for("heavy_load", "B_coulomb_viscous", seed)
            eta_gaps.append(abs(ea - eb))
            err_a, = [gear.metrics_for("light_load", "A_constant_eta", seed)[1]]
            light_errs.append(err_a)
        self.assertLess(sum(eta_gaps) / 5, 0.02)  # near-tie, not huge
        self.assertGreater(sum(light_errs) / 5, 1.0)  # clear light-load gap

    def test_c_matches_b_on_heavy_by_construction(self):
        for seed in gear.SEEDS:
            err_c = gear.metrics_for("heavy_load", "C_heavy_fit_eta", seed)[1]
            self.assertAlmostEqual(err_c, 0.0, places=12)


class DiscreteLqr(unittest.TestCase):
    def test_shared_seeds_and_markers(self):
        self.assertEqual(len(dlqr.SEEDS), 5)
        src = (
            ROOT / "examples/month-5/state-space-lqr/discrete_lqr_zoh_toy.py"
        ).read_text()
        self.assertIn("zoh_discretize", src)
        self.assertIn("RICCATI_TOL", src)
        self.assertIn("expm", src)
        self.assertIn("本页未运行", src)
        self.assertIn("near-tie", src)

    def test_identical_noise_series_across_arms_per_seed(self):
        for seed in dlqr.SEEDS:
            n0 = dlqr.shared_noise_series(seed)
            n1 = dlqr.shared_noise_series(seed)
            self.assertEqual(n0, n1)
            # Arms consume the same series object content
            Kc = dlqr.design_cont_K()
            Kd, *_ = dlqr.design_disc_K(dlqr.TS_COARSE)
            c0, _, used0 = dlqr.simulate(Kc, dlqr.TS_COARSE, seed, noise=n0)
            c1, _, used1 = dlqr.simulate(Kd, dlqr.TS_COARSE, seed, noise=n0)
            self.assertIs(used0, n0)
            self.assertIs(used1, n0)
            self.assertNotEqual(c0, c1)  # different K, same noise

    def test_stability_moduli_lt_one(self):
        for ts in (dlqr.TS_COARSE, dlqr.TS_FINE):
            _, rho, n_it, _, _ = dlqr.design_disc_K(ts)
            self.assertLess(rho, 1.0)
            self.assertGreater(n_it, 1)

    def test_zoh_not_forward_euler(self):
        # Forward-Euler Ad = I + Ac*Ts differs from expm ZOH for coarse Ts
        Ad, Bd = dlqr.zoh_discretize(dlqr.A_C, dlqr.B_C, dlqr.TS_COARSE)
        fe = [
            [
                (1.0 if i == j else 0.0) + dlqr.TS_COARSE * dlqr.A_C[i][j]
                for j in range(2)
            ]
            for i in range(2)
        ]
        self.assertGreater(
            abs(Ad[0][1] - fe[0][1]) + abs(Ad[1][1] - fe[1][1]), 1e-4
        )

    def test_coarse_gap_fine_near_tie(self):
        Kc = dlqr.design_cont_K()
        Kd_c, *_ = dlqr.design_disc_K(dlqr.TS_COARSE)
        Kd_f, *_ = dlqr.design_disc_K(dlqr.TS_FINE)
        coarse_gaps, fine_gaps = [], []
        for seed in dlqr.SEEDS:
            noise = dlqr.shared_noise_series(seed)
            ca, _, _ = dlqr.simulate(Kc, dlqr.TS_COARSE, seed, noise=noise)
            cb, _, _ = dlqr.simulate(Kd_c, dlqr.TS_COARSE, seed, noise=noise)
            coarse_gaps.append(ca - cb)
            fa, _, _ = dlqr.simulate(Kc, dlqr.TS_FINE, seed, noise=noise)
            fb, _, _ = dlqr.simulate(Kd_f, dlqr.TS_FINE, seed, noise=noise)
            fine_gaps.append(abs(fa - fb))
        self.assertGreater(sum(coarse_gaps) / 5, 0.2)
        self.assertLess(sum(fine_gaps) / 5, 0.05)

    def test_step_size_stability(self):
        """Halving SUBSTEP should not change cost by more than a small relative amount."""
        Kc = dlqr.design_cont_K()
        old = dlqr.SUBSTEP
        try:
            noise = dlqr.shared_noise_series(0)
            c1, _, _ = dlqr.simulate(Kc, dlqr.TS_FINE, 0, noise=noise)
            dlqr.SUBSTEP = old / 2
            # rebuild noise length for new substep
            noise2 = dlqr.shared_noise_series(0)
            c2, _, _ = dlqr.simulate(Kc, dlqr.TS_FINE, 0, noise=noise2)
            self.assertLess(abs(c1 - c2) / max(c1, 1e-9), 0.05)
        finally:
            dlqr.SUBSTEP = old


if __name__ == "__main__":
    unittest.main()
