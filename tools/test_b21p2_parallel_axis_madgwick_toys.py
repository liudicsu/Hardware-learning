#!/usr/bin/env python3
"""Independent contract tests for batch-21 PR2 parallel-axis + Madgwick toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PA_REL = "examples/month-4/urdf-tf/urdf_parallel_axis_inertia_toy.py"
MW_REL = "examples/month-2/first-robots/madgwick_vs_complementary_balancer_toy.py"
PA_EXP = "examples/month-4/expected/urdf_parallel_axis_inertia_toy.txt"
MW_EXP = "examples/month-2/expected/madgwick_vs_complementary_balancer_toy.txt"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pa = load("urdf_parallel_axis_inertia_toy", PA_REL)
mw = load("madgwick_vs_complementary_balancer_toy", MW_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def section(out: str, start: str, end: str) -> str:
    return out.split(start)[1].split(end)[0]


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((pa, PA_REL), (mw, MW_REL)):
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
            for marker in ("Common random numbers", "本页未运行", "written before the first run", "ROUND_HALF_UP"):
                self.assertIn(marker, src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))

    def test_half_up(self):
        for mod in (pa, mw):
            self.assertEqual(mod.num(0.12345), "0.1235")
            self.assertEqual(mod.num(2.00005), "2.0001")
            self.assertEqual(mod.num(0.00012345), "1.235e-4")
            self.assertEqual(mod.num(-0.0), "0.0000")


class ParallelAxis(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((pa.MASS, pa.SIZE, pa.MASS_TOL, pa.SIZE_TOL, pa.TAU), (2.0, (0.30, 0.24, 0.08), 0.03, 0.02, 0.05))
        self.assertEqual(pa.ARMS, ("A_com", "B_typo", "C_shifted"))
        self.assertEqual(list(pa.REGIMES), ["zero", "small", "large", "along_axis", "diagonal"])
        self.assertIn("No integration step", (ROOT / PA_REL).read_text())
        self.assertFalse(any(name in vars(pa) for name in ("DT", "dt", "STEP", "rk4", "euler")))

    def test_box_matches_lesson_macro(self):
        icm = pa.box_icm(2.0, 0.30, 0.24, 0.08)
        self.assertAlmostEqual(icm[0][0], 2.0 / 12 * (0.24 ** 2 + 0.08 ** 2), places=15)
        self.assertAlmostEqual(icm[2][2], 0.0246, places=12)

    def test_tensor_form_independent(self):
        # Independent: I_zz about a parallel axis d away = I_cm + m d^2; along-axis shift leaves I_zz; J_xy = -m x y.
        icm = pa.box_icm(1.7, 0.2, 0.1, 0.05)
        j = pa.shift(icm, 1.7, (0.3, 0.0, 0.0))
        self.assertAlmostEqual(j[2][2], icm[2][2] + 1.7 * 0.09, places=14)
        self.assertAlmostEqual(j[0][0], icm[0][0], places=14)
        j = pa.shift(icm, 1.7, (0.0, 0.0, 0.2))
        self.assertAlmostEqual(j[2][2], icm[2][2], places=14)
        j = pa.shift(icm, 1.7, (0.1, 0.2, 0.0))
        self.assertAlmostEqual(j[0][1], -1.7 * 0.1 * 0.2, places=14)

    def test_crn_and_arm_rules(self):
        for regime in pa.REGIMES:
            for s in pa.SEEDS:
                self.assertEqual(pa.shared_body(regime, s), pa.shared_body(regime, s))
                a, b, c = (pa.run_arm(arm, regime, s) for arm in pa.ARMS)
                self.assertEqual(a["m"], b["m"])
                self.assertEqual(b["m"], c["m"])
                r = pa.REGIMES[regime]
                d2 = r[0] ** 2 + r[1] ** 2
                self.assertAlmostEqual(a["J_zz"] - b["J_zz"], a["m"] * d2, places=12)
                self.assertAlmostEqual(c["J_zz"], a["J_zz"], places=12)
                self.assertEqual(b["tau_g"], 0.0)
                self.assertEqual(c["tau_g"], 0.0)

    def test_expected_and_regimes(self):
        out = run(PA_REL)
        self.assertEqual(out, (ROOT / PA_EXP).read_text())
        self.assertEqual(out, run(PA_REL))
        zero = section(out, "zero (COM", "small (COM")
        self.assertEqual(zero.count("tie: identical on every seed"), 10)
        large = section(out, "large (COM", "along_axis (COM")
        self.assertIn("paired B-A J_zz: -0.0448+-4.431e-4: clear gap", large)
        self.assertIn("paired C-A J_zz: 0.0000+-0.0000: tie: identical on every seed", large)
        self.assertIn("paired C-A tau_g: -2.9280+-0.0290: clear gap", large)
        small = section(out, "small (COM", "large (COM")
        self.assertIn("paired B-A J_zz: -2.009e-4+-2.789e-6: small but consistent gap", small)
        self.assertNotIn("near-tie", small)
        along = section(out, "along_axis (COM", "diagonal (COM")
        self.assertIn("paired B-A J_zz: 0.0000+-0.0000: tie: identical on every seed", along)
        self.assertIn("hand_calc d=0.15 m: m d^2=2.0*0.15^2=0.0450 kg m^2; I=Izz_cm+m d^2=0.0696 kg m^2", out)


class Madgwick(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((mw.RATE, mw.TAU, mw.BETA_LOW, mw.BETA_HIGH), (200.0, 0.5, 0.033, 0.5))
        self.assertEqual((mw.BIAS_DEG, mw.GYRO_NOISE_DEG, mw.ACC_NOISE, mw.A_LIN, mw.WARMUP), (1.0, 0.1, 0.04, 2.0, 2.0))
        self.assertEqual(mw.ARMS, ("A_gyro", "B_complementary", "C_madgwick", "D_madgwick_big"))
        self.assertEqual(list(mw.REGIMES), ["static", "slow_tilt", "accelerate"])
        self.assertIn("Integration step: dt=1/", (ROOT / MW_REL).read_text())

    def test_gravity_convention_independent(self):
        # Report gravity term for q = (cos t/2, 0, sin t/2, 0): (2(q1q3-q0q2), 2(q0q1+q2q3), q0^2-q1^2-q2^2+q3^2).
        th = 0.3
        q = (math.cos(th / 2), 0.0, math.sin(th / 2), 0.0)
        f = mw.to_sensor(q, (0.0, 0.0, 1.0))
        self.assertAlmostEqual(f[0], 2 * (0 - q[0] * q[2]), places=14)
        self.assertAlmostEqual(f[2], q[0] ** 2 - q[2] ** 2, places=14)
        # A steady lean atan(a/g) makes the specific force point along sensor z.
        lean = math.atan2(2.0, 9.81)
        q = (math.cos(lean / 2), 0.0, math.sin(lean / 2), 0.0)
        f = mw.to_sensor(q, (2.0 / 9.81, 0.0, 1.0))
        self.assertAlmostEqual(f[0], 0.0, places=12)

    def test_madgwick_converges_static(self):
        # Noise-free, no bias: the IMU update pulls a level estimate to a 5 deg tilt.
        th = math.radians(5.0)
        acc = list(mw.to_sensor((math.cos(th / 2), 0.0, math.sin(th / 2), 0.0), (0.0, 0.0, 1.0)))
        q = (1.0, 0.0, 0.0, 0.0)
        for _ in range(4000):
            q = mw.madgwick_step(q, 0.0, acc, 0.1)
        self.assertLess(abs(2 * math.atan2(q[2], q[0]) - th), math.radians(0.1))

    def test_crn(self):
        for regime in mw.REGIMES:
            a, b = mw.truth(regime, 2), mw.truth(regime, 2)
            self.assertEqual(a, b)

    def test_expected_and_regimes(self):
        out = run(MW_REL)
        self.assertEqual(out, (ROOT / MW_EXP).read_text())
        static = section(out, "static (", "slow_tilt (")
        self.assertIn("paired A-B end_err: 35.5376+-23.4941: clear gap", static)
        self.assertIn("paired C-B rmse: 0.2661+-0.2218: clear gap", static)
        slow = section(out, "slow_tilt (", "accelerate (")
        self.assertIn("paired C-B rmse: 0.2049+-0.2241: near-tie", slow)
        acc = section(out, "accelerate (", "alternatives")
        self.assertIn("paired D-B rmse: 0.7386+-0.0326: small but consistent gap, not a tie (|m| > sd); same sign on all 5 seeds", acc)
        self.assertIn("paired C-B rmse: -2.9664+-0.3624: clear gap", acc)
        self.assertIn("hand_calc lean while accelerating: atan(A_LIN/g)=atan(2.0000/9.8100)=11.5232 deg", out)


if __name__ == "__main__":
    unittest.main()
