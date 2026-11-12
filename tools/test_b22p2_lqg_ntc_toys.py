#!/usr/bin/env python3
"""Independent contract tests for the LQG separation and NTC inrush limiter toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LQ_REL = "examples/month-5/state-space-lqr/lqg_kalman_lqr_separation_toy.py"
NT_REL = "examples/month-11/power-battery-emc/ntc_inrush_limiter_toy.py"
LQ_EXP = "examples/month-5/expected/lqg_kalman_lqr_separation_toy.txt"
NT_EXP = "examples/month-11/expected/ntc_inrush_limiter_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR\d|sources note|来源说明|来源笔记|this batch|本批|this round|本轮|polish"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lq = load("lqg_kalman_lqr_separation_toy", LQ_REL)
nt = load("ntc_inrush_limiter_toy", NT_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def section(out: str, start: str, end: str) -> str:
    return out.split(start)[1].split(end)[0]


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        for mod, rel in ((lq, LQ_REL), (nt, NT_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertEqual(mod.SEEDS, (0, 1, 2, 3, 4))
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1e-16, -2e-16, 3e-16, 0.0, 1e-16], [0.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("small but consistent", mod.verdict([10.5, 10.6, 10.4, 10.5, 10.5], [10.0] * 5))
            self.assertIn("1 of 5 seeds has the opposite sign", mod.verdict([5.0, 5.0, 5.0, 5.0, -0.5], [0.0] * 5))
            self.assertEqual(mod.num(0.12345), "0.1235")
            self.assertEqual(mod.num(-0.0), "0.0000")
            src = (ROOT / rel).read_text()
            for marker in ("Common random numbers", "本页未运行", "ROUND_HALF_UP"):
                self.assertIn(marker, src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")

    def test_expected_byte_identical_and_no_process_labels(self):
        for rel, exp in ((LQ_REL, LQ_EXP), (NT_REL, NT_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "本轮"):
            self.assertRegex(bad, PROCESS)


def mm(X, Y):
    return [[sum(X[i][k] * Y[k][j] for k in range(len(Y))) for j in range(len(Y[0]))] for i in range(len(X))]


def tr(X):
    return [list(r) for r in zip(*X)]


class Lqg(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((lq.DT, lq.M, lq.B_DAMP, lq.SIG_W, lq.R, lq.HORIZON), (0.02, 1.0, 0.40, 0.04, 0.01, 500))
        self.assertEqual(lq.REGIMES, {"matched": 0.05, "noisy_sensor": 0.25, "quiet_sensor": 0.005})
        self.assertEqual((lq.PAGE_POLES, lq.FAST_POLES), ((0.85, 0.80), (0.20, 0.20)))
        self.assertEqual(lq.ARMS, ("A_oracle", "B_lqg", "C_luen_page", "D_luen_fast", "E_kf_misspec"))

    def independent_K(self):
        # Finite-horizon backward recursion with explicit scalar algebra (no shared helpers).
        a11, a12, a21, a22 = 1.0, 0.02, 0.0, 1.0 - 0.4 * 0.02
        b2 = 0.02
        s11, s12, s22 = 1.0, 0.0, 0.1
        for _ in range(20000):
            # S B = [s12*b2, s22*b2]; B'SB = s22*b2^2; B'SA row = b2*[s12*a11+s22*a21, s12*a12+s22*a22]
            g = s22 * b2 * b2 + 0.01
            h1 = b2 * (s12 * a11 + s22 * a21)
            h2 = b2 * (s12 * a12 + s22 * a22)
            k1, k2 = h1 / g, h2 / g
            c11, c12, c21, c22 = a11, a12, a21 - b2 * k1, a22 - b2 * k2
            # S = Acl' S Acl + Q + K' R K
            n11 = c11 * (s11 * c11 + s12 * c21) + c21 * (s12 * c11 + s22 * c21) + 1.0 + 0.01 * k1 * k1
            n12 = c11 * (s11 * c12 + s12 * c22) + c21 * (s12 * c12 + s22 * c22) + 0.01 * k1 * k2
            n22 = c12 * (s11 * c12 + s12 * c22) + c22 * (s12 * c12 + s22 * c22) + 0.1 + 0.01 * k2 * k2
            s11, s12, s22 = n11, n12, n22
        return k1, k2

    def test_lqr_gain_independent(self):
        K = lq.lqr_gain(lq.A, lq.B, lq.Q, lq.R)
        k1, k2 = self.independent_K()
        self.assertAlmostEqual(K[0][0], k1, places=6)
        self.assertAlmostEqual(K[0][1], k2, places=6)
        self.assertEqual((lq.num(K[0][0]), lq.num(K[0][1])), ("9.5023", "5.0042"))

    def test_kalman_fixed_point_and_first_step(self):
        L = lq.kalman_gain(lq.A, lq.C, lq.V_TRUE, 0.05 ** 2, lq.P0)
        self.assertEqual((lq.num(L[0][0]), lq.num(L[1][0])), ("0.1576", "0.6712"))
        # Iterate a covariance until the gain stops moving, independently.
        P = [[0.25, 0.0], [0.0, 0.01]]
        for _ in range(20000):
            s = P[0][0] + 0.0025
            l1, l2 = P[0][0] / s, P[1][0] / s
            Pb = [[P[0][0] - l1 * P[0][0], P[0][1] - l1 * P[0][1]], [P[1][0] - l2 * P[0][0], P[1][1] - l2 * P[0][1]]]
            P = mm(mm(lq.A, Pb), tr(lq.A))
            P[1][1] += 0.04 ** 2
        self.assertAlmostEqual(L[0][0], P[0][0] / (P[0][0] + 0.0025), places=6)
        self.assertAlmostEqual(L[1][0], P[1][0] / (P[0][0] + 0.0025), places=6)
        self.assertAlmostEqual(0.25 / 0.2525, 0.990099, places=6)

    def test_ackermann_places_poles(self):
        for poles in (lq.PAGE_POLES, lq.FAST_POLES, (0.90, 0.85)):
            Lp = lq.ackermann_observer(lq.A, lq.C, poles)
            F = [[lq.A[0][0] - Lp[0][0], lq.A[0][1]], [lq.A[1][0] - Lp[1][0], lq.A[1][1]]]
            self.assertAlmostEqual(F[0][0] + F[1][1], sum(poles), places=9)
            self.assertAlmostEqual(F[0][0] * F[1][1] - F[0][1] * F[1][0], poles[0] * poles[1], places=9)

    def test_crn_and_same_K(self):
        K = lq.lqr_gain(lq.A, lq.B, lq.Q, lq.R)
        for regime in lq.REGIMES:
            for seed in lq.SEEDS:
                self.assertEqual(lq.shared_draws(regime, seed, 50), lq.shared_draws(regime, seed, 50))
        # With a gain of zero the observers never correct, so both estimator forms track only the model.
        Z = [[0.0], [0.0]]
        b = lq.run_arm("B_lqg", "matched", 0, K, Z, None, 50, 0.05)
        c = lq.run_arm("C_luen_page", "matched", 0, K, None, Z, 50, 0.05)
        self.assertEqual(b, c)

    def test_directions(self):
        out = run(LQ_REL)
        m = section(out, "matched (", "noisy_sensor (")
        self.assertRegex(m, r"paired B-A cost: 0\.0284\+-0\.0202: clear gap.*same sign on all 5 seeds")
        self.assertRegex(m, r"paired B-C cost: -0\.0049\+-0\.0026: small but consistent")
        self.assertRegex(m, r"paired E-C cost: 0\.0807\+-0\.0444: clear gap")
        n = section(out, "noisy_sensor (", "quiet_sensor (")
        self.assertRegex(n, r"paired B-C cost: -0\.1084\+-0\.0036: clear gap")
        q = section(out, "quiet_sensor (", "alternative parameters")
        self.assertRegex(q, r"paired E-C cost: 0\.0127\+-0\.0147: near-tie")
        self.assertRegex(q, r"paired B-C cost: 0\.0127\+-0\.0235: near-tie")
        self.assertRegex(q, r"paired B-A cost: 0\.0253\+-0\.0355: near-tie")


class Ntc(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((nt.V_S, nt.R_SRC, nt.C_BUS, nt.R_LOAD, nt.R_LOAD_HEAVY), (24.0, 0.05, 2200e-6, 12.0, 6.0))
        self.assertEqual((nt.R25, nt.BETA, nt.R_TH, nt.C_TH, nt.WINDOW, nt.I2T_BUDGET), (5.0, 3500.0, 60.0, 0.5, 0.05, 1.0))
        self.assertEqual(nt.ARMS, ("A_none", "B_ntc", "C_fixed", "D_bypass"))

    def test_hand_calc(self):
        self.assertAlmostEqual(24 / 0.05, 480.0, places=9)
        self.assertAlmostEqual(24 / 5.05, 4.752475, places=6)
        self.assertAlmostEqual(24 ** 2 * 0.0022 / (2 * 0.05), 12.672, places=9)
        self.assertAlmostEqual(0.5 * 0.0022 * 24 ** 2, 0.6336, places=9)
        self.assertAlmostEqual(nt.ntc_r(nt.T25, 5.0), 5.0, places=12)
        self.assertLess(nt.ntc_r(nt.T25 + 50, 5.0), 5.0)

    def test_steady_balance(self):
        t, r, i = nt.steady_ntc(nt.T25, 5.0, 12.0, 0.05, 60.0)
        self.assertAlmostEqual(t - nt.T25, i * i * r * 60.0, places=6)
        self.assertAlmostEqual(i, 24.0 / (0.05 + r + 12.0), places=12)

    def test_crn_and_bypass_equals_cold(self):
        for regime in nt.REGIMES:
            for seed in nt.SEEDS:
                self.assertEqual(nt.shared_draws(regime, seed), nt.shared_draws(regime, seed))
        b = nt.run_arm("B_ntc", "cold_start", 0)
        d = nt.run_arm("D_bypass", "cold_start", 0)
        self.assertEqual((b["peak_a"], b["i2t"]), (d["peak_a"], d["i2t"]))
        self.assertEqual((d["v_drop_ss"], d["p_ss"]), (0.0, 0.0))

    def test_directions(self):
        out = run(NT_REL)
        c = section(out, "cold_start:", "hot_restart:")
        self.assertRegex(c, r"paired A-B peak_a: 483\.8672\+-62\.9814: clear gap")
        self.assertRegex(c, r"paired C-B peak_a: 0\.3278\+-0\.0755: small but consistent")
        self.assertRegex(c, r"paired B-D peak_a: 0\.0000\+-0\.0000: tie")
        h = section(out, "hot_restart:", "heavy_load:")
        self.assertIn("B_ntc peak_a 56.1052+-0.8280 i2t 1.7419+-0.1192 fuse_ok 0.0000+-0.0000", h)
        self.assertRegex(h, r"paired A-B fuse_ok: 0\.0000\+-0\.0000: tie")
        hv = section(out, "heavy_load:", "alternative parameters")
        self.assertRegex(hv, r"paired C-B peak_a: -0\.1153\+-0\.3361: near-tie")


if __name__ == "__main__":
    unittest.main()
