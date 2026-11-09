#!/usr/bin/env python3
"""Independent regression for batch-11 PR3 CogACT + continual ER toys."""
from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_cogact_common_random_numbers():
    m = load("examples/month-6/act-diffusion/cogact_dit_action_toy.py")
    seed = 7
    # Same seed / regime → identical pack for every arm
    regime = m.REGIMES[0]  # unimodal_short
    pack_a = m.shared_demo_pack(seed, *regime[1:])
    pack_b = m.shared_demo_pack(seed, *regime[1:])
    assert pack_a == pack_b
    # Arms share inputs: fit on identical feats/acts/noises
    feats, acts, noises = pack_a
    params = {arm: m.fit_arm(arm, feats, acts, noises) for arm in m.ARMS}
    # Predictions for A and B on unimodal should be close in MSE to targets
    mses = {}
    for arm, p in params.items():
        ms = [m.mse(m.predict(p, feats[i]), acts[i]) for i in range(len(feats))]
        mses[arm] = sum(ms) / len(ms)
    assert abs(mses["A_mlp_head"] - mses["B_dit_denoiser"]) < 5e-3
    # Multimodal: B should not be worse than A on average across seeds
    mm = m.REGIMES[1]
    a_mses, b_mses, c_mses = [], [], []
    for s in m.SEEDS:
        feats, acts, noises = m.shared_demo_pack(s, *mm[1:])
        for arm, bucket in (
            ("A_mlp_head", a_mses),
            ("B_dit_denoiser", b_mses),
            ("C_quant_tokens", c_mses),
        ):
            p = m.fit_arm(arm, feats, acts, noises)
            ms = [m.mse(m.predict(p, feats[i]), acts[i]) for i in range(len(feats))]
            bucket.append(sum(ms) / len(ms))
    assert sum(b_mses) / len(b_mses) <= sum(a_mses) / len(a_mses) + 1e-9
    assert sum(c_mses) / len(c_mses) > sum(a_mses) / len(a_mses)


def test_er_common_random_numbers_and_costs():
    m = load("examples/month-8/vla-finetune/vla_continual_er_toy.py")
    seed = 11
    t0a, t1a, eva = m.shared_tasks(seed)
    t0b, t1b, evb = m.shared_tasks(seed)
    assert t0a == t0b and t1a == t1b and eva == evb
    # Aggregate over SEEDS like main()
    summary = {}
    for regime in m.REGIMES:
        for arm in m.ARMS:
            avgs, nbts, caps, comps, rps = [], [], [], [], []
            for s in m.SEEDS:
                avg, nbt, cap, comp, rp = m.run_arm(arm, s, regime)
                avgs.append(avg)
                nbts.append(nbt)
                caps.append(cap)
                comps.append(comp)
                rps.append(rp)
            summary[(regime, arm)] = (
                sum(avgs) / len(avgs),
                sum(nbts) / len(nbts),
                caps[0],
                sum(comps) / len(comps),
                rps[0],
            )
    ns_vals = [summary[("no_shift", a)][0] for a in m.ARMS]
    gap = max(ns_vals) - min(ns_vals)
    assert gap < 0.05, gap
    assert summary[("no_shift", "A_sequential")][2] == 0
    assert summary[("no_shift", "B_er_small")][2] == 8
    assert summary[("no_shift", "C_er_large")][2] == 48
    assert (
        summary[("no_shift", "A_sequential")][3]
        < summary[("no_shift", "B_er_small")][3]
        < summary[("no_shift", "C_er_large")][3]
    )
    assert summary[("task_shift", "B_er_small")][1] <= summary[("task_shift", "A_sequential")][1] + 1e-9
    assert summary[("task_shift", "A_sequential")][3] == 320.0
    assert summary[("task_shift", "B_er_small")][3] == 480.0
    assert summary[("task_shift", "C_er_large")][3] == 640.0


def test_expected_files_match():
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    for rel, exp in [
        (
            "examples/month-6/act-diffusion/cogact_dit_action_toy.py",
            "examples/month-6/expected/cogact_dit_action_toy.txt",
        ),
        (
            "examples/month-8/vla-finetune/vla_continual_er_toy.py",
            "examples/month-8/expected/vla_continual_er_toy.txt",
        ),
    ]:
        out = subprocess.check_output(
            [sys.executable, str(ROOT / rel)], cwd=ROOT, env=env, text=True
        )
        assert out == (ROOT / exp).read_text(), rel


def main():
    test_cogact_common_random_numbers()
    test_er_common_random_numbers_and_costs()
    test_expected_files_match()
    print("test_b11_cogact_continual_toys: OK")


if __name__ == "__main__":
    main()
