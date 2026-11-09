#!/usr/bin/env python3
"""Independent contract tests for batch-11 PR1 bridge + GD&T toys; stdlib only."""
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


wb = load(
    "wheatstone_bridge_sense_toy",
    "examples/month-1/components/wheatstone_bridge_sense_toy.py",
)
gdt = load(
    "gdt_tolerance_stack_toy",
    "examples/month-3/cad-parametric/gdt_tolerance_stack_toy.py",
)


class Wheatstone(unittest.TestCase):
    def test_shared_constants_and_seeds(self):
        self.assertEqual(len(wb.SEEDS), 5)
        self.assertEqual(wb.VEXC, 5.0)
        self.assertEqual(wb.R0, 350.0)
        self.assertEqual(wb.G_AMP, 100.0)
        src = (
            ROOT / "examples/month-1/components/wheatstone_bridge_sense_toy.py"
        ).read_text()
        self.assertIn("_ARM_SALT", src)
        self.assertNotIn("hash(arm)", src)
        self.assertIn("本页未运行", src)

    def test_quarter_bridge_formula(self):
        delta = 0.002
        vg = wb.v_bridge(delta)
        # exact: Vexc * ((1+d)/(2+d) - 1/2)
        pred = wb.VEXC * ((1.0 + delta) / (2.0 + delta) - 0.5)
        self.assertAlmostEqual(vg, pred, places=12)
        # small-delta ≈ Vexc*d/4
        self.assertAlmostEqual(vg, wb.VEXC * delta / 4.0, delta=1e-5)

    def test_small_delta_bridge_wins_snr(self):
        name, delta, cm = wb.REGIMES[0]
        self.assertEqual(name, "small_delta_noisy_cm")
        snr_a = [wb.metrics_for(delta, cm, "A_single_ended", s)[2] for s in wb.SEEDS]
        snr_b = [wb.metrics_for(delta, cm, "B_bridge_ideal", s)[2] for s in wb.SEEDS]
        self.assertGreater(sum(snr_b) / 5, sum(snr_a) / 5 + 10.0)

    def test_large_delta_quiet_tie(self):
        name, delta, cm = wb.REGIMES[1]
        self.assertEqual(name, "large_delta_quiet_cm")
        snr_a = sum(wb.metrics_for(delta, cm, "A_single_ended", s)[2] for s in wb.SEEDS) / 5
        snr_b = sum(wb.metrics_for(delta, cm, "B_bridge_ideal", s)[2] for s in wb.SEEDS) / 5
        self.assertLess(abs(snr_a - snr_b), 3.0)

    def test_offset_arm_c_worse_than_b(self):
        _, delta, cm = wb.REGIMES[0]
        off_b = sum(wb.metrics_for(delta, cm, "B_bridge_ideal", s)[1] for s in wb.SEEDS) / 5
        off_c = sum(wb.metrics_for(delta, cm, "C_bridge_offset", s)[1] for s in wb.SEEDS) / 5
        self.assertGreater(off_c, off_b)


class GdtStack(unittest.TestCase):
    def test_shared_seeds_and_arms(self):
        self.assertEqual(len(gdt.SEEDS), 5)
        self.assertEqual(gdt.ARMS[0], "A_worst_case")
        src = (
            ROOT / "examples/month-3/cad-parametric/gdt_tolerance_stack_toy.py"
        ).read_text()
        self.assertIn("ASME Y14.5", src)
        self.assertIn("本页未运行", src)

    def test_short_chain_exact_tie(self):
        tols = gdt.REGIMES[0][1]
        self.assertEqual(len(tols), 1)
        self.assertAlmostEqual(gdt.worst_half(tols), gdt.rss_half(tols), places=12)

    def test_long_skew_rss_unsafe(self):
        name, tols, reroot, dist = gdt.REGIMES[2]
        self.assertEqual(name, "long_skew")
        self.assertEqual(dist, "skew")
        pred_rss = gdt.predict("B_rss", tols, reroot)
        pred_wc = gdt.predict("A_worst_case", tols, reroot)
        hits_rss, hits_wc = [], []
        for seed in gdt.SEEDS:
            samples = gdt.mc_stack(tols, seed, dist)
            hits_rss.append(gdt.hit_rate(samples, pred_rss))
            hits_wc.append(gdt.hit_rate(samples, pred_wc))
        self.assertLess(sum(hits_rss) / 5, 0.90)
        self.assertGreater(sum(hits_wc) / 5, 0.99)

    def test_datum_reroot_shortens(self):
        _, tols, reroot, _ = gdt.REGIMES[1]
        full = gdt.predict("A_worst_case", tols, reroot)
        short = gdt.predict("C_datum_reroot", tols, reroot)
        self.assertLess(short, full)

    def test_rss_algebra(self):
        tols = [0.05, 0.08, 0.06]
        self.assertAlmostEqual(
            gdt.rss_half(tols), math.sqrt(sum(t * t for t in tols)), places=12
        )


if __name__ == "__main__":
    unittest.main()
