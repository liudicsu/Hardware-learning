#!/usr/bin/env python3
"""Independent tests for batch-18 PR3 toys (Knowledge Insulation and VLA-Adapter)."""
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KI_REL = "examples/month-10/flow-matching-policies/knowledge_insulation_flow_toy.py"
AD_REL = "examples/month-10/edge-deploy-checklist/vla_adapter_bridge_attention_toy.py"
sys.path.insert(0, str(ROOT / "examples/month-10/flow-matching-policies"))
sys.path.insert(0, str(ROOT / "examples/month-10/edge-deploy-checklist"))
import knowledge_insulation_flow_toy as ki  # noqa: E402
import vla_adapter_bridge_attention_toy as ad  # noqa: E402


def run(rel: str) -> str:
    return subprocess.check_output(
        [sys.executable, str(ROOT / rel)],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
    )


class TestKnowledgeInsulation(unittest.TestCase):
    def test_stdlib_and_seeds(self):
        src = (ROOT / KI_REL).read_text()
        self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|cv2)")
        self.assertEqual(ki.SEEDS, (0, 1, 2, 3, 4))
        self.assertIn("NUM_ZERO = 1e-9", src)
        self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))
        self.assertIn("Common random numbers", src)
        self.assertIn("本页未运行", src)
        self.assertIn("以论文为准", src)

    def test_crn_and_regimes(self):
        self.assertEqual(list(ki.REGIMES), ["conflict", "coarse_bins", "aligned"])
        a = ki.shared_draws("conflict", 3)
        b = ki.shared_draws("conflict", 3)
        self.assertEqual(a["batches"], b["batches"])
        self.assertEqual(a["A0"], b["A0"])
        c = ki.shared_draws("conflict", 4)
        self.assertNotEqual(a["batches"], c["batches"])

    def test_declared_outputs_and_expected(self):
        out = run(KI_REL)
        expected = (ROOT / "examples/month-10/expected/knowledge_insulation_flow_toy.txt").read_text()
        self.assertEqual(expected, out)
        self.assertIn("no plant integration step (discrete SGD)", out)
        self.assertIn("paired B_insulate-A_naive probe_%: 33.9000+-6.9991: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("paired C_frozen-B_insulate probe_%: 0.0000+-0.0000: tie: identical on every seed", out)
        self.assertIn("paired B_insulate-A_naive control_%: 0.8500+-4.2815: near-tie / small gap, within seed noise (|m| <= sd); 3 of 5 seeds have the opposite sign", out)
        self.assertIn("paired C_frozen-B_insulate control_%: -10.1500+-6.3161: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("paired B_insulate-A_naive fit_mid: 2.1921+-0.6843: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("alternative discrete=full h (first-run head, same seeds) on conflict:", out)
        self.assertIn("paired B_insulate-A_naive probe_%: -12.7500+-12.1861: clear gap, not a tie (|m| > sd); 1 of 5 seeds has the opposite sign", out)
        self.assertIn("not ChatVLA phased alignment; not OneDP one-step regression", out)


class TestVLAAdapter(unittest.TestCase):
    def test_stdlib_and_seeds(self):
        src = (ROOT / AD_REL).read_text()
        self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+(numpy|scipy|torch|pandas|cv2)")
        self.assertEqual(ad.SEEDS, (0, 1, 2, 3, 4))
        self.assertIn("NUM_ZERO = 1e-9", src)
        self.assertLess(src.index("abs(m) < NUM_ZERO"), src.index("if abs(m) <= s:"))
        self.assertIn("Common random numbers", src)
        self.assertIn("本页未运行", src)
        self.assertIn("以论文为准", src)

    def test_crn_and_regimes(self):
        self.assertEqual(list(ad.REGIMES), ["short_id", "need_vl", "precise"])
        a = ad.shared_draws("need_vl", 2)
        b = ad.shared_draws("need_vl", 2)
        self.assertEqual(a["demos"], b["demos"])
        self.assertEqual(a["shuffles"], b["shuffles"])
        c = ad.shared_draws("need_vl", 3)
        self.assertNotEqual(a["demos"], c["demos"])
        self.assertLess(ad.count_params(ad.init_bridge(ad.random.Random(0), 6)), ad.count_params(ad.init_large(ad.random.Random(0), 6)))

    def test_declared_outputs_and_expected(self):
        out = run(AD_REL)
        expected = (ROOT / "examples/month-10/expected/vla_adapter_bridge_attention_toy.txt").read_text()
        self.assertEqual(expected, out)
        self.assertIn("param counts A/B: d_raw=6 2882/489", out)
        self.assertIn("paired B_bridge-A_large success_%: 5.6000+-7.9009: near-tie / small gap, within seed noise (|m| <= sd); no seed has the opposite sign, 2 of 5 equal", out)
        self.assertIn("paired B_bridge-A_large params: -2393.0000+-0.0000: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("paired C_shuffle-B_bridge success_%: -41.9000+-12.6461: clear gap, not a tie (|m| > sd); same sign on all 5 seeds", out)
        self.assertIn("paired B_bridge-A_large success_%: -20.2000+-14.4075: clear gap, not a tie (|m| > sd); 1 of 5 seeds has the opposite sign", out)
        self.assertIn("alternative first-run architecture on short_id", out)
        self.assertIn("B_bridge success_%=11.3000+-9.9411", out)
        self.assertIn("not SmolVLA; not the weights-only budget table; not OpenVLA-OFT", out)


if __name__ == "__main__":
    unittest.main()
