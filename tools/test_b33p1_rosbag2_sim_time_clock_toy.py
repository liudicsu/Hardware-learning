#!/usr/bin/env python3
"""Independent contract tests for the rosbag2 simulation-time clock toy; stdlib only."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = "examples/month-8/robot-devops/rosbag2_sim_time_clock_toy.py"
EXP = "examples/month-8/expected/rosbag2_sim_time_clock_toy.txt"
PROCESS = r"(?i)\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|\bGLM\b|\bMiMo\b|LongCat|MiniMax"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


toy = load("rosbag2_sim_time_clock_toy", REL)


def run(rel: str) -> str:
    return subprocess.run(
        [sys.executable, str(ROOT / rel)], check=True, capture_output=True, text=True
    ).stdout


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        self.assertEqual(toy.NUM_ZERO, 1e-9)
        self.assertEqual(toy.SEEDS, (0, 1, 2, 3, 4))
        self.assertAlmostEqual(toy.CLEAR_FRAC, 0.2000)
        self.assertEqual(toy.CLOCK_HZ_DEFAULT, 0)
        self.assertEqual(toy.CLOCK_HZ_BARE, 40)
        self.assertEqual(toy.PLAY_PERIOD_MS, 25)
        self.assertEqual(toy.SESSION_ACTIVE_MS, 250)
        self.assertEqual(toy.SIM_T0_MS, 1000)
        self.assertIn("tie: identical on every seed", toy.verdict([1.0] * 5, [1.0] * 5))
        v = toy.verdict([1e-16, -2e-16, 3e-16, 0.0, 1e-16], [0.0] * 5)
        self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
        self.assertIn("near-tie", toy.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
        self.assertIn("clear gap", toy.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
        self.assertIn("small but consistent", toy.verdict([10.5, 10.6, 10.4, 10.5, 10.5], [10.0] * 5))
        self.assertIn("1 of 5 seeds has the opposite sign", toy.verdict([5.0, 5.0, 5.0, 5.0, -0.5], [0.0] * 5))
        self.assertEqual(toy.num(0.12345), "0.1235")
        self.assertEqual(toy.num(0.0), "0.0000")
        src = (ROOT / REL).read_text()
        for marker in ("Common random numbers", "本页未运行", "declared before the first run"):
            self.assertIn(marker, src)
        # House label order in verdict: exact identity, numerically zero, |m|<=sd, then small vs clear.
        order_src = src[src.index("def verdict") : src.index("def collect")]
        self.assertLess(order_src.index("all(d == 0.0 for d in diffs)"), order_src.index("abs(m) < NUM_ZERO"))
        self.assertLess(order_src.index("abs(m) < NUM_ZERO"), order_src.index("if abs(m) <= s:"))
        self.assertLess(order_src.index("if abs(m) <= s:"), order_src.index("CLEAR_FRAC"))
        self.assertIn("abs(m) < CLEAR_FRAC", order_src)
        self.assertNotRegex(src, PROCESS)
        self.assertNotRegex((ROOT / EXP).read_text(), PROCESS)
        # Official frequencies only.
        self.assertNotIn("const=30", src)
        self.assertNotIn("const=50", src)
        self.assertIn("CLOCK_HZ_BARE = 40", src)
        self.assertIn("CLOCK_HZ_DEFAULT = 0", src)

    def test_stdlib_only(self):
        src = (ROOT / REL).read_text()
        self.assertNotRegex(src, r"^\s*(import|from)\s+(numpy|scipy|torch|pandas|control)",)

    def test_schedule_starts_late(self):
        for seed in toy.SEEDS:
            data, clocks = toy.shared_schedule(seed, toy.CLOCK_FIRST_MS)
            self.assertTrue(clocks)
            self.assertTrue(any(t < clocks[0][0] for t in data), f"seed {seed} has no data before first /clock")
            official = toy.record_arm(data, clocks, official=True)
            lose = toy.record_arm(data, clocks, official=False)
            self.assertEqual(official["zero_then_n_jump"], 0.0)
            self.assertEqual(official["jump_from_zero_ms"], 0.0)
            self.assertGreater(official["dropped"], 0.0)
            self.assertEqual(lose["zero_then_n_jump"], 1.0)
            self.assertEqual(lose["jump_from_zero_ms"], float(toy.SIM_T0_MS))
            self.assertEqual(lose["dropped"], 0.0)
            self.assertEqual(lose["first_stamp_ms"], 0.0)
            self.assertEqual(official["playable"], 1.0)
            self.assertEqual(lose["playable"], 0.0)

    def test_play_clock_contract(self):
        self.assertEqual(toy.play_clock_publishes(0, toy.SESSION_ACTIVE_MS, toy.PLAY_PERIOD_MS), 0)
        self.assertEqual(toy.play_clock_publishes(40, toy.SESSION_ACTIVE_MS, toy.PLAY_PERIOD_MS), 10)
        self.assertEqual(toy.SESSION_ACTIVE_MS // toy.PLAY_PERIOD_MS, 10)
        self.assertEqual(1000 // toy.CLOCK_HZ_BARE, toy.PLAY_PERIOD_MS)
        run_n, pause_n, paused_time, all_paused, further = toy.play_pause_demo()
        self.assertEqual((run_n, pause_n, paused_time, all_paused, further), (4, 4, 100, True, 0))

    def test_expected_output(self):
        out = run(REL)
        expected = (ROOT / EXP).read_text()
        self.assertEqual(out, expected)
        self.assertIn("seeds=5", out)
        self.assertIn("clear_frac=0.2000", out)
        self.assertIn("work_plan 30+25+50+40+35=180", out)
        self.assertIn("hand_calc 1000/40=25", out)
        self.assertIn("hand_calc 250/25=10", out)
        self.assertIn(
            "Arm C lose mode, declared before the first run: write early messages with timestamp 0 "
            "until /clock arrives, then stamp later messages with time N from /clock; "
            "pre-declared as remaining playable / not introducing the official 0-then-N jump",
            out,
        )
        self.assertIn(
            "paired C-A zero_then_n_jump: 1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn(
            "paired C-A jump_from_zero_ms: 1000.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn(
            "paired C-A playable: -1.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn(
            "paired A-C dropped: 4.2000+-0.4472: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn(
            "paired A-C written: -4.2000+-0.4472: clear gap, not a tie (|m| > sd); same sign on all 5 seeds",
            out,
        )
        self.assertIn(
            "alternative clock_first_ms=250 (same seed family, CRN: same data arrivals, later /clock, not adopted)",
            out,
        )
        self.assertIn(
            "The /clock topic needs to be discovered to record with sim time.",
            out,
        )
        self.assertIn("play --clock default=0: publish_count=0 bag_clock_excluded=no", out)
        self.assertIn("play --clock bare const=40:", out)
        self.assertIn("publish_count=10 bag_clock_excluded=yes", out)
        self.assertIn("further_publish_count=0", out)
        self.assertIn("pause_times_all_paused=yes", out)
        self.assertIn("restart_publish_count=4", out)
        self.assertIn("本页未运行", out)
        self.assertIn("以原文为准", out)
        self.assertIn("essentially unplayable", out)

    def test_hook_before_exit(self):
        hook = (ROOT / "examples/month-8/check.sh").read_text()
        self.assertIn("rosbag2_sim_time_clock_toy.txt", hook)
        self.assertLess(hook.index("nora_fastplus_small_vla_toy"), hook.index("rosbag2_sim_time_clock_toy"))
        self.assertLess(hook.index("rosbag2_sim_time_clock_toy"), hook.index("exit $fail"))
        self.assertGreater(hook.index("exit $fail"), hook.rindex("rosbag2_sim_time_clock_toy"))
        after_new = hook[hook.rindex("rosbag2_sim_time_clock_toy") :]
        self.assertIn("exit $fail", after_new)
        self.assertNotRegex(after_new.split("exit $fail")[0], r"python3 \"\$M8/")


if __name__ == "__main__":
    unittest.main()
