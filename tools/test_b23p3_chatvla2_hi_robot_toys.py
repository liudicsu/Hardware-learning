#!/usr/bin/env python3
"""Independent contract tests for the ChatVLA-2 and Hi Robot toys."""
import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROC = re.compile(
    r"\bbatch\b|\bPR ?\d+\b|sources? notes?\b|来源说明|来源笔记|this batch|本批|"
    r"this round|本轮|polish|\b[bB]\d{1,2}p(?:\d|ol)\b|opencode|deepseek|"
    r"\bGLM\b|\bMiMo\b|LongCat|MiniMax",
    re.I,
)
FILES = [
    ROOT / "examples/month-9/llm-skill-planning/chatvla2_reasoning_following_toy.py",
    ROOT / "examples/month-9/expected/chatvla2_reasoning_following_toy.txt",
    ROOT / "examples/month-6/policy-evaluation/hi_robot_hierarchical_feedback_toy.py",
    ROOT / "examples/month-6/expected/hi_robot_hierarchical_feedback_toy.txt",
]


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(path):
    return subprocess.check_output([sys.executable, str(path)], cwd=ROOT, text=True)


class Common(unittest.TestCase):
    def test_labels_and_rounding(self):
        for path in FILES[0:1] + FILES[2:3]:
            mod = load(path)
            self.assertIn("tie: identical on every seed", mod.verdict([1.0] * 5, [1.0] * 5))
            v = mod.verdict([1e-12] * 5, [0.0] * 5)
            self.assertIn("numerically zero (floating-point residue), effectively a tie", v)
            self.assertIn("near-tie", mod.verdict([1.0, 3.0, 2.0, 1.5, 2.5], [2.0] * 5))
            self.assertIn("clear gap", mod.verdict([5.0, 5.1, 4.9, 5.2, 5.0], [1.0] * 5))
            self.assertIn("small but consistent", mod.verdict([10.5, 10.6, 10.4, 10.5, 10.5], [10.0] * 5))
            self.assertIn("1 of 5 seeds has the opposite sign", mod.verdict([5.0, 5.0, 5.0, 5.0, -0.5], [0.0] * 5))
            src = path.read_text()
            for marker in ("SEEDS = (0, 1, 2, 3, 4)", "Common random numbers", "本页未运行", "written before the first run", "ROUND_HALF_UP", "NUM_ZERO = 1e-9"):
                self.assertIn(marker, src)

    def test_expected_byte_identical_and_no_process_labels(self):
        for src, exp in ((FILES[0], FILES[1]), (FILES[2], FILES[3])):
            out = run(src)
            self.assertEqual(out, exp.read_text())
            self.assertIsNone(PROC.search(src.read_text()))
            self.assertIsNone(PROC.search(out))


class ChatVLA2(unittest.TestCase):
    def test_hand_calc_and_declared_header(self):
        out = FILES[1].read_text()
        for s in (
            "hand_calc 7+5 = 12.0000",
            "hand_calc untrained_y = -100.0000",
            "hand_calc n_add_pairs = 81",
            "hand_calc card range = 2 to 18",
            "hand_calc mean of in-domain train_mean over seeds = 9.8500",
            "n_id_eq=12 n_ood_eq=20 n_cards=5 n_arith=40 n_add_pairs=81 untrained_y=-100.0000 hand_a=7 hand_b=5",
            "paired B-A pick_acc: 0.6100+-0.0548: clear gap",
            "paired B-A reason_then_pick: 0.9800+-0.0447: clear gap",
            "paired C-B pick_acc: -0.9000+-0.0791: clear gap",
            "paired B-A pick_acc: 0.0000+-0.0000: tie: identical on every seed",
        ):
            self.assertIn(s, out)

    def test_common_random_numbers_shared(self):
        mod = load(FILES[0])
        w0 = mod.build_scenes(0)
        w1 = mod.build_scenes(0)
        self.assertEqual(w0["id_eq"], w1["id_eq"])
        self.assertEqual(w0["ood_eq"], w1["ood_eq"])
        self.assertEqual(w0["id_scenes"], w1["id_scenes"])
        a = mod.run_regime("ood", 0)[0]
        b = mod.run_regime("ood", 0)[0]
        self.assertEqual(a, b)


class HiRobot(unittest.TestCase):
    def test_hand_calc_and_declared_header(self):
        out = FILES[3].read_text()
        for s in (
            "hand_calc task_progress if all trash and the forbidden object are binned = 0.6667",
            "hand_calc task_progress if trash is binned and the forbidden object is left = 1.0000",
            "n_scenes=8 n_steps=6 n_atomic_steps=3 interrupt_after=2 replan_every=1 n_true_trash=2 n_forbidden=1 n_objects=4 hand_trash=2 hand_forbidden=1",
            "paired B-A instruction_acc: 1.0000+-0.0000: clear gap",
            "paired B-A task_progress: 0.3333+-0.0000: clear gap",
            "paired B-A instruction_acc: 0.0000+-0.0000: tie: identical on every seed",
        ):
            self.assertIn(s, out)

    def test_common_random_numbers_shared(self):
        mod = load(FILES[2])
        a = mod.build_scenes("mid_task_correction", 1)
        b = mod.build_scenes("mid_task_correction", 1)
        self.assertEqual(a, b)
        self.assertEqual(mod.run_regime("mid_task_correction", 1), mod.run_regime("mid_task_correction", 1))


if __name__ == "__main__":
    unittest.main()
