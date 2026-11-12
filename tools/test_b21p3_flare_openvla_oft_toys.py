#!/usr/bin/env python3
"""Independent contract tests for batch-21 PR3 FLARE + OpenVLA-OFT toys; stdlib only."""
from __future__ import annotations

import copy
import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FL_REL = "examples/month-6/act-diffusion/flare_future_latent_alignment_toy.py"
OF_REL = "examples/month-8/vla-finetune/openvla_oft_parallel_l1_toy.py"
FL_EXP = "examples/month-6/expected/flare_future_latent_alignment_toy.txt"
OF_EXP = "examples/month-8/expected/openvla_oft_parallel_l1_toy.txt"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


fl = load("flare_future_latent_alignment_toy", FL_REL)
of = load("openvla_oft_parallel_l1_toy", OF_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def section(out: str, start: str, end: str) -> str:
    return out.split(start)[1].split(end)[0]


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((fl, FL_REL), (of, OF_REL)):
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
            for marker in ("Common random numbers", "本页未运行", "以论文为准", "written before the first run", "ROUND_HALF_UP"):
                self.assertIn(marker, src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))

    def test_half_up(self):
        for mod in (fl, of):
            self.assertEqual(mod.num(0.12345), "0.1235")
            self.assertEqual(mod.num(2.00005), "2.0001")
            self.assertEqual(mod.num(0.00012345), "1.235e-4")
            self.assertEqual(mod.num(-0.0), "0.0000")


class Flare(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((fl.D, fl.K, fl.LAMBDA, fl.LAMBDA_BIG, fl.LR, fl.EPOCHS, fl.SUCCESS_TOL, fl.N_TEST),
                         (8, 2, 0.2, 2.0, 0.05, 400, 0.25, 200))
        self.assertEqual(fl.ARMS, ("A_action_only", "B_flare", "C_big_lambda"))
        self.assertEqual(fl.REGIMES, {"delayed": {"n_lab": 6, "n_vid": 60}, "reactive": {"n_lab": 60, "n_vid": 0}})

    def test_gradient_independent(self):
        # One full-batch step from train() must equal LR times a central finite-difference gradient of
        # mean (v.Wx - a)^2 + lam * mean(-cos(P W x, G xf)), computed here without the toy's gradient code.
        lab, vid, _ = fl.generate("delayed", 3)
        G = fl.frozen_G(3)
        lam = 0.7
        W0, v0, P0 = fl.init_params(3)

        def loss(W, v, P):
            act = sum((sum(v[k] * sum(W[k][j] * x[j] for j in range(fl.D)) for k in range(fl.K)) - a) ** 2
                      for x, a, _ in lab) / len(lab)
            al = [(x, xf) for x, _, xf in lab] + list(vid)
            c = 0.0
            for x, xf in al:
                h = [sum(W[k][j] * x[j] for j in range(fl.D)) for k in range(fl.K)]
                z = [sum(P[k][l] * h[l] for l in range(fl.K)) for k in range(fl.K)]
                t = [sum(G[k][j] * xf[j] for j in range(fl.D)) for k in range(fl.K)]
                c += -sum(z[k] * t[k] for k in range(fl.K)) / (math.hypot(*z) * math.hypot(*t))
            return act + lam * c / len(al)

        old = fl.EPOCHS
        try:
            fl.EPOCHS = 1
            W1, v1, P1 = fl.train(copy.deepcopy(W0), list(v0), copy.deepcopy(P0), G, lam, lab, vid)
        finally:
            fl.EPOCHS = old
        eps = 1e-6
        for k in range(fl.K):
            for j in range(fl.D):
                Wp = copy.deepcopy(W0); Wp[k][j] += eps
                Wm = copy.deepcopy(W0); Wm[k][j] -= eps
                g = (loss(Wp, v0, P0) - loss(Wm, v0, P0)) / (2 * eps)
                self.assertAlmostEqual(W1[k][j], W0[k][j] - fl.LR * g, places=7)
            vp = list(v0); vp[k] += eps
            vm = list(v0); vm[k] -= eps
            self.assertAlmostEqual(v1[k], v0[k] - fl.LR * (loss(W0, vp, P0) - loss(W0, vm, P0)) / (2 * eps), places=7)
            for l in range(fl.K):
                Pp = copy.deepcopy(P0); Pp[k][l] += eps
                Pm = copy.deepcopy(P0); Pm[k][l] -= eps
                self.assertAlmostEqual(P1[k][l], P0[k][l] - fl.LR * (loss(W0, v0, Pp) - loss(W0, v0, Pm)) / (2 * eps), places=7)

    def test_crn(self):
        for regime in fl.REGIMES:
            self.assertEqual(fl.generate(regime, 2), fl.generate(regime, 2))
        self.assertEqual(fl.init_params(4), fl.init_params(4))
        self.assertEqual(fl.frozen_G(4), fl.frozen_G(4))
        lab, vid, _ = fl.generate("reactive", 1)
        self.assertEqual(len(vid), 0)
        lab, vid, test = fl.generate("delayed", 1)
        self.assertEqual((len(lab), len(vid), len(test)), (6, 60, 200))

    def test_expected_and_regimes(self):
        out = run(FL_REL)
        self.assertEqual(out, (ROOT / FL_EXP).read_text())
        self.assertEqual(out, run(FL_REL))
        delayed = section(out, "delayed (N_LAB", "reactive (N_LAB")
        self.assertIn("paired B-A action_mse: -0.1002+-0.1756: near-tie", delayed)
        self.assertIn("paired C-B action_mse: 0.1016+-0.2475: near-tie", delayed)
        reactive = section(out, "reactive (N_LAB", "alternatives")
        self.assertIn("paired B-A action_mse: 1.343e-4+-2.827e-4: near-tie", reactive)
        self.assertIn("paired B-A success: 0.0000+-0.0000: tie: identical on every seed", reactive)
        self.assertIn("paired C-B action_mse: 0.0166+-0.0154: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", reactive)
        self.assertIn("hand_calc delayed goal/distractor std ratio: current obs 0.3*sqrt(1/3)/1.0=0.1732; future obs 1.0*sqrt(1/3)=0.5774", out)


class OpenVlaOft(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((of.NCELL, of.K, of.DA, of.N_DEMO, of.NOISE, of.SUCCESS_TOL, of.MODE_TOL, of.T_DIFF, of.NBIN),
                         (8, 8, 2, 10, 0.002, 0.003, 0.1, 10, 256))
        self.assertEqual(of.ARMS, ("A_ar_256bin", "B_oft_l1", "C_diffusion", "D_oft_film"))
        self.assertEqual(of.REGIMES, ("unimodal", "bimodal", "language", "k1"))

    def test_bins_median_passes_independent(self):
        # 256 uniform bins on [-1, 1]: width 2/256; decoding to the centre is within half a bin.
        for v in (-1.0, -0.73, -0.0001, 0.0, 0.31, 0.999):
            self.assertLessEqual(abs(of.bin_centre(of.bin_index(v)) - v), 1.0 / 256 + 1e-15)
        # The L1 minimiser of a set is its median (mean of the middle pair for an even count).
        vals = [0.3, -0.1, 0.7, 0.2]
        self.assertAlmostEqual(of.median_pred([[x] for x in vals], 1)[0], 0.25, places=15)
        self.assertAlmostEqual(of.median_pred([[x] for x in vals + [0.9]], 1)[0], 0.3, places=15)
        # Passes per chunk: K*D autoregressive, 1 parallel, T_DIFF diffusion.
        self.assertEqual(of.passes_of("A_ar_256bin", 8), 16.0)
        self.assertEqual(of.passes_of("B_oft_l1", 8), 1.0)
        self.assertEqual(of.passes_of("C_diffusion", 8), 10.0)
        self.assertEqual(of.passes_of("A_ar_256bin", 1), 2.0)

    def test_crn(self):
        for regime in of.REGIMES:
            self.assertEqual(of.gen_demos(regime, 3), of.gen_demos(regime, 3))
        cells = of.gen_demos("language", 0)
        self.assertEqual(of.predict_arm("C_diffusion", cells, 8, 0), of.predict_arm("C_diffusion", cells, 8, 0))

    def test_expected_and_regimes(self):
        out = run(OF_REL)
        self.assertEqual(out, (ROOT / OF_EXP).read_text())
        self.assertEqual(out, run(OF_REL))
        uni = section(out, "unimodal (", "bimodal (")
        self.assertIn("paired B-A abs_err: -0.0015+-1.281e-4: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", uni)
        self.assertIn("paired C-B success: 0.0000+-0.0000: tie: identical on every seed", uni)
        bi = section(out, "bimodal (", "language (")
        self.assertIn("paired C-B success: 0.2000+-0.2592: near-tie", bi)
        self.assertIn("paired B-A success: 0.5000+-0.3062: clear gap", bi)
        lang = section(out, "language (", "k1 (")
        self.assertIn("paired D-B follow_err: -0.4000+-0.0713: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", lang)
        k1 = section(out, "k1 (", "alternatives")
        self.assertIn("paired B-A passes: -1.0000+-0.0000: clear gap", k1)
        self.assertIn("hand_calc binning: 256 uniform bins on [-1,1] -> bin width 2/256=0.0078; worst-case quantisation error half a bin=0.0039", out)


if __name__ == "__main__":
    unittest.main()
