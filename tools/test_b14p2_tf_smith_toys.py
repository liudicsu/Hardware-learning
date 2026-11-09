#!/usr/bin/env python3
"""Independent contract tests for batch-14 PR2 tf2 Buffer lookup-time + Smith predictor toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TF_REL = "examples/month-4/urdf-tf/tf_buffer_time_lookup_toy.py"
SM_REL = "examples/month-5/control-modelling/smith_predictor_delay_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


tf = load("tf_buffer_time_lookup_toy", TF_REL)
sm = load("smith_predictor_delay_toy", SM_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Labels(unittest.TestCase):
    """Both toys share one labelling rule; check it on hand-made paired data."""

    def test_order_and_thresholds(self):
        for mod, rel in ((tf, TF_REL), (sm, SM_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1.0 + 1e-12, 1.0, 1.0 - 1e-12, 1.0, 1.0], [1.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertNotIn("seeds", v)  # no sign count on a numerically-zero line
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("same sign on all 5 seeds", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("1 of 5 seeds has the opposite sign", mod.verdict([5.0, 5.1, 4.9, 5.2, 0.5], [1.0] * 5))
            self.assertIn("same sign on all 3 seeds", mod.verdict([5.0, 5.1, 4.9], [1.0] * 3))
            self.assertIn("1 of 3 seeds has the opposite sign", mod.verdict([5.0, 5.1, 0.5], [1.0] * 3))
            src = (ROOT / rel).read_text()
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))

    def test_no_signed_zero(self):
        for mod in (tf, sm):
            self.assertEqual(mod.num(-1e-5), "-1.000e-05")
            self.assertEqual(mod.num(0.0), "0.0000")
            self.assertNotEqual(mod.num(-4e-5), "-0.0000")

    def test_divergence_is_reported_not_averaged(self):
        v = sm.verdict([math.inf, 1.0, 1.0, 1.0, 1.0], [0.5] * 5)
        self.assertIn("diverged on 1 vs 0 of 5 seeds", v)
        self.assertIn("the diverging arm loses", v)


class TfBuffer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(TF_REL)

    def test_scope(self):
        self.assertEqual(tf.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / TF_REL).read_text()
        self.assertIn("本页未运行", text)
        self.assertIn("Common random numbers", text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|rclpy|tf2_ros)")
        self.assertNotRegex(text, r"\bDT\b")  # closed-form trajectory, nothing to integrate
        self.assertEqual(tf.CACHE, 10 * tf.US)  # tf2 BUFFER_CORE_DEFAULT_CACHE_TIME = 10 s

    def test_common_random_numbers(self):
        self.assertEqual(tf.shared_draws("lagging_stamp", 2), tf.shared_draws("lagging_stamp", 2))
        self.assertNotEqual(tf.shared_draws("lagging_stamp", 2)[0], tf.shared_draws("lagging_stamp", 3)[0])

    def test_lookup_rules_by_hand(self):
        # Independent of the toy's timeline: two samples 20 ms apart, angles 0.0 and 0.2 rad.
        buf = [(0, 0.0), (20_000, 0.2)]
        self.assertEqual(tf.lookup("A_latest", buf, 10_000, 30_000, [])[0], 0.2)       # time 0 = newest
        self.assertAlmostEqual(tf.lookup("B_stamped", buf, 10_000, 30_000, [])[0], 0.1, places=12)
        self.assertAlmostEqual(tf.lookup("C_extrapolate", buf, 10_000, 30_000, [])[0], 0.1, places=12)
        # Newer than the newest sample: C extrapolates, B waits for the next sample within the timeout.
        self.assertAlmostEqual(tf.lookup("C_extrapolate", buf, 30_000, 31_000, [])[0], 0.3, places=12)
        ang, wait = tf.lookup("B_stamped", buf, 30_000, 31_000, [(40_000, 0.25, 45_000)])
        self.assertAlmostEqual(ang, 0.225, places=12)
        self.assertEqual(wait, 14_000)
        # No sample within the timeout: B fails (tf2 raises ExtrapolationException).
        self.assertIsNone(tf.lookup("B_stamped", buf, 30_000, 31_000, [(40_000, 0.25, 31_000 + tf.TIMEOUT + 1)])[0])
        # Older than the oldest sample: B and C both fail (extrapolation into the past).
        self.assertIsNone(tf.lookup("B_stamped", [(5_000, 0.0), (20_000, 0.2)], 1_000, 30_000, [])[0])

    def test_static_tree_bit_identical(self):
        for seed in tf.SEEDS:
            r = tf.run("static_tree", seed)
            self.assertEqual(r["A_latest"]["err"], 0.0)
            self.assertEqual(r["A_latest"]["err"], r["B_stamped"]["err"])
            self.assertEqual(r["C_extrapolate"]["err"], r["B_stamped"]["err"])

    def test_lagging_stamp_b_equals_c(self):
        # Every stamp is inside the buffer, so C never extrapolates and is B bit for bit.
        for seed in tf.SEEDS:
            r = tf.run("lagging_stamp", seed)
            self.assertEqual(r["B_stamped"]["err"], r["C_extrapolate"]["err"])
            self.assertEqual(r["B_stamped"]["wait"], 0.0)

    def test_output_lines(self):
        self.assertEqual(self.out, (ROOT / "examples/month-4/expected/tf_buffer_time_lookup_toy.txt").read_text())
        self.assertRegex(self.out, r"static_tree[\s\S]*paired A-B err: 0\.0000\+-0\.0000: tie: identical on every seed")
        self.assertRegex(self.out, r"lagging_stamp[\s\S]*paired A-B err: [\d.]+\+-[\d.]+: clear gap, not a tie \(\|m\| > sd\); same sign on all 5 seeds")
        self.assertRegex(self.out, r"fresh_stamp[\s\S]*paired C-B err: [\d.]+\+-[\d.]+: clear gap")
        self.assertRegex(self.out, r"tf_dropout[\s\S]*paired A-B fail: -[\d.]+\+-[\d.]+: clear gap")


class Smith(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(SM_REL)

    def test_scope(self):
        self.assertEqual(sm.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / SM_REL).read_text()
        self.assertIn("本页未运行", text)
        self.assertIn("Common random numbers", text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|control)")
        self.assertIn("assert H < 2.0 * tau", text)

    def test_common_random_numbers(self):
        self.assertEqual(sm.shared_draws("long_delay", 1), sm.shared_draws("long_delay", 1))
        self.assertNotEqual(sm.shared_draws("long_delay", 1)["tau"], sm.shared_draws("long_delay", 2)["tau"])

    def test_euler_stability_boundary(self):
        # tau dx/dt = -x: explicit Euler multiplies x by (1 - h / tau) per step; |.| < 1 iff h < 2 tau.
        tau = 0.5
        for factor, grows in ((0.98, False), (1.02, True)):
            x = sm.euler_first_order(1.0, 0.0, 1.0, tau, factor * 2.0 * tau, 400)
            self.assertEqual(abs(x) > 1.0, grows, factor)

    def test_step_halving_converged(self):
        base = sm.run("long_delay", 0, "B_smith")
        old_h, old_sub = sm.H, sm.SUB
        try:
            sm.SUB, sm.H = 2 * old_sub, sm.TS / (2 * old_sub)
            half = sm.run("long_delay", 0, "B_smith")
        finally:
            sm.H, sm.SUB = old_h, old_sub
        self.assertLess(abs(half["ise"] - base["ise"]), 0.01 * base["ise"])

    def test_zero_delay_bit_identical(self):
        # With k = 0 the Smith correction y_model - y_model_delayed is exactly 0, whatever the model gain.
        for seed in sm.SEEDS:
            a, b, c = (sm.run("zero_delay", seed, arm) for arm in sm.ARMS)
            self.assertEqual(a, b)
            self.assertEqual(b, c)

    def test_matched_smith_is_delayed_design(self):
        # Independent check of C_bar = C / (1 + C G (1 - z^-k)): with a true model and no noise or load,
        # the Smith loop's output is the k = 0 loop's output shifted by k periods.
        k = sm.REGIMES["long_delay"][0]
        y0 = trace(dict(K=1.0, tau=0.5, ref=1.0, k=0), "B_smith")
        yk = trace(dict(K=1.0, tau=0.5, ref=1.0, k=k), "B_smith")
        self.assertLess(max(abs(a - b) for a, b in zip(y0[: len(y0) - k], yk[k:])), 1e-9)

    def test_output_lines(self):
        self.assertEqual(self.out, (ROOT / "examples/month-5/expected/smith_predictor_delay_toy.txt").read_text())
        self.assertRegex(self.out, r"zero_delay[\s\S]*paired A-B ise: 0\.0000\+-0\.0000: tie: identical on every seed")
        self.assertRegex(self.out, r"long_delay[\s\S]*paired A-B ise: [\d.]+\+-[\d.]+: clear gap, not a tie \(\|m\| > sd\); same sign on all 5 seeds")
        self.assertRegex(self.out, r"short_delay[\s\S]*paired A-B ise: -[\d.]+\+-[\d.]+: small but consistent gap")
        self.assertRegex(self.out, r"wrong_delay_big[\s\S]*paired C-B ise: [\d.]+\+-[\d.]+: clear gap, not a tie \(\|m\| > sd\); same sign on all 5 seeds")
        self.assertIn("wrong_delay_big pure-mismatch subset (seeds 2-4 only; seeds 0-1 have k_hat=0 so C≡A and inflate the 5-seed mean and sd)", self.out)
        self.assertRegex(self.out, r"pure-mismatch subset[\s\S]*paired C-B over: 13\.5172\+-1\.3548: clear gap, not a tie \(\|m\| > sd\); same sign on all 3 seeds")
        self.assertRegex(self.out, r"pure-mismatch subset[\s\S]*paired C-B ise: 0\.1096\+-0\.0054: clear gap, not a tie \(\|m\| > sd\); same sign on all 3 seeds")
        self.assertRegex(self.out, r"pure-mismatch subset[\s\S]*paired C-B settle: 2\.7367\+-0\.0058: clear gap, not a tie \(\|m\| > sd\); same sign on all 3 seeds")

    def test_wrong_delay_big_pure_mismatch_subset(self):
        # Seeds 0–1 collapse to A (k_hat=0); seeds 2–4 are the pure mismatch.
        for seed in (0, 1):
            d = sm.shared_draws("wrong_delay_big", seed)
            self.assertEqual(d["k_hat_wrong"], 0)
            self.assertEqual(sm.run("wrong_delay_big", seed, "C_smith_wrong"), sm.run("wrong_delay_big", seed, "A_pi_ignore"))
        for seed in (2, 3, 4):
            self.assertGreater(sm.shared_draws("wrong_delay_big", seed)["k_hat_wrong"], 0)
        subset = (2, 3, 4)
        over_c = [sm.run("wrong_delay_big", s, "C_smith_wrong")["over"] for s in subset]
        over_b = [sm.run("wrong_delay_big", s, "B_smith")["over"] for s in subset]
        v = sm.verdict(over_c, over_b)
        self.assertIn("13.5172+-1.3548", v)
        self.assertIn("same sign on all 3 seeds", v)
        self.assertIn("clear gap", v)


def trace(d, arm):
    """Re-run one Smith loop and return x after every period (noise-free helper for the delay-shift test)."""
    gain, tau, k = d["K"], d["tau"], d["k"]
    kp, ti = tau / (gain * sm.LAMBDA_C), tau
    n = int(round(sm.T_END / sm.TS))
    u_hist, ym_hist, x, xm, integ, out = [0.0] * (k + 1), [0.0] * (k + 1), 0.0, 0.0, 0.0, []
    for i in range(n):
        r = d["ref"] if i * sm.TS >= sm.T_STEP else 0.0
        e = r - x - (ym_hist[-1] - ym_hist[-1 - k])
        integ += e * sm.TS / ti
        u = kp * (e + integ)
        u_hist.append(u)
        x = sm.euler_first_order(x, u_hist[-1 - k], gain, tau, sm.H, sm.SUB)
        xm = sm.euler_first_order(xm, u, gain, tau, sm.H, sm.SUB)
        ym_hist.append(xm)
        out.append(x)
    return out


class ExpectedFiles(unittest.TestCase):
    def test_labels_match_numbers(self):
        for rel in ("examples/month-4/expected/tf_buffer_time_lookup_toy.txt", "examples/month-5/expected/smith_predictor_delay_toy.txt"):
            text = (ROOT / rel).read_text()
            self.assertNotRegex(text, r"(?<![\d.e+])-0\.0+(?![\d.e])")
            for line in text.splitlines():
                m = re.search(r": (-?[\d.]+(?:e-?\d+)?)\+-([\d.]+(?:e-?\d+)?): ", line)
                if not m or "paired" not in line:
                    continue
                mu, sd = float(m.group(1)), float(m.group(2))
                if "near-tie" in line:
                    self.assertLessEqual(abs(mu), sd, line)
                elif "gap" in line:
                    self.assertGreater(abs(mu), sd, line)
                    self.assertRegex(line, r"same sign on all [35] seeds|1 of [35] seeds has the opposite sign|no seed has")


if __name__ == "__main__":
    unittest.main()
