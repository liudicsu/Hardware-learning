#!/usr/bin/env python3
"""Independent contract tests for batch-13 PR3 MAP-VLA memory-prompt + Diffusion Forcing toys; stdlib only."""
from __future__ import annotations

import importlib.util
import math
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MV_REL = "examples/month-10/intervention-logging/map_vla_memory_prompt_toy.py"
DF_REL = "examples/month-10/flow-matching-policies/diffusion_forcing_token_noise_toy.py"
SIGNED_ZERO = r"(?<![+\d.e])-0\.0+(?![\d.e])"
PAIR = re.compile(r": (-?\d+\.\d+(?:e-?\d+)?)\+-(\d+\.\d+(?:e-?\d+)?): ")


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


mv = load("map_vla_memory_prompt_toy", MV_REL)
df = load("diffusion_forcing_token_noise_toy", DF_REL)


def run(rel: str) -> str:
    return subprocess.run([sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True).stdout


def check_labels(case: unittest.TestCase, out: str) -> None:
    for line in out.splitlines():
        case.assertNotRegex(line, SIGNED_ZERO)
        if "tie: identical on every seed" in line:
            case.assertIn("0.0000+-0.0000", line)
            continue
        mm = PAIR.search(line)
        if "numerically zero" in line:
            case.assertTrue(mm and abs(float(mm.group(1))) < 1e-9 and float(mm.group(2)) < 1e-9, line)
            case.assertTrue(line.endswith("numerically zero (floating-point residue), effectively a tie"), line)
            case.assertNotRegex(line, r"sign|consistent|clear")
            continue
        if "near-tie" in line:
            case.assertTrue(mm and abs(float(mm.group(1))) <= float(mm.group(2)), line)
            case.assertRegex(line, r"same sign on all 5 seeds|of 5 seeds ha(s|ve) the opposite sign|no seed has the opposite sign")
        if "consistent gap" in line or "clear gap" in line:
            case.assertTrue(mm and abs(float(mm.group(1))) > float(mm.group(2)), line)
            case.assertRegex(line, r"same sign on all 5 seeds|of 5 seeds ha(s|ve) the opposite sign|no seed has the opposite sign")
            if "opposite sign" in line and "no seed" not in line:
                opp = int(re.search(r"(\d) of 5 seeds ha", line).group(1))
                case.assertLessEqual(opp, 1, "a consistent label needs a clear same-sign majority")


def paired(out: str, prefix: str):
    line = next(l for l in out.splitlines() if l.startswith(prefix))
    mm = PAIR.search(line)
    return float(mm.group(1)), float(mm.group(2)), line


class NumericallyZeroRule(unittest.TestCase):
    """Rule shared by both toys: |m| < 1e-9 and sd < 1e-9 -> numerically zero, checked before |m| vs sd."""

    def test_threshold_boundary_both_toys(self):
        for mod in (mv, df):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            zero = [0.0] * 5
            tiny = [0.9e-9, 0.95e-9, 0.9e-9, 0.92e-9, 0.93e-9]
            v = mod.verdict(tiny, zero)
            self.assertTrue(v.endswith("numerically zero (floating-point residue), effectively a tie"), v)
            self.assertNotIn("sign", v)
            v = mod.verdict([x + 0.2e-9 for x in tiny], zero)
            self.assertNotIn("numerically zero", v)
            self.assertIn("clear gap", v)
            self.assertIn("same sign on all 5 seeds", v)
            v = mod.verdict([3e-9, -3e-9, 2e-9, -2e-9, 1e-10], zero)
            self.assertNotIn("numerically zero", v)
            self.assertEqual(mod.verdict([0.25] * 5, [0.25] * 5), "0.0000+-0.0000: tie: identical on every seed")
            src = (ROOT / (MV_REL if mod is mv else DF_REL)).read_text()
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))

    def test_small_values_never_print_signed_zero(self):
        for mod in (mv, df):
            self.assertEqual(mod.num(-1e-5), "-1.000e-05")
            self.assertEqual(mod.num(0.0), "0.0000")


class MapVla(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(MV_REL)

    def test_constants_seeds_scope(self):
        self.assertEqual(mv.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / MV_REL).read_text()
        for x in ("本页未运行", "以论文为准", "Common random numbers"):
            self.assertIn(x, text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")

    def test_prompt_is_mean_residual_of_frozen_base(self):
        reg = mv.REGIMES[0]
        demo = mv.demos(reg, 1)
        w = mv.fit_base(demo)
        prompts = mv.tune_prompts(w, demo, len(reg[1]))
        for k in range(len(reg[1])):
            rows = [(s, c, a) for tr in demo for s, c, a, kk in tr if kk == k]
            r = [sum(a[i] - mv.policy(w, s, c)[i] for s, c, a in rows) / len(rows) for i in range(2)]
            self.assertAlmostEqual(prompts[k][0], r[0], places=12)
            self.assertAlmostEqual(prompts[k][1], r[1], places=12)
            # least-squares property of a constant offset on the unclipped residuals
            def sse(off):
                return sum((a[0] - mv.policy(w, s, c)[0] - off[0]) ** 2 + (a[1] - mv.policy(w, s, c)[1] - off[1]) ** 2 for s, c, a in rows)
            for d in ((0.01, 0.0), (0.0, -0.01)):
                self.assertLess(sse(prompts[k]), sse((prompts[k][0] + d[0], prompts[k][1] + d[1])))

    def test_ambiguous_look_hides_the_stage_from_the_base(self):
        reg = mv.REGIMES[0]
        self.assertEqual(reg[2][0], reg[2][2])
        w = mv.fit_base(mv.demos(reg, 0))
        zero = [0.0] * mv.LOOKS
        s = (0.6, 0.4)
        self.assertEqual(mv.policy(w, s, mv.look(zero, 0, reg[2], 0.0)), mv.policy(w, s, mv.look(zero, 2, reg[2], 0.0)))

    def test_retrieval_respects_neighbouring_stage_rule(self):
        reg = mv.REGIMES[0]
        demo = mv.demos(reg, 2)
        hist = [demo[0][j][0] for j in range(10, 14)]
        for k_cur in range(4):
            k, ref = mv.retrieve(demo, hist, lambda kk: abs(kk - k_cur) <= 1)
            self.assertLessEqual(abs(k - k_cur), 1)
            self.assertEqual(len(ref), mv.H)

    def test_ensemble_weight_is_softmax(self):
        for dm, db in ((0.1, 0.3), (2.0, 0.5), (0.0, 0.0)):
            alpha = 1.0 / (1.0 + math.exp(dm - db))
            self.assertAlmostEqual(alpha, math.exp(-dm) / (math.exp(-dm) + math.exp(-db)), places=14)

    def test_common_random_numbers(self):
        reg = mv.REGIMES[0]
        self.assertEqual(mv.episode_draws(reg, 2, 5), mv.episode_draws(reg, 2, 5))
        self.assertNotEqual(mv.episode_draws(reg, 2, 5), mv.episode_draws(reg, 3, 5))
        self.assertEqual(mv.demos(reg, 4), mv.demos(reg, 4))

    def test_labels_and_key_lines(self):
        out = self.out
        check_labels(self, out)
        m, s, line = paired(out, "ambiguous_long paired B-A stage")
        self.assertTrue(m > s and "clear gap" in line and "same sign on all 5 seeds" in line, line)
        for metric in ("stage", "full", "steps"):
            self.assertIn("near-tie", paired(out, f"distinct_long paired B-A {metric}")[2])
        self.assertIn("single_stage paired B-A stage: 0.0000+-0.0000: tie: identical on every seed", out)
        self.assertIn("single_stage paired B-A full: 0.0000+-0.0000: tie: identical on every seed", out)
        for regime in ("ambiguous_long", "noisy_retrieval"):
            m, s, line = paired(out, f"{regime} paired C-B stage")
            self.assertTrue(m < 0 and abs(m) > s and "same sign on all 5 seeds" in line, line)
        hit = lambda r: float(re.search(rf"^{r} B_map .* (\d\.\d+)\+-\d\.\d+$", out, re.M).group(1))
        self.assertLess(hit("noisy_retrieval"), hit("ambiguous_long"))


class DiffusionForcing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = run(DF_REL)
        data, draws = df.training_draws(0)
        cls.models = {arm: df.train(arm, data, draws) for arm in df.ARMS}

    def test_constants_seeds_scope(self):
        self.assertEqual(df.SEEDS, (0, 1, 2, 3, 4))
        text = (ROOT / DF_REL).read_text()
        for x in ("本页未运行", "以论文为准", "Common random numbers"):
            self.assertIn(x, text)
        self.assertNotRegex(text, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas)")

    def test_cosine_schedule(self):
        self.assertEqual(df.ABAR[0], 1.0)
        self.assertEqual(df.ABAR[df.K], 0.0)
        self.assertTrue(all(a > b for a, b in zip(df.ABAR, df.ABAR[1:])))
        self.assertAlmostEqual(df.ABAR[1], math.cos(math.pi / 20) ** 2, places=15)
        self.assertEqual(df.noisy((0.3, -0.2), 0, (5.0, 5.0)), (0.3, -0.2))
        self.assertEqual(df.noisy((0.3, -0.2), df.K, (5.0, -1.0)), (5.0, -1.0))

    def test_training_noise_patterns(self):
        keys = {arm: set(m) for arm, m in self.models.items()}
        self.assertTrue(all(kp == 0 for kp, _ in keys["A_teacher"]))
        self.assertTrue(all(kp == kc for kp, kc in keys["C_fullseq"]))
        self.assertEqual(keys["B_dforcing"], {(i, j) for i in range(df.K + 1) for j in range(df.K + 1)})

    def test_sampler_needs_only_trained_patterns(self):
        x = (0.5, 0.5)
        for arm in df.ARMS:
            y = df.sample_token(self.models[arm], arm, x, (0.1, -0.2), (0.3, 0.4))
            self.assertTrue(all(math.isfinite(v) for v in y))

    def test_sampler_affine_in_previous_token(self):
        for arm in df.ARMS:
            z = ((0.2, -0.1), (0.4, 0.3))
            f = lambda p: df.sample_token(self.models[arm], arm, p, *z)
            a, b, c = f((0.1, 0.2)), f((0.7, -0.4)), f((0.4, -0.1))
            self.assertAlmostEqual(c[0], (a[0] + b[0]) / 2, places=10)
            self.assertAlmostEqual(c[1], (a[1] + b[1]) / 2, places=10)

    def test_stability_criterion_matches_divergence(self):
        out = self.out
        rho = {arm: [float(x) for x in re.search(rf"^{arm} one-token gain rho\(G\) per seed: (.*)$", out, re.M).group(1).split()] for arm in df.ARMS}
        self.assertTrue(all(r > 1 for r in rho["A_teacher"]))
        self.assertTrue(all(r < 1 for r in rho["B_dforcing"] + rho["C_fullseq"]))
        self.assertRegex(out, r"past_horizon A_teacher div=1\.0000\+-0\.0000")
        self.assertRegex(out, r"past_horizon B_dforcing div=0\.0000\+-0\.0000")
        self.assertRegex(out, r"B_dforcing k_small=0: in_horizon mse=\S+ past_horizon div=1\.0000\+-0\.0000")
        k0 = [float(x) for x in re.search(r"^B_dforcing k_small=0 rho\(G\) per seed: ([\d. ]+) \(", out, re.M).group(1).split()]
        self.assertTrue(all(r > 1 for r in k0))

    def test_common_random_numbers(self):
        self.assertEqual(df.episode_draws("guided_s8", 2, 5), df.episode_draws("guided_s8", 2, 5))
        self.assertNotEqual(df.episode_draws("guided_s8", 2, 5), df.episode_draws("guided_s8", 3, 5))
        a, b = df.training_draws(1), df.training_draws(1)
        self.assertEqual(a, b)

    def test_labels_and_key_lines(self):
        out = self.out
        check_labels(self, out)
        m, s, line = paired(out, "in_horizon paired B-A mse")
        self.assertTrue(m > s and "same sign on all 5 seeds" in line, "B loses in-horizon: " + line)
        self.assertIn("near-tie", paired(out, "in_horizon paired B(k_small=0)-A mse")[2])
        m, s, line = paired(out, "past_horizon paired B-A amp")
        self.assertTrue(m < 0 and abs(m) > s and "same sign on all 5 seeds" in line, line)
        self.assertIn("past_horizon paired C-B div: 0.0000+-0.0000: tie: identical on every seed", out)
        m, s, line = paired(out, "guided_s8 paired B-A goal")
        self.assertTrue(m > s, "teacher forcing beats B at S=8: " + line)
        m, s, line = paired(out, "guided_s32 paired B-A goal")
        self.assertTrue(m < 0 and abs(m) > s, line)
        for regime in ("guided_s8", "guided_s32"):
            m, s, line = paired(out, f"{regime} paired C-B goal")
            self.assertTrue(m > 0, "full-sequence does not beat B here (disclosed): " + line)


if __name__ == "__main__":
    unittest.main(verbosity=1)
