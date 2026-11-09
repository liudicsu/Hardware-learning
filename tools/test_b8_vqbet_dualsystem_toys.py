#!/usr/bin/env python3
"""Independent contract tests for batch-8 PR3 toys; stdlib only."""
import importlib.util
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, slug):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'examples/month-6' / slug / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


vq = load('vqbet_residual_vq_toy', 'behaviour-cloning')
ds = load('dual_system_vla_cadence_toy', 'vla-models')


class VQ(unittest.TestCase):
    def setUp(self):
        rng = random.Random(0)
        self.rows = [r for _ in range(vq.N_DEMOS) for r in vq.demo(rng)]

    def test_demos_are_bimodal(self):
        first = [a[1] for o, a in self.rows if o // 3 == 0]
        self.assertTrue(any(v > 0.02 for v in first) and any(v < -0.02 for v in first))

    def test_equal_codebook_vectors_and_iterations(self):
        km = vq.Quantizer('kmeans', [a for _, a in self.rows], random.Random(1))
        rq = vq.Quantizer('rvq', [a for _, a in self.rows], random.Random(1))
        self.assertEqual(sum(len(b) for b in km.books), sum(len(b) for b in rq.books))
        self.assertEqual(km.combos(), 8)
        self.assertEqual(rq.combos(), 16)
        self.assertEqual(vq.ITERS // 2 * 2, vq.ITERS)

    def test_residual_decode_is_sum_of_stages(self):
        rq = vq.Quantizer('rvq', [a for _, a in self.rows], random.Random(2))
        a = self.rows[3][1]
        c = rq.encode(a)
        dec = rq.decode(c)
        b1, b2 = rq.books
        self.assertAlmostEqual(dec[0], b1[c[0]][0] + b2[c[1]][0])
        self.assertAlmostEqual(dec[1], b1[c[0]][1] + b2[c[1]][1])
        # second stage never makes the residual worse than stopping after stage 1
        self.assertLessEqual(vq.d2(a, dec), vq.d2(a, b1[c[0]]) + 1e-12)

    def test_mse_is_the_observation_mean(self):
        m = vq.fit('MSE', self.rows, random.Random(0))
        o = self.rows[0][0]
        acts = [a for oo, a in self.rows if oo == o]
        self.assertAlmostEqual(m['mean'][o][1], sum(a[1] for a in acts) / len(acts))
        self.assertLess(abs(m['mean'][o][1]), 0.02)  # the two modes nearly cancel at the start

    def test_seed_count(self):
        self.assertGreaterEqual(len(vq.SEEDS), 5)


class Dual(unittest.TestCase):
    def test_equal_compute(self):
        for arm in ds.ARMS:
            self.assertAlmostEqual(ds.episode(arm, 0)['unit'], 1.0, places=6)

    def test_common_random_numbers(self):
        r1, r2 = ds.episode('C', 3), ds.episode('C', 3)
        self.assertEqual(r1, r2)

    def test_static_scenario_removes_the_gap(self):
        for arm in ds.ARMS:
            self.assertEqual(ds.episode(arm, 1, 'static_no_switch')['miss'], False)

    def test_fast_single_ignores_switch_and_dual_rt_follows(self):
        misses_b = sum(ds.episode('B', s)['miss'] for s in ds.SEEDS)
        misses_c = sum(ds.episode('C', s)['miss'] for s in ds.SEEDS)
        self.assertGreater(misses_b, misses_c)

    def test_seed_count(self):
        self.assertGreaterEqual(len(ds.SEEDS), 5)


if __name__ == '__main__':
    unittest.main(verbosity=1)
