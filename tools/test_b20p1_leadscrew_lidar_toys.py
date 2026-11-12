#!/usr/bin/env python3
"""Independent contract tests for batch-20 PR1 leadscrew + lidar realism toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LS_REL = "examples/month-3/transmissions/leadscrew_self_locking_toy.py"
LI_REL = "examples/month-4/gazebo-sim/gazebo_lidar_realism_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ls = load("leadscrew_self_locking_toy", LS_REL)
li = load("gazebo_lidar_realism_toy", LI_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def section(out: str, start: str, end: str) -> str:
    return out.split(start)[1].split(end)[0]


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((ls, LS_REL), (li, LI_REL)):
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
            self.assertIn("Common random numbers", src)
            self.assertIn("本页未运行", src)
            self.assertIn("No integration step", src)
            self.assertIn("written before the first run", src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))
            self.assertFalse(any(name in vars(mod) for name in ("DT", "dt", "STEP", "rk4", "euler")))


class Leadscrew(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((ls.F_NOM, ls.DM, ls.MU_NOM, ls.VIB_FACTOR), (500.0, 0.010, 0.15, 0.30))
        self.assertEqual((ls.LEAD_A, ls.LEAD_B), (0.010, 0.002))
        self.assertEqual(ls.ARMS, ("A_steep", "B_fine", "C_vibrated"))
        self.assertEqual(list(ls.REGIMES), ["nominal", "borderline"])

    def test_formulas_match_wikipedia_form(self):
        # Independent form: T = F*dm/2 * tan(phi +/- lambda); eta = tan(lambda)/tan(phi+lambda).
        for lead, mu in ((0.002, 0.15), (0.010, 0.15), (0.002, 0.045), (0.0047, 0.12)):
            r = ls.screw(500.0, lead, mu)
            lam, phi = math.atan(lead / (math.pi * 0.010)), math.atan(mu)
            self.assertAlmostEqual(r["t_raise"], 500.0 * 0.010 / 2 * math.tan(phi + lam), places=12)
            self.assertAlmostEqual(r["t_lower"], 500.0 * 0.010 / 2 * math.tan(phi - lam), places=12)
            self.assertAlmostEqual(r["eta"], math.tan(lam) / math.tan(phi + lam), places=12)
            self.assertEqual(r["holds"] == 1.0, phi > lam)

    def test_boundary_is_strict(self):
        lead = math.pi * ls.DM * ls.MU_NOM
        tl = math.tan(ls.lead_angle(lead))
        self.assertEqual(ls.screw(500.0, lead, tl)["holds"], 0.0)
        self.assertAlmostEqual(ls.screw(500.0, lead, tl)["t_lower"], 0.0, places=12)
        self.assertEqual(ls.screw(500.0, lead, tl + 1e-6)["holds"], 1.0)
        self.assertEqual(ls.screw(500.0, lead, tl - 1e-6)["holds"], 0.0)

    def test_crn(self):
        self.assertEqual(ls.shared_draws("nominal", 2), ls.shared_draws("nominal", 2))
        mu, f = ls.shared_draws("nominal", 2)
        a, b = ls.run_arm("A_steep", "nominal", 2), ls.run_arm("B_fine", "nominal", 2)
        self.assertAlmostEqual(a["t_raise"], ls.screw(f, ls.LEAD_A, mu)["t_raise"], places=12)
        self.assertAlmostEqual(b["t_raise"], ls.screw(f, ls.LEAD_B, mu)["t_raise"], places=12)
        c = ls.run_arm("C_vibrated", "nominal", 2)
        self.assertAlmostEqual(c["t_raise"], ls.screw(f, ls.LEAD_B, mu * ls.VIB_FACTOR)["t_raise"], places=12)

    def test_expected(self):
        out = run(LS_REL)
        self.assertIn("T_raise=500.0*0.010/2*tan(12.1734 deg)=0.5393 N*m T_lower=500.0*0.010/2*tan(4.8881 deg)=0.2138 N*m eta=tan(lambda)/tan(phi+lambda)=0.2951", out)
        nom = section(out, "nominal (", "borderline (")
        self.assertIn("paired B-A t_lower: 0.5823+-0.0264: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", nom)
        self.assertIn("paired B-A eta: -0.3505+-0.0034: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", nom)
        self.assertIn("paired C-B t_lower: -0.2535+-0.0395: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", nom)
        bor = section(out, "borderline (", "alternative ")
        self.assertIn("paired B-A holds: 0.6000+-0.5477: clear gap, not a tie (|m| > sd); no seed has the opposite sign, 2 of 5 equal", bor)
        self.assertIn("B_fine eta 0.4869+-0.0352 t_raise 0.7669+-0.0704 t_lower 0.0050+-0.0478 holds 0.6000+-0.5477 holds_on 3/5", bor)
        for reg in (nom, bor):
            self.assertIn("self_lock_flag_check: holds == (phi > lambda) == (T_lower > 0) on every arm and seed: True", reg)
        self.assertIn("paired C-B holds@alt: 0.0000+-0.0000: tie: identical on every seed", out)
        self.assertIn("paired B-A holds@alt: 0.8000+-0.4472", out)
        self.assertEqual((ROOT / "examples/month-3/expected/leadscrew_self_locking_toy.txt").read_text(), out)


class Lidar(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((li.MIN, li.MAX, li.SIGMA, li.N_BEAMS), (0.20, 8.0, 0.01, 61))
        self.assertEqual((li.C_BIAS, li.P_DROP_C, li.R_BIAS, li.R_SIGMA, li.P_DROP_R, li.TOL), (0.015, 0.5, 0.02, 0.012, 0.6, 0.10))
        self.assertEqual(list(li.REGIMES), ["clear_wall", "glossy", "min_range", "visual_only"])
        xacro = (ROOT / "examples/month-4/gazebo-sim/m4_gazebo/urdf/sensors.gazebo.xacro").read_text()
        for tag in ("<min>0.20</min>", "<max>8.0</max>", "<stddev>0.01</stddev>"):
            self.assertIn(tag, xacro)

    def test_geometry_and_clamp(self):
        # Collision-only box invisible to visual rays; visual-only banner invisible to collision rays.
        surf = li.REGIMES["visual_only"]
        theta = math.atan2(-0.35, 1.0)
        self.assertAlmostEqual(li.cast(theta, surf, "collision")[0], 1.0 / math.cos(theta), places=12)
        self.assertAlmostEqual(li.cast(theta, surf, "visual")[0], 2.5 / math.cos(theta), places=12)
        theta = math.atan2(0.45, 0.9)
        self.assertAlmostEqual(li.cast(theta, surf, "visual")[0], 0.9 / math.cos(theta), places=12)
        self.assertAlmostEqual(li.cast(theta, surf, "collision")[0], 2.5 / math.cos(theta), places=12)
        # B clamps a below-min surface to MIN; C and R return nothing; A reports the truth.
        zero = [(0.0, 0.99)] * li.N_BEAMS
        a, b, c = (li.scan(arm, "min_range", zero) for arm in li.ARMS)
        mid = li.N_BEAMS // 2
        self.assertAlmostEqual(a[mid], 0.12, places=12)
        self.assertEqual(b[mid], li.MIN)
        self.assertIsNone(c[mid])
        self.assertIsNone(li.scan("R", "min_range", zero)[mid])

    def test_crn(self):
        s1, r1 = li.shared_draws("glossy", 3)
        s2, r2 = li.shared_draws("glossy", 3)
        self.assertEqual((s1, r1), (s2, r2))
        self.assertNotEqual(s1, r1)

    def test_expected(self):
        out = run(LI_REL)
        self.assertIn("hand_calc straight-ahead wall: 1.80 - 0.12 = 1.68 m; beam at 30 deg: 1.68 / cos(30 deg) = 1.9399 m", out)
        self.assertIn("  boundary below MIN: true=0.1200 m -> A 0.1200 B 0.2000 C none (no noise, no bias)", out)
        self.assertIn("  boundary at MIN: true=0.2000 m -> A 0.2000 B 0.2000 C 0.2000 (no noise, no bias)", out)
        clear = section(out, "clear_wall (", "glossy (")
        self.assertIn("paired B-A mean_err: 0.0011+-0.0013: near-tie / small gap, within seed noise (|m| <= sd); 1 of 5 seeds has the opposite sign", clear)
        self.assertIn("paired C-A mean_err: 0.0161+-0.0013: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", clear)
        gl = section(out, "glossy (", "min_range (")
        self.assertIn("paired A-C ret_err: 0.2689+-0.0563: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", gl)
        self.assertIn("paired A-C mismatch: 3.6000+-2.7928: small but consistent gap, not a tie (|m| > sd); same sign on all 5 seeds", gl)
        mr = section(out, "min_range (", "visual_only (")
        self.assertIn("paired A-C mismatch: 19.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", mr)
        self.assertIn("paired A-C near_err: 1.5834+-0.0089: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", mr)
        vo = section(out, "visual_only (", "alternative ")
        self.assertIn("paired A-C mismatch: 27.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", vo)
        self.assertIn("paired B-C mismatch: 27.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", vo)
        self.assertIn("clear_wall paired A-C mismatch@TOL0.05: 0.4000+-0.5477: near-tie", out)
        self.assertIn("paired A-C ret_err@alt: 0.2492+-0.1052: clear gap", out)
        self.assertEqual((ROOT / "examples/month-4/expected/gazebo_lidar_realism_toy.txt").read_text(), out)


if __name__ == "__main__":
    unittest.main()
