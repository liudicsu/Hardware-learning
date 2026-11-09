#!/usr/bin/env python3
"""Independent contract tests for batch-15 PR1 Nyquist aliasing + notch-on-resonance toys; stdlib only."""
from __future__ import annotations

import cmath
import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NY_REL = "examples/month-1/python-terminal/nyquist_aliasing_toy.py"
NO_REL = "examples/month-3/pid-control/notch_vs_lead_resonant_toy.py"
LL_REL = "examples/month-3/pid-control/lead_lag_vs_pid_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ny = load("nyquist_aliasing_toy", NY_REL)
no = load("notch_vs_lead_resonant_toy", NO_REL)
ll = load("lead_lag_vs_pid_toy", LL_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Labels(unittest.TestCase):
    """Both toys share one labelling rule; check it on hand-made paired data."""

    def test_order_and_thresholds(self):
        for mod, rel in ((ny, NY_REL), (no, NO_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1.0 + 1e-12, 1.0, 1.0 - 1e-12, 1.0, 1.0], [1.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertNotIn("seeds", v)  # no sign count on a numerically-zero line
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("same sign on all 5 seeds", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            src = (ROOT / rel).read_text()
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))

    def test_no_signed_zero(self):
        for mod in (ny, no):
            self.assertEqual(mod.num(-1e-5), "-1.000e-05")
            self.assertEqual(mod.num(0.0), "0.0000")
            self.assertNotEqual(mod.num(-4e-5), "-0.0000")


class Nyquist(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(NY_REL)

    def test_scope(self):
        self.assertEqual(ny.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / NY_REL).read_text()
        self.assertIn("本页未运行", text)
        self.assertIn("Common random numbers", text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
        # No integration step: samples are evaluated in closed form, nothing is stepped in time.
        self.assertNotRegex(text, r"\bDT\b|\bdt\b|rk4|euler")
        self.assertIn("no time step", self.out)

    def test_common_random_numbers(self):
        self.assertEqual(ny.shared_trial("interferer", 2, 3), ny.shared_trial("interferer", 2, 3))
        self.assertNotEqual(ny.shared_trial("interferer", 2, 3), ny.shared_trial("interferer", 3, 3))
        tones, noise = ny.shared_trial("single_tone", 1, 0)
        # B and C see the same tones and the same noise samples; only the prefilter differs.
        b, c = ny.sample("B_aaf", tones, noise), ny.sample("C_raw", tones, noise)
        g = ny.prefilter(tones[0][0], ny.FS_HIGH)
        for n in range(len(b)):
            self.assertAlmostEqual(b[n] - noise[n], g * (c[n] - noise[n]), delta=1e-12)

    def test_folding_boundary(self):
        # Independent check at 0.98x and 1.02x the Nyquist frequency of fs = 100 Hz.
        fs = 100
        for f, seen in ((49, 49), (51, 49)):
            x = [math.sin(2 * math.pi * f * n / fs + 0.3) for n in range(fs)]
            spec = {k: abs(sum(v * cmath.exp(-2j * math.pi * k * i / fs) for i, v in enumerate(x))) for k in range(1, fs // 2)}
            self.assertEqual(max(spec, key=spec.get), seen, f)
            self.assertEqual(ny.alias(f, fs), seen)
        self.assertEqual(ny.alias(150, 200), 50)

    def test_safe_rule(self):
        self.assertTrue(ny.safe("B_aaf", [(40, 1.0, 0.0), (150, 0.5, 0.0)]))  # 150 Hz filtered to 0.0301 x 0.5
        self.assertFalse(ny.safe("C_raw", [(40, 1.0, 0.0), (150, 0.5, 0.0)]))
        self.assertFalse(ny.safe("A_low", [(40, 1.0, 0.0)]))  # 50 Hz < 2 x 40 Hz
        self.assertTrue(ny.safe("A_low", [(8, 1.0, 0.0)]))

    def test_output_lines(self):
        self.assertEqual(self.out, (ROOT / "examples/month-1/expected/nyquist_aliasing_toy.txt").read_text())
        self.assertRegex(self.out, r"single_tone[\s\S]*?paired A-B freq: [\d.]+\+-[\d.]+: clear gap")
        self.assertRegex(self.out, r"single_tone[\s\S]*?paired C-B amp: -[\d.]+\+-[\d.]+: clear gap")
        self.assertRegex(self.out, r"interferer[\s\S]*?paired C-B false: [\d.]+\+-[\d.]+: clear gap")
        self.assertRegex(self.out, r"near_edge[\s\S]*?paired C-B amp: -[\d.]+\+-[\d.]+: clear gap")
        self.assertRegex(self.out, r"slow_tone[\s\S]*?paired A-B freq: 0\.0000\+-0\.0000: tie: identical on every seed")


class Notch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(NO_REL)

    def test_scope(self):
        self.assertEqual(no.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / NO_REL).read_text()
        self.assertIn("本页未运行", text)
        self.assertIn("Common random numbers", text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|control)")

    def test_common_random_numbers(self):
        self.assertEqual(no.shared_draws(3), no.shared_draws(3))
        self.assertNotEqual(no.shared_draws(3)[2], no.shared_draws(4)[2])

    def test_rk4_stability_boundary(self):
        # Independent: x <- R(h lambda) x decays at 0.98 h_max and grows at 1.02 h_max for the sharp mode.
        lam = complex(-0.05 * 40.0, 40.0 * math.sqrt(1 - 0.05 ** 2))
        h_max = no.rk4_h_max(lam)
        self.assertGreater(h_max, 100 * no.H)
        for factor, grows in ((0.98, False), (1.02, True)):
            z = factor * h_max * lam
            r = 1 + z + z * z / 2 + z ** 3 / 6 + z ** 4 / 24
            x = 1.0 + 0j
            for _ in range(5000):
                x *= r
                if abs(x) > 1e6:
                    break
            self.assertEqual(abs(x) > 1.0, grows, factor)

    def test_step_halving(self):
        dr = no.shared_draws(0)
        a = no.simulate("B_notch", 40.0, 0.2, dr)
        b = no.simulate("B_notch", 40.0, 0.2, dr, sub=2 * no.SUB)
        for k in a:
            self.assertAlmostEqual(a[k], b[k], delta=1e-6 * max(1.0, abs(a[k])))

    def test_discrete_notch_matches_continuous(self):
        c = no.Controller("B_notch", 1.0)
        b0, b1, b2, a1, a2 = c.secs[0][:5]
        for w in (5.0, 20.0, 60.0, 200.0):
            z = cmath.exp(1j * w * no.TS)
            hd = (b0 + b1 / z + b2 / z / z) / (1 + a1 / z + a2 / z / z)
            self.assertAlmostEqual(abs(hd), abs(no.notch(w, no.WN, no.WIDTH * no.WN)), delta=1e-3)
        z = cmath.exp(1j * no.WN * no.TS)
        self.assertLess(abs((b0 + b1 / z + b2 / z / z) / (1 + a1 / z + a2 / z / z)), 1e-3)

    def test_lead_arm_reproduces_lead_lag_toy(self):
        dr = no.shared_draws(1)
        for wr, zr in ((0.0, 0.0), (40.0, 0.3)):
            mine = no.simulate("C_leadlag", wr, zr, dr)
            theirs = ll.simulate("B_leadlag", wr, zr, ll.shared_draws(1))
            for k in mine:
                self.assertAlmostEqual(mine[k], theirs[k], delta=1e-9)

    def test_output_lines(self):
        self.assertEqual(self.out, (ROOT / "examples/month-3/expected/notch_vs_lead_resonant_toy.txt").read_text())
        self.assertRegex(self.out, r"well_damped paired B-A ise: [\d.]+\+-[\d.]+: clear gap")
        self.assertRegex(self.out, r"resonant paired B-A ise: [\d.]+\+-[\d.]+: clear gap")
        self.assertIn("resonant_sharp A_pid diverged (|y| > 10 rad) on 5 of 5 seeds", self.out)
        self.assertRegex(self.out, r"resonant_sharp B_notch [\d.]+\+-")
        self.assertIn("resonant_light C_leadlag diverged", self.out)
        self.assertIn("0.5 was fixed before the first run", self.out)
        self.assertIn("alternative zr=0.1", self.out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
