#!/usr/bin/env python3
"""Independent contract tests for the first-/third-angle and executor/callback-group toys; stdlib only."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H1_REL = "examples/month-3/cad-parametric/first_third_angle_projection_toy.py"
H2_REL = "examples/month-4/ros2-graph/executor_callback_group_toy.py"
H1_EXP = "examples/month-3/expected/first_third_angle_projection_toy.txt"
H2_EXP = "examples/month-4/expected/executor_callback_group_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


h1 = load("first_third_angle_projection_toy", H1_REL)
h2 = load("executor_callback_group_toy", H2_REL)


def run(rel: str) -> str:
    return subprocess.run(
        [sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True
    ).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        for mod, rel in ((h1, H1_REL), (h2, H2_REL)):
            self.assertEqual(mod.NUM_ZERO, 1e-9)
            self.assertEqual(mod.SEEDS, (0, 1, 2, 3, 4))
            self.assertAlmostEqual(mod.SMALL_FRAC, 0.2000)
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1e-16, -2e-16, 3e-16, 0.0, 1e-16], [0.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("small but consistent", mod.verdict([10.5, 10.6, 10.4, 10.5, 10.5], [10.0] * 5))
            self.assertIn("1 of 5 seeds has the opposite sign", mod.verdict([5.0, 5.0, 5.0, 5.0, -0.5], [0.0] * 5))
            self.assertEqual(mod.num(0.12345), "0.1235")
            self.assertEqual(mod.num(-0.0), "0.0000")
            src = (ROOT / rel).read_text()
            for marker in ("Common random numbers", "本页未运行", "ROUND_HALF_UP", "written before the first run"):
                self.assertIn(marker, src)
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|rclpy|rclcpp)")
            self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+subprocess")
            self.assertNotIn("subprocess.", src)
            self.assertNotIn("Popen", src)
            # Label order in verdict: exact tie, then numerically zero, then the sd test.
            self.assertLess(src.index("all(d == 0.0 for d in diffs)"), src.index("abs(m) < NUM_ZERO"))
            self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))

    def test_expected_byte_identical_and_no_process_labels(self):
        for rel, exp in ((H1_REL, H1_EXP), (H2_REL, H2_EXP)):
            out = run(rel)
            self.assertEqual(out, run(rel))
            self.assertEqual(out, (ROOT / exp).read_text())
            for text in (out, (ROOT / rel).read_text()):
                self.assertNotRegex(text, PROCESS)

    def test_process_regex_catches_new_words(self):
        for bad in ("polish pass", "来源笔记", "batch 3", "PR2", "PR 3", "本轮", "sources note", "b27p1"):
            self.assertRegex(bad, PROCESS)


class Projection(unittest.TestCase):
    def test_symbol_hand_calc(self):
        first, third = h1.symbol_hand_calc()
        self.assertEqual(first, "first-angle")
        self.assertEqual(third, "third-angle")

    def test_same_convention_exact_and_cross_loses(self):
        for seed in h1.SEEDS:
            obj = h1.shared_object(seed)
            a = h1.run_arm(obj, "A_first")
            b = h1.run_arm(obj, "B_third")
            c = h1.run_arm(obj, "C_cross")
            d = h1.run_arm(obj, "D_ignore")
            for rec in (a, b):
                self.assertEqual(rec["slot_match"], 1.0)
                self.assertEqual(rec["boss_ok"], 1.0)
                self.assertEqual(rec["notch_ok"], 1.0)
                self.assertEqual(rec["rec_boss"], obj["boss_side"])
                self.assertEqual(rec["rec_notch"], obj["notch_face"])
            self.assertEqual(c["slot_match"], 0.0)
            self.assertEqual(c["boss_ok"], 0.0)
            self.assertEqual(c["notch_ok"], 0.0)
            self.assertNotEqual(c["rec_boss"], obj["boss_side"])
            self.assertNotEqual(c["rec_notch"], obj["notch_face"])
            self.assertEqual(d["slot_match"], 0.0)
            self.assertEqual(d["boss_ok"], 0.0)
            self.assertEqual(d["notch_ok"], 1.0)
            self.assertNotEqual(d["rec_boss"], obj["boss_side"])
            self.assertEqual(d["rec_notch"], obj["notch_face"])

    def test_layout_tables(self):
        self.assertEqual(h1.FIRST_ANGLE["left"], "right")
        self.assertEqual(h1.FIRST_ANGLE["right"], "left")
        self.assertEqual(h1.FIRST_ANGLE["above"], "bottom")
        self.assertEqual(h1.FIRST_ANGLE["below"], "top")
        self.assertEqual(h1.THIRD_ANGLE["left"], "left")
        self.assertEqual(h1.THIRD_ANGLE["right"], "right")
        self.assertEqual(h1.THIRD_ANGLE["above"], "top")
        self.assertEqual(h1.THIRD_ANGLE["below"], "bottom")
        self.assertEqual(h1.FIRST_ANGLE["centre"], "front")
        self.assertEqual(h1.THIRD_ANGLE["centre"], "front")

    def test_expected_markers(self):
        out = (ROOT / H1_EXP).read_text()
        for x in (
            "hand_calc symbol: two concentric circles (solid inner) + isosceles trapezoid, shortest side away from the circles => first-angle",
            "hand_calc symbol: two concentric circles (solid inner) + isosceles trapezoid, shortest side towards the circles => third-angle",
            "hand_calc 20 percent small-vs-clear factor = 0.2000",
            "paired B-A slot_match: 0.0000+-0.0000: tie: identical on every seed",
            "paired B-A boss_ok: 0.0000+-0.0000: tie: identical on every seed",
            "paired C-A slot_match: -1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "paired C-A boss_ok: -1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "paired C-A notch_ok: -1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "paired D-A boss_ok: -1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "paired D-A notch_ok: 0.0000+-0.0000: tie: identical on every seed",
            "named alternative invert_symbol",
            "本页未运行",
            "以原文为准",
        ):
            self.assertIn(x, out)


class Executor(unittest.TestCase):
    def test_no_sync_tie_and_sync_deadlock(self):
        for seed in h2.SEEDS:
            _ = seed
            no_sync = {arm: h2.run_arm(arm, False, 0) for arm in h2.ARMS}
            for arm in h2.ARMS:
                self.assertEqual(no_sync[arm]["timer_done"], 4.0)
                self.assertEqual(no_sync[arm]["sub_done"], 20.0)
                self.assertEqual(no_sync[arm]["starved_ticks"], 0.0)
                self.assertEqual(no_sync[arm]["deadlock"], 0.0)
            sync = {arm: h2.run_arm(arm, True, h2.SVC_WORK_LONG) for arm in h2.ARMS}
            for arm in ("A_single", "A_mt_default", "C_shared_me"):
                self.assertEqual(sync[arm]["req_done"], 0.0)
                self.assertEqual(sync[arm]["handler_progress"], 0.0)
                self.assertEqual(sync[arm]["sub_done"], 0.0)
                self.assertEqual(sync[arm]["deadlock"], 1.0)
                self.assertEqual(sync[arm]["starved_ticks"], 39.0)
            b = sync["B_two_groups"]
            self.assertEqual(b["timer_done"], 4.0)
            self.assertEqual(b["req_done"], 4.0)
            self.assertEqual(b["sub_done"], 20.0)
            self.assertEqual(b["handler_progress"], 32.0)
            self.assertEqual(b["starved_ticks"], 0.0)
            self.assertEqual(b["deadlock"], 0.0)
            alt = h2.run_arm("B_reentrant", True, h2.SVC_WORK_LONG)
            for metric in ("timer_done", "req_done", "sub_done", "handler_progress", "starved_ticks", "deadlock"):
                self.assertEqual(alt[metric], b[metric])

    def test_default_group_is_mutually_exclusive(self):
        a = h2.arm_config("A_mt_default")
        self.assertEqual(a["threads"], 3)
        self.assertEqual(a["timer"], ("ME", "default"))
        self.assertEqual(a["service"], ("ME", "default"))
        self.assertEqual(a["sub"], ("ME", "default"))
        c = h2.arm_config("C_shared_me")
        self.assertEqual(c["timer"], c["service"])
        self.assertEqual(c["timer"][0], "ME")
        self.assertNotEqual(c["timer"][1], "default")
        b = h2.arm_config("B_two_groups")
        self.assertEqual(len({b["timer"], b["service"], b["sub"]}), 3)

    def test_no_invented_executor_type(self):
        src = (ROOT / H2_REL).read_text()
        self.assertNotRegex(src, r"EventsExecutor|events_executor")
        self.assertIn("WaitSet", src)
        self.assertIn("rclc", src)
        self.assertIn("Static Single-Threaded", src)
        self.assertIn("will always cause a deadlock", src)

    def test_expected_markers(self):
        out = (ROOT / H2_EXP).read_text()
        for x in (
            "hand_calc 20 percent small-vs-clear factor = 0.2000",
            "hand_calc ticks in horizon = 40",
            "hand_calc subscription arrivals in horizon = 20",
            "hand_calc timer firings in horizon = 4",
            "declared N_THREADS=3",
            "paired A_mt_default-A_single timer_done: 0.0000+-0.0000: tie: identical on every seed",
            "paired B-A_single sub_done: 0.0000+-0.0000: tie: identical on every seed",
            "paired B-A_single sub_done: 20.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "paired B-A_single starved_ticks: -39.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "paired C-B handler_progress: -32.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            "paired C-A_mt_default handler_progress: 0.0000+-0.0000: tie: identical on every seed",
            "named alternative B_reentrant",
            "本页未运行",
            "以文档为准",
        ):
            self.assertIn(x, out)


if __name__ == "__main__":
    unittest.main()
