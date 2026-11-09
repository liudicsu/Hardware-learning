#!/usr/bin/env python3
"""Independent contract tests for batch-13 PR2 eight-point essential + antipodal force-closure toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import random
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EP_REL = "examples/month-5/camera-calibration/eight_point_essential_toy.py"
FC_REL = "examples/month-7/perception-to-grasp/antipodal_force_closure_toy.py"
SIGNED_ZERO = r"(?<![+\d.e])-0\.0+(?![\d.e])"
PAIR = re.compile(r": (-?\d+\.\d+(?:e-?\d+)?)\+-(\d+\.\d+(?:e-?\d+)?): ")


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ep = load("eight_point_essential_toy", EP_REL)
fc = load("antipodal_force_closure_toy", FC_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def check_labels(case: unittest.TestCase, out: str) -> None:
    for line in out.splitlines():
        case.assertNotRegex(line, SIGNED_ZERO)
        if "tie: identical on every seed" in line:
            case.assertIn("0.0000+-0.0000", line)
            continue
        mm = PAIR.search(line)
        if "near-tie" in line:
            case.assertTrue(mm and abs(float(mm.group(1))) <= float(mm.group(2)), line)
        if "consistent gap" in line or "clear gap" in line:
            case.assertTrue(mm and abs(float(mm.group(1))) > float(mm.group(2)), line)
            case.assertRegex(line, r"same sign on all 5 seeds|of 5 seeds ha(s|ve) the opposite sign|no seed has the opposite sign")
            if "opposite sign" in line and "no seed" not in line:
                opp = int(re.search(r"(\d) of 5 seeds ha", line).group(1))
                case.assertLessEqual(opp, 1, "a consistent label needs a clear same-sign majority")


class EightPoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(EP_REL)

    def test_constants_seeds_scope(self):
        self.assertEqual(ep.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / EP_REL).read_text()
        self.assertIn("本页未运行", text)
        self.assertIn("Common random numbers", text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|cv2|torch)")

    def test_svd_reconstructs_and_is_orthonormal(self):
        rng = random.Random(7)
        a = [[rng.gauss(0, 1) * 10 ** rng.randint(-3, 3) for _ in range(9)] for _ in range(20)]
        u, s, v = ep.svd(a)
        self.assertEqual(s, sorted(s, reverse=True))
        rec = [[sum(u[i][k] * s[k] * v[j][k] for k in range(9)) for j in range(9)] for i in range(20)]
        scale = max(abs(x) for r in a for x in r)
        self.assertLess(max(abs(rec[i][j] - a[i][j]) for i in range(20) for j in range(9)), 1e-10 * scale)
        vtv = [[sum(v[k][i] * v[k][j] for k in range(9)) for j in range(9)] for i in range(9)]
        self.assertLess(max(abs(vtv[i][j] - (i == j)) for i in range(9) for j in range(9)), 1e-12)

    def test_internal_constraint(self):
        rng = random.Random(3)
        e = [[rng.gauss(0, 1) for _ in range(3)] for _ in range(3)]
        s = ep.svd(ep.enforce_essential(e))[1]
        self.assertAlmostEqual(s[0], s[1], places=12)
        self.assertLess(s[2], 1e-12)
        self.assertAlmostEqual(math.hypot(s[0], s[1]), 1.0, places=12)

    def test_hartley_normalisation(self):
        rng = random.Random(5)
        pts = [[rng.uniform(800, 1000), rng.uniform(400, 600)] for _ in range(30)]
        h = ep.hartley(pts)
        q = [ep.apply_h(h, p) for p in pts]
        self.assertAlmostEqual(sum(p[0] for p in q) / 30, 0.0, places=12)
        self.assertAlmostEqual(sum(p[1] for p in q) / 30, 0.0, places=12)
        self.assertAlmostEqual(sum(math.hypot(*p) for p in q) / 30, math.sqrt(2), places=12)

    def test_true_e_satisfies_constraint_and_pose_recovers(self):
        sc = ep.scene(ep.REGIMES[0], 2)
        for x1, x2 in sc["test"]:
            y1, y2 = ep.apply_h(ep.KINV, x1) + [1.0], ep.apply_h(ep.KINV, x2) + [1.0]
            self.assertLess(abs(sum(a * b for a, b in zip(y2, ep.matvec(sc["E"], y1)))), 1e-12)
        rot, t = ep.recover_pose(sc["E"], sc["train"])
        self.assertLess(ep.rot_err_deg(rot, sc["R"]), 1e-5)
        self.assertLess(ep.angle_deg(t, sc["t"]), 1e-5)

    def test_common_random_numbers(self):
        reg = ep.REGIMES[1]
        self.assertEqual(ep.scene(reg, 4)["train"], ep.scene(reg, 4)["train"])
        self.assertNotEqual(ep.scene(reg, 4)["train"], ep.scene(reg, 3)["train"])

    def test_conditioning_raw_vs_hartley(self):
        sc = ep.scene(ep.REGIMES[1], 0)
        cond = {arm: ep.estimate(arm, sc["train"])[1] for arm in ep.ARMS}
        self.assertGreater(math.log10(cond["A_raw_px"]) - math.log10(cond["B_hartley_px"]), 2.5)
        self.assertLess(abs(math.log10(cond["C_calib"]) - math.log10(cond["B_hartley_px"])), 1.5)

    def test_noise_free_all_arms_exact(self):
        sc = ep.scene(ep.REGIMES[0], 1)
        for arm in ep.ARMS:
            r = ep.evaluate(arm, sc)
            self.assertLess(r["e_err"], 1e-9, arm)
            self.assertLess(r["epi_px"], 1e-9, arm)

    def test_epi_blind_to_t_at_tiny_baseline(self):
        # Independent: with t -> 0, y2 ~ R y1, so ANY [t']x R gives ~0 residual on clean points.
        sc = ep.scene(ep.REGIMES[3], 0)
        wrong = ep.matmul(ep.skew([0.0, 0.0, 1.0]), sc["R"])
        n = ep.fro(wrong)
        wrong = [[x / n for x in r] for r in wrong]
        self.assertLess(ep.epi_px(wrong, sc["test"]), 3.0)
        self.assertGreater(ep.angle_deg([0.0, 0.0, 1.0], sc["t"]), 60.0)

    def test_labels_and_key_lines(self):
        out = self.out
        check_labels(self, out)
        self.assertIn("noise_free paired B-A t_deg: 0.0000+-0.0000: tie: identical on every seed", out)
        self.assertRegex(out, r"pixel_noise paired B-A e_err: -0\.0683\+-0\.0510: clear gap.*same sign on all 5 seeds")
        self.assertRegex(out, r"pixel_noise paired C-B e_err: 0\.0071\+-0\.0222: near-tie")
        self.assertRegex(out, r"clustered paired B-A epi_px: -204\.7447\+-197\.8867: clear gap.*same sign on all 5 seeds")
        self.assertRegex(out, r"tiny_baseline paired B-A t_deg: -25\.2740\+-63\.6009: near-tie")


class ForceClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(FC_REL)

    def test_constants_seeds_scope(self):
        self.assertEqual(fc.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / FC_REL).read_text()
        self.assertIn("本页未运行", text)
        self.assertIn("Common random numbers", text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch)")

    def test_diametric_disc_epsilon_closed_form(self):
        # Independent: centred antipodal grasp on a disc with L = r has wrenches (+-1, +-mu, +-mu);
        # facet distance mu / sqrt(mu^2 + 2).
        for mu in (0.2, 0.5, 1.0):
            con = fc.hit("disc", (0.04, 0.04), (0.0, 0.0, 0.0), (0.0, 0.0), (1.0, 0.0))
            e = fc.epsilon(fc.primitive_wrenches(con, (0.0, 0.0), mu, 0.04))
            self.assertAlmostEqual(e, mu / math.sqrt(mu * mu + 2), places=12)

    def test_friction_cone_boundary(self):
        # Offset line on a disc: force closure iff asin(o / r) < atan(mu).
        mu, r = 0.5, 0.04
        o_crit = r * math.sin(math.atan(mu))
        for o, want in ((0.98 * o_crit, True), (1.02 * o_crit, False)):
            con = fc.hit("disc", (r, r), (0.0, 0.0, 0.0), (0.0, o), (1.0, 0.0))
            self.assertEqual(fc.epsilon(fc.primitive_wrenches(con, (0.0, 0.0), mu, r)) > 0, want)

    def test_frictionless_never_closure(self):
        con = fc.hit("box", (0.04, 0.025), (0.0, 0.0, 0.3), (0.0, 0.0), (math.cos(0.3), math.sin(0.3)))
        self.assertEqual(fc.epsilon(fc.primitive_wrenches(con, (0.0, 0.0), 0.0, 0.05)), 0.0)

    def test_resists_ball_of_radius_epsilon(self):
        con = fc.hit("box", (0.04, 0.025), (0.0, 0.0, 0.0), (0.0, 0.005), (1.0, 0.0))
        ws = fc.primitive_wrenches(con, (0.0, 0.0), 0.5, math.hypot(0.04, 0.025))
        e = fc.epsilon(ws)
        self.assertGreater(e, 0)
        rng = random.Random(11)
        for _ in range(200):
            d = [rng.gauss(0, 1) for _ in range(3)]
            n = math.sqrt(sum(x * x for x in d))
            self.assertTrue(fc.resists(ws, [0.999 * e * x / n for x in d]))
            big = max(math.sqrt(sum(x * x for x in w)) for w in ws)
            self.assertFalse(fc.resists(ws, [1.01 * big * x / n for x in d]))

    def test_common_random_numbers(self):
        reg = fc.REGIMES[0]
        self.assertEqual(fc.trial_draws(reg, 2, 5), fc.trial_draws(reg, 2, 5))
        self.assertNotEqual(fc.trial_draws(reg, 2, 5), fc.trial_draws(reg, 3, 5))

    def test_labels_and_key_lines(self):
        out = self.out
        check_labels(self, out)
        self.assertIn("box_near_perfect paired B-A fc: 0.0000+-0.0000: tie: identical on every seed", out)
        self.assertRegex(out, r"disc_noisy_centre paired B-A fc: 0\.3500\+-0\.0685: clear gap.*same sign on all 5 seeds")
        self.assertRegex(out, r"box_pose_error paired B-A lift: 0\.0600\+-0\.0877: near-tie")
        for regime in ("disc_noisy_centre", "box_near_perfect", "box_pose_error"):
            self.assertRegex(out, rf"{regime} C_frictionless 0\.0000\+-0\.0000 0\.0000\+-0\.0000 0\.0000\+-0\.0000")


if __name__ == "__main__":
    unittest.main(verbosity=1)
