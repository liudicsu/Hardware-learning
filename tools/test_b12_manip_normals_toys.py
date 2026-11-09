#!/usr/bin/env python3
"""Independent contract tests for batch-12 PR2 manipulability + PCA-normal toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import random
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MA_REL = "examples/month-5/kinematics-ik/manipulability_yoshikawa_toy.py"
PN_REL = "examples/month-7/depth-pointcloud/pointcloud_pca_normals_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ma = load("manipulability_yoshikawa_toy", MA_REL)
pn = load("pointcloud_pca_normals_toy", PN_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def num_jac(q1: float, q2: float, h: float = 1e-7):
    """Central-difference Jacobian of the toy's FK, independent of ma.jac."""
    cols = []
    for dq in ((h, 0.0), (0.0, h)):
        a = ma.fk(q1 + dq[0], q2 + dq[1])
        b = ma.fk(q1 - dq[0], q2 - dq[1])
        cols.append(((a[0] - b[0]) / (2 * h), (a[1] - b[1]) / (2 * h)))
    return (cols[0][0], cols[1][0], cols[0][1], cols[1][1])


class Manipulability(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(ma.SEEDS, (0, 1, 2, 3, 4))
        self.assertEqual((ma.L1, ma.L2), (0.116, 0.135))
        self.assertLess(ma.KP * ma.DT, 2.0)  # explicit-Euler error loop |1 - KP DT| < 1
        self.assertLess(abs(1 - ma.KP * ma.DT), 1.0)

    def test_jacobian_and_yoshikawa_identity(self):
        rng = random.Random(7)
        for _ in range(200):
            q1, q2 = rng.uniform(-3, 3), rng.uniform(-3, 3)
            j, jn = ma.jac(q1, q2), num_jac(q1, q2)
            for a, b in zip(j, jn):
                self.assertAlmostEqual(a, b, places=6)
            s1, s2 = ma.svd2(j)
            self.assertGreaterEqual(s1, s2)
            self.assertAlmostEqual(s1 * s2, ma.L1 * ma.L2 * abs(math.sin(q2)), places=10)
            # sqrt(det(J J^T)) computed directly
            a, b, c, d = j
            jjt = (a * a + b * b, a * c + b * d, c * c + d * d)
            self.assertAlmostEqual(math.sqrt(max(jjt[0] * jjt[2] - jjt[1] ** 2, 0.0)), s1 * s2, places=9)
            self.assertAlmostEqual(s1 * s1 + s2 * s2, a * a + b * b + c * c + d * d, places=12)

    def test_rcap_hits_threshold(self):
        c2 = (ma.R_CAP ** 2 - ma.L1 ** 2 - ma.L2 ** 2) / (2 * ma.L1 * ma.L2)
        self.assertAlmostEqual(ma.L1 * ma.L2 * math.sqrt(1 - c2 * c2), ma.W_MIN, places=12)
        self.assertLess(ma.R_CAP, 0.2505)

    def test_dls_tends_to_inverse(self):
        j = ma.jac(0.4, -1.2)
        exact = ma.rate("A_ignore_w", j, 0.01, -0.02)
        old = ma.LAM
        try:
            ma.LAM = 1e-9
            dls = ma.rate("C_dls", j, 0.01, -0.02)
        finally:
            ma.LAM = old
        for a, b in zip(exact, dls):
            self.assertAlmostEqual(a, b, places=8)

    def test_crn_and_far_tie_is_bitwise(self):
        steps = int(round(((0.200 - 0.130) / ma.V + ma.HOLD) / ma.DT))
        for seed in ma.SEEDS:
            h1, n1 = ma.shared_draws("far_from_singularity", seed, steps)
            h2, n2 = ma.shared_draws("far_from_singularity", seed, steps)
            self.assertEqual((h1, n1), (h2, n2))
            self.assertEqual(len(n1[0]), 4)  # two actuator + two measurement draws per step
            a = ma.run("A_ignore_w", 0.130, 0.200, h1, n1)
            b = ma.run("B_keep_w", 0.130, 0.200, h1, n1)
            self.assertEqual(a, b)  # identical, so "tie" is literal
            self.assertGreater(a["w_min"], ma.W_MIN)

    def test_near_regime_directions(self):
        steps = int(round(((0.2505 - 0.150) / ma.V + ma.HOLD) / ma.DT))
        for seed in ma.SEEDS:
            h, n = ma.shared_draws("near_singularity", seed, steps)
            a, b, c = (ma.run(arm, 0.150, 0.2505, h, n) for arm in ma.ARMS)
            self.assertGreater(b["final_mm"], a["final_mm"])  # B gives up reach
            self.assertGreater(b["w_min"], a["w_min"])
            self.assertLess(b["hold_dps"], a["hold_dps"])
            self.assertAlmostEqual(a["peak_dps"], math.degrees(ma.QD_MAX), places=9)
            self.assertNotEqual(c, a)

    def test_verdict_rule(self):
        self.assertTrue(ma.verdict([1.0, 2.0], [1.0, 2.0]).startswith("tie"))
        self.assertIn("near-tie", ma.verdict([1.0, 2.0, 3.0], [1.01, 1.98, 3.0]))
        self.assertIn("small but consistent", ma.verdict([1.1, 2.1, 3.1], [1.0, 2.02, 3.0]))
        self.assertIn("clear gap", ma.verdict([5.0, 6.0, 7.0], [1.0, 1.1, 1.0]))

    def test_expected_file(self):
        exp = (ROOT / "examples/month-5/expected/manipulability_yoshikawa_toy.txt").read_text()
        self.assertEqual(run(MA_REL), exp)
        self.assertEqual(run(MA_REL), exp)
        self.assertIn("tie: identical on every seed", exp)
        self.assertNotIn("exact tie", exp)


class Normals(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(pn.SEEDS, (0, 1, 2, 3, 4))
        self.assertEqual(pn.K_OF, {"B_pca_k20": 20, "C_pca_k4": 4})

    def test_jacobi_against_known_rotation(self):
        rng = random.Random(3)
        for _ in range(50):
            ax = [rng.gauss(0, 1) for _ in range(3)]
            n = math.sqrt(sum(x * x for x in ax))
            u = [x / n for x in ax]
            ang = rng.uniform(0, math.pi)
            c, s = math.cos(ang), math.sin(ang)
            ux, uy, uz = u
            R = [[c + ux * ux * (1 - c), ux * uy * (1 - c) - uz * s, ux * uz * (1 - c) + uy * s],
                 [uy * ux * (1 - c) + uz * s, c + uy * uy * (1 - c), uy * uz * (1 - c) - ux * s],
                 [uz * ux * (1 - c) - uy * s, uz * uy * (1 - c) + ux * s, c + uz * uz * (1 - c)]]
            lam = [3.0, 1.5, 0.01]
            M = [[sum(R[i][k] * lam[k] * R[j][k] for k in range(3)) for j in range(3)] for i in range(3)]
            vals, vecs = pn.jacobi_eig(M)
            self.assertEqual(sorted(round(v, 9) for v in vals), sorted(lam))
            i = min(range(3), key=lambda k: vals[k])
            v = [vecs[r][i] for r in range(3)]
            self.assertAlmostEqual(abs(sum(v[r] * R[r][2] for r in range(3))), 1.0, places=9)

    def test_exact_tilted_plane_and_orientation(self):
        nrm = pn.unit((0.2, -0.1, -1.0))
        pts = []
        for i in range(-3, 4):
            for j in range(-3, 4):
                x, y = 0.005 * i, 0.005 * j
                z = 0.4 - (nrm[0] * x + nrm[1] * y) / nrm[2]
                pts.append((x, y, z))
        raw = pn.pca_normal(pts)
        self.assertAlmostEqual(abs(sum(a * b for a, b in zip(raw, nrm))), 1.0, places=9)
        o, flipped = pn.orient(raw, pts[0])
        self.assertGreater(-(o[0] * pts[0][0] + o[1] * pts[0][1] + o[2] * pts[0][2]), 0.0)
        o2, flipped2 = pn.orient((-o[0], -o[1], -o[2]), pts[0])
        self.assertEqual(o2, o)
        self.assertTrue(flipped2)

    def test_true_normal_matches_finite_difference(self):
        a, lam, h = 0.004, 0.04, 1e-7
        for x, y in ((0.003, -0.011), (0.017, 0.002), (-0.02, 0.031)):
            _, fx, fy = pn.height(a, lam, x, y)
            fxn = (pn.height(a, lam, x + h, y)[0] - pn.height(a, lam, x - h, y)[0]) / (2 * h)
            fyn = (pn.height(a, lam, x, y + h)[0] - pn.height(a, lam, x, y - h)[0]) / (2 * h)
            self.assertAlmostEqual(fx, fxn, places=6)
            self.assertAlmostEqual(fy, fyn, places=6)

    def test_shared_scene_crn(self):
        s1 = pn.shared_scene("ripple_noisy", 0.008, 0.10, 0.002, 2)
        s2 = pn.shared_scene("ripple_noisy", 0.008, 0.10, 0.002, 2)
        self.assertEqual(s1, s2)
        cloud, truth, q = s1
        self.assertEqual(len(cloud), pn.N_GRID ** 2)
        self.assertEqual(len(set(q)), pn.QUERIES)
        for t in truth[:50]:
            self.assertLess(t[2], 0.0)  # faces the camera at the origin

    def test_regime_directions(self):
        flat = pn.evaluate("flat_low_noise", 0.0, 0.10, 0.0003, 0)
        self.assertLess(flat["A_global_plane"]["ang"], flat["B_pca_k20"]["ang"])
        fine = pn.evaluate("fine_ripple_low_noise", 0.004, 0.04, 0.0001, 0)
        self.assertLess(fine["C_pca_k4"]["ang"], fine["B_pca_k20"]["ang"])
        noisy = pn.evaluate("ripple_noisy", 0.008, 0.10, 0.002, 0)
        self.assertLess(noisy["B_pca_k20"]["ang"], noisy["A_global_plane"]["ang"])
        self.assertLess(noisy["B_pca_k20"]["ang"], noisy["C_pca_k4"]["ang"])

    def test_expected_file(self):
        exp = (ROOT / "examples/month-7/expected/pointcloud_pca_normals_toy.txt").read_text()
        self.assertEqual(run(PN_REL), exp)
        self.assertIn("No winner declared", exp)
        self.assertNotIn("exact tie", exp)


if __name__ == "__main__":
    unittest.main(verbosity=1)
