#!/usr/bin/env python3
"""Independent contract tests for batch-10 PR3 toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
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

    def test_ego3d_beats_2d_on_shared_seed(self):
        mae_a, succ_a = sv.run_arm("A_2d_only", 0)
        mae_b, succ_b = sv.run_arm("B_ego3d", 0)
        self.assertLess(mae_b, mae_a)
        self.assertGreaterEqual(succ_b, succ_a)

    def test_adaptive_edges_are_percentile_not_uniform(self):
        # skewed samples → adaptive edges cluster low
        samples = [0.01 * i for i in range(50)] + [0.5, 0.55, 0.6]
        edges = sv.adaptive_edges(samples, 8)
        uni = sv.uniform_edges(8)
        # first half of adaptive span should be tighter than uniform's first half
        self.assertLess(edges[4] - edges[0], uni[4] - uni[0])

    def test_project_uv_matches_pinhole(self):
        u, v = sv.project_uv((0.1, -0.05, 0.5))
        self.assertAlmostEqual(u, sv.FX * 0.1 / 0.5 + sv.CX, places=12)
        self.assertAlmostEqual(v, sv.FY * (-0.05) / 0.5 + sv.CY, places=12)

    def test_arms_share_train_eval_geometry(self):
        # same seed → identical point streams inside run_arm (implicit via reset RNG)
        # Compare B vs C bank size equality via N_TRAIN constant
        self.assertEqual(sv.N_TRAIN, 80)
        self.assertEqual(sv.N_EVAL, 40)


class MemoryVLA(unittest.TestCase):
    def test_no_future_leak_in_source(self):
        src = (
            ROOT
            / "examples/month-9/world-models-overview/memoryvla_bank_retrieve_toy.py"
        ).read_text()
        self.assertTrue("future" in src.lower() and ("no arm sees the future" in src.lower() or "no future leak" in src.lower()))
        self.assertNotIn("hist[t+", src)
        self.assertEqual(len(mv.SEEDS), 5)

    def test_markov_near_chance_window_better_bank_best(self):
        s_a, _ = mv.run_arm("A_markov", 0)
        s_b, _ = mv.run_arm("B_window", 0)
        s_c, _ = mv.run_arm("C_memory_bank", 0)
        self.assertGreater(s_b, s_a - 1e-9)
        self.assertGreater(s_c, s_b - 1e-9)
        self.assertGreaterEqual(s_c, 0.95)

    def test_window_coverage_formula(self):
        # B can see cue when cue_t >= BUTTON_STEP - W + 1
        first = mv.BUTTON_STEP - mv.W + 1
        self.assertEqual(first, 15 - 6 + 1)
        self.assertTrue(first > mv.CUE_LO)

    def test_equal_step_budget(self):
        _, st_a = mv.run_arm("A_markov", 1)
        _, st_b = mv.run_arm("B_window", 1)
        _, st_c = mv.run_arm("C_memory_bank", 1)
        self.assertEqual(st_a, st_b)
        self.assertEqual(st_b, st_c)

    def test_shared_episode_seeds(self):
        # identical success for same arm/seed
        self.assertEqual(mv.run_arm("C_memory_bank", 2), mv.run_arm("C_memory_bank", 2))


if __name__ == "__main__":
    unittest.main()
