#!/usr/bin/env python3
"""Independent contract tests for batch-9 PR1 toys; stdlib only."""
import importlib.util
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, slug):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'examples/month-2' / slug / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dt = load('pwm_deadtime_distortion_toy', 'motors-drivers')
rs = load('rs485_termination_toy', 'arduino-io')


class DeadTime(unittest.TestCase):
    def test_rl_step_matches_fine_euler(self):
        i, h, v = 0.3, 40e-6, 12.0
        exact, _ = dt.rl_step(i, v, h)
        x, n = i, 20000
        for _ in range(n):
            x += (v - dt.R * x) / dt.L * (h / n)
        self.assertAlmostEqual(exact, x, places=5)

    def test_dead_interval_clamps_by_current_sign(self):
        _, vs_pos = dt.dead_interval(1.0, 1e-6)
        _, vs_neg = dt.dead_interval(-1.0, 1e-6)
        self.assertAlmostEqual(vs_pos, -dt.VDC / 2 * 1e-6, places=12)
        self.assertAlmostEqual(vs_neg, dt.VDC / 2 * 1e-6, places=12)
        i, vs0 = dt.dead_interval(0.0, 1e-6)
        self.assertEqual((i, vs0), (0.0, 0.0))

    def test_ideal_arm_tracks_reference_volt_seconds(self):
        rows = dt.run('A_ideal', 0.3, 0)
        self.assertLess(max(abs(v - r) for r, v, _ in rows), 1e-9)

    def test_dead_time_error_matches_formula_at_normal_load(self):
        rows = dt.run('B_td', 0.3, 0)
        pos = [v - r for r, v, i in rows if i > 0.5]
        neg = [v - r for r, v, i in rows if i < -0.5]
        pred = dt.TD / dt.TS * dt.VDC
        self.assertAlmostEqual(sum(pos) / len(pos), -pred, delta=0.01)
        self.assertAlmostEqual(sum(neg) / len(neg), pred, delta=0.01)

    def test_shared_streams_and_no_extra_bus(self):
        self.assertEqual(dt.run('B_td', 0.05, 3), dt.run('B_td', 0.05, 3))
        self.assertEqual(len(dt.SEEDS), 5)
        src = (ROOT / 'examples/month-2/motors-drivers/pwm_deadtime_distortion_toy.py').read_text()
        self.assertEqual(src.count('VDC = '), 1)


class RS485(unittest.TestCase):
    def test_reflection_coefficients(self):
        g = lambda z: (z - rs.Z0) / (z + rs.Z0)
        self.assertAlmostEqual(g(rs.RIN), 0.980, places=3)
        self.assertAlmostEqual(g(rs.RS), -0.714, places=3)
        self.assertEqual(g(rs.Z0), 0.0)
        self.assertAlmostEqual(g(rs.par(rs.Z0, rs.Z0)), -1 / 3)

    def test_uart_decoder_on_clean_logic(self):
        spb = 10
        bits = rs.bits_of(rs.PAYLOAD)
        logic = [b for b in bits for _ in range(spb)]
        got, framing = rs.uart_decode(logic, spb)
        self.assertEqual(bytes(got), rs.PAYLOAD)
        self.assertEqual(framing, 0)

    def test_terminated_line_settles_to_divider(self):
        spb = 200
        vs = [rs.VOPEN] * (40 * spb)
        line, _ = rs.lattice(vs, 5.0, 'A_term_diff')
        near = rs.Z0 / (rs.Z0 + rs.RS) * rs.VOPEN * rs.Z0 / (rs.par(rs.RS, rs.Z0) + rs.Z0)
        self.assertAlmostEqual(line[-1], near * rs.LOSS, places=6)
        self.assertAlmostEqual(rs.VOPEN / (rs.RS + rs.Z0 / 2) * 1000, 62.5)

    def test_noise_is_shared_per_seed(self):
        self.assertEqual(rs.noise(500, 5.0, 2), rs.noise(500, 5.0, 2))
        self.assertNotEqual(rs.noise(500, 5.0, 2), rs.noise(500, 5.0, 3))
        self.assertEqual(len(rs.SEEDS), 5)

    def test_reflections_not_noise_break_unterminated_line(self):
        errs = {rs.run('B_unterm_diff', 1_000_000, 5.0, s)[0] for s in rs.SEEDS}
        self.assertEqual(len(errs), 1)
        self.assertGreater(errs.pop(), 0)
        self.assertEqual(rs.run('B_unterm_diff', 125_000, 20.0, 0)[0], 0)
        self.assertEqual(rs.run('A_term_diff', 1_000_000, 5.0, 0)[0], 0)


if __name__ == '__main__':
    unittest.main(verbosity=1)
