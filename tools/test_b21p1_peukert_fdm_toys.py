#!/usr/bin/env python3
"""Independent contract tests for batch-21 PR1 Peukert + FDM orientation toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PK_REL = "examples/month-1/components/peukert_rate_capacity_toy.py"
FD_REL = "examples/month-3/fdm-printing/fdm_build_orientation_anisotropy_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pk = load("peukert_rate_capacity_toy", PK_REL)
fd = load("fdm_build_orientation_anisotropy_toy", FD_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def section(out: str, start: str, end: str) -> str:
    return out.split(start)[1].split(end)[0]


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((pk, PK_REL), (fd, FD_REL)):
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
            for marker in ("Common random numbers", "本页未运行", "No integration step", "written before the first run", "ROUND_HALF_UP"):
                self.assertIn(marker, src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))
            self.assertFalse(any(name in vars(mod) for name in ("DT", "dt", "STEP", "rk4", "euler")))

    def test_half_up(self):
        for mod in (pk, fd):
            self.assertEqual(mod.num(0.00078125 * 10), "0.0078")
            self.assertEqual(mod.num(0.12345), "0.1235")  # Decimal(repr) half-up, not banker's / binary
            self.assertEqual(mod.num(2.00005), "2.0001")
            self.assertEqual(mod.num(-0.00001), "-1.000e-5")
            self.assertEqual(mod.num(0.00012345), "1.235e-4")
            self.assertEqual(mod.num(-0.0), "0.0000")


class Peukert(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((pk.C_RATED, pk.H_RATED, pk.K_DECL), (100.0, 20.0, 1.2))
        self.assertEqual((pk.K_LA_LO, pk.K_LA_HI, pk.K_ONE_LO, pk.K_ONE_HI), (1.15, 1.25, 1.00, 1.03))
        self.assertEqual((pk.I_KNEE, pk.GAMMA, pk.D_DERATE, pk.I_SD), (50.0, 0.25, 0.80, 0.05))
        self.assertEqual(pk.ARMS, ("A_nameplate", "B_peukert", "C_k1", "D_cap"))
        self.assertEqual(list(pk.REGIMES), ["rated", "high", "very_high", "low", "misapplied"])

    def test_formula_matches_wikipedia(self):
        # Independent form: t = H * (C/(I*H))**k; Wikipedia example 100 Ah, 20 h, k=1.2, 10 A -> ~8.7 h, ~87 Ah.
        t = 20.0 * (100.0 / (10.0 * 20.0)) ** 1.2
        self.assertAlmostEqual(pk.peukert_t(10.0, 1.2), t, places=12)
        self.assertEqual(round(t, 1), 8.7)
        self.assertEqual(round(10.0 * t), 87)
        for k in (1.0, 1.1, 1.2, 1.3, 1.6):
            self.assertEqual(pk.peukert_t(pk.C_RATED / pk.H_RATED, k), pk.H_RATED)
        for i in (0.5, 5.0, 20.0, 100.0):
            self.assertAlmostEqual(pk.predict("C_k1", i), pk.predict("A_nameplate", i), places=9)
            # delivered charge I*t = C*(C/(I*H))**(k-1)
            self.assertAlmostEqual(i * pk.peukert_t(i, 1.2), 100.0 * (100.0 / (i * 20.0)) ** 0.2, places=9)

    def test_boundary_strict(self):
        b = pk.predict("B_peukert", pk.I_KNEE)
        self.assertEqual(pk.predict("D_cap", pk.I_KNEE), b)
        self.assertAlmostEqual(pk.predict("D_cap", pk.I_KNEE + 1e-6) / pk.predict("B_peukert", pk.I_KNEE + 1e-6), 0.8, places=12)

    def test_crn(self):
        for regime in pk.REGIMES:
            for seed in pk.SEEDS:
                k = pk.shared_k(regime, seed)
                self.assertEqual(k, pk.shared_k(regime, seed))
                tts = {pk.run_arm(arm, regime, seed)["t_true"] for arm in pk.ARMS}
                self.assertEqual(len(tts), 1)
                lo, hi = (pk.K_LA_LO, pk.K_LA_HI) if pk.REGIMES[regime]["pack"] == "lead_acid" else (pk.K_ONE_LO, pk.K_ONE_HI)
                self.assertTrue(lo <= k <= hi)

    def test_expected(self):
        out = run(PK_REL)
        self.assertIn("t=20*(100/(10*20))^1.2=8.7055 h, delivered I*t=87.0551 Ah", out)
        self.assertIn("boundary_rule: I=I_KNEE=50.0000 A -> D/B=1.0000 (no cap at equality); I=I_KNEE+1e-6 A -> D/B=0.8000", out)
        r = section(out, "rated (", "high (")
        self.assertIn("paired A-B t: 0.0000+-0.0000: tie: identical on every seed", r)
        self.assertIn("paired A-B abs_err: 0.0000+-0.0000: tie: identical on every seed", r)
        h = section(out, "\nhigh (", "very_high (")
        self.assertIn("paired A-B abs_err: 1.0280+-0.2552: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", h)
        self.assertIn("A_nameplate over-predicts (err > 0) on 5/5 seeds", h)
        v = section(out, "very_high (", "\nlow (")
        self.assertIn("B_peukert over-predicts (err > 0) on 5/5 seeds", v)
        self.assertIn("paired D-B abs_err: -0.0277+-0.0757: near-tie / small gap, within seed noise (|m| <= sd); 2 of 5 seeds have the opposite sign", v)
        lo = section(out, "\nlow (", "misapplied (")
        self.assertIn("B_peukert t 316.9786+-0.0000 q 158.4893+-0.0000", lo)
        self.assertIn("paired A-B abs_err: 38.3430+-39.5659: near-tie", lo)
        m = section(out, "misapplied (", "alternative ")
        self.assertIn("paired A-B abs_err: -1.0787+-0.1315: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", m)
        for reg in (r, h, v, lo, m):
            self.assertIn("paired C-A t: 0.0000+-0.0000: tie: identical on every seed", reg)
        self.assertIn("D_DERATE=0.90: paired D-B abs_err@alt: -0.0393+-0.0251", out)
        self.assertEqual((ROOT / "examples/month-1/expected/peukert_rate_capacity_toy.txt").read_text(), out)


class FDM(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((fd.SPAN, fd.WIDTH, fd.THICK), (80.0, 15.0, 5.0))
        self.assertEqual(fd.SETS["default"]["S"], {"flat": 90.0, "edge": 85.0, "up": 55.0})
        self.assertEqual(fd.SETS["zigzag_like"]["E"], {"flat": 3.0, "edge": 2.2, "up": 2.5})
        self.assertEqual(fd.ARMS, ("A_flatwise", "B_upright", "C_isotropic", "D_edgewise"))
        self.assertEqual(list(fd.REGIMES), ["light", "mid", "modulus"])
        src = (ROOT / FD_REL).read_text()
        for paper_value in ("107.95", "62.32", "3.36", "2.185"):
            self.assertNotIn(paper_value, src)  # paper numbers are cited, not toy outputs

    def test_beam_theory(self):
        self.assertAlmostEqual(fd.peak_stress(220.0), 3 * 220 * 80 / (2 * 15 * 25), places=12)
        self.assertAlmostEqual(fd.second_moment(), 15 * 125 / 12, places=12)
        self.assertAlmostEqual(fd.deflection(100.0, 3.2), 100 * 80 ** 3 / (48 * 3200 * 15 * 125 / 12), places=12)

    def test_strict_snap_boundary(self):
        # survives iff sigma < S
        for regime in fd.REGIMES:
            for seed in fd.SEEDS:
                for arm in fd.ARMS:
                    r = fd.run_arm(arm, regime, seed)
                    self.assertEqual(r["snap"] == 1.0, r["util"] >= 1.0)

    def test_crn(self):
        for regime in fd.REGIMES:
            for seed in fd.SEEDS:
                self.assertEqual(fd.shared_draws(regime, seed), fd.shared_draws(regime, seed))
                self.assertEqual(len({fd.run_arm(a, regime, seed)["sigma"] for a in fd.ARMS}), 1)

    def test_expected(self):
        out = run(FD_REL)
        self.assertIn("sigma=3*220*80/(2*15*5^2)=70.4000 MPa; util vs S_FLAT 90.0 MPa = 0.7822; vs S_UP 55.0 MPa = 1.2800", out)
        self.assertIn("boundary_rule: S=sigma=70.4000 MPa -> snap=1 (equality snaps); S=sigma+1e-6 -> snap=0", out)
        li = section(out, "light (", "mid (")
        self.assertIn("paired B-A snap: 0.0000+-0.0000: tie: identical on every seed", li)
        mid = section(out, "mid (", "modulus (")
        self.assertIn("paired B-A snap: 1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", mid)
        self.assertIn("paired B-C snap: 1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", mid)
        mo = section(out, "modulus (", "alternative ")
        self.assertIn("paired D-A defl: 0.8295+-0.0478: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", mo)
        for reg in (li, mid, mo):
            self.assertIn("paired A-B sigma: 0.0000+-0.0000: tie: identical on every seed", reg)
        self.assertIn("paired B-A snap@alt: 0.2000+-0.4472: near-tie", out)
        self.assertEqual((ROOT / "examples/month-3/expected/fdm_build_orientation_anisotropy_toy.txt").read_text(), out)


if __name__ == "__main__":
    unittest.main()
