#!/usr/bin/env python3
"""Independent contract tests for batch-19 PR1 true-RMS + Zener/LDO toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RMS_REL = "examples/month-1/bench-multimeter/true_rms_vs_average_responding_toy.py"
ZEN_REL = "examples/month-1/components/zener_shunt_ldo_headroom_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rms = load("true_rms_vs_average_responding_toy", RMS_REL)
zen = load("zener_shunt_ldo_headroom_toy", ZEN_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((rms, RMS_REL), (zen, ZEN_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertEqual(mod.SEEDS, (0, 1, 2, 3, 4))
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1e-16, -2e-16, 3e-16, 0.0, 1e-16], [0.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertNotIn("seeds", v)
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("1 of 5 seeds has the opposite sign", mod.verdict([5.0, 5.0, 5.0, 5.0, -0.5], [0.0] * 5))
            src = (ROOT / rel).read_text()
            self.assertIn("Common random numbers", src)
            self.assertIn("本页未运行", src)
            self.assertIn("No integration step", src)
            self.assertIn("written before the first run", src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))


class TrueRms(unittest.TestCase):
    def test_hand_calcs(self):
        self.assertAlmostEqual(rms.SINE_FF, math.pi / (2.0 * math.sqrt(2.0)), places=12)
        self.assertAlmostEqual(rms.analytic_rms("sine"), 1.0 / math.sqrt(2.0), places=12)
        self.assertAlmostEqual(rms.analytic_rms("square"), 1.0, places=12)
        self.assertAlmostEqual(rms.analytic_rms("triangle"), 1.0 / math.sqrt(3.0), places=12)
        self.assertAlmostEqual(rms.analytic_rms("pwm_high_crest"), math.sqrt(rms.DUTY_PWM), places=12)
        self.assertAlmostEqual(rms.analytic_cf("pwm_high_crest"), 4.0, places=12)
        self.assertGreater(rms.analytic_cf("pwm_high_crest"), rms.CF_CAP)

    def test_crn_and_no_time_step(self):
        a = rms.shared_wave("sine", 3)
        b = rms.shared_wave("sine", 3)
        self.assertEqual(a["phase"], b["phase"])
        self.assertEqual(a["v"], b["v"])
        self.assertFalse(any(name in vars(rms) for name in ("DT", "dt", "STEP", "rk4", "euler")))

    def test_declared_regimes_and_expected(self):
        self.assertEqual(list(rms.REGIMES), ["sine", "square", "triangle", "pwm_high_crest"])
        out = run(RMS_REL)
        sine = out.split("sine (analytic_RMS=")[1].split("square (analytic_RMS=")[0]
        self.assertIn("paired B-A reading: -6.112e-06+-1.805e-05: near-tie / small gap, within seed noise (|m| <= sd); 2 of 5 seeds have the opposite sign", sine)
        square = out.split("square (analytic_RMS=")[1].split("triangle (analytic_RMS=")[0]
        self.assertIn("paired B-A reading: 0.1107+-8.278e-07: small but consistent gap, not a tie (|m| > sd); same sign on all 5 seeds", square)
        self.assertIn("paired C-A reading: -0.2902+-2.475e-04: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", square)
        pwm = out.split("pwm_high_crest (analytic_RMS=")[1].split("alternative")[0]
        self.assertIn("paired B-A reading: -0.1793+-0.0024: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", pwm)
        self.assertIn("paired C-A reading: 0.4603+-0.0053: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", pwm)
        self.assertIn("hand_calc 1V_peak_sine: RMS=Vp/sqrt(2)=0.7071067812 V", out)
        self.assertIn("error=0.1107207345 V (11.0721 %)", out)
        self.assertIn("alternative CF_CAP=2.0 on pwm_high_crest (same seeds):", out)
        self.assertIn("alternative CF_CAP=4.0 on pwm_high_crest (same seeds):", out)
        self.assertEqual((ROOT / "examples/month-1/expected/true_rms_vs_average_responding_toy.txt").read_text(), out)


class ZenerLdo(unittest.TestCase):
    def test_hand_and_boundary(self):
        self.assertAlmostEqual(zen.HEADROOM, 0.40, places=12)
        self.assertEqual(zen.ldo_solve(5.4, 0.02, 5.0)["in_reg"], 1.0)
        self.assertAlmostEqual(zen.ldo_solve(5.4, 0.02, 5.0)["vout"], 5.0, places=12)
        self.assertEqual(zen.ldo_solve(5.399, 0.02, 5.0)["in_reg"], 0.0)
        ir = (12.0 - 5.0) / 100.0
        iz = ir - 0.020
        pz = 5.0 * iz
        self.assertAlmostEqual(ir, 0.07, places=12)
        self.assertAlmostEqual(iz, 0.05, places=12)
        self.assertAlmostEqual(pz, 0.25, places=12)
        pz_h = 5.0 * ((12.0 - 5.0) / 22.0 - 0.200)
        self.assertAlmostEqual(pz_h, 0.5909090909, places=9)
        self.assertFalse(pz_h < zen.P_THERMAL)
        # Equality is out of budget (strict P < P_THERMAL), matching I_D V_B < P_max
        self.assertEqual(zen.zener_solve(12.0, 0.020, 100.0, 5.0)["thermal_ok"], 1.0)

    def test_crn_and_no_time_step(self):
        a = zen.shared_draw("in_regulation", 3)
        b = zen.shared_draw("in_regulation", 3)
        self.assertEqual(a, b)
        self.assertFalse(any(name in vars(zen) for name in ("DT", "dt", "STEP", "rk4", "euler")))

    def test_declared_regimes_and_expected(self):
        self.assertEqual(list(zen.REGIMES), ["in_regulation", "below_headroom", "thermal_small_R"])
        out = run(ZEN_REL)
        self.assertIn("headroom_boundary: Vin=5.4000000000 V in_reg=1; Vin=5.3990000000 V in_reg=0", out)
        self.assertIn("below_headroom_spare: Vin-Vset=0.1500000000 V (5.15-5.0), below HEADROOM 0.40 V", out)
        self.assertIn("zener_in_reg_rule: in regulation iff I_Z>0 (rz=0 model; not a datasheet knee current I_Z,min)", out)
        self.assertIn("hand_calc Vin=12.0 V R=100 ohm VZ=5.0 V IL=0.020 A: IR=(Vin-VZ)/R=0.0700000000 A; IZ=IR-IL=0.0500000000 A; PZ=VZ*IZ=0.2500000000 W", out)
        reg = out.split("in_regulation (")[1].split("below_headroom (")[0]
        self.assertIn("paired A-B vout: -0.0233+-0.0516: near-tie / small gap, within seed noise (|m| <= sd); 2 of 5 seeds have the opposite sign", reg)
        below = out.split("below_headroom (")[1].split("thermal_small_R (")[0]
        self.assertIn("paired B in_reg vs 1: -1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", below)
        self.assertIn("paired A in_reg vs 1: -1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", below)
        therm = out.split("thermal_small_R (Vin_nom=12.00")[1].split("thermal_small_R light-load")[0]
        self.assertIn("paired A thermal_ok vs 1: -1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", therm)
        self.assertIn("A_zener_shunt light p 1.5368+-0.0231", out)
        self.assertIn("alternative HEADROOM=0.20 V on below_headroom (same seeds):", out)
        self.assertIn("alternative P_THERMAL=0.80 W on thermal_small_R (same seeds):", out)
        self.assertEqual((ROOT / "examples/month-1/expected/zener_shunt_ldo_headroom_toy.txt").read_text(), out)


if __name__ == "__main__":
    unittest.main()
