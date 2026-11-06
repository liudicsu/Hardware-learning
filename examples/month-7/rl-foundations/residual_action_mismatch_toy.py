#!/usr/bin/env python3
"""Synthetic two-stage tracker transfer, NOT humanoid PPO or ASAP reproduction.
Equal B-data: all arms see the SAME 160 noisy (u,v,acceleration) transitions.
Fit a delta ACTION in nominal A action coordinates; freeze it in SIM tuning;
all real-proxy B evaluations call the tuned policy alone, never the delta model.
"""
from __future__ import annotations
import itertools
import math
import random
import statistics

SEED = 720
SEEDS = tuple(range(SEED, SEED + 5))
DT = 0.04
BUDGET = 160
STEPS = 100
A = (1.0, 0.5, 0.0, 0.0)  # gain, damping, nonlinear drag, torque-bias proxy


def plant(params):
    g, d, c, b = params
    return lambda u, v: g * u - d * v - c * v * abs(v) + b


def reference(phase, omega, amp):
    return tuple((amp * math.sin(omega * i * DT + phase),
                  amp * omega * math.cos(omega * i * DT + phase),
                  -amp * omega ** 2 * math.sin(omega * i * DT + phase))
                 for i in range(STEPS))


def trajectories(seed, count):
    rng = random.Random(seed)
    return tuple(reference(rng.uniform(-1, 1), rng.uniform(0.6, 1.8),
                           rng.uniform(0.3, 0.7)) for _ in range(count))


def action(policy, q, v, ref):
    kp, kd, ff, bias = policy
    x, vel, acc = ref
    return max(-5.0, min(5.0, kp * (x - q) + kd * (vel - v) + ff * acc + bias))


def rollout(policy, model, refs):
    q, v = refs[0][0], refs[0][1]
    errors, transitions = [], []
    for ref in refs:
        u = action(policy, q, v, ref)
        acc = model(u, v)
        transitions.append((u, v, acc))
        errors.append(abs(q - ref[0]))
        v += DT * acc
        q += DT * v
    return sum(errors) / len(errors), max(errors), transitions


def objective(policy, models, refs):
    # Equal 4 simulation trajectories/candidate for all arms; no B evaluation.
    return sum(rollout(policy, model, trajectory)[0]
               for model, trajectory in zip(models, refs)) / len(refs)


def tune(initial, models, refs, pretrain=False):
    if pretrain:
        candidates = itertools.product((4.0, 8.0, 12.0), (2.0, 4.0, 6.0),
                                       (0.6, 1.0, 1.4), (0.0,))
    else:
        kp, kd, ff, _ = initial
        candidates = itertools.product((kp * 0.75, kp, kp * 1.25),
                                       (kd * 0.75, kd, kd * 1.25),
                                       (ff * 0.75, ff, ff * 1.25), (-0.3, 0.0, 0.3))
    return min(candidates, key=lambda p: objective(p, models, refs))


def fit(rows, targets):
    """Small ridge least squares via pivoted Gaussian elimination (stdlib)."""
    n = len(rows[0])
    mat = [[sum(x[i] * x[j] for x in rows) + (1e-5 if i == j else 0)
            for j in range(n)] + [sum(x[i] * y for x, y in zip(rows, targets))]
           for i in range(n)]
    for i in range(n):
        pivot = max(range(i, n), key=lambda k: abs(mat[k][i]))
        mat[i], mat[pivot] = mat[pivot], mat[i]
        scale = mat[i][i]
        assert abs(scale) > 1e-12
        mat[i] = [v / scale for v in mat[i]]
        for j in range(n):
            if j != i:
                scale = mat[j][i]
                mat[j] = [a - scale * b for a, b in zip(mat[j], mat[i])]
    return tuple(row[-1] for row in mat)


def adapt(data):
    # SysID's explicit linear physical family omits nonlinear drag on purpose.
    linear_rows = [(u, -v, 1.0) for u, v, _ in data]
    g, d, bias = fit(linear_rows, [acc for _, _, acc in data])
    sysid = plant((g, d, 0.0, bias))
    # DR uses exactly those rows, residual spread -> lesson-defined wide bounds.
    rms = math.sqrt(sum((acc - sysid(u, v)) ** 2 for u, v, acc in data) / len(data))
    width = max(0.08, 2 * rms)
    dr = tuple(plant((max(0.2, g + sign * width), max(0.0, d - sign * width),
                      0.0, bias + other * width)) for sign, other in
               ((-1, -1), (-1, 1), (1, -1), (1, 1)))
    # Since g_A=1, delta-action target = observed acceleration - a_A(u,v).
    # This is an action correction, NOT an identified mass/friction parameter.
    features = [(u, v, v * abs(v), 1.0) for u, v, _ in data]
    coeff = fit(features, [acc - plant(A)(u, v) for u, v, acc in data])
    def aligned_sim(u, v):
        delta_action = sum(c * f for c, f in zip(coeff, (u, v, v * abs(v), 1.0)))
        return plant(A)(u + delta_action, v)
    return {"SysID-retune": (sysid,) * 4, "DR-widen": dr,
            "residual-action": (aligned_sim,) * 4}


def deploy(policy, real_proxy, eval_refs):
    # The signature deliberately has NO learned delta argument.
    results = [rollout(policy, real_proxy, refs) for refs in eval_refs]
    mae = statistics.mean(r[0] for r in results)
    fall_proxy = sum(r[1] > 0.35 for r in results) / len(results)
    return mae, fall_proxy


def main():
    train_refs = trajectories(71, 4)
    base = tune(None, (plant(A),) * 4, train_refs, pretrain=True)
    assert len(fit([(1, 0), (0, 1)], [2, 3])) == 2
    print(f"pretrained_A_policy={base} dt_s={DT:.2f} seeds={len(SEEDS)}")
    print(f"PlantB_samples_per_arm={BUDGET}/{BUDGET}/{BUDGET}; same_data_object=yes")
    print("finetune_sim_steps_per_arm=81_candidates*4_trajectories*100_steps")
    print("seed arm zero_shot_MAE_m tuned_MAE_m fall_proxy_episodes/5")
    summary = {name: [] for name in ("SysID-retune", "DR-widen", "residual-action")}
    for seed in SEEDS:
        rng = random.Random(seed)
        real = plant((rng.uniform(0.65, 0.95), rng.uniform(0.3, 0.8),
                      rng.uniform(0.8, 2.5), rng.uniform(-0.4, 0.4)))
        raw = []
        for refs in train_refs:
            remaining = BUDGET - len(raw)
            if remaining <= 0:
                break
            raw.extend(rollout(base, real, refs[:remaining])[2])
        data = tuple((u, v, a + rng.gauss(0, 0.025)) for u, v, a in raw)
        assert len(data) == BUDGET
        # Reserved seed namespace: neither calibration nor tuning sees eval refs.
        eval_refs = trajectories(seed + 10000, 5)
        zero, _ = deploy(base, real, eval_refs)
        for name, sims in adapt(data).items():
            policy = tune(base, sims, train_refs)
            mae, fall = deploy(policy, real, eval_refs)
            summary[name].append(mae)
            print(f"{seed} {name} {zero:.5f} {mae:.5f} {round(fall * 5)}/5")
    print("arm MAE_mean_m population_sd_m min_m max_m (across_5_seeds)")
    for name, values in summary.items():
        print(f"{name} {statistics.mean(values):.5f} {statistics.pstdev(values):.5f} "
              f"{min(values):.5f} {max(values):.5f}")
    print("deploy=policy_only_without_delta_model; residual_is_not_dynamics_SysID")
    print("model_families_differ; no_universal_winner; fall_proxy_not_humanoid_fall; Isaac_real_robot_not_run")


if __name__ == "__main__":
    main()
