#!/usr/bin/env python3
"""Independent contract tests for batch-10 PR1 ENOB + magcal toys; stdlib only."""
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


enob = load("adc_enob_noise_toy", "examples/month-2/arduino-io/adc_enob_noise_toy.py")
mag = load(
    "mag_hard_soft_iron_toy",
    "examples/month-2/sensors-fusion/mag_hard_soft_iron_toy.py",
)


class AdcEnob(unittest.TestCase):
    def test_ideal_snr_formula_and_enob_map(self):
        self.assertAlmostEqual(enob.ideal_snr_db(10), 6.02 * 10 + 1.76, places=12)
        self.assertAlmostEqual(enob.enob(61.96), (61.96 - 1.76) / 6.02, places=12)

    def test_shared_tone_and_seeds(self):
        self.assertEqual(len(enob.SEEDS), 5)
        self.assertEqual(enob.N_BITS, 10)
        self.assertEqual(enob.TONE_BIN, 17)
        self.assertEqual(enob.N_SAMPLES, 1024)
        a = enob.tone_samples()
        b = enob.tone_samples()
        self.assertEqual(a, b)
        src = (ROOT / "examples/month-2/arduino-io/adc_enob_noise_toy.py").read_text()
        self.assertEqual(src.count("TONE_BIN = "), 1)
        self.assertIn("ENOB = (SINAD", src)

    def test_arm_ordering_enob_falls_with_corruption(self):
        clean = enob.tone_samples()
        rows = {}
        for arm in enob.ARMS:
            snrs, sinads, enobs = [], [], []
            for seed in enob.SEEDS:
                xs = enob.apply_arm(clean, arm, seed)
                snr, sinad = enob.snr_sinad(xs)
                snrs.append(snr)
                sinads.append(sinad)
                enobs.append(enob.enob(sinad))
            rows[arm] = (
                sum(snrs) / len(snrs),
                sum(sinads) / len(sinads),
                sum(enobs) / len(enobs),
            )
        self.assertGreater(rows["A_ideal"][2], 9.5)
        self.assertLess(rows["B_noise"][2], rows["A_ideal"][2] - 2.0)
        self.assertLess(rows["C_distort"][1], rows["B_noise"][1])  # SINAD drops with harmonics
        self.assertLess(rows["C_distort"][2], rows["B_noise"][2] + 0.05)

    def test_quantize_mid_riser_bounds(self):
        self.assertAlmostEqual(enob.quantize(-1.0), 0.5 * enob.LSB, places=12)
        self.assertAlmostEqual(
            enob.quantize(enob.VREF + 1.0),
            (enob.N_LEVELS - 1 + 0.5) * enob.LSB,
            places=12,
        )


class MagHardSoft(unittest.TestCase):
    def test_shared_path_and_seeds(self):
        self.assertEqual(len(mag.SEEDS), 5)
        self.assertEqual(mag.N_YAWS, 72)
        self.assertEqual(mag.S_SOFT, (1.35, 0.72))
        self.assertEqual(mag.B_HARD, (0.35, -0.22))
        p1 = mag.true_path()
        p2 = mag.true_path()
        self.assertEqual(p1, p2)
        src = (
            ROOT / "examples/month-2/sensors-fusion/mag_hard_soft_iron_toy.py"
        ).read_text()
        self.assertIn("off-diagonals omitted", src)
        self.assertNotIn("AHRS certification claimed", src)

    def test_hard_only_recenters_soft_unstretches(self):
        path = mag.true_path()
        samples = mag.measure(path, 0)
        a = mag.evaluate(samples, "A_raw")
        b = mag.evaluate(samples, "B_hard_only")
        c = mag.evaluate(samples, "C_hard_soft")
        self.assertLess(b[0], a[0])  # mean |heading| err
        self.assertLess(c[0], b[0])
        self.assertLess(c[2], b[2])  # radius residual RMS
        self.assertLess(c[2], 0.05)

    def test_bias_estimate_near_hard_iron(self):
        path = mag.true_path()
        # zero noise path via measure then ignore noise by averaging many seeds' biases
        biases = [mag.calibrate_bias(mag.measure(path, s)) for s in mag.SEEDS]
        bx = sum(b[0] for b in biases) / len(biases)
        by = sum(b[1] for b in biases) / len(biases)
        self.assertAlmostEqual(bx, mag.B_HARD[0], delta=0.05)
        self.assertAlmostEqual(by, mag.B_HARD[1], delta=0.05)

    def test_wrap180_and_heading(self):
        self.assertAlmostEqual(mag.wrap180(190.0), -170.0, places=12)
        self.assertAlmostEqual(mag.heading_deg(1.0, 0.0), 0.0, places=12)
        self.assertAlmostEqual(mag.heading_deg(0.0, 1.0), 90.0, places=12)


if __name__ == "__main__":
    unittest.main()
