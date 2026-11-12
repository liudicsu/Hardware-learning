#!/usr/bin/env python3
"""Independent contract tests for batch-18 PR1 superposition + form-closure toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SP_REL = "examples/month-1/ohms-law/superposition_linear_circuit_toy.py"
FC_REL = "examples/month-3/gripper-fingers/form_closure_frictionless_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sp = load("superposition_linear_circuit_toy", SP_REL)
fc = load("form_closure_frictionless_toy", FC_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((sp, SP_REL), (fc, FC_REL)):
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


class Superposition(unittest.TestCase):
    def test_hand_voltages(self):
        v = sp.linear_node(sp.VS1, sp.VS2)
        v1 = sp.linear_node(sp.VS1, 0.0)
        v2 = sp.linear_node(0.0, sp.VS2)
        self.assertAlmostEqual(v, 26.0 / 7.0, places=12)
        self.assertAlmostEqual(v1, 20.0 / 7.0, places=12)
        self.assertAlmostEqual(v2, 6.0 / 7.0, places=12)
        self.assertEqual(v - (v1 + v2), 0.0)
        i1 = (sp.VS1 - v) / sp.R1
        i2 = (v - sp.VS2) / sp.R2
        i3 = v / sp.R3
        self.assertAlmostEqual(i1 - i2 - i3, 0.0, places=15)

    def test_nonlinear_residual(self):
        v = sp.nonlinear_node(sp.VS1, sp.VS2)
        v1 = sp.nonlinear_node(sp.VS1, 0.0)
        v2 = sp.nonlinear_node(0.0, sp.VS2)
        self.assertAlmostEqual(v, 3.425, places=12)
        self.assertAlmostEqual(v1 + v2, 3.6, places=12)
        self.assertAlmostEqual((v1 + v2) - v, 0.175, places=12)
        self.assertGreater(v, sp.VF)
        self.assertAlmostEqual(sp.nonlinear_residual(v, sp.VS1, sp.VS2, sp.VF, sp.RF), 0.0, places=12)

    def test_crn_and_no_time_step(self):
        d1 = sp.shared_noise("linear_meter", 3, sp.SIGMA)
        d2 = sp.shared_noise("linear_meter", 3, sp.SIGMA)
        self.assertEqual(d1, d2)
        self.assertEqual(len(d1), sp.BOARDS)
        self.assertFalse(any(name in vars(sp) for name in ("DT", "dt", "STEP", "rk4", "euler")))

    def test_declared_regimes_and_expected(self):
        self.assertEqual(list(sp.REGIMES), ["linear_noiseless", "linear_meter", "nonlinear_diode"])
        out = run(SP_REL)
        self.assertIn("paired A-B nodeV: 0.0000+-0.0000: tie: identical on every seed", out.split("linear_noiseless")[1].split("linear_meter")[0])
        meter = out.split("linear_meter (")[1].split("nonlinear_diode (")[0]
        self.assertIn("paired A-B nodeV: -0.0001+-0.0003: near-tie / small gap, within seed noise (|m| <= sd); 1 of 5 seeds has the opposite sign", meter)
        diode = out.split("nonlinear_diode (")[1].split("alternative")[0]
        self.assertIn("paired residual B-A vs 0: 0.1750+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", diode)
        self.assertIn("alternative linear_meter sigma=0.01 V", out)
        self.assertIn("alternative nonlinear Rf=1000ohm V_joint=2.8800000000 V", out)
        self.assertEqual((ROOT / "examples/month-1/expected/superposition_linear_circuit_toy.txt").read_text(), out)


class FormClosure(unittest.TestCase):
    def test_nominal_witnesses(self):
        nom_b = [fc.contact(e, s) for e, s in fc.NOMINAL_B]
        nom_a = nom_b[:3]
        nom_c = [fc.contact(e, s) for e, s in fc.NOMINAL_C]
        nom_al = [fc.contact(e, s) for e, s in fc.NOMINAL_ALIGNED]
        self.assertEqual(fc.is_closed(fc.frictionless_wrenches(nom_b)), 1.0)
        self.assertEqual(fc.is_closed(fc.frictionless_wrenches(nom_a)), 0.0)
        self.assertEqual(fc.is_closed(fc.frictionless_wrenches(nom_c)), 0.0)
        self.assertEqual(fc.is_closed(fc.frictionless_wrenches(nom_al)), 0.0)
        self.assertEqual(fc.is_closed(fc.cone_wrenches(nom_c, fc.MU)), 1.0)
        mid = [fc.contact(e, 0.50) for e, _ in fc.NOMINAL_B]
        self.assertEqual(fc.is_closed(fc.frictionless_wrenches(mid)), 0.0)
        esc = fc.escape_twist(fc.frictionless_wrenches(mid))
        self.assertIsNotNone(esc)
        self.assertAlmostEqual(abs(esc[2]), 1.0, places=6)

    def test_mid_edge_moment_vanishes(self):
        w = fc.wrench((1.0, 0.0), (-1.0, 0.0))
        self.assertEqual(w, (-1.0, 0.0, 0.0))

    def test_crn_shared_across_mu(self):
        a = fc.shared_contacts("mu0_form", 3, fc.JITTER)
        b = fc.shared_contacts("large_mu_force", 3, fc.JITTER)
        self.assertEqual(a["B_four"], b["B_four"])
        self.assertEqual(a["C_two_finger"], b["C_two_finger"])
        self.assertEqual(len(a["A_three"]), 3)
        self.assertEqual(len(a["B_four"]), 4)
        self.assertEqual(len(a["C_two_finger"]), 2)

    def test_declared_regimes_and_expected(self):
        self.assertEqual(list(fc.REGIMES), ["mu0_form", "large_mu_force", "aligned_normals"])
        out = run(FC_REL)
        mu0 = out.split("mu0_form (")[1].split("large_mu_force (")[0]
        self.assertIn("paired B-A form_mu0: 1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", mu0)
        self.assertIn("paired B-C form_mu0: 1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", mu0)
        large = out.split("large_mu_force (")[1].split("aligned_normals (")[0]
        self.assertIn("paired C-A force_at_regime_mu: 0.0000+-0.0000: tie: identical on every seed", large)
        self.assertIn("paired C-B force_at_regime_mu: 0.0000+-0.0000: tie: identical on every seed", large)
        self.assertIn("paired B-C form_mu0: 1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", large)
        aligned = out.split("aligned_normals (")[1].split("alternative")[0]
        self.assertIn("paired B_four-B_aligned form_mu0: 1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", aligned)
        self.assertIn("paper_min_frictionless_wrenches_2d_polygon=4", out)
        self.assertIn("paper_min_contact_points_3d=7", out)
        self.assertIn("alternative four mid-edge contacts", out)
        self.assertIn("alternative mu=0.2", out)
        self.assertEqual((ROOT / "examples/month-3/expected/form_closure_frictionless_toy.txt").read_text(), out)


if __name__ == "__main__":
    unittest.main()
