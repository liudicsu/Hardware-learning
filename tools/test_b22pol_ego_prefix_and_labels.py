#!/usr/bin/env python3
"""Independent tests for the EgoVLA pre-fix solver comparison and the site-wide toy label sweep; stdlib only."""
from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EG_REL = "examples/month-11/umi-style-collection/egovla_human_pretrain_retarget_toy.py"
EG_EXP = "examples/month-11/expected/egovla_human_pretrain_retarget_toy.txt"
LABELS = re.compile(r"(?i)\bbatch[- ]\d+\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|"
                    r"\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax")


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


eg = load("egovla_human_pretrain_retarget_toy", EG_REL)


def solve(M, v):
    n = len(v)
    a = [row[:] + [v[i]] for i, row in enumerate(M)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(a[r][c]))
        a[c], a[p] = a[p], a[c]
        for r in range(n):
            if r != c:
                f = a[r][c] / a[c][c]
                for k in range(c, n + 1):
                    a[r][k] -= f * a[c][k]
    return [a[i][n] / a[i][i] for i in range(n)]


def normal_eq(X, Y, lam, fill_row):
    d = len(X[0])
    M = [[0.0] * (d + 1) for _ in range(d + 1)]
    v = [0.0] * (d + 1)
    for x, y in zip(X, Y):
        for i in range(d):
            for j in range(d):
                M[i][j] += x[i] * x[j]
            M[i][d] += x[i]
            if fill_row:
                M[d][i] += x[i]
            v[i] += x[i] * y
        M[d][d] += 1.0
        v[d] += y
    for i in range(d):
        M[i][i] += lam
    M[d][d] += 1e-6
    return M, v


class PreFix(unittest.TestCase):
    def setUp(self):
        th, _, X, _, _, _ = eg.draws_for(0, 0)
        self.th, self.X = th, X
        self.Y = [sum(a * b for a, b in zip(x, th)) + eg.B_ROBOT for x in X]

    def test_prefix_is_the_unfilled_row_and_corrected_is_filled(self):
        for fill, fn in ((False, eg.ridge_fit_prefix), (True, eg.ridge_fit)):
            ref = solve(*normal_eq(self.X, self.Y, 0.0, fill))
            th, b = fn(self.X, self.Y, [0.0] * eg.D, 0.0)
            self.assertLess(max(abs(p - q) for p, q in zip(ref, th + [b])), 1e-9)

    def test_printed_solver_check(self):
        out = (ROOT / EG_EXP).read_text()
        tp, bp = eg.ridge_fit_prefix(self.X, self.Y, [0.0] * eg.D, 0.0)
        tc, bc = eg.ridge_fit(self.X, self.Y, [0.0] * eg.D, 0.0)
        ep = max(abs(a - b) for a, b in zip(tp, self.th))
        ec = max(abs(a - b) for a, b in zip(tc, self.th))
        self.assertGreater(ep, 0.05)
        self.assertLess(ec, 1e-6)
        self.assertLess(abs(bc - eg.B_ROBOT), 1e-6)
        line = (f"pre-fix max |theta error| {eg.num(ep)} |b error| {eg.num(abs(bp - eg.B_ROBOT))}; "
                f"corrected max |theta error| {eg.num(ec)} |b error| {eg.num(abs(bc - eg.B_ROBOT))}")
        self.assertIn(line, out)

    def test_prefix_comparison_line_and_label(self):
        out = (ROOT / EG_EXP).read_text()
        self.assertIn("漏填对称截距行的错误版本，仅作对照", out)
        self.assertIn("erroneous version, kept only for comparison", out)
        self.assertIn("pre-fix paired B(half_data)-B(in_domain_full) long_sr: 0.0400+-0.1012: near-tie", out)
        self.assertIn("paired B(half_data)-B(in_domain_full) long_sr: -0.1620+-0.0841: clear gap", out)
        lines = out.split("\n")
        k = next(i for i, l in enumerate(lines) if l.startswith("No winner beyond the declared prior"))
        self.assertTrue(lines[k - 3].startswith("comparison only, not an official verdict"))


class Labels(unittest.TestCase):
    def test_no_process_label_in_any_toy_or_output(self):
        files = list((ROOT / "examples").rglob("*.py")) + list((ROOT / "examples").glob("month-*/expected/*.txt"))
        self.assertGreater(len(files), 300)
        hits = [f"{p.relative_to(ROOT)}:{n}" for p in files for n, l in enumerate(p.read_text(encoding="utf-8").split("\n"), 1) if LABELS.search(l)]
        self.assertEqual(hits, [])

    def test_regex_has_no_false_positive_on_training_batches(self):
        for ok in ("BATCH=8", "batch i is the same set", "Full-batch gradient descent", "before any VQA batch", "ROUND_HALF_UP"):
            self.assertIsNone(LABELS.search(ok))
        for bad in ("batch-13 lead-lag toy", "Batch-19 polish", "this round", "opencode DeepSeek", "PR3", "b22p3"):
            self.assertIsNotNone(LABELS.search(bad))


if __name__ == "__main__":
    unittest.main()
