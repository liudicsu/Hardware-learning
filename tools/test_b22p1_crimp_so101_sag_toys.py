#!/usr/bin/env python3
"""Independent contract tests for the crimp-vs-solder and SO-101 shared-rail sag toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CR_REL = "examples/month-1/soldering/crimp_vs_solder_strain_relief_toy.py"
SG_REL = "examples/month-3/so101-arm/so101_shared_rail_sag_toy.py"
CR_EXP = "examples/month-1/expected/crimp_vs_solder_strain_relief_toy.txt"
SG_EXP = "examples/month-3/expected/so101_shared_rail_sag_toy.txt"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


cr = load("crimp_vs_solder_strain_relief_toy", CR_REL)
sg = load("so101_shared_rail_sag_toy", SG_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def section(out: str, start: str, end: str) -> str:
    return out.split(start)[1].split(end)[0]


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        for mod, rel in ((cr, CR_REL), (sg, SG_REL)):
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
            for marker in ("Common random numbers", "本页未运行", "written before the first run", "ROUND_HALF_UP"):
                self.assertIn(marker, src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")
            self.assertFalse(any(name in vars(mod) for name in ("DT", "dt", "STEP", "rk4", "euler")))

    def test_expected_byte_identical_and_no_process_labels(self):
        for rel, exp in ((CR_REL, CR_EXP), (SG_REL, SG_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, r"(?i)\bbatch\b|\bPR\d|sources note|来源说明|this batch|本批|this round|本轮")


class Crimp(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((cr.N_STRANDS, cr.D_STRAND, cr.N_REF, cr.EPS_REF, cr.K_FAT), (19, 0.16, 2000, 0.02, 2.0))
        self.assertEqual(cr.RHO, {"A_solder_bare": 3.0, "B_crimp_good": 6.0, "C_crimp_under": 6.0, "D_solder_relief": 12.0})
        self.assertEqual(cr.GAS["C_crimp_under"], 0)
        self.assertEqual(list(cr.REGIMES), ["flex", "light_flex", "static"])

    def test_strain_and_life_independent(self):
        for rho, life in ((3.0, 1125.0), (6.0, 4500.0), (12.0, 18000.0)):
            eps = 0.16 / (2 * rho)
            self.assertAlmostEqual(2000 * (0.02 / eps) ** 2, life, places=6)

    def test_crn_shared_and_arms_differ_only_by_rho_contact(self):
        for regime in cr.REGIMES:
            for seed in cr.SEEDS:
                self.assertEqual(cr.shared_draws(regime, seed), cr.shared_draws(regime, seed))
                b = cr.run_arm("B_crimp_good", regime, seed)
                c = cr.run_arm("C_crimp_under", regime, seed)
                self.assertEqual(b["intact"], c["intact"])
                self.assertEqual(b["life_half"], c["life_half"])
                self.assertGreater(c["contact_mohm"], b["contact_mohm"])

    def test_flex_directions(self):
        out = run(CR_REL)
        flex = section(out, "flex (", "light_flex (")
        self.assertRegex(flex, r"paired B-A intact: 16\.2000\+-1\.6432: clear gap.*same sign on all 5 seeds")
        self.assertRegex(flex, r"paired C-D contact_mohm: 2\.1192\+-0\.0670: clear gap")
        self.assertRegex(flex, r"paired C-D intact: 0\.0000\+-0\.0000: tie: identical on every seed")
        static = out.split("static (")[1].split("alternatives")[0]
        self.assertRegex(static, r"paired B-A intact: 0\.0000\+-0\.0000: tie")


class Sag(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((sg.V_SUP, sg.I_RATED, sg.I_STALL, sg.V_FLOOR, sg.I_NAMEPLATE), (5.0, 0.5, 2.0, 4.0, 4.0))
        self.assertEqual(sg.ARM_R, {"A_ideal": (0.0, 0.0), "B_wired": (0.10, 0.05), "C_thick": (0.03, 0.025)})
        self.assertEqual(sg.JOINTS[0], "shoulder_pan")
        self.assertEqual(sg.JOINTS[-1], "gripper")
        self.assertEqual(sg.STALLED["one_stall"], (6,))

    def independent_vmin(self, lead, seg, currents):
        # Node voltages walking the chain: lead carries all, link k carries the servos beyond it.
        v = 5.0 - lead * sum(currents)
        vs = [v]
        for k in range(1, 6):
            v -= seg * sum(currents[k:])
            vs.append(v)
        return min(vs)

    def test_nominal_hand_calc(self):
        self.assertAlmostEqual(self.independent_vmin(0.10, 0.05, [2.0] * 6), 2.3, places=12)
        self.assertAlmostEqual(self.independent_vmin(0.10, 0.05, [0.5] * 6), 4.325, places=12)
        # Stall at the near end costs less than at the far end (exercise 4 check).
        self.assertGreater(self.independent_vmin(0.10, 0.05, [2.0] + [0.5] * 5), 4.0)
        self.assertLess(self.independent_vmin(0.10, 0.05, [0.5] * 5 + [2.0]), 4.0)

    def test_toy_matches_independent_solver(self):
        for regime in sg.STALLED:
            for seed in sg.SEEDS:
                rj, ij = sg.shared_draw(regime, seed)
                cur = [(2.0 if (k + 1) in sg.STALLED[regime] else 0.5) * ij[k] for k in range(6)]
                for arm in sg.ARMS:
                    got = sg.run_arm(arm, regime, seed)
                    lead, seg = sg.ARM_R[arm]
                    v = 5.0 - lead * rj[0] * sum(cur)
                    vs = [v]
                    for k in range(1, 6):
                        v -= seg * rj[k] * sum(cur[k:])
                        vs.append(v)
                    self.assertTrue(math.isclose(got["v_min"], min(vs), abs_tol=1e-12))
                    self.assertTrue(math.isclose(got["i_sum"], sum(cur), abs_tol=1e-12))

    def test_directions(self):
        out = run(SG_REL)
        rated = section(out, "rated (", "one_stall (")
        self.assertRegex(rated, r"paired B-A v_min: -0\.6654\+-0\.0455: small but consistent")
        self.assertRegex(rated, r"paired B-A v_ok: 0\.0000\+-0\.0000: tie")
        one = section(out, "one_stall (", "multi_stall (")
        self.assertRegex(one, r"paired B-A v_ok: -1\.0000\+-0\.0000: clear gap")
        self.assertIn("i_sum 4.3757+-0.0804", one)
        allst = out.split("all_stall (")[1].split("alternatives")[0]
        self.assertRegex(allst, r"paired C-B v_ok: 0\.0000\+-0\.0000: tie")
        self.assertRegex(allst, r"paired C-B v_min: 1\.5317\+-0\.1076: clear gap")


if __name__ == "__main__":
    unittest.main()
