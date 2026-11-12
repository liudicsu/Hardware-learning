#!/usr/bin/env python3
"""Independent contract tests for batch-20 PR2 rolling-shutter + Tobin visual-DR toys; stdlib only."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RS_REL = "examples/month-5/camera-calibration/rolling_vs_global_shutter_toy.py"
DR_REL = "examples/month-7/sim-to-real/tobin_visual_domain_randomization_toy.py"
RS_EXP = "examples/month-5/expected/rolling_vs_global_shutter_toy.txt"
DR_EXP = "examples/month-7/expected/tobin_visual_domain_randomization_toy.txt"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rs = load("rolling_vs_global_shutter_toy", RS_REL)
dr = load("tobin_visual_domain_randomization_toy", DR_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def section(out: str, start: str, end: str) -> str:
    return out.split(start)[1].split(end)[0]


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((rs, RS_REL), (dr, DR_REL)):
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
            for marker in ("Common random numbers", "本页未运行", "No integration step", "written before the first run"):
                self.assertIn(marker, src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|cv2)")
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))

    def test_byte_identical_rerun(self):
        for rel, exp in ((RS_REL, RS_EXP), (DR_REL, DR_EXP)):
            first, second = run(rel), run(rel)
            self.assertEqual(first, second)
            self.assertEqual(first, (ROOT / exp).read_text())


class RollingShutter(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((rs.H, rs.DT_ROW, rs.SLOW, rs.SIGMA_PX), (480, 30e-6, 4, 0.3))
        self.assertEqual(rs.ARMS, ("A_global", "B_rolling", "C_slow"))
        self.assertEqual(rs.REGIMES, {"static": 0.0, "moderate": 300.0, "fast": 1500.0})

    def test_row_stamp_rule(self):
        for r in (0, 1, 17, 479):
            self.assertEqual(rs.row_time("A_global", r), 0.0)
            self.assertEqual(rs.row_time("B_rolling", r), r * rs.DT_ROW)
            self.assertEqual(rs.row_time("C_slow", r), r * rs.DT_ROW * rs.SLOW)

    def test_crn_and_static_tie(self):
        for seed in rs.SEEDS:
            self.assertEqual(rs.shared_draws("moderate", seed), rs.shared_draws("moderate", seed))
            rows = [rs.capture(arm, "static", seed)[1] for arm in rs.ARMS]
            self.assertEqual(rows[0], rows[1])
            self.assertEqual(rows[1], rows[2])

    def test_skew_matches_closed_form_without_noise(self):
        # Independent form: noiseless rolling capture is x0 + v*r*dt; slope*(H-1) = v*(H-1)*dt.
        v, dt = 300.0, rs.DT_ROW
        cols = [100.0 + v * r * dt for r in range(rs.H)]
        a, b, cbar = rs.fit_line(cols)
        self.assertAlmostEqual(abs(b) * (rs.H - 1), v * (rs.H - 1) * dt, places=9)
        self.assertAlmostEqual(cbar - 100.0, v * (rs.H - 1) / 2 * dt, places=9)
        self.assertAlmostEqual(a, 100.0, places=9)

    def test_printed_regimes(self):
        out = (ROOT / RS_EXP).read_text()
        static = section(out, "static (", "moderate (")
        self.assertEqual(static.count("0.0000+-0.0000: tie: identical on every seed"), 4)
        for reg, nxt in (("moderate (", "fast ("), ("fast (", "alternative DT_ROW")):
            block = section(out, reg, nxt)
            for line in [l for l in block.splitlines() if "paired" in l]:
                self.assertIn("clear gap", line)
                self.assertIn("same sign on all 5 seeds", line)
        self.assertIn("paired B-A skew: 4.2034+-0.1754", out)
        self.assertIn("paired C-B pos_err: 6.3269+-0.2589", out)
        self.assertIn("readout=(H-1)*DT_ROW=479*30.0 us=14.3700 ms", out)
        self.assertIn("numerically zero (floating-point residue), effectively a tie", section(out, "RS-aware", "No winner"))


class VisualDR(unittest.TestCase):
    def test_declared_parameters(self):
        self.assertEqual((dr.W, dr.OBJ_W, dr.N_TRAIN, dr.N_TEST, dr.K_NN, dr.PALETTE), (24, 4.0, 600, 40, 3, 200))
        self.assertEqual((dr.U_MOVE, dr.TAU_REAL, dr.TAU_SIM, dr.TOL), (30.0, 0.10, 0.05, 1.0))
        self.assertEqual(dr.ARMS, ("A_canonical", "B_random", "C_rand_tau"))
        self.assertEqual(list(dr.REGIMES), ["heldout", "canonical", "moving"])

    def test_no_peek(self):
        for seed in dr.SEEDS:
            for size in (dr.PALETTE, 10):
                pal = dr.palette(seed, size)
                self.assertFalse(any(p in dr.REAL or p == dr.CANON for p in pal))

    def test_crn_training_shared(self):
        a = dr.train_set("A_canonical", 0)
        b = dr.train_set("B_random", 0)
        self.assertEqual([x for _, x in a], [x for _, x in b])
        self.assertEqual(dr.test_draws("moving", 2), dr.test_draws("moving", 2))

    def test_strict_tolerance(self):
        # One test row with a known detector error: success iff err < TOL strictly.
        self.assertFalse(dr.TOL < dr.TOL)
        bias = dr.U_MOVE * (dr.TAU_REAL - dr.TAU_SIM)
        self.assertAlmostEqual(bias, 1.5, places=12)
        self.assertFalse(bias < dr.TOL)

    def test_render_coverage(self):
        row = dr.render(2.5, ("flat", 1.0, 1.0), ("flat", 0.0, 0.0), 1.0, [0.0] * dr.W)
        self.assertAlmostEqual(sum(row), dr.OBJ_W, places=12)
        self.assertAlmostEqual(row[2], 0.5, places=12)
        self.assertAlmostEqual(row[6], 0.5, places=12)

    def test_printed_regimes(self):
        out = (ROOT / DR_EXP).read_text()
        self.assertIn("peek_check: any held-out real texture or the canonical texture inside B's palette on any seed: False", out)
        held = section(out, "heldout (", "canonical (")
        self.assertIn("paired B-A loc_err: -3.4207+-0.8743: clear gap", held)
        self.assertEqual(held.count("paired C-B"), 3)
        self.assertEqual(held.count("tie: identical on every seed"), 3)
        canon = section(out, "canonical (", "moving (")
        self.assertIn("paired B-A loc_err: 0.1828+-0.0448: clear gap", canon)
        moving = section(out, "moving (", "alternative PALETTE")
        self.assertIn("paired C-B loc_err: 0.0000+-0.0000: tie", moving)
        self.assertIn("paired C-B success: -0.3300+-0.1110: clear gap", moving)
        self.assertIn("paired B200-B10 loc_err: 0.7390+-0.3862: clear gap", out)
        self.assertIn("paired C-B success@alt: -0.0450+-0.0818: near-tie", out)


if __name__ == "__main__":
    unittest.main()
