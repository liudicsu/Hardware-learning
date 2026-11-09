#!/usr/bin/env python3
"""Independent contract tests for batch-10 PR2 toys; stdlib only."""
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


esd = load("esd_tvs_clamp_toy", "examples/month-1/components/esd_tvs_clamp_toy.py")
gl = load(
    "ground_loop_return_ir_toy",
    "examples/month-11/power-battery-emc/ground_loop_return_ir_toy.py",
)


class EsdTvs(unittest.TestCase):
    def test_dt_invariance_peak_b(self):
        r1 = esd.simulate("B_tvs", 2000.0, dt=1e-12)
        r2 = esd.simulate("B_tvs", 2000.0, dt=0.5e-12)
        self.assertAlmostEqual(r1["peak_ic_V"], r2["peak_ic_V"], delta=1e-3)

    def test_window_covers_five_hbm_tau(self):
        tau = esd.R_HBM * esd.C_HBM
        self.assertGreaterEqual(esd.T_END, 5.0 * tau)
        self.assertGreaterEqual(esd.T_END, 1.0e-6)

    def test_dt_resolves_clamp_tau(self):
        tau_clamp = esd.RDYN * esd.C_PIN
        self.assertLessEqual(esd.DT, tau_clamp / 5.0)

    def test_isc_and_vclamp_formula(self):
        i_sc = esd.V_HBM0 / esd.R_HBM
        self.assertAlmostEqual(i_sc, 2000.0 / 1500.0, places=12)
        # SLVAE37: VCLAMP = VBR + I * RDYN ≈ 8 + 1.333*1.5 = 10
        pred = esd.VBR + i_sc * esd.RDYN
        r = esd.simulate("B_tvs", esd.V_HBM0)
        self.assertAlmostEqual(r["peak_ic_V"], pred, delta=0.05)

    def test_energy_split_most_in_rhbm(self):
        r = esd.simulate("B_tvs", esd.V_HBM0)
        e0 = r["e_stored_J"]
        self.assertAlmostEqual(e0, 200e-6, delta=1e-9)
        self.assertGreater(r["e_rhbm_J"], 0.9 * e0)
        self.assertLess(r["e_tvs_J"], 0.02 * e0)
        self.assertAlmostEqual(r["e_tvs_J"], 1.8e-6, delta=0.5e-6)

    def test_arm_c_topology_lowers_ic_peak_and_ic_current(self):
        b = esd.simulate("B_tvs", esd.V_HBM0)
        c = esd.simulate("C_series_tvs", esd.V_HBM0)
        self.assertLess(c["peak_ic_V"], c["peak_conn_V"])
        self.assertLess(c["peak_ic_V"], b["peak_ic_V"])
        self.assertLess(c["peak_i_ic_A"], c["peak_i_tvs_A"])
        self.assertGreater(c["peak_i_ic_A"], 0.0)
        # B has no separate IC clamp
        self.assertEqual(b["peak_i_ic_A"], 0.0)

    def test_unprotected_near_precharge(self):
        r = esd.simulate("A_unprotected", esd.V_HBM0)
        share = esd.C_HBM / (esd.C_HBM + esd.C_PIN) * esd.V_HBM0
        self.assertAlmostEqual(r["peak_ic_V"], share, delta=1.0)
        self.assertEqual(r["e_tvs_J"], 0.0)

    def test_shared_constants_and_seeds(self):
        self.assertEqual(len(esd.SEEDS), 5)
        src = (ROOT / "examples/month-1/components/esd_tvs_clamp_toy.py").read_text()
        self.assertEqual(src.count("V_HBM0 = "), 1)
        self.assertTrue("backward" in src.lower() or "Backward" in src)
        self.assertNotIn("softens the edge", src)


class GroundLoop(unittest.TestCase):
    def test_a_vs_b_is_ir_on_chosen_r(self):
        peak_a, _, _, _ = gl.run("A_shared_return", gl.I_PEAK0)
        peak_b, _, _, _ = gl.run("B_star", gl.I_PEAK0)
        self.assertAlmostEqual(peak_a, gl.I_PEAK0 * gl.R_SHARED_RETURN, places=12)
        self.assertAlmostEqual(peak_b, gl.I_PEAK0 * gl.R_STAR_RETURN, places=12)

    def test_kelvin_is_physical_bias_not_fudge(self):
        peak_c, mean_c, false_c, _ = gl.run("C_star_kelvin", gl.I_PEAK0)
        pred = gl.I_ADC_BIAS * gl.R_SENSE_LEAD
        self.assertAlmostEqual(peak_c, pred, places=12)
        self.assertAlmostEqual(mean_c, pred, places=12)
        self.assertEqual(false_c, 0)
        src = (
            ROOT / "examples/month-11/power-battery-emc/ground_loop_return_ir_toy.py"
        ).read_text()
        self.assertNotIn("0.001 * i * R_SENSE_LEAD", src)
        self.assertIn("I_ADC_BIAS", src)

    def test_motor_feed_reported_not_in_bounce(self):
        _, _, _, feed = gl.run("A_shared_return", gl.I_PEAK0)
        self.assertAlmostEqual(feed, gl.I_PEAK0 * gl.R_MOTOR_FEED, places=12)
        # sense bounce on A must equal shared return IR, not feed+return
        peak_a, _, _, _ = gl.run("A_shared_return", gl.I_PEAK0)
        self.assertAlmostEqual(peak_a, gl.I_PEAK0 * gl.R_SHARED_RETURN, places=12)
        src = (
            ROOT / "examples/month-11/power-battery-emc/ground_loop_return_ir_toy.py"
        ).read_text()
        self.assertIn("R_MOTOR_FEED", src)
        self.assertIn("L*di/dt not modelled", src)

    def test_shared_streams_and_seeds(self):
        self.assertEqual(gl.run("B_star", 7.0), gl.run("B_star", 7.0))
        self.assertEqual(len(gl.SEEDS), 5)
        self.assertEqual(gl.R_MOTOR_FEED, 0.020)


if __name__ == "__main__":
    unittest.main()
