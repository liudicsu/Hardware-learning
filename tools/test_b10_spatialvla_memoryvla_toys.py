#!/usr/bin/env python3
"""Independent contract tests for batch-10 PR3 toys; stdlib only."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sv = load(
    "spatialvla_ego3d_grid_toy",
    "examples/month-10/multi-view-extrinsics/spatialvla_ego3d_grid_toy.py",
)
mv = load(
    "memoryvla_bank_retrieve_toy",
    "examples/month-9/world-models-overview/memoryvla_bank_retrieve_toy.py",
)


class SpatialVLA(unittest.TestCase):
    def test_shared_points_no_base_frame_leak(self):
        src = (
            ROOT
            / "examples/month-10/multi-view-extrinsics/spatialvla_ego3d_grid_toy.py"
        ).read_text()
        self.assertNotIn("T_base", src)
        self.assertNotIn("robot_base", src)
        self.assertIn("camera-frame", src.lower())
        self.assertEqual(len(sv.SEEDS), 5)
        self.assertEqual(sv.N_BINS, 16)

    def test_mae_primary_ego3d_beats_2d(self):
        a = sv.run_arm("A_2d_only", 0)
        b = sv.run_arm("B_ego3d", 0)
        c = sv.run_arm("C_adaptive_grids", 0)
        self.assertLess(b["mae_iid"], a["mae_iid"])
        self.assertLess(c["mae_iid"], b["mae_iid"])

    def test_shift_narrows_adaptive_gap(self):
        b = sv.run_arm("B_ego3d", 0)
        c = sv.run_arm("C_adaptive_grids", 0)
        gap_iid = b["mae_iid"] - c["mae_iid"]
        gap_shift = b["mae_shift"] - c["mae_shift"]
        self.assertGreater(gap_iid, 0.0)
        self.assertLess(gap_shift, gap_iid + 1e-9)

    def test_strict_tol_not_ceiling(self):
        self.assertAlmostEqual(sv.TOL_STRICT, 0.05, places=12)
        for arm in sv.ARMS:
            r = sv.run_arm(arm, 0)
            self.assertLess(r["succ_strict"], 1.0)

    def test_adaptive_edges_percentile(self):
        samples = [0.01 * i for i in range(50)] + [0.5, 0.55, 0.6]
        edges = sv.adaptive_edges(samples, 8)
        uni = sv.uniform_edges(8)
        self.assertLess(edges[4] - edges[0], uni[4] - uni[0])

    def test_project_uv_matches_pinhole(self):
        u, v = sv.project_uv((0.1, -0.05, 0.5))
        self.assertAlmostEqual(u, sv.FX * 0.1 / 0.5 + sv.CX, places=12)
        self.assertAlmostEqual(v, sv.FY * (-0.05) / 0.5 + sv.CY, places=12)


class MemoryVLA(unittest.TestCase):
    def test_no_future_leak(self):
        src = (
            ROOT
            / "examples/month-9/world-models-overview/memoryvla_bank_retrieve_toy.py"
        ).read_text()
        self.assertIn("no future leak", src.lower())
        self.assertNotIn("hist[t+", src)
        self.assertEqual(len(mv.SEEDS), 5)
        self.assertEqual(len(mv.REGIMES), 3)

    def test_regime_a_arms_tie(self):
        vals = [mv.run_arm(arm, 0, "a_no_delay") for arm in mv.ARMS]
        self.assertTrue(all(abs(v - vals[0]) < 1e-12 for v in vals))
        self.assertGreaterEqual(vals[0], 0.95)

    def test_regime_b_delay_exceeds_window(self):
        self.assertEqual(mv.BEYOND_CUE_HI, mv.BUTTON_STEP - mv.W)
        s_a = mv.run_arm("A_markov", 0, "b_beyond_window")
        s_b = mv.run_arm("B_window", 0, "b_beyond_window")
        s_c = mv.run_arm("C_memory_bank", 0, "b_beyond_window")
        self.assertAlmostEqual(s_a, s_b, places=12)
        self.assertGreater(s_c, s_b)

    def test_regime_c_bank_degrades(self):
        s_a = mv.run_arm("A_markov", 0, "c_stale_switch")
        s_c = mv.run_arm("C_memory_bank", 0, "c_stale_switch")
        self.assertLess(s_c, s_a)

    def test_unequal_info_stated(self):
        src = (
            ROOT
            / "examples/month-9/world-models-overview/memoryvla_bank_retrieve_toy.py"
        ).read_text()
        self.assertIn("unequal information", src)
        self.assertNotIn("No winner declared", src)

    def test_shared_episode_seeds(self):
        self.assertEqual(
            mv.run_arm("C_memory_bank", 2, "b_beyond_window"),
            mv.run_arm("C_memory_bank", 2, "b_beyond_window"),
        )


if __name__ == "__main__":
    unittest.main()
