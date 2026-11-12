#!/usr/bin/env python3
"""Independent tests for batch-18 PR2 toys (octomap/TSDF and integrator energy)."""
from __future__ import annotations

import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OCTO_REL = "examples/month-4/slam-nav/octomap_tsdf_volume_toy.py"
INT_REL = "examples/month-7/mujoco-so101/mujoco_integrator_energy_toy.py"
sys.path.insert(0, str(ROOT / "examples/month-4/slam-nav"))
sys.path.insert(0, str(ROOT / "examples/month-7/mujoco-so101"))
import octomap_tsdf_volume_toy as oc  # noqa: E402
import mujoco_integrator_energy_toy as ie  # noqa: E402


def run(rel: str) -> str:
    return subprocess.check_output(
        [sys.executable, str(ROOT / rel)],
        cwd=ROOT,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
    )


class TestOctomapTsdf(unittest.TestCase):
    def test_crn_shared_ranges(self):
        views = oc.CAMS
        a = oc.shared_ranges("overhang_multiview", 3, views, oc.SIGMA_LIGHT)
        b = oc.shared_ranges("overhang_multiview", 3, views, oc.SIGMA_LIGHT)
        self.assertEqual(a, b)
        c = oc.shared_ranges("noisy_multiview", 3, views, oc.SIGMA_NOISY)
        self.assertNotEqual(a, c)

    def test_unknown_means_untouched(self):
        acc = oc.integrate_octree(oc.CAMS, oc.shared_ranges("overhang_multiview", 0, oc.CAMS, oc.SIGMA_LIGHT), oc.L_CLAMP)
        self.assertEqual(oc.unknown_correct(acc), 0)
        for cls, hit, miss, _ in acc.values():
            self.assertIn(cls, ("occ", "free"))
            self.assertTrue(hit or miss)

    def test_declared_regimes_and_expected(self):
        self.assertEqual(list(oc.REGIMES), ["overhang_multiview", "single_frame_clean", "noisy_multiview", "bad_pose"])
        out = run(OCTO_REL)
        self.assertIn("sdf_trunc=0.25 was chosen after the first run", out)
        self.assertIn("paired C-A overhang_recall: 0.9833+-0.0062: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("paired B-A overhang_recall: 0.9861+-1.241e-16: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("paired B-S occ_IoU: 0.0316+-0.0000: small but consistent gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("paired C-raw surface_MAE: -0.0322+-0.0024: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("paired C_bad-C surface_MAE: 0.0026+-0.0004: small but consistent gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("alternative sdf_trunc=0.50 m on noisy_multiview (same seeds; first-run truncation, kept):", out)
        self.assertIn("paired C-raw surface_MAE: 0.0131+-0.0034: small but consistent gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("B unknown-with-hit-or-miss count 0.0000+-0.0000", out)
        self.assertIn("not PGM / DWA / costmap inflation; not depth-pointcloud voxels", out)
        self.assertEqual((ROOT / "examples/month-4/expected/octomap_tsdf_volume_toy.txt").read_text(), out)


class TestIntegratorEnergy(unittest.TestCase):
    def test_no_mujoco_import(self):
        src = (ROOT / INT_REL).read_text()
        self.assertNotIn("import mujoco", src)
        self.assertNotIn("from mujoco", src)

    def test_hstar_and_stable_step(self):
        self.assertAlmostEqual(ie.H_STAR, 2.0 / ie.OMEGA0, places=12)
        self.assertLess(ie.H_MOD, ie.H_STAR)
        self.assertEqual(ie.energy_bounded_run(0.98 * ie.H_STAR, 40.0), 1)
        self.assertEqual(ie.energy_bounded_run(1.02 * ie.H_STAR, 40.0), 0)
        self.assertEqual(ie.energy_bounded_run(0.50 * ie.H_STAR, 40.0), 1)
        self.assertEqual(ie.energy_bounded_run(0.50 * ie.H_MOD, 40.0), 1)
        rho_hi = ie.spectral_radius(ie.amp_matrix(1.02 * ie.H_STAR, ie.OMEGA0))
        rho_lo = ie.spectral_radius(ie.amp_matrix(0.98 * ie.H_STAR, ie.OMEGA0))
        self.assertGreater(rho_hi, 1.0)
        self.assertAlmostEqual(rho_lo, 1.0, places=6)
        src = (ROOT / INT_REL).read_text()
        self.assertIn("iff h < h*", src)
        self.assertNotIn("iff h <= h*", src)
        self.assertNotIn("h <= 2/omega0", src)
        # Analytic check only: at h = h* the trace is -2 (Jordan block). Not printed.
        M = ie.amp_matrix(ie.H_STAR, ie.OMEGA0)
        self.assertAlmostEqual(M[0][0] + M[1][1], -2.0, places=12)

    def test_crn_shared_ic(self):
        self.assertEqual(ie.ic_pend(2), ie.ic_pend(2))
        self.assertEqual(ie.ic_spin(2), ie.ic_spin(2))
        self.assertNotEqual(ie.ic_pend(2), ie.ic_pend(3))

    def test_spinner_A_equals_B(self):
        w = ie.ic_spin(0)
        a = ie.run_spin(w, ie.H_SPIN, ie.T_SPIN, "A_explicit")
        b = ie.run_spin(w, ie.H_SPIN, ie.T_SPIN, "B_semimpl")
        self.assertEqual(a["dE"], b["dE"])

    def test_declared_regimes_and_expected(self):
        self.assertEqual(list(ie.REGIMES), ["moderate_h", "tiny_h", "large_h_spin", "inconsistent_D"])
        out = run(INT_REL)
        self.assertIn("h < 2/omega0", out)
        self.assertNotIn("h <= 2/omega0", out)
        self.assertIn("assert_below_hstar=1", out)
        self.assertIn("0.98x_hstar", out)
        self.assertIn("1.02x_hstar", out)
        self.assertIn("half_default", out)
        self.assertIn("above_hstar_grows=1  below_hstar_bounded=1", out)
        self.assertIn("paired A-B |dE|: 62.9097+-3.0587: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("paired A-B |dE|: -0.4534+-0.0850: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("paired A-B |dE|: 0.0000+-0.0000: tie: identical on every seed", out)
        self.assertIn("paired C_bad-C |dE|: 12514.0224+-6611.4795: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("alternative C_damp=0.0 on moderate_h (same seeds):", out)
        self.assertIn("paired B-C |dE|: 0.0000+-0.0000: tie: identical on every seed", out)
        self.assertIn("not mujoco.step; ≠ grip_sweep", out)
        self.assertEqual((ROOT / "examples/month-7/expected/mujoco_integrator_energy_toy.txt").read_text(), out)


if __name__ == "__main__":
    unittest.main()
