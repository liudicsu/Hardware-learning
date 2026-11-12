#!/usr/bin/env python3
"""Batch-20 polish: verify the signed-skew convention stated on m5/camera-calibration.

The toy samples row r at t0 + r*DT_ROW (row 0 first, the row index grows down the
frame) and the detected column is x0 + v*t_r + noise, so a positive v moves the edge
towards larger column indices (rightward).  The fitted slope b (columns per row) is
v*DT_ROW plus noise, so the signed skew b*(H-1) has the same sign as v; the toy
prints only |b|*(H-1).  stdlib only; the toy file and expected/ are not modified.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RS_REL = "examples/month-5/camera-calibration/rolling_vs_global_shutter_toy.py"
RS_EXP = "examples/month-5/expected/rolling_vs_global_shutter_toy.txt"


def load():
    spec = importlib.util.spec_from_file_location("rs_toy_b20pol", ROOT / RS_REL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rs = load()


def signed_skew(arm, v, seed):
    x0, _, noise = rs.shared_draws("moderate", seed)
    cols = [x0 + v * rs.row_time(arm, r) + noise[r] for r in range(rs.H)]
    _, b, _ = rs.fit_line(cols)
    return b * (rs.H - 1)


class SkewSign(unittest.TestCase):
    def test_row_order(self):
        self.assertEqual(rs.row_time("B_rolling", 0), 0.0)
        self.assertGreater(rs.row_time("B_rolling", rs.H - 1), rs.row_time("B_rolling", 1))
        self.assertGreater(rs.row_time("B_rolling", 1), rs.row_time("B_rolling", 0))

    def test_sign_matches_v(self):
        for arm in ("B_rolling", "C_slow"):
            for v in (300.0, -300.0, 1500.0, -1500.0):
                for seed in rs.SEEDS:
                    s = signed_skew(arm, v, seed)
                    self.assertGreater(s * v, 0.0, (arm, v, seed, s))

    def test_toy_speeds_positive_and_skew_unsigned(self):
        for regime in ("moderate", "fast"):
            for seed in rs.SEEDS:
                self.assertGreater(rs.shared_draws(regime, seed)[1], 0.0)
        src = (ROOT / RS_REL).read_text(encoding="utf-8")
        self.assertIn('"skew": abs(b) * (H - 1)', src)
        self.assertIn("x0 + v * row_time(arm, r, dt_row) + noise[r]", src)

    def test_expected_unchanged_bytes(self):
        out = subprocess.run([sys.executable, str(ROOT / RS_REL)], check=True,
                             capture_output=True, text=True).stdout
        self.assertEqual(out, (ROOT / RS_EXP).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
