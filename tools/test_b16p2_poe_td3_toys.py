#!/usr/bin/env python3
"""Independent contract tests for batch-16 PR2 PoE-vs-DH FK + TD3 clipped double Q toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PO_REL = "examples/month-5/kinematics-ik/poe_vs_dh_fk_toy.py"
TD_REL = "examples/month-7/rl-foundations/td3_clipped_double_q_toy.py"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


po = load("poe_vs_dh_fk_toy", PO_REL)
td = load("td3_clipped_double_q_toy", TD_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


class Labels(unittest.TestCase):
    def test_order_and_thresholds(self):
        for mod, rel in ((po, PO_REL), (td, TD_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertEqual(mod.SEEDS, (0, 1, 2, 3, 4))
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1e-16, -2e-16, 3e-16, 0.0, 1e-16], [0.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertNotIn("seeds", v)
            self.assertNotIn("clear", v)
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            src = (ROOT / rel).read_text()
            self.assertIn("Common random numbers", src)
            self.assertIn("本页未运行", src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|gym|gymnasium)")
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))
            self.assertNotEqual(mod.num(-4e-5), "-0.0000")


class PoE(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(PO_REL)

    def test_lesson_configuration(self):
        # The lesson's worked example: q = [30, 45, -60] deg -> tip (0.1840, 0.1062, 0.1637) m.
        q = tuple(math.radians(x) for x in (30.0, 45.0, -60.0))
        for f in (po.fk_dh, po.fk_poe, po.truth):
            t = f(q)
            self.assertAlmostEqual(t[0][3], 0.1840, places=4)
            self.assertAlmostEqual(t[1][3], 0.1062, places=4)
            self.assertAlmostEqual(t[2][3], 0.1637, places=4)

    def test_dh_equals_poe_to_rounding(self):
        for regime in ("matched", "near_singular"):
            for seed in po.SEEDS:
                for q, _ in po.shared_draws(regime, seed)[:50]:
                    self.assertLess(po.frob(po.fk_dh(q), po.fk_poe(q)), 1e-12)

    def test_twist_exponential_independent(self):
        # e^[xi]theta for a revolute twist about w through p equals Trans(p) Rot(w, theta) Trans(-p).
        w, p, th = (0.0, -1.0, 0.0), (0.3, 0.0, 0.2), 0.7
        e = po.twist_exp(w, p, th)
        c, s = math.cos(th), math.sin(th)
        rot = [[c, 0.0, -s], [0.0, 1.0, 0.0], [s, 0.0, c]]  # rotation about -y
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(e[i][j], rot[i][j], places=12)
            t_i = p[i] - sum(rot[i][k] * p[k] for k in range(3))
            self.assertAlmostEqual(e[i][3], t_i, places=12)

    def test_wrong_twist_is_a_real_error(self):
        q = tuple(math.radians(x) for x in (10.0, 20.0, 90.0))
        self.assertGreater(po.frob(po.fk_poe(q, "C_poe_tilt"), po.truth(q)), 1e-3)
        q0 = (0.3, 0.2, 0.0)  # elbow at zero: the tilted elbow axis does not move the tip
        self.assertLess(po.frob(po.fk_poe(q0, "C_poe_tilt"), po.truth(q0)), 1e-12)

    def test_common_random_numbers(self):
        self.assertEqual(po.shared_draws("encoder_noise", 2), po.shared_draws("encoder_noise", 2))
        self.assertNotEqual(po.shared_draws("encoder_noise", 2), po.shared_draws("encoder_noise", 3))

    def test_no_integration_step(self):
        text = (ROOT / PO_REL).read_text()
        self.assertNotRegex(text, r"\bDT\b|\bdt\b|rk4|euler")
        self.assertIn("no integration step", self.out)

    def test_output_lines(self):
        self.assertEqual(self.out, (ROOT / "examples/month-5/expected/poe_vs_dh_fk_toy.txt").read_text())
        for regime in ("matched", "near_singular", "encoder_noise"):
            block = self.out.split(regime + " (")[1]
            self.assertRegex(block, r"paired B-A pose: [-\d.e]+\+-[\d.e-]+: numerically zero")
            self.assertRegex(block, r"paired C-B pose: [\d.e-]+\+-[\d.e-]+: clear gap")
        for line in self.out.splitlines():
            if "paired B-A" in line:
                self.assertNotIn("clear", line)


class TD3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(TD_REL)

    def test_sgd_stability_boundary(self):
        # Single-sample LMS update on the worst feature vector: the error is multiplied by 1 - lr |phi|^2.
        f = td.phi(2.0, 1.0)
        n2 = sum(x * x for x in f)
        self.assertEqual(n2, td.max_phi2())
        self.assertLess(td.LR * n2, 2.0)
        for factor, grows in ((0.98, False), (1.02, True)):
            lr = factor * 2.0 / n2
            w = [0.0] * 6
            target = 1.0
            err0 = target
            for _ in range(200):
                err = target - sum(a * b for a, b in zip(w, f))
                w = [wi + lr * err * fi for wi, fi in zip(w, f)]
            err = target - sum(a * b for a, b in zip(w, f))
            self.assertEqual(abs(err) > abs(err0), grows, factor)

    def test_clipped_target_never_exceeds_either_critic(self):
        w1, w2 = [0.1, 0.2, -0.3, 0.05, -0.4, 0.1], [-0.2, 0.1, 0.4, -0.1, -0.2, 0.3]
        for s in (-1.0, 0.0, 1.5):
            for a in (-1.0, 0.2, 1.0):
                m = min(td.q(w1, s, a), td.q(w2, s, a))
                self.assertLessEqual(m, td.q(w1, s, a))
                self.assertLessEqual(m, td.q(w2, s, a))

    def test_mc_return_independent(self):
        k, b, s, g = -1.0, 0.0, 1.0, 0.8
        # a = -1 -> s' = 0.5, r = -0.25 - 0.1; a = -0.5 -> s' = 0.25, r = -0.0625 - 0.025; ...
        total, disc, x = 0.0, 1.0, s
        for _ in range(60):
            a = max(-1.0, min(1.0, k * x + b))
            x = max(-2.0, min(2.0, x + 0.5 * a))
            total += disc * (-x * x - 0.1 * a * a)
            disc *= g
        self.assertAlmostEqual(td.mc_return(k, b, s, g), total, places=12)
        self.assertAlmostEqual(td.mc_return(k, b, s, 0.0), -0.35, places=12)

    def test_no_bootstrap_makes_cdq_identical_to_single_critic(self):
        d = td.shared_draws(1)
        a, c = td.run("A_ddpg", "bandit_no_bootstrap", d), td.run("C_cdq_nodelay", "bandit_no_bootstrap", d)
        self.assertEqual(a, c)

    def test_common_random_numbers(self):
        self.assertEqual(td.shared_draws(2)["expl"], td.shared_draws(2)["expl"])
        self.assertNotEqual(td.shared_draws(2)["expl"], td.shared_draws(3)["expl"])

    def test_output_lines(self):
        self.assertEqual(self.out, (ROOT / "examples/month-7/expected/td3_clipped_double_q_toy.txt").read_text())
        self.assertRegex(self.out, r"noisy_reward[\s\S]*?paired B-A bias: -[\d.]+\+-[\d.]+: clear gap")
        self.assertRegex(self.out, r"bandit_no_bootstrap[\s\S]*?paired B-A ret: -[\d.]+\+-[\d.]+: clear gap")
        self.assertRegex(self.out, r"bandit_no_bootstrap[\s\S]*?paired C-A ret: 0\.0000\+-0\.0000: tie: identical on every seed")
        self.assertIn("No winner declared", self.out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
