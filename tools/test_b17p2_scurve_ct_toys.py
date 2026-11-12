#!/usr/bin/env python3
"""Independent checks for batch-17 PR2 toys: jerk-limited S-curve and computed torque."""
import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SC_REL = "examples/month-5/moveit-pick-place/scurve_jerk_limit_toy.py"
CT_REL = "examples/month-5/control-modelling/computed_torque_inverse_dynamics_toy.py"


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sc = load("scurve_jerk_limit_toy", SC_REL)
ct = load("computed_torque_inverse_dynamics_toy", CT_REL)


class SCurve(unittest.TestCase):
    def test_hand_profile_times(self):
        self.assertAlmostEqual(sc.Profile(0.30, None).total, 0.25 + 0.35 + 0.25, places=12)
        self.assertAlmostEqual(sc.Profile(0.30, 8.0).total, 0.5 + 0.1 + 0.5, places=12)
        self.assertAlmostEqual(sc.Profile(0.02, None).total, 2 * math.sqrt(0.02 / 2.0), places=9)
        b = sc.Profile(0.02, 8.0)
        v = b.vpeak
        self.assertAlmostEqual(v * 2.0 * math.sqrt(v / 8.0), 0.02, places=9)

    def test_bounds_and_rest(self):
        for dist in (0.30, 0.02):
            for j in (8.0, 2.0):
                vm, am, jm, ok, end_ok, a_zero = sc.bounds(sc.Profile(dist, j), j, dist)
                self.assertTrue(ok and end_ok and a_zero)
            vm, am, jm, ok, end_ok, a_zero = sc.bounds(sc.Profile(dist, None), None, dist)
            self.assertTrue(ok and end_ok)
            self.assertFalse(a_zero)

    def test_stable_step(self):
        w = 2 * math.pi * 50.0
        hs = sc.h_star(w)
        self.assertAlmostEqual(sc.spectral_radius(w, hs), 1.0, places=9)
        self.assertLess(sc.spectral_radius(w, 0.98 * hs), 1.0)
        self.assertGreater(sc.spectral_radius(w, 1.02 * hs), 1.0)
        self.assertLess(sc.free_run(w, 0.98 * hs), 1.0)
        self.assertGreater(sc.free_run(w, 1.02 * hs), 1.0)
        self.assertLess(sc.DT, 0.1 * hs)

    def test_crn_and_regimes(self):
        self.assertEqual(sc.plant_freqs("flexible"), sc.plant_freqs("flexible"))
        self.assertEqual(set(sc.REGIMES), {"flexible", "rigid_short"})
        src = (ROOT / SC_REL).read_text()
        self.assertIn("written before the first run", src)
        self.assertIn("B loses to A on profile time and cycle time", src)

    def test_expected_byte_identical(self):
        out = subprocess.run([sys.executable, str(ROOT / SC_REL)], capture_output=True, text=True, check=True).stdout
        self.assertEqual(out, (ROOT / "examples/month-5/expected/scurve_jerk_limit_toy.txt").read_text())


class ComputedTorque(unittest.TestCase):
    def test_mass_matrix_hand(self):
        m, cv, gv = ct.dyn((0.0, 0.0), (0.0, 0.0), 0.5)
        self.assertAlmostEqual(m[2], 1.5 * 0.25 ** 2, places=12)
        self.assertAlmostEqual(m[1], 1.5 * 0.25 ** 2 + 1.5 * 0.3 * 0.25, places=12)
        self.assertAlmostEqual(m[0], 3.0 * 0.09 + 1.5 * 0.0625 + 2 * 1.5 * 0.075, places=12)
        self.assertEqual([abs(x) for x in cv], [0.0, 0.0])
        self.assertAlmostEqual(gv[1], 1.5 * 9.81 * 0.25, places=12)

    def test_stable_step(self):
        hs = ct.h_star()
        self.assertAlmostEqual(hs, 2 * (math.sqrt(2) - 1) / 20, places=12)
        self.assertLess(ct.matched_error_run(0.98 * hs), 0.0707)
        self.assertGreater(ct.matched_error_run(1.02 * hs), 0.0707)

    def test_matched_tracks_without_friction_or_noise(self):
        f, scale, ph = 1.0, 0.9, (0.3, 1.1)
        q, qd, _ = ct.desired(0.0, f, scale, ph)
        dt = 1e-3
        worst = 0.0
        for k in range(2000):
            qr, qdr, qddr = ct.desired(k * dt, f, scale, ph)
            worst = max(worst, math.hypot(qr[0] - q[0], qr[1] - q[1]))
            tau, _ = ct.control("B_ct", q, qd, qr, qdr, qddr, 0.5, 0.0, None)
            q, qd = ct.step_plant(q, qd, tau, 0.5, dt, friction=False)
        self.assertLess(worst, 5e-3)

    def test_crn(self):
        a = ct.shared_draws("fast_coupled", 2)
        b = ct.shared_draws("fast_coupled", 2)
        self.assertEqual(a, b)
        src = (ROOT / CT_REL).read_text()
        self.assertIn("written before the first run", src)
        self.assertIn('"payload_mismatch": (0.25, 6.0, 2.0, 0.0)', src)

    def test_expected_byte_identical(self):
        out = subprocess.run([sys.executable, str(ROOT / CT_REL)], capture_output=True, text=True, check=True).stdout
        self.assertEqual(out, (ROOT / "examples/month-5/expected/computed_torque_inverse_dynamics_toy.txt").read_text())

    def test_centre_pose_stiffness_and_fc0_block(self):
        m, minv22, inv_m22, k_ct, k_pd, e_ct, e_pd = ct.centre_pose_stiffness()
        self.assertAlmostEqual(m[2], 1.5 * 0.25 ** 2, places=12)
        det = m[0] * m[2] - m[1] * m[1]
        self.assertAlmostEqual(minv22, m[0] / det, places=12)
        self.assertAlmostEqual(inv_m22, 1.0 / m[2], places=12)
        self.assertAlmostEqual(k_ct, ct.KP / minv22, places=12)
        self.assertAlmostEqual(k_pd, m[2] * ct.KP, places=12)
        self.assertAlmostEqual(e_ct, 1000.0 * ct.FC / k_ct, places=12)
        self.assertAlmostEqual(e_pd, 1000.0 * ct.FC / k_pd, places=12)
        src = (ROOT / CT_REL).read_text()
        self.assertIn("added after the first run", src)
        self.assertIn("not a pre-declared regime", src)
        out = (ROOT / "examples/month-5/expected/computed_torque_inverse_dynamics_toy.txt").read_text()
        self.assertIn("FC=0 sensitivity (added after the first run; not a pre-declared regime)", out)
        self.assertIn("(M⁻¹)22=27.1535  1/M22=10.6667", out)
        self.assertIn("stiffness KP/(M⁻¹)22=14.7311 N m/rad vs D0 KP=M22 KP=37.5000 N m/rad", out)
        self.assertIn("0.3 N m friction leaves 20.3651 mrad vs 8.0000 mrad", out)
        self.assertIn("slow_quasi_static FC=0", out)
        self.assertIn("payload_mismatch FC=0", out)
        self.assertIn("  paired B-A rms: -0.1168+-0.0515: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("  paired B-A rms: -5.1016+-1.3586: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
