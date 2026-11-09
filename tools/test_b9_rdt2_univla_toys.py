#!/usr/bin/env python3
"""Independent contract tests for batch-9 PR3 toys; stdlib only."""
import importlib.util
import math
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, month, slug):
    spec = importlib.util.spec_from_file_location(name, ROOT / f'examples/month-{month}' / slug / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rdt = load('rdt2_rvq_fm_distill_toy', 6, 'vla-models')
uni = load('univla_latent_action_toy', 11, 'cross-embodiment-datasets')


class Rdt2(unittest.TestCase):
    def test_equal_bit_budget(self):
        for name, stages in rdt.TOKENIZERS:
            self.assertAlmostEqual(sum(math.log2(k) for k in stages), 8.0, msg=name)

    def test_rvq_decode_is_sum_of_stage_entries(self):
        rng = random.Random(0)
        data = [rdt.sample_chunk(rng) for _ in range(64)]
        books = rdt.train_rvq(data, [4, 4], random.Random(1))
        rec, codes = rdt.encode_decode(data[0], books)
        manual = [books[0][codes[0]][j] + books[1][codes[1]][j] for j in range(4)]
        for a, b in zip(rec, manual):
            self.assertAlmostEqual(a, b, places=12)

    def test_one_euler_step_lands_on_smoothed_mean(self):
        rng = random.Random(2)
        train = [rdt.sample_chunk(rng) for _ in range(32)]
        mean = [sum(a[j] for a in train) / len(train) for j in range(4)]
        out = rdt.euler([rng.gauss(0, 1) for _ in range(4)], 1, train)
        for a, b in zip(out, mean):
            self.assertAlmostEqual(a, b, places=9)

    def test_velocity_matches_finite_difference_of_posterior_mean(self):
        # with a single train chunk the FM field must point from x to that chunk
        a = [0.3, -0.2, 0.1, 0.4]
        x, tau = [0.0, 0.1, -0.1, 0.2], 0.4
        v = rdt.velocity(x, tau, [a])
        var = (1 - tau) ** 2 + (tau * rdt.SMOOTH) ** 2
        ea = [a[j] + tau * rdt.SMOOTH ** 2 / var * (x[j] - tau * a[j]) for j in range(4)]
        for j in range(4):
            self.assertAlmostEqual(v[j], (ea[j] - x[j]) / (1 - tau), places=12)

    def test_nn_student_returns_stored_output(self):
        pairs = [([0.0] * 4, [1.0, 2.0, 3.0, 4.0]), ([5.0] * 4, [9.0] * 4)]
        self.assertEqual(rdt.knn_student(pairs, [0.1] * 4, 1), [1.0, 2.0, 3.0, 4.0])


class UniVLA(unittest.TestCase):
    def test_motor_maps_invert(self):
        for emb in ('A', 'B'):
            d = (0.03, -0.02)
            s = uni.to_step(emb, uni.to_motor(emb, d))
            self.assertAlmostEqual(s[0], d[0], places=12)
            self.assertAlmostEqual(s[1], d[1], places=12)

    def test_a_commands_misdirect_b(self):
        d = (0.05, 0.0)
        s = uni.to_step('B', uni.to_motor('A', d))
        self.assertLess(s[0] * d[0] + s[1] * d[1], 1e-12)

    def test_expert_reaches_goals_without_collision(self):
        rng = random.Random(3)
        ok = 0
        for _ in range(200):
            task = rng.choice(('left', 'right'))
            ee = uni.start(rng)
            for _ in range(uni.T_MAX):
                d = uni.expert_step(ee, uni.GOALS[task])
                ee = uni.clip((ee[0] + d[0], ee[1] + d[1]))
                if uni.hit(ee):
                    break
                if math.hypot(ee[0] - uni.GOALS[task][0], ee[1] - uni.GOALS[task][1]) < 0.06:
                    ok += 1
                    break
        self.assertGreater(ok / 200, 0.95)

    def test_linear_decoder_recovers_b_inverse(self):
        rng = random.Random(4)
        xs, ys = [], []
        for _ in range(20):
            d = (rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05))
            xs.append(list(d))
            ys.append(uni.to_motor('B', d))
        W = uni.lstsq(xs, ys)
        self.assertAlmostEqual(W[0][1], 1 / 1.4, places=3)  # tiny ridge term
        self.assertAlmostEqual(W[1][0], -1 / 0.6, places=3)

    def test_still_scene_wanderer_is_static_but_streams_shared(self):
        r1, r2 = random.Random(5), random.Random(5)
        w = uni.wander((0.4, 0.4), r1, 0.0)
        uni.wander((0.4, 0.4), r2, 0.06)
        self.assertEqual(w, (0.4, 0.4))
        self.assertEqual(r1.random(), r2.random())


if __name__ == '__main__':
    unittest.main(verbosity=1)
